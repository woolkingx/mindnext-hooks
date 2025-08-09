"""
ActionUtility - Utility Action Executor (包含核心Component: Buffer/Cache/AISDK)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import hashlib
import time
import threading
from pathlib import Path
from collections import OrderedDict, deque

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionUtility(ActionExecutor):
    """Utility Action Executor - 包含核心ComponentFunction"""
    
    def __init__(self):
        super().__init__()
        # 核心ComponentInitialize
        self.buffer_component = BufferComponent()
        self.cache_component = CacheComponent()
        self.aisdk_component = AISDKComponent()
        
    def get_action_type(self) -> str:
        return "action.utility"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """Execute toolAction"""
        start_time = datetime.now()
        
        try:
            operation = parameters.get('operation', 'log')
            
            # 基本ToolOperation
            if operation == 'log':
                result = self._log_operation(event, parameters)
            elif operation == 'delay':
                result = self._delay_operation(event, parameters)
            elif operation == 'timestamp':
                result = self._timestamp_operation(event, parameters)
            elif operation == 'uuid':
                result = self._uuid_operation(event, parameters)
            
            # 核心ComponentOperation
            elif operation.startswith('buffer.'):
                result = self._buffer_operations(operation, event, parameters, context)
            elif operation.startswith('cache.'):
                result = self._cache_operations(operation, event, parameters, context)
            elif operation.startswith('aisdk.'):
                result = self._aisdk_operations(operation, event, parameters, context)
            
            # SystemOperation
            elif operation == 'system_info':
                result = self._system_info_operation(event, parameters)
            elif operation == 'health_check':
                result = self._health_check_operation(event, parameters)
            elif operation == 'cleanup':
                result = self._cleanup_operation(event, parameters)
            
            else:
                return self._create_result(
                    action_id="action.utility",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.utility",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.utility",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _buffer_operations(self, operation: str, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Buffer ComponentOperation"""
        op_name = operation.split('.')[1]
        
        if op_name == 'push':
            return self.buffer_component.push(parameters.get('data'), parameters.get('buffer_id', 'default'))
        elif op_name == 'pop':
            return self.buffer_component.pop(parameters.get('buffer_id', 'default'))
        elif op_name == 'peek':
            return self.buffer_component.peek(parameters.get('buffer_id', 'default'))
        elif op_name == 'size':
            return self.buffer_component.get_size(parameters.get('buffer_id', 'default'))
        elif op_name == 'clear':
            return self.buffer_component.clear(parameters.get('buffer_id', 'default'))
        elif op_name == 'list':
            return self.buffer_component.list_buffers()
        elif op_name == 'flush':
            return self.buffer_component.flush(parameters.get('buffer_id', 'default'), parameters.get('target'))
        else:
            return {'error': f'未知 Buffer Operation: {op_name}'}
    
    def _cache_operations(self, operation: str, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Cache ComponentOperation"""
        op_name = operation.split('.')[1]
        
        if op_name == 'set':
            key = parameters.get('key')
            value = parameters.get('value')
            ttl = parameters.get('ttl', 3600)  # Default1小時
            return self.cache_component.set(key, value, ttl)
        elif op_name == 'get':
            key = parameters.get('key')
            return self.cache_component.get(key)
        elif op_name == 'delete':
            key = parameters.get('key')
            return self.cache_component.delete(key)
        elif op_name == 'exists':
            key = parameters.get('key')
            return self.cache_component.exists(key)
        elif op_name == 'clear':
            return self.cache_component.clear()
        elif op_name == 'stats':
            return self.cache_component.get_stats()
        elif op_name == 'cleanup':
            return self.cache_component.cleanup_expired()
        else:
            return {'error': f'未知 Cache Operation: {op_name}'}
    
    def _aisdk_operations(self, operation: str, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """AI SDK ComponentOperation"""
        op_name = operation.split('.')[1]
        
        if op_name == 'analyze':
            return self.aisdk_component.analyze_text(parameters.get('text', ''))
        elif op_name == 'summarize':
            return self.aisdk_component.summarize(parameters.get('content', ''))
        elif op_name == 'extract_keywords':
            return self.aisdk_component.extract_keywords(parameters.get('text', ''))
        elif op_name == 'classify':
            return self.aisdk_component.classify_text(parameters.get('text', ''), parameters.get('categories', []))
        elif op_name == 'sentiment':
            return self.aisdk_component.analyze_sentiment(parameters.get('text', ''))
        elif op_name == 'generate':
            return self.aisdk_component.generate_text(parameters.get('prompt', ''), parameters.get('options', {}))
        elif op_name == 'translate':
            return self.aisdk_component.translate(parameters.get('text', ''), parameters.get('target_lang', 'en'))
        elif op_name == 'stats':
            return self.aisdk_component.get_stats()
        else:
            return {'error': f'未知 AI SDK Operation: {op_name}'}
    
    def _log_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """日誌Operation"""
        message = parameters.get('message', f'Hook Event: {event.event_type}')
        level = parameters.get('level', 'info')
        
        # Format化日誌
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        
        print(log_entry)
        
        # 可選：寫入日誌File
        if parameters.get('write_file', False):
            log_file = parameters.get('log_file', '/root/Dev/mindnext/logs/hooks.log')
            Path(log_file).parent.mkdir(exist_ok=True)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        
        return {
            'operation': 'log',
            'message': message,
            'level': level,
            'timestamp': timestamp,
            'logged_to_file': parameters.get('write_file', False)
        }
    
    def _delay_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """延遲Operation"""
        delay_seconds = parameters.get('seconds', 1)
        message = parameters.get('message', f'延遲 {delay_seconds} 秒')
        
        start_time = time.time()
        time.sleep(delay_seconds)
        actual_delay = time.time() - start_time
        
        return {
            'operation': 'delay',
            'requested_delay': delay_seconds,
            'actual_delay': actual_delay,
            'message': message
        }
    
    def _timestamp_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Time戳Operation"""
        format_type = parameters.get('format', 'iso')
        timezone = parameters.get('timezone', 'local')
        
        now = datetime.now()
        
        formats = {
            'iso': now.isoformat(),
            'unix': int(now.timestamp()),
            'human': now.strftime('%Y-%m-%d %H:%M:%S'),
            'filename': now.strftime('%Y%m%d_%H%M%S'),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S')
        }
        
        return {
            'operation': 'timestamp',
            'format': format_type,
            'timestamp': formats.get(format_type, formats['iso']),
            'timezone': timezone,
            'all_formats': formats
        }
    
    def _uuid_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """UUID GenerateOperation"""
        import uuid
        
        uuid_type = parameters.get('type', 'uuid4')
        count = parameters.get('count', 1)
        
        uuids = []
        for _ in range(min(count, 100)):  # 限制最多Generate100個
            if uuid_type == 'uuid1':
                new_uuid = str(uuid.uuid1())
            elif uuid_type == 'uuid4':
                new_uuid = str(uuid.uuid4())
            else:
                new_uuid = str(uuid.uuid4())
            uuids.append(new_uuid)
        
        return {
            'operation': 'uuid',
            'type': uuid_type,
            'count': len(uuids),
            'uuids': uuids[0] if count == 1 else uuids
        }
    
    def _system_info_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """SystemInformationOperation"""
        import platform
        import psutil
        
        info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'python': {
                'version': platform.python_version(),
                'implementation': platform.python_implementation()
            },
            'resources': {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/').free
            } if 'psutil' in globals() else {},
            'hooks_info': {
                'buffer_count': len(self.buffer_component.buffers),
                'cache_size': len(self.cache_component.cache),
                'ai_requests': self.aisdk_component.request_count
            }
        }
        
        return {
            'operation': 'system_info',
            'info': info,
            'timestamp': datetime.now().isoformat()
        }
    
    def _health_check_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Health checkOperation"""
        checks = {
            'buffer_component': self.buffer_component.health_check(),
            'cache_component': self.cache_component.health_check(),
            'aisdk_component': self.aisdk_component.health_check()
        }
        
        overall_health = all(check['healthy'] for check in checks.values())
        
        return {
            'operation': 'health_check',
            'overall_health': overall_health,
            'component_checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    
    def _cleanup_operation(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """清理Operation"""
        cleanup_results = {}
        
        # 清理過期Cache
        cache_cleanup = self.cache_component.cleanup_expired()
        cleanup_results['cache'] = cache_cleanup
        
        # 清理空的緩衝區
        buffer_cleanup = self.buffer_component.cleanup_empty()
        cleanup_results['buffer'] = buffer_cleanup
        
        # AI SDK 清理
        aisdk_cleanup = self.aisdk_component.cleanup()
        cleanup_results['aisdk'] = aisdk_cleanup
        
        return {
            'operation': 'cleanup',
            'results': cleanup_results,
            'timestamp': datetime.now().isoformat()
        }


class BufferComponent:
    """Buffer Component - 提供Data緩衝Function"""
    
    def __init__(self):
        self.buffers: Dict[str, deque] = {}
        self.buffer_configs: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def push(self, data: Any, buffer_id: str = 'default') -> Dict[str, Any]:
        """推入Data到緩衝區"""
        with self._lock:
            if buffer_id not in self.buffers:
                self.buffers[buffer_id] = deque()
                self.buffer_configs[buffer_id] = {'max_size': 1000}
            
            buffer = self.buffers[buffer_id]
            config = self.buffer_configs[buffer_id]
            
            # Check最大Size限制
            if len(buffer) >= config['max_size']:
                buffer.popleft()  # 移除最舊的Data
            
            # 添加Time戳
            item = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'id': hashlib.md5(str(data).encode()).hexdigest()[:8]
            }
            
            buffer.append(item)
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'item_id': item['id'],
                'buffer_size': len(buffer)
            }
    
    def pop(self, buffer_id: str = 'default') -> Dict[str, Any]:
        """從緩衝區彈出Data"""
        with self._lock:
            if buffer_id not in self.buffers or not self.buffers[buffer_id]:
                return {'success': False, 'error': 'Buffer empty or not found'}
            
            item = self.buffers[buffer_id].pop()
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'item': item,
                'buffer_size': len(self.buffers[buffer_id])
            }
    
    def peek(self, buffer_id: str = 'default') -> Dict[str, Any]:
        """查看緩衝區頂部Data（不移除）"""
        with self._lock:
            if buffer_id not in self.buffers or not self.buffers[buffer_id]:
                return {'success': False, 'error': 'Buffer empty or not found'}
            
            item = self.buffers[buffer_id][-1]
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'item': item,
                'buffer_size': len(self.buffers[buffer_id])
            }
    
    def get_size(self, buffer_id: str = 'default') -> Dict[str, Any]:
        """獲取緩衝區Size"""
        with self._lock:
            size = len(self.buffers.get(buffer_id, []))
            return {
                'buffer_id': buffer_id,
                'size': size,
                'exists': buffer_id in self.buffers
            }
    
    def clear(self, buffer_id: str = 'default') -> Dict[str, Any]:
        """清空緩衝區"""
        with self._lock:
            if buffer_id in self.buffers:
                old_size = len(self.buffers[buffer_id])
                self.buffers[buffer_id].clear()
                return {
                    'success': True,
                    'buffer_id': buffer_id,
                    'cleared_items': old_size
                }
            else:
                return {'success': False, 'error': 'Buffer not found'}
    
    def list_buffers(self) -> Dict[str, Any]:
        """列出所有緩衝區"""
        with self._lock:
            buffer_info = {}
            for buf_id, buffer in self.buffers.items():
                buffer_info[buf_id] = {
                    'size': len(buffer),
                    'max_size': self.buffer_configs.get(buf_id, {}).get('max_size', 1000),
                    'oldest_item': buffer[0]['timestamp'] if buffer else None,
                    'newest_item': buffer[-1]['timestamp'] if buffer else None
                }
            
            return {
                'total_buffers': len(self.buffers),
                'buffers': buffer_info
            }
    
    def flush(self, buffer_id: str = 'default', target: Optional[str] = None) -> Dict[str, Any]:
        """刷新緩衝區到目標"""
        with self._lock:
            if buffer_id not in self.buffers:
                return {'success': False, 'error': 'Buffer not found'}
            
            buffer = self.buffers[buffer_id]
            items = list(buffer)
            buffer.clear()
            
            # 如果指定了目標，寫入File
            if target:
                try:
                    Path(target).parent.mkdir(exist_ok=True)
                    with open(target, 'w', encoding='utf-8') as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)
                    
                    return {
                        'success': True,
                        'buffer_id': buffer_id,
                        'items_flushed': len(items),
                        'target': target
                    }
                except Exception as e:
                    # 恢復Data
                    buffer.extend(items)
                    return {
                        'success': False,
                        'error': f'Failed to write to {target}: {str(e)}'
                    }
            
            return {
                'success': True,
                'buffer_id': buffer_id,
                'items_flushed': len(items),
                'data': items
            }
    
    def cleanup_empty(self) -> Dict[str, Any]:
        """清理空的緩衝區"""
        with self._lock:
            empty_buffers = [buf_id for buf_id, buffer in self.buffers.items() if not buffer]
            
            for buf_id in empty_buffers:
                del self.buffers[buf_id]
                if buf_id in self.buffer_configs:
                    del self.buffer_configs[buf_id]
            
            return {
                'cleaned_buffers': empty_buffers,
                'count': len(empty_buffers)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        with self._lock:
            return {
                'healthy': True,
                'total_buffers': len(self.buffers),
                'total_items': sum(len(buffer) for buffer in self.buffers.values()),
                'memory_usage': 'normal'  # 簡化實現
            }


class CacheComponent:
    """Cache Component - 提供DataCacheFunction"""
    
    def __init__(self):
        self.cache: Dict[str, Dict] = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        self._lock = threading.RLock()
        self.max_size = 1000
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> Dict[str, Any]:
        """SettingsCache"""
        with self._lock:
            # CheckCacheSize限制
            if len(self.cache) >= self.max_size and key not in self.cache:
                # 移除最舊的項目
                self.cache.popitem(last=False)
            
            expire_time = datetime.now() + timedelta(seconds=ttl)
            
            self.cache[key] = {
                'value': value,
                'expire_time': expire_time,
                'created_time': datetime.now(),
                'access_count': 0
            }
            
            self.stats['sets'] += 1
            
            return {
                'success': True,
                'key': key,
                'ttl': ttl,
                'expire_time': expire_time.isoformat()
            }
    
    def get(self, key: str) -> Dict[str, Any]:
        """獲取Cache"""
        with self._lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return {'success': False, 'error': 'Key not found'}
            
            item = self.cache[key]
            
            # Check是否過期
            if datetime.now() > item['expire_time']:
                del self.cache[key]
                self.stats['misses'] += 1
                return {'success': False, 'error': 'Key expired'}
            
            # Update訪問統計
            item['access_count'] += 1
            
            # 移動到末尾（LRU）
            self.cache.move_to_end(key)
            
            self.stats['hits'] += 1
            
            return {
                'success': True,
                'key': key,
                'value': item['value'],
                'created_time': item['created_time'].isoformat(),
                'access_count': item['access_count']
            }
    
    def delete(self, key: str) -> Dict[str, Any]:
        """DeleteCache"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.stats['deletes'] += 1
                return {'success': True, 'key': key}
            else:
                return {'success': False, 'error': 'Key not found'}
    
    def exists(self, key: str) -> Dict[str, Any]:
        """CheckCache是否存在"""
        with self._lock:
            exists = key in self.cache
            if exists:
                # Check是否過期
                if datetime.now() > self.cache[key]['expire_time']:
                    del self.cache[key]
                    exists = False
            
            return {
                'key': key,
                'exists': exists
            }
    
    def clear(self) -> Dict[str, Any]:
        """清空所有Cache"""
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            
            return {
                'success': True,
                'cleared_items': count
            }
    
    def cleanup_expired(self) -> Dict[str, Any]:
        """清理過期的Cache項目"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, item in self.cache.items()
                if now > item['expire_time']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return {
                'cleaned_keys': expired_keys,
                'count': len(expired_keys)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取Cache統計"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'stats': self.stats.copy(),
                'hit_rate': hit_rate,
                'cache_size': len(self.cache),
                'max_size': self.max_size
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        with self._lock:
            return {
                'healthy': True,
                'cache_size': len(self.cache),
                'hit_rate': self.get_stats()['hit_rate'],
                'memory_usage': 'normal'
            }


class AISDKComponent:
    """AI SDK Component - 提供 AI 相關Function"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.cache = {}  # 簡單的ResultCache
        self._lock = threading.RLock()
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze文本"""
        with self._lock:
            self.request_count += 1
            
            # 簡化的文本Analyze實現
            analysis = {
                'length': len(text),
                'word_count': len(text.split()),
                'sentence_count': len([s for s in text.split('.') if s.strip()]),
                'language': 'zh' if any('\u4e00' <= char <= '\u9fff' for char in text) else 'en',
                'complexity': 'high' if len(text.split()) > 100 else 'medium' if len(text.split()) > 20 else 'low'
            }
            
            return {
                'success': True,
                'analysis': analysis,
                'processing_time': 0.1  # 模擬Processing time
            }
    
    def summarize(self, content: str, max_length: int = 100) -> Dict[str, Any]:
        """文本摘要"""
        with self._lock:
            self.request_count += 1
            
            # 簡化的摘要實現
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            
            if len(sentences) <= 2:
                summary = content[:max_length]
            else:
                # 取前兩句作為摘要
                summary = '. '.join(sentences[:2])
                if len(summary) > max_length:
                    summary = summary[:max_length] + '...'
            
            return {
                'success': True,
                'summary': summary,
                'original_length': len(content),
                'summary_length': len(summary),
                'compression_ratio': len(summary) / len(content) if content else 0
            }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """Extract keywords"""
        with self._lock:
            self.request_count += 1
            
            # 簡化的關鍵字提取
            words = text.lower().split()
            
            # 過濾停用詞
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
            
            # 統計詞頻
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 排序並取前N個
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
            
            return {
                'success': True,
                'keywords': [{'word': word, 'frequency': freq} for word, freq in keywords],
                'total_words': len(words),
                'unique_words': len(set(words))
            }
    
    def classify_text(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """文本分類"""
        with self._lock:
            self.request_count += 1
            
            # 簡化的分類實現
            if not categories:
                categories = ['技術', '商業', '個人', '其他']
            
            text_lower = text.lower()
            
            # 簡單的關鍵字匹配
            tech_keywords = ['code', 'programming', '代碼', '編程', 'api', 'database']
            business_keywords = ['business', '商業', 'market', '市場', 'profit', '利潤']
            personal_keywords = ['personal', '個人', 'diary', '日記', 'feeling', '感覺']
            
            scores = {}
            for category in categories:
                if category.lower() in ['tech', '技術']:
                    scores[category] = sum(1 for kw in tech_keywords if kw in text_lower)
                elif category.lower() in ['business', '商業']:
                    scores[category] = sum(1 for kw in business_keywords if kw in text_lower)
                elif category.lower() in ['personal', '個人']:
                    scores[category] = sum(1 for kw in personal_keywords if kw in text_lower)
                else:
                    scores[category] = 0
            
            # 找出最高分的類別
            best_category = max(scores.items(), key=lambda x: x[1]) if scores else ('其他', 0)
            
            return {
                'success': True,
                'predicted_category': best_category[0],
                'confidence': min(1.0, best_category[1] / 10),  # 簡化的信心度
                'all_scores': scores
            }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Sentiment analysis"""
        with self._lock:
            self.request_count += 1
            
            # 簡化的Sentiment analysis
            positive_words = ['good', 'great', 'excellent', 'happy', '好', '棒', '優秀', '開心']
            negative_words = ['bad', 'terrible', 'awful', 'sad', '壞', '糟糕', '難過']
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                score = min(1.0, positive_count / (positive_count + negative_count + 1))
            elif negative_count > positive_count:
                sentiment = 'negative'
                score = min(1.0, negative_count / (positive_count + negative_count + 1))
            else:
                sentiment = 'neutral'
                score = 0.5
            
            return {
                'success': True,
                'sentiment': sentiment,
                'score': score,
                'positive_indicators': positive_count,
                'negative_indicators': negative_count
            }
    
    def generate_text(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate text"""
        with self._lock:
            self.request_count += 1
            
            if options is None:
                options = {}
            
            max_length = options.get('max_length', 100)
            style = options.get('style', 'informative')
            
            # 簡化的文本Generate
            templates = {
                'informative': f"基於提示「{prompt}」，這裡是一些相關Information...",
                'creative': f"想像一下，如果{prompt}會發生什麼...",
                'technical': f"關於{prompt}的技術Analyze如下...",
                'casual': f"說到{prompt}，我覺得..."
            }
            
            generated = templates.get(style, templates['informative'])
            
            if len(generated) > max_length:
                generated = generated[:max_length] + '...'
            
            return {
                'success': True,
                'generated_text': generated,
                'prompt': prompt,
                'style': style,
                'length': len(generated)
            }
    
    def translate(self, text: str, target_lang: str = 'en') -> Dict[str, Any]:
        """Translate text"""
        with self._lock:
            self.request_count += 1
            
            # 簡化的翻譯實現
            translations = {
                'hello': {'en': 'hello', 'zh': '你好', 'ja': 'こんにちは'},
                '你好': {'en': 'hello', 'zh': '你好', 'ja': 'こんにちは'},
                'thank you': {'en': 'thank you', 'zh': '謝謝', 'ja': 'ありがとう'},
                '謝謝': {'en': 'thank you', 'zh': '謝謝', 'ja': 'ありがとう'}
            }
            
            # Detection源語言
            source_lang = 'zh' if any('\u4e00' <= char <= '\u9fff' for char in text) else 'en'
            
            # 簡單的翻譯邏輯
            text_lower = text.lower().strip()
            translated = translations.get(text_lower, {}).get(target_lang, f"[翻譯到 {target_lang}] {text}")
            
            return {
                'success': True,
                'original_text': text,
                'translated_text': translated,
                'source_language': source_lang,
                'target_language': target_lang
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計Information"""
        with self._lock:
            success_rate = ((self.request_count - self.error_count) / self.request_count) if self.request_count > 0 else 1.0
            
            return {
                'total_requests': self.request_count,
                'error_count': self.error_count,
                'success_rate': success_rate,
                'cache_size': len(self.cache)
            }
    
    def cleanup(self) -> Dict[str, Any]:
        """清理Operation"""
        with self._lock:
            old_cache_size = len(self.cache)
            self.cache.clear()
            
            return {
                'cleared_cache_items': old_cache_size
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        with self._lock:
            stats = self.get_stats()
            
            return {
                'healthy': stats['success_rate'] > 0.8,
                'request_count': stats['total_requests'],
                'error_rate': stats['error_count'] / max(1, stats['total_requests']),
                'status': 'operational'
            }