#!/usr/bin/env python3
"""
MindNext Hooks - Core Claude SDK Service
=======================================

Core Claude SDK service for AI-powered analysis and intelligent suggestions.
This is a SYSTEM SERVICE that provides centralized AI capabilities.

Features:
- Unified Claude SDK interface
- AI-powered analysis and insights
- Pattern recognition and suggestions
- Error prevention and optimization
- Thread-safe operations
"""

import os
import sys
import json
import subprocess
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from pathlib import Path


class CoreClaudeSDK:
    """
    Core Claude SDK System - AI capabilities service
    
    This is a system-level service that provides centralized AI functionality
    for all components in the MindNext Hooks system.
    """
    
    def __init__(self):
        self.sdk_available = self._check_sdk_availability()
        self.request_history = []
        self.analysis_cache = {}
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'created_at': datetime.now()
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Analysis templates
        self.analysis_templates = self._init_analysis_templates()
    
    def _check_sdk_availability(self) -> bool:
        """Check if Claude SDK is available"""
        try:
            # Check if claude_sdk.py exists in parent directory
            sdk_path = Path(__file__).parent.parent / "claude_sdk.py"
            return sdk_path.exists()
        except Exception:
            return False
    
    def _init_analysis_templates(self) -> Dict[str, str]:
        """Initialize analysis prompt templates"""
        return {
            'pattern_detection': """
分析以下開發會話事件，識別操作模式和工作流程：

事件數據：
{event_data}

請以 JSON 格式回應：
{{
  "patterns": [
    {{"name": "模式名稱", "frequency": 次數, "description": "描述"}}
  ],
  "workflows": [
    {{"name": "流程名稱", "steps": ["步驟1", "步驟2"], "optimization": "優化建議"}}
  ],
  "automation_opportunities": ["自動化機會1", "自動化機會2"]
}}
""",
            
            'error_prevention': """
基於以下開發活動，預測潛在問題和風險：

最近活動：
{recent_activities}

工具使用：
{tool_usage}

請以 JSON 格式回應：
{{
  "risks": [
    {{"type": "風險類型", "severity": "high/medium/low", "description": "描述"}}
  ],
  "prevention_suggestions": ["建議1", "建議2"],
  "best_practices": ["最佳實踐1", "最佳實踐2"]
}}
""",
            
            'productivity_insights': """
分析開發生產力和效率：

統計資料：
{statistics}

事件分布：
{event_distribution}

請以 JSON 格式回應：
{{
  "productivity_score": 0-100,
  "efficiency_analysis": {{"score": 0-100, "insights": "分析"}},
  "improvement_suggestions": ["建議1", "建議2", "建議3"],
  "tool_recommendations": [
    {{"tool": "工具名", "reason": "推薦原因"}}
  ]
}}
""",
            
            'smart_suggestions': """
基於當前開發上下文，提供智能建議：

當前狀態：
{current_context}

歷史模式：
{historical_patterns}

請以 JSON 格式回應：
{{
  "next_steps": ["下一步建議1", "下一步建議2"],
  "potential_issues": ["可能問題1", "可能問題2"],
  "knowledge_reminders": ["提醒1", "提醒2"],
  "workflow_optimization": ["優化建議1", "優化建議2"]
}}
""",
            
            'code_quality': """
分析代碼修改和品質：

修改記錄：
{code_changes}

工具使用：
{development_tools}

請以 JSON 格式回應：
{{
  "quality_score": 0-100,
  "code_health": {{"score": 0-100, "issues": ["問題1", "問題2"]}},
  "testing_suggestions": ["測試建議1", "測試建議2"],
  "refactoring_opportunities": ["重構機會1", "重構機會2"]
}}
"""
        }
    
    # === Core SDK Operations ===
    
    def call_claude(self, prompt: str, system_prompt: Optional[str] = None, 
                   cache_key: Optional[str] = None) -> Optional[str]:
        """
        Call Claude SDK with unified interface
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            cache_key: Cache key for result caching (optional)
        
        Returns:
            Claude response or None if failed
        """
        with self._lock:
            self.stats['total_requests'] += 1
            
            # Check cache first
            if cache_key and cache_key in self.analysis_cache:
                cache_entry = self.analysis_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < timedelta(hours=1):
                    self.stats['cache_hits'] += 1
                    return cache_entry['response']
            
            if not self.sdk_available:
                return self._fallback_response(prompt)
            
            try:
                # Call external Claude SDK
                result = self._call_external_sdk(prompt, system_prompt)
                
                if result:
                    self.stats['successful_requests'] += 1
                    
                    # Cache successful results
                    if cache_key:
                        self.analysis_cache[cache_key] = {
                            'response': result,
                            'timestamp': datetime.now()
                        }
                    
                    # Add to request history
                    self.request_history.append({
                        'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                        'success': True,
                        'timestamp': datetime.now().isoformat(),
                        'cache_key': cache_key
                    })
                    
                    return result
                else:
                    self.stats['failed_requests'] += 1
                    return self._fallback_response(prompt)
                    
            except Exception as e:
                print(f"Claude SDK error: {e}", file=sys.stderr)
                self.stats['failed_requests'] += 1
                return self._fallback_response(prompt)
    
    def _call_external_sdk(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Call external Claude SDK"""
        try:
            # Prepare the SDK call
            sdk_path = Path(__file__).parent.parent / "claude_sdk.py"
            
            # Build command
            cmd = [sys.executable, str(sdk_path)]
            
            # Prepare input
            input_data = {
                'prompt': prompt,
                'system_prompt': system_prompt or "你是 MindNext 助手，請以 JSON 格式回應。"
            }
            
            # Execute SDK
            result = subprocess.run(
                cmd,
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"SDK stderr: {result.stderr}", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"External SDK call failed: {e}", file=sys.stderr)
            return None
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when SDK is not available"""
        return json.dumps({
            "status": "fallback",
            "message": "Claude SDK 不可用，使用基本分析",
            "suggestions": [
                "檢查 Claude SDK 配置",
                "使用離線分析模式",
                "查看系統日誌"
            ],
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
    
    # === Analysis Methods ===
    
    def analyze_patterns(self, event_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in event data"""
        template = self.analysis_templates['pattern_detection']
        simplified_data = self._simplify_event_data(event_data)
        
        prompt = template.format(event_data=json.dumps(simplified_data, indent=2))
        cache_key = f"patterns_{hash(str(simplified_data))}"
        
        response = self.call_claude(prompt, cache_key=cache_key)
        return self._parse_json_response(response, 'pattern_detection')
    
    def analyze_risks(self, recent_activities: List[Dict], tool_usage: Dict[str, int]) -> Dict[str, Any]:
        """Analyze potential risks and issues"""
        template = self.analysis_templates['error_prevention']
        
        prompt = template.format(
            recent_activities=json.dumps(recent_activities, indent=2),
            tool_usage=json.dumps(tool_usage, indent=2)
        )
        cache_key = f"risks_{hash(str(recent_activities))}"
        
        response = self.call_claude(prompt, cache_key=cache_key)
        return self._parse_json_response(response, 'error_prevention')
    
    def analyze_productivity(self, statistics: Dict[str, Any], 
                           event_distribution: Dict[str, int]) -> Dict[str, Any]:
        """Analyze productivity and efficiency"""
        template = self.analysis_templates['productivity_insights']
        
        prompt = template.format(
            statistics=json.dumps(statistics, indent=2),
            event_distribution=json.dumps(event_distribution, indent=2)
        )
        cache_key = f"productivity_{hash(str(statistics))}"
        
        response = self.call_claude(prompt, cache_key=cache_key)
        return self._parse_json_response(response, 'productivity_insights')
    
    def get_smart_suggestions(self, current_context: Dict[str, Any], 
                            historical_patterns: List[Dict]) -> Dict[str, Any]:
        """Get smart suggestions based on context"""
        template = self.analysis_templates['smart_suggestions']
        
        prompt = template.format(
            current_context=json.dumps(current_context, indent=2),
            historical_patterns=json.dumps(historical_patterns, indent=2)
        )
        cache_key = f"suggestions_{hash(str(current_context))}"
        
        response = self.call_claude(prompt, cache_key=cache_key)
        return self._parse_json_response(response, 'smart_suggestions')
    
    def analyze_code_quality(self, code_changes: List[Dict], 
                           development_tools: Dict[str, int]) -> Dict[str, Any]:
        """Analyze code quality and development practices"""
        template = self.analysis_templates['code_quality']
        
        prompt = template.format(
            code_changes=json.dumps(code_changes, indent=2),
            development_tools=json.dumps(development_tools, indent=2)
        )
        cache_key = f"quality_{hash(str(code_changes))}"
        
        response = self.call_claude(prompt, cache_key=cache_key)
        return self._parse_json_response(response, 'code_quality')
    
    # === Utility Methods ===
    
    def _simplify_event_data(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplify event data for analysis"""
        simplified = []
        for event in events[-20:]:  # Last 20 events
            simplified.append({
                'type': event.get('type'),
                'tool': event.get('context', {}).get('tool'),
                'timestamp': event.get('timestamp'),
                'session_time': event.get('session_time')
            })
        return simplified
    
    def _parse_json_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse JSON response from Claude"""
        if not response:
            return self._fallback_analysis(analysis_type)
        
        try:
            # Try to find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {'raw_response': response, 'analysis_type': analysis_type}
                
        except json.JSONDecodeError:
            return {'raw_response': response, 'analysis_type': analysis_type}
    
    def _fallback_analysis(self, analysis_type: str) -> Dict[str, Any]:
        """Fallback analysis when AI is not available"""
        fallbacks = {
            'pattern_detection': {
                'patterns': [],
                'workflows': [],
                'automation_opportunities': ['考慮使用腳本自動化重複任務']
            },
            'error_prevention': {
                'risks': [],
                'prevention_suggestions': ['定期備份', '謹慎使用刪除操作'],
                'best_practices': ['遵循編碼規範', '編寫測試']
            },
            'productivity_insights': {
                'productivity_score': 70,
                'efficiency_analysis': {'score': 70, 'insights': '正常開發節奏'},
                'improvement_suggestions': ['使用快捷鍵', '批量處理任務'],
                'tool_recommendations': []
            },
            'smart_suggestions': {
                'next_steps': ['繼續當前任務'],
                'potential_issues': [],
                'knowledge_reminders': [],
                'workflow_optimization': []
            },
            'code_quality': {
                'quality_score': 75,
                'code_health': {'score': 75, 'issues': []},
                'testing_suggestions': ['增加單元測試'],
                'refactoring_opportunities': []
            }
        }
        
        result = fallbacks.get(analysis_type, {})
        result.update({
            'fallback_mode': True,
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get SDK system status"""
        with self._lock:
            uptime = datetime.now() - self.stats['created_at']
            success_rate = 0
            
            if self.stats['total_requests'] > 0:
                success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            
            return {
                'service': 'CoreClaudeSDK',
                'status': 'operational' if self.sdk_available else 'limited',
                'sdk_available': self.sdk_available,
                'performance': {
                    'success_rate_percent': round(success_rate, 2),
                    'cache_hit_rate_percent': round((self.stats['cache_hits'] / max(1, self.stats['total_requests'])) * 100, 2),
                    'total_requests': self.stats['total_requests'],
                    'successful_requests': self.stats['successful_requests'],
                    'failed_requests': self.stats['failed_requests']
                },
                'uptime_seconds': uptime.total_seconds(),
                'cache_entries': len(self.analysis_cache),
                'request_history_size': len(self.request_history)
            }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear analysis cache"""
        with self._lock:
            cache_size = len(self.analysis_cache)
            self.analysis_cache.clear()
            
            return {
                'success': True,
                'cleared_entries': cache_size,
                'message': 'Analysis cache cleared'
            }
    
    def get_recent_requests(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent SDK requests"""
        with self._lock:
            return self.request_history[-count:] if self.request_history else []


# Singleton instance
_core_claude_sdk = None

def get_core_claude_sdk() -> CoreClaudeSDK:
    """Get core Claude SDK instance"""
    global _core_claude_sdk
    if _core_claude_sdk is None:
        _core_claude_sdk = CoreClaudeSDK()
    return _core_claude_sdk


# Convenience functions for actions
def call_claude_sdk(prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
    """Convenience function for calling Claude SDK"""
    sdk = get_core_claude_sdk()
    return sdk.call_claude(prompt, system_prompt)


if __name__ == '__main__':
    # Test Core Claude SDK
    sdk = get_core_claude_sdk()
    
    print("=== Core Claude SDK Test ===")
    print(f"SDK Available: {sdk.sdk_available}")
    
    # Test basic call
    response = sdk.call_claude("分析這個測試請求", "你是測試助手")
    print(f"Test response: {response[:100]}...")
    
    # Test pattern analysis
    test_events = [
        {'type': 'UserPromptSubmit', 'context': {'tool': 'query'}, 'timestamp': '2025-01-01T10:00:00'},
        {'type': 'PostToolUse', 'context': {'tool': 'mcp__mindnext-graph__execute_template'}, 'timestamp': '2025-01-01T10:01:00'}
    ]
    
    patterns = sdk.analyze_patterns(test_events)
    print(f"Pattern analysis: {json.dumps(patterns, indent=2, ensure_ascii=False)[:200]}...")
    
    # Show status
    status = sdk.get_system_status()
    print(f"System status: {json.dumps(status, indent=2)}")
    
    print("\n✅ Core Claude SDK is ready!")