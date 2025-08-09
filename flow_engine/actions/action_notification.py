"""
ActionNotification - 通知動作執行器
"""

from typing import Dict, Any, List
from datetime import datetime
import subprocess
import platform

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionNotification(ActionExecutor):
    """通知動作執行器"""
    
    def get_action_type(self) -> str:
        return "action.notification"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行通知動作"""
        start_time = datetime.now()
        
        try:
            notification_type = parameters.get('type', 'console')
            
            if notification_type == 'console':
                result = self._console_notification(event, parameters)
            elif notification_type == 'system':
                result = self._system_notification(event, parameters)
            elif notification_type == 'toast':
                result = self._toast_notification(event, parameters)
            elif notification_type == 'email':
                result = self._email_notification(event, parameters)
            elif notification_type == 'webhook':
                result = self._webhook_notification(event, parameters)
            elif notification_type == 'slack':
                result = self._slack_notification(event, parameters)
            else:
                return self._create_result(
                    action_id="action.notification",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"未知通知類型: {notification_type}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.notification",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.notification",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _console_notification(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """控制台通知"""
        message = parameters.get('message', self._generate_default_message(event))
        severity = parameters.get('severity', 'info')
        
        # 圖標映射
        icons = {
            'info': '💡',
            'success': '✅', 
            'warning': '⚠️',
            'error': '❌',
            'debug': '🐛',
            'security': '🔒',
            'performance': '⚡',
            'quality': '🔍'
        }
        
        icon = icons.get(severity, '📢')
        formatted_message = f"{icon} {message}"
        
        print(formatted_message)
        
        return {
            'type': 'console',
            'message': message,
            'severity': severity,
            'formatted_message': formatted_message,
            'timestamp': datetime.now().isoformat()
        }
    
    def _system_notification(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """系統通知"""
        title = parameters.get('title', 'MindNext Hooks')
        message = parameters.get('message', self._generate_default_message(event))
        
        try:
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{message}" with title "{title}"'
                ], check=True)
            elif system == 'linux':
                subprocess.run([
                    'notify-send', title, message
                ], check=True)
            elif system == 'windows':
                # Windows 通知需要更複雜的實現
                print(f"系統通知: {title} - {message}")
            
            return {
                'type': 'system',
                'title': title,
                'message': message,
                'system': system,
                'status': 'sent'
            }
            
        except Exception as e:
            return {
                'type': 'system',
                'title': title,
                'message': message,
                'status': 'failed',
                'error': str(e)
            }
    
    def _toast_notification(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Toast 通知（前端）"""
        message = parameters.get('message', self._generate_default_message(event))
        severity = parameters.get('severity', 'info')
        duration = parameters.get('duration', 5000)
        
        # 這可以通過 WebSocket 發送到前端
        toast_data = {
            'type': 'toast',
            'message': message,
            'severity': severity,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        # 實際實現時可以發送到 WebSocket 或消息隊列
        print(f"🍞 Toast: {message} ({severity})")
        
        return toast_data
    
    def _email_notification(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """郵件通知"""
        to_email = parameters.get('to', 'admin@mindnext.dev')
        subject = parameters.get('subject', f'MindNext Hooks 通知 - {event.event_type}')
        message = parameters.get('message', self._generate_detailed_message(event))
        
        # 模擬郵件發送
        email_data = {
            'type': 'email',
            'to': to_email,
            'subject': subject,
            'message': message,
            'status': 'simulated',  # 實際實現時發送真實郵件
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📧 郵件通知: {subject} -> {to_email}")
        
        return email_data
    
    def _webhook_notification(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Webhook 通知"""
        url = parameters.get('url', 'https://hooks.example.com/mindnext')
        payload = {
            'event_type': event.event_type,
            'tool_name': event.tool_name,
            'timestamp': event.timestamp.isoformat(),
            'message': parameters.get('message', self._generate_default_message(event)),
            'metadata': event.metadata
        }
        
        # 模擬 Webhook 調用
        webhook_data = {
            'type': 'webhook',
            'url': url,
            'payload': payload,
            'status': 'simulated',  # 實際實現時發送 HTTP 請求
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"🔗 Webhook: {url}")
        
        return webhook_data
    
    def _slack_notification(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Slack 通知"""
        channel = parameters.get('channel', '#mindnext-hooks')
        username = parameters.get('username', 'MindNext Bot')
        message = parameters.get('message', self._generate_default_message(event))
        
        # Slack 消息格式
        slack_payload = {
            'channel': channel,
            'username': username,
            'text': message,
            'attachments': [
                {
                    'color': self._get_severity_color(parameters.get('severity', 'info')),
                    'fields': [
                        {
                            'title': '事件類型',
                            'value': event.event_type,
                            'short': True
                        },
                        {
                            'title': '工具',
                            'value': event.tool_name or 'N/A',
                            'short': True
                        },
                        {
                            'title': '時間',
                            'value': event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            'short': False
                        }
                    ]
                }
            ]
        }
        
        slack_data = {
            'type': 'slack',
            'channel': channel,
            'payload': slack_payload,
            'status': 'simulated',  # 實際實現時發送到 Slack API
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"💬 Slack: {channel} - {message}")
        
        return slack_data
    
    def _generate_default_message(self, event: HookEvent) -> str:
        """生成默認消息"""
        if event.event_type == "PostToolUse":
            file_info = f" ({len(event.file_paths)} files)" if event.file_paths else ""
            return f"Completed {event.tool_name} operation{file_info}"
        elif event.event_type == "UserPromptSubmit":
            return f"收到用戶提示: {event.user_prompt[:50]}..." if event.user_prompt else "收到用戶提示"
        elif event.event_type == "PreToolUse":
            return f"準備執行 {event.tool_name}"
        else:
            return f"Hook 事件: {event.event_type}"
    
    def _generate_detailed_message(self, event: HookEvent) -> str:
        """生成詳細消息"""
        details = [
            f"事件類型: {event.event_type}",
            f"時間: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        if event.tool_name:
            details.append(f"工具: {event.tool_name}")
        
        if event.file_paths:
            details.append(f"文件: {', '.join(event.file_paths)}")
        
        if event.user_prompt:
            details.append(f"用戶提示: {event.user_prompt}")
        
        if event.metadata:
            details.append("元數據:")
            for key, value in event.metadata.items():
                details.append(f"  {key}: {value}")
        
        return '\n'.join(details)
    
    def _get_severity_color(self, severity: str) -> str:
        """獲取嚴重程度顏色"""
        colors = {
            'info': '#36a64f',      # 綠色
            'success': '#2eb886',   # 深綠色
            'warning': '#ff9500',   # 橙色
            'error': '#ff0000',     # 紅色
            'debug': '#808080',     # 灰色
            'security': '#ff6b6b',  # 紅色
            'performance': '#4ecdc4', # 青色
            'quality': '#45b7d1'    # 藍色
        }
        return colors.get(severity, '#36a64f')