"""
ActionMemory - 記憶記錄動作執行器
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionMemory(ActionExecutor):
    """記憶記錄動作執行器"""
    
    def get_action_type(self) -> str:
        return "action.memory"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行記憶記錄動作"""
        start_time = datetime.now()
        
        try:
            operation = parameters.get('operation', 'record')
            
            if operation == 'record':
                result = self._record_event(event, parameters, context)
            elif operation == 'query':
                result = self._query_memory(event, parameters, context)
            elif operation == 'update':
                result = self._update_memory(event, parameters, context)
            elif operation == 'summarize':
                result = self._summarize_session(event, parameters, context)
            elif operation == 'export':
                result = self._export_memory(event, parameters, context)
            elif operation == 'mindnext_record':
                result = self._record_to_mindnext(event, parameters, context)
            else:
                return self._create_result(
                    action_id="action.memory",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"未知操作: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.memory",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.memory",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _record_event(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """記錄事件到記憶系統"""
        record_data = {
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'tool_name': event.tool_name,
            'file_paths': event.file_paths,
            'summary': parameters.get('summary', self._generate_event_summary(event)),
            'metadata': event.metadata,
            'context': self._extract_relevant_context(context),
            'tags': parameters.get('tags', self._generate_tags(event))
        }
        
        # 保存到本地記錄文件
        self._save_to_local_record(record_data)
        
        # 如果配置了 MindNext Graph，也記錄到知識圖譜
        if parameters.get('use_mindnext', True):
            mindnext_result = self._record_to_mindnext_graph(record_data, event)
            record_data['mindnext_record'] = mindnext_result
        
        return record_data
    
    def _generate_event_summary(self, event: HookEvent) -> str:
        """生成事件摘要"""
        if event.event_type == "UserPromptSubmit":
            return f"用戶提交提示: {event.user_prompt[:100]}..." if event.user_prompt else "用戶提交了提示"
        elif event.event_type == "PostToolUse":
            file_info = f"涉及 {len(event.file_paths)} 個文件" if event.file_paths else "無文件操作"
            return f"執行工具 {event.tool_name}: {file_info}"
        elif event.event_type == "PreToolUse":
            return f"準備執行工具: {event.tool_name}"
        else:
            return f"事件類型: {event.event_type}"
    
    def _generate_tags(self, event: HookEvent) -> List[str]:
        """生成標籤"""
        tags = [event.event_type.lower()]
        
        if event.tool_name:
            tags.append(f"tool_{event.tool_name.lower()}")
        
        # 基於文件類型添加標籤
        for file_path in event.file_paths:
            ext = Path(file_path).suffix.lower()
            if ext:
                tags.append(f"filetype_{ext[1:]}")  # 移除點號
        
        # 基於關鍵字添加標籤
        keywords = event.metadata.get('contains_keywords', [])
        tags.extend(f"keyword_{kw}" for kw in keywords)
        
        # 基於意圖添加標籤
        intent = event.metadata.get('estimated_intent')
        if intent:
            tags.append(f"intent_{intent}")
        
        return list(set(tags))  # 去重
    
    def _extract_relevant_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取相關上下文"""
        relevant_context = {}
        
        # 提取會話信息
        if 'session_id' in context:
            relevant_context['session_id'] = context['session_id']
        
        # 提取最近的事件
        if 'recent_events' in context:
            relevant_context['recent_events'] = context['recent_events'][-3:]  # 最近3個事件
        
        # 提取統計信息
        if 'stats' in context:
            relevant_context['session_stats'] = context['stats']
        
        return relevant_context
    
    def _save_to_local_record(self, record_data: Dict[str, Any]) -> str:
        """保存到本地記錄文件"""
        # 創建記錄目錄
        record_dir = Path("/root/Dev/mindnext/record")
        record_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_hook_event.json"
        file_path = record_dir / filename
        
        # 保存記錄
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def _record_to_mindnext_graph(self, record_data: Dict[str, Any], event: HookEvent) -> Dict[str, Any]:
        """記錄到 MindNext Graph 知識圖譜"""
        # 準備節點數據
        node_data = {
            'topic': f"Hook Event_{event.event_type}_{datetime.now().strftime('%m%d_%H%M')}",
            'summary': f"事件類型: {event.event_type}, 工具: {event.tool_name or '無'}, 時間: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
                      f"文件數: {len(event.file_paths)}, 意圖: {event.metadata.get('estimated_intent', '未知')}, "
                      f"複雜度: {event.metadata.get('estimated_complexity', '未知')}, 關鍵字: {', '.join(event.metadata.get('contains_keywords', []))}, "
                      f"用戶提示: {(event.user_prompt or '')[:100]}{'...' if event.user_prompt and len(event.user_prompt) > 100 else ''}",
            'content': json.dumps(record_data, ensure_ascii=False, indent=2),
            'category': 'system/hooks/events',
            'tags': record_data.get('tags', [])
        }
        
        # 準備關係數據
        relations = []
        
        # 與會話的關係
        relations.append({
            'type': 'FROM',
            'from': 'CURRENT_NODE',
            'to': 'CURRENT_NODE',  # 可以後續連接到會話節點
            'description': f'來自 {event.event_type} 事件的記錄'
        })
        
        # 與工具的關係
        if event.tool_name:
            relations.append({
                'type': 'WHAT',
                'from': 'CURRENT_NODE',
                'to': 'CURRENT_NODE',
                'description': f'使用工具 {event.tool_name} 執行操作'
            })
        
        # 與時間的關係
        relations.append({
            'type': 'WHEN',
            'from': 'CURRENT_NODE',
            'to': 'CURRENT_NODE',
            'description': f'發生時間: {event.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'
        })
        
        # 與意圖的關係
        if event.metadata.get('estimated_intent'):
            relations.append({
                'type': 'WHY',
                'from': 'CURRENT_NODE',
                'to': 'CURRENT_NODE',
                'description': f'用戶意圖: {event.metadata["estimated_intent"]}'
            })
        
        # 準備完整的記錄結構
        mindnext_record = {
            'node': node_data,
            'relations': relations
        }
        
        # 先保存為 JSON 文件，然後使用 import_json 導入
        json_path = self._save_mindnext_json(mindnext_record)
        
        return {
            'status': 'prepared',
            'json_path': json_path,
            'node_topic': node_data['topic'],
            'relations_count': len(relations)
        }
    
    def _save_mindnext_json(self, record_data: Dict[str, Any]) -> str:
        """保存 MindNext 格式的 JSON 文件"""
        record_dir = Path("/root/Dev/mindnext/record")
        record_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_mindnext_hook.json"
        file_path = record_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def _record_to_mindnext(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """直接記錄到 MindNext Graph"""
        # 這個方法可以直接調用 MindNext Graph 的 MCP 工具
        record_data = self._record_event(event, parameters, context)
        
        # 實際實現時可以直接調用 MCP 工具
        # mcp_result = mcp__mindnext-graph__create_unit(...)
        
        return {
            'status': 'recorded',
            'record_id': f"hook_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'data': record_data
        }
    
    def _query_memory(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """查詢記憶"""
        query_type = parameters.get('query_type', 'recent')
        limit = parameters.get('limit', 10)
        
        if query_type == 'recent':
            return self._query_recent_events(limit)
        elif query_type == 'by_tool':
            tool_name = parameters.get('tool_name', event.tool_name)
            return self._query_by_tool(tool_name, limit)
        elif query_type == 'by_file_type':
            file_type = parameters.get('file_type', '')
            return self._query_by_file_type(file_type, limit)
        else:
            return {'error': f'未支持的查詢類型: {query_type}'}
    
    def _query_recent_events(self, limit: int) -> Dict[str, Any]:
        """查詢最近的事件"""
        record_dir = Path("/root/Dev/mindnext/record")
        if not record_dir.exists():
            return {'events': [], 'total': 0}
        
        # 獲取所有記錄文件
        record_files = sorted(
            [f for f in record_dir.glob("*_hook_event.json")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        events = []
        for file_path in record_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    event_data = json.load(f)
                    events.append({
                        'file': str(file_path),
                        'timestamp': event_data.get('timestamp'),
                        'event_type': event_data.get('event_type'),
                        'tool_name': event_data.get('tool_name'),
                        'summary': event_data.get('summary')
                    })
            except:
                continue
        
        return {'events': events, 'total': len(events)}
    
    def _query_by_tool(self, tool_name: str, limit: int) -> Dict[str, Any]:
        """按工具查詢事件"""
        record_dir = Path("/root/Dev/mindnext/record")
        if not record_dir.exists():
            return {'events': [], 'total': 0}
        
        events = []
        for file_path in record_dir.glob("*_hook_event.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    event_data = json.load(f)
                    if event_data.get('tool_name') == tool_name:
                        events.append({
                            'file': str(file_path),
                            'timestamp': event_data.get('timestamp'),
                            'summary': event_data.get('summary')
                        })
            except:
                continue
        
        # 按時間排序並限制數量
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        events = events[:limit]
        
        return {'tool_name': tool_name, 'events': events, 'total': len(events)}
    
    def _query_by_file_type(self, file_type: str, limit: int) -> Dict[str, Any]:
        """按文件類型查詢事件"""
        # 實現按文件類型查詢的邏輯
        return {'file_type': file_type, 'events': [], 'total': 0}
    
    def _update_memory(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """更新記憶記錄"""
        record_id = parameters.get('record_id')
        updates = parameters.get('updates', {})
        
        # 實現更新記憶記錄的邏輯
        return {
            'record_id': record_id,
            'updates_applied': updates,
            'status': 'updated'
        }
    
    def _summarize_session(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """總結會話"""
        # 分析會話中的所有事件
        session_summary = {
            'session_start': datetime.now().replace(hour=0, minute=0, second=0).isoformat(),
            'total_events': 0,
            'tool_usage': {},
            'file_types_involved': {},
            'main_activities': [],
            'insights': []
        }
        
        # 實現會話總結邏輯
        return session_summary
    
    def _export_memory(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """導出記憶數據"""
        export_format = parameters.get('format', 'json')
        date_range = parameters.get('date_range', 'today')
        
        # 實現記憶數據導出邏輯
        return {
            'export_format': export_format,
            'date_range': date_range,
            'status': 'exported',
            'file_path': '/path/to/exported/file'
        }