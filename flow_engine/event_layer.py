"""
事件層 - 負責事件的接收、解析和標準化
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json

@dataclass
class HookEvent:
    """標準化的 Hook 事件"""
    event_type: str                    # UserPromptSubmit, PreToolUse, PostToolUse, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # 解析後的標準字段
    tool_name: Optional[str] = None
    tool_input: Optional[Dict] = None
    file_paths: List[str] = field(default_factory=list)
    content: Optional[str] = None
    user_prompt: Optional[str] = None
    
    # 上下文信息
    session_id: Optional[str] = None
    sequence_number: int = 0
    
    # 事件元數據
    metadata: Dict[str, Any] = field(default_factory=dict)

class EventProcessor:
    """事件處理器 - 將原始 Hook 數據轉換為標準事件"""
    
    def __init__(self):
        self.event_sequence = 0
        self.session_context = {}
    
    def process_hook_event(self, event_type: str, raw_data: Dict[str, Any]) -> HookEvent:
        """將原始 Hook 數據處理為標準事件"""
        self.event_sequence += 1
        
        event = HookEvent(
            event_type=event_type,
            raw_data=raw_data,
            sequence_number=self.event_sequence
        )
        
        # 根據事件類型解析特定字段
        if event_type == "UserPromptSubmit":
            self._parse_user_prompt_event(event, raw_data)
        elif event_type in ["PreToolUse", "PostToolUse"]:
            self._parse_tool_event(event, raw_data)
        elif event_type == "Notification":
            self._parse_notification_event(event, raw_data)
        
        # 更新會話上下文
        self._update_session_context(event)
        
        return event
    
    def _parse_user_prompt_event(self, event: HookEvent, raw_data: Dict[str, Any]):
        """解析用戶提示事件"""
        event.user_prompt = raw_data.get('user_prompt', '')
        
        # 提取關鍵字和意圖
        event.metadata.update({
            'prompt_length': len(event.user_prompt),
            'contains_keywords': self._extract_keywords(event.user_prompt),
            'estimated_intent': self._estimate_intent(event.user_prompt)
        })
    
    def _parse_tool_event(self, event: HookEvent, raw_data: Dict[str, Any]):
        """解析工具事件"""
        event.tool_name = raw_data.get('tool_name', '')
        event.tool_input = raw_data.get('tool_input', {})
        
        # 提取文件路徑
        file_paths = []
        
        # 從 tool_input 提取
        if 'file_path' in event.tool_input:
            file_paths.append(event.tool_input['file_path'])
        
        # 從環境變量提取
        env_paths = raw_data.get('env', {}).get('CLAUDE_FILE_PATHS', '')
        if env_paths:
            file_paths.extend(env_paths.split())
        
        # 過濾和標準化路徑
        event.file_paths = self._normalize_file_paths(file_paths)
        
        # 分析文件類型和特徵
        event.metadata.update({
            'file_types': self._analyze_file_types(event.file_paths),
            'is_code_modification': self._is_code_modification_event(event),
            'estimated_complexity': self._estimate_operation_complexity(event)
        })
        
        # 讀取文件內容 (對於 PostToolUse)
        if event.event_type == "PostToolUse" and event.file_paths:
            event.content = self._read_file_content(event.file_paths[0])
    
    def _parse_notification_event(self, event: HookEvent, raw_data: Dict[str, Any]):
        """解析通知事件"""
        event.metadata.update({
            'message': raw_data.get('message', ''),
            'severity': raw_data.get('severity', 'info')
        })
    
    def _extract_keywords(self, prompt: str) -> List[str]:
        """提取提示中的關鍵字"""
        keywords = []
        key_patterns = {
            'query': ['查詢', '搜索', '找', 'search', 'find', 'query'],
            'record': ['記錄', '保存', '儲存', 'record', 'save', 'store'],
            'backup': ['備份', 'backup', 'copy'],
            'test': ['測試', 'test', 'check'],
            'refactor': ['重構', '優化', 'refactor', 'optimize'],
            'debug': ['調試', '除錯', 'debug', 'fix'],
            'analysis': ['分析', 'analyze', 'analysis'],
            'mindnext': ['mindnext', '8d', 'qkvl', '容器', 'container']
        }
        
        prompt_lower = prompt.lower()
        for category, patterns in key_patterns.items():
            if any(pattern in prompt_lower for pattern in patterns):
                keywords.append(category)
        
        return keywords
    
    def _estimate_intent(self, prompt: str) -> str:
        """估計用戶意圖"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['建立', 'create', '新增', 'add', '寫']):
            return 'create'
        elif any(word in prompt_lower for word in ['修改', 'modify', '更新', 'update', '編輯', 'edit']):
            return 'modify'
        elif any(word in prompt_lower for word in ['刪除', 'delete', '移除', 'remove']):
            return 'delete'
        elif any(word in prompt_lower for word in ['查詢', 'query', '搜索', 'search', '找', 'find']):
            return 'query'
        elif any(word in prompt_lower for word in ['分析', 'analyze', '檢查', 'check', '驗證', 'validate']):
            return 'analyze'
        elif any(word in prompt_lower for word in ['解釋', 'explain', '說明', 'describe']):
            return 'explain'
        else:
            return 'unknown'
    
    def _normalize_file_paths(self, file_paths: List[str]) -> List[str]:
        """標準化和過濾文件路徑"""
        normalized = []
        for path_str in file_paths:
            if not path_str:
                continue
            
            try:
                path = Path(path_str)
                if path.exists() and path.is_file():
                    normalized.append(str(path.resolve()))
            except:
                continue
        
        return list(set(normalized))  # 去重
    
    def _analyze_file_types(self, file_paths: List[str]) -> Dict[str, int]:
        """分析文件類型分布"""
        type_count = {}
        
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            if ext:
                type_count[ext] = type_count.get(ext, 0) + 1
        
        return type_count
    
    def _is_code_modification_event(self, event: HookEvent) -> bool:
        """判斷是否為代碼修改事件"""
        if event.tool_name not in ['Write', 'Edit', 'MultiEdit']:
            return False
        
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go', '.java', '.cpp', '.c'}
        return any(Path(fp).suffix.lower() in code_extensions for fp in event.file_paths)
    
    def _estimate_operation_complexity(self, event: HookEvent) -> str:
        """估計操作複雜度"""
        if not event.file_paths:
            return 'simple'
        
        # 基於文件數量和大小估計
        file_count = len(event.file_paths)
        total_size = 0
        
        try:
            for file_path in event.file_paths:
                total_size += Path(file_path).stat().st_size
        except:
            pass
        
        if file_count == 1 and total_size < 1000:
            return 'simple'
        elif file_count <= 3 and total_size < 10000:
            return 'medium'
        else:
            return 'complex'
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """安全地讀取文件內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 限制內容大小，避免記憶體問題
                if len(content) > 100000:  # 100KB
                    return content[:100000] + "...[truncated]"
                return content
        except:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    if len(content) > 100000:
                        return content[:100000] + "...[truncated]"
                    return content
            except:
                return None
    
    def _update_session_context(self, event: HookEvent):
        """更新會話上下文"""
        # 記錄最近的事件
        if 'recent_events' not in self.session_context:
            self.session_context['recent_events'] = []
        
        self.session_context['recent_events'].append({
            'type': event.event_type,
            'timestamp': event.timestamp.isoformat(),
            'tool': event.tool_name,
            'files': len(event.file_paths)
        })
        
        # 保持最近 20 個事件
        self.session_context['recent_events'] = self.session_context['recent_events'][-20:]
        
        # 統計信息
        if 'stats' not in self.session_context:
            self.session_context['stats'] = {}
        
        stats = self.session_context['stats']
        stats[event.event_type] = stats.get(event.event_type, 0) + 1
        
        if event.tool_name:
            tool_stats = stats.get('tools', {})
            tool_stats[event.tool_name] = tool_stats.get(event.tool_name, 0) + 1
            stats['tools'] = tool_stats
    
    def get_session_context(self) -> Dict[str, Any]:
        """獲取當前會話上下文"""
        return self.session_context.copy()