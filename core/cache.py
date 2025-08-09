#!/usr/bin/env python3
"""
MindNext Hooks - Core Cache System
==================================

Core cache service for high-performance data caching with LRU eviction and TTL support.
This is a SYSTEM SERVICE, not an action component.

Features:
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) expiration
- Thread-safe operations
- Statistics and monitoring
- Configurable size limits
"""

import threading
import time
from collections import OrderedDict
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json


class CoreCache:
    """
    Core Cache System - High-performance caching service
    
    This is a system-level service that provides centralized cache management
    for all components in the MindNext Hooks system.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl_minutes: int = 60):
        self.max_size = max_size
        self.default_ttl_minutes = default_ttl_minutes
        
        # LRU Cache with TTL
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'expirations': 0,
            'created_at': datetime.now()
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize system cache entries
        self._init_system_cache()
    
    def _init_system_cache(self):
        """Initialize system-level cache entries"""
        system_entries = {
            'system_config': {
                'description': 'System configuration cache',
                'ttl_minutes': 30
            },
            'rule_cache': {
                'description': 'Rule processing cache',
                'ttl_minutes': 15
            },
            'session_context': {
                'description': 'Session context cache',
                'ttl_minutes': 120
            }
        }
        
        # Pre-populate with metadata only (actual data comes later)
        for key, config in system_entries.items():
            self._set_internal(f"_meta_{key}", config, config.get('ttl_minutes', self.default_ttl_minutes))
    
    def _set_internal(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        """Internal set method (no locking, no stats)"""
        if ttl_minutes is None:
            ttl_minutes = self.default_ttl_minutes
        
        expire_time = datetime.now() + timedelta(minutes=ttl_minutes)
        
        # Remove if exists and re-add at end (LRU)
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.max_size:
            # Evict least recently used
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1
        
        self.cache[key] = {
            'value': value,
            'expire_time': expire_time,
            'created_at': datetime.now(),
            'access_count': 0,
            'ttl_minutes': ttl_minutes
        }
    
    # === Core Cache Operations ===
    
    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Set cache entry with optional TTL"""
        with self._lock:
            try:
                self._set_internal(key, value, ttl_minutes)
                self.stats['sets'] += 1
                
                return {
                    'success': True,
                    'key': key,
                    'ttl_minutes': ttl_minutes or self.default_ttl_minutes,
                    'expires_at': self.cache[key]['expire_time'].isoformat()
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'key': key
                }
    
    def get(self, key: str) -> Dict[str, Any]:
        """Get cache entry (updates LRU order)"""
        with self._lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return {
                    'success': False,
                    'key': key,
                    'error': 'Key not found'
                }
            
            entry = self.cache[key]
            
            # Check if expired
            if datetime.now() > entry['expire_time']:
                del self.cache[key]
                self.stats['expirations'] += 1
                self.stats['misses'] += 1
                return {
                    'success': False,
                    'key': key,
                    'error': 'Key expired'
                }
            
            # Update LRU order and access stats
            self.cache.move_to_end(key)
            entry['access_count'] += 1
            entry['last_accessed'] = datetime.now()
            self.stats['hits'] += 1
            
            return {
                'success': True,
                'key': key,
                'value': entry['value'],
                'created_at': entry['created_at'].isoformat(),
                'expires_at': entry['expire_time'].isoformat(),
                'access_count': entry['access_count']
            }
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get just the value (convenience method)"""
        result = self.get(key)
        return result.get('value', default)
    
    def exists(self, key: str) -> Dict[str, Any]:
        """Check if key exists and is not expired"""
        with self._lock:
            if key not in self.cache:
                return {'exists': False, 'key': key}
            
            entry = self.cache[key]
            if datetime.now() > entry['expire_time']:
                del self.cache[key]
                self.stats['expirations'] += 1
                return {'exists': False, 'key': key, 'reason': 'expired'}
            
            return {
                'exists': True,
                'key': key,
                'expires_at': entry['expire_time'].isoformat(),
                'ttl_remaining_minutes': (entry['expire_time'] - datetime.now()).total_seconds() / 60
            }
    
    def delete(self, key: str) -> Dict[str, Any]:
        """Delete cache entry"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.stats['deletes'] += 1
                return {
                    'success': True,
                    'key': key,
                    'message': 'Key deleted'
                }
            else:
                return {
                    'success': False,
                    'key': key,
                    'error': 'Key not found'
                }
    
    def clear_all(self) -> Dict[str, Any]:
        """Clear all cache entries"""
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            
            return {
                'success': True,
                'cleared_count': count,
                'message': 'All cache entries cleared'
            }
    
    def cleanup_expired(self) -> Dict[str, Any]:
        """Remove all expired entries"""
        with self._lock:
            expired_keys = []
            now = datetime.now()
            
            for key, entry in list(self.cache.items()):
                if now > entry['expire_time']:
                    expired_keys.append(key)
                    del self.cache[key]
            
            self.stats['expirations'] += len(expired_keys)
            
            return {
                'success': True,
                'expired_count': len(expired_keys),
                'expired_keys': expired_keys
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / max(1, total_requests)) * 100
            
            uptime = datetime.now() - self.stats['created_at']
            
            return {
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate_percent': round(hit_rate, 2),
                'statistics': {
                    'hits': self.stats['hits'],
                    'misses': self.stats['misses'],
                    'sets': self.stats['sets'],
                    'deletes': self.stats['deletes'],
                    'evictions': self.stats['evictions'],
                    'expirations': self.stats['expirations'],
                    'total_requests': total_requests
                },
                'uptime_seconds': uptime.total_seconds(),
                'average_requests_per_minute': total_requests / max(1, uptime.total_seconds() / 60)
            }
    
    def list_keys(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """List cache keys with optional pattern filtering"""
        with self._lock:
            keys_info = []
            
            for key, entry in self.cache.items():
                if pattern is None or pattern in key:
                    ttl_remaining = (entry['expire_time'] - datetime.now()).total_seconds()
                    
                    keys_info.append({
                        'key': key,
                        'created_at': entry['created_at'].isoformat(),
                        'expires_at': entry['expire_time'].isoformat(),
                        'ttl_remaining_seconds': max(0, ttl_remaining),
                        'access_count': entry['access_count'],
                        'size_estimate': len(str(entry['value']))
                    })
            
            return {
                'success': True,
                'total_keys': len(keys_info),
                'pattern': pattern,
                'keys': keys_info
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        with self._lock:
            stats = self.get_stats()
            return {
                'service': 'CoreCache',
                'status': 'operational',
                'performance': stats,
                'memory_usage': {
                    'entries': len(self.cache),
                    'max_entries': self.max_size,
                    'usage_percent': (len(self.cache) / self.max_size) * 100
                },
                'thread_safe': True,
                'features': ['LRU_eviction', 'TTL_expiration', 'thread_safe']
            }
    
    def cache_recent_events(self, events: list, ttl_minutes: int = 30) -> bool:
        """Cache recent events for quick access"""
        result = self.set('recent_events', events, ttl_minutes)
        return result['success']
    
    def get_recent_events(self) -> list:
        """Get cached recent events"""
        return self.get_value('recent_events', [])
    
    def cache_session_data(self, session_id: str, data: Dict[str, Any], ttl_minutes: int = 120) -> bool:
        """Cache session-specific data"""
        key = f"session_{session_id}"
        result = self.set(key, data, ttl_minutes)
        return result['success']
    
    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get cached session data"""
        key = f"session_{session_id}"
        return self.get_value(key, {})
    
    def export_cache_data(self, format: str = 'json') -> Dict[str, Any]:
        """Export cache data for backup or analysis"""
        with self._lock:
            cache_data = {
                'exported_at': datetime.now().isoformat(),
                'stats': self.get_stats(),
                'entries': {}
            }
            
            for key, entry in self.cache.items():
                cache_data['entries'][key] = {
                    'value': entry['value'],
                    'created_at': entry['created_at'].isoformat(),
                    'expire_time': entry['expire_time'].isoformat(),
                    'access_count': entry['access_count'],
                    'ttl_minutes': entry['ttl_minutes']
                }
            
            if format == 'json':
                return {
                    'success': True,
                    'format': 'json',
                    'data': json.dumps(cache_data, indent=2, ensure_ascii=False)
                }
            else:
                return {
                    'success': True,
                    'format': 'dict',
                    'data': cache_data
                }