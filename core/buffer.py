#!/usr/bin/env python3
"""
MindNext Hooks - Core Buffer System
===================================

Core buffer service for event buffering, queuing, and historical data management.
This is a SYSTEM SERVICE, not an action component.

Features:
- Multi-buffer support with independent configurations
- FIFO queue operations with size limits
- Event history tracking and retrieval
- Auto-cleanup and maintenance
- Thread-safe operations
"""

import threading
from collections import deque
from typing import Dict, Any, List, Optional, Deque
from datetime import datetime, timedelta
import json


class CoreBuffer:
    """
    Core Buffer System - Event buffering and queuing service
    
    This is a system-level service that provides centralized buffer management
    for all components in the MindNext Hooks system.
    """
    
    def __init__(self, default_max_size: int = 1000):
        self.default_max_size = default_max_size
        self.buffers: Dict[str, Deque] = {}
        self.buffer_configs: Dict[str, Dict] = {}
        self.stats: Dict[str, Dict] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize system buffers
        self._init_system_buffers()
    
    def _init_system_buffers(self):
        """Initialize core system buffers"""
        system_buffers = {
            'events': {'max_size': 100, 'description': 'Recent hook events'},
            'errors': {'max_size': 50, 'description': 'System errors and warnings'},
            'actions': {'max_size': 200, 'description': 'Action execution history'},
            'notifications': {'max_size': 30, 'description': 'System notifications'},
            'session': {'max_size': 10, 'description': 'Session context data'}
        }
        
        for buffer_id, config in system_buffers.items():
            self._create_buffer(buffer_id, config)
    
    def _create_buffer(self, buffer_id: str, config: Dict[str, Any]):
        """Create a new buffer with configuration"""
        with self._lock:
            self.buffers[buffer_id] = deque()
            self.buffer_configs[buffer_id] = {
                'max_size': config.get('max_size', self.default_max_size),
                'description': config.get('description', ''),
                'created_at': datetime.now(),
                'auto_cleanup': config.get('auto_cleanup', True)
            }
            self.stats[buffer_id] = {
                'total_items': 0,
                'items_dropped': 0,
                'last_access': datetime.now()
            }
    
    # === Core Buffer Operations ===
    
    def push(self, buffer_id: str, data: Any, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Push data to buffer (FIFO)"""
        with self._lock:
            # Create buffer if not exists
            if buffer_id not in self.buffers:
                self._create_buffer(buffer_id, {'max_size': self.default_max_size})
            
            buffer = self.buffers[buffer_id]
            config = self.buffer_configs[buffer_id]
            stats = self.stats[buffer_id]
            
            # Create buffer item
            item = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {},
                'buffer_id': buffer_id
            }
            
            # Check size limit and drop oldest if needed
            if len(buffer) >= config['max_size']:
                buffer.popleft()
                stats['items_dropped'] += 1
            
            # Add new item
            buffer.append(item)
            stats['total_items'] += 1
            stats['last_access'] = datetime.now()
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'current_size': len(buffer),
                'timestamp': item['timestamp']
            }
    
    def get_latest(self, buffer_id: str, count: int = 5) -> Dict[str, Any]:
        """Get latest N items from buffer (most recent first)"""
        with self._lock:
            if buffer_id not in self.buffers:
                return {
                    'success': False,
                    'error': f'Buffer {buffer_id} not found',
                    'items': []
                }
            
            buffer = self.buffers[buffer_id]
            self.stats[buffer_id]['last_access'] = datetime.now()
            
            # Get latest items (reverse order for most recent first)
            items = list(buffer)[-count:] if count > 0 else list(buffer)
            items.reverse()
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'items': items,
                'count': len(items),
                'total_size': len(buffer)
            }
    
    def get_latest_events(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get latest events - commonly used by actions"""
        result = self.get_latest('events', count)
        return result.get('items', [])
    
    def push_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Push event to events buffer - commonly used by system"""
        result = self.push('events', {
            'event_type': event_type,
            'event_data': event_data
        }, {'source': 'system'})
        return result['success']
    
    def push_action_result(self, action_id: str, result: Dict[str, Any]) -> bool:
        """Push action result to actions buffer"""
        result_data = self.push('actions', {
            'action_id': action_id,
            'result': result
        }, {'source': 'action_layer'})
        return result_data['success']
    
    def get_buffer_info(self, buffer_id: str) -> Dict[str, Any]:
        """Get buffer information and statistics"""
        with self._lock:
            if buffer_id not in self.buffers:
                return {'success': False, 'error': 'Buffer not found'}
            
            buffer = self.buffers[buffer_id]
            config = self.buffer_configs[buffer_id]
            stats = self.stats[buffer_id]
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'current_size': len(buffer),
                'max_size': config['max_size'],
                'description': config.get('description', ''),
                'created_at': config['created_at'].isoformat(),
                'statistics': {
                    'total_items': stats['total_items'],
                    'items_dropped': stats['items_dropped'],
                    'last_access': stats['last_access'].isoformat()
                },
                'oldest_item': buffer[0]['timestamp'] if buffer else None,
                'newest_item': buffer[-1]['timestamp'] if buffer else None
            }
    
    def list_all_buffers(self) -> Dict[str, Any]:
        """List all buffers with summary information"""
        with self._lock:
            buffer_summary = {}
            total_items = 0
            
            for buffer_id in self.buffers.keys():
                info = self.get_buffer_info(buffer_id)
                if info['success']:
                    buffer_summary[buffer_id] = {
                        'size': info['current_size'],
                        'max_size': info['max_size'], 
                        'description': info['description'],
                        'total_processed': info['statistics']['total_items'],
                        'dropped': info['statistics']['items_dropped']
                    }
                    total_items += info['current_size']
            
            return {
                'success': True,
                'total_buffers': len(self.buffers),
                'total_items': total_items,
                'buffers': buffer_summary
            }
    
    def clear_buffer(self, buffer_id: str) -> Dict[str, Any]:
        """Clear specific buffer"""
        with self._lock:
            if buffer_id not in self.buffers:
                return {'success': False, 'error': 'Buffer not found'}
            
            old_size = len(self.buffers[buffer_id])
            self.buffers[buffer_id].clear()
            self.stats[buffer_id]['last_access'] = datetime.now()
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'cleared_items': old_size
            }
    
    def cleanup_expired(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up old items from all buffers"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            total_cleaned = 0
            
            for buffer_id, buffer in self.buffers.items():
                cleaned_count = 0
                items_to_keep = []
                
                for item in buffer:
                    item_time = datetime.fromisoformat(item['timestamp'])
                    if item_time >= cutoff_time:
                        items_to_keep.append(item)
                    else:
                        cleaned_count += 1
                
                buffer.clear()
                buffer.extend(items_to_keep)
                total_cleaned += cleaned_count
            
            return {
                'success': True,
                'total_cleaned': total_cleaned,
                'cutoff_time': cutoff_time.isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        with self._lock:
            return {
                'service': 'CoreBuffer',
                'status': 'operational',
                'buffers': self.list_all_buffers(),
                'memory_usage': {
                    'total_items': sum(len(buf) for buf in self.buffers.values()),
                    'buffer_count': len(self.buffers)
                },
                'thread_safe': True
            }
    
    def export_buffer_data(self, buffer_id: str, format: str = 'json') -> Dict[str, Any]:
        """Export buffer data for backup or analysis"""
        with self._lock:
            if buffer_id not in self.buffers:
                return {'success': False, 'error': 'Buffer not found'}
            
            buffer_data = {
                'buffer_id': buffer_id,
                'config': self.buffer_configs[buffer_id].copy(),
                'stats': self.stats[buffer_id].copy(),
                'items': list(self.buffers[buffer_id]),
                'exported_at': datetime.now().isoformat()
            }
            
            # Convert datetime objects to strings for JSON serialization
            if 'created_at' in buffer_data['config']:
                buffer_data['config']['created_at'] = buffer_data['config']['created_at'].isoformat()
            if 'last_access' in buffer_data['stats']:
                buffer_data['stats']['last_access'] = buffer_data['stats']['last_access'].isoformat()
            
            if format == 'json':
                return {
                    'success': True,
                    'format': 'json',
                    'data': json.dumps(buffer_data, indent=2, ensure_ascii=False)
                }
            else:
                return {
                    'success': True,
                    'format': 'dict',
                    'data': buffer_data
                }