"""
ActionAnalysis - Analysis Action Executor
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionAnalysis(ActionExecutor):
    """Analysis Action Executor"""
    
    def get_action_type(self) -> str:
        return "action.analysis"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """ExecuteAnalysis action"""
        start_time = datetime.now()
        
        try:
            analysis_type = parameters.get('type', 'basic')
            
            if analysis_type == 'basic':
                result = self._basic_analysis(event, parameters, context)
            elif analysis_type == 'trend':
                result = self._trend_analysis(event, parameters, context)
            elif analysis_type == 'pattern':
                result = self._pattern_analysis(event, parameters, context)
            elif analysis_type == 'performance':
                result = self._performance_analysis(event, parameters, context)
            elif analysis_type == 'usage':
                result = self._usage_analysis(event, parameters, context)
            elif analysis_type == 'impact':
                result = self._impact_analysis(event, parameters, context)
            else:
                return self._create_result(
                    action_id="action.analysis",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"未知AnalyzeType: {analysis_type}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.analysis",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.analysis",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _basic_analysis(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Basic analysis"""
        analysis = {
            'event_summary': {
                'type': event.event_type,
                'tool': event.tool_name,
                'timestamp': event.timestamp.isoformat(),
                'complexity': event.metadata.get('estimated_complexity', 'unknown'),
                'intent': event.metadata.get('estimated_intent', 'unknown')
            },
            'file_analysis': self._analyze_files(event.file_paths),
            'context_analysis': self._analyze_context(context),
            'recommendations': []
        }
        
        # Generate基本建議
        if event.event_type == "PostToolUse" and event.tool_name in ['Write', 'Edit']:
            analysis['recommendations'].append("建議Execute代碼Quality check")
        
        if event.metadata.get('estimated_intent') == 'create':
            analysis['recommendations'].append("新Create的代碼建議添加Test")
        
        if len(event.file_paths) > 5:
            analysis['recommendations'].append("涉及多files，建議Check一致性")
        
        return analysis
    
    def _analyze_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """AnalyzeFile"""
        if not file_paths:
            return {'total_files': 0}
        
        file_types = {}
        total_size = 0
        languages = set()
        
        for file_path in file_paths:
            path = Path(file_path)
            ext = path.suffix.lower()
            
            # 統計FileType
            file_types[ext] = file_types.get(ext, 0) + 1
            
            # 統計FileSize
            try:
                total_size += path.stat().st_size
            except:
                pass
            
            # 識別編程語言
            lang = self._detect_language(ext)
            if lang != 'unknown':
                languages.add(lang)
        
        return {
            'total_files': len(file_paths),
            'file_types': file_types,
            'total_size': total_size,
            'average_size': total_size / len(file_paths) if file_paths else 0,
            'languages': list(languages)
        }
    
    def _detect_language(self, ext: str) -> str:
        """Detection編程語言"""
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript', 
            '.tsx': 'TypeScript',
            '.rs': 'Rust',
            '.go': 'Go',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        return lang_map.get(ext, 'unknown')
    
    def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze上下文"""
        context_analysis = {
            'session_info': {},
            'recent_activity': {},
            'patterns': []
        }
        
        # SessionInformationAnalyze
        if 'session_id' in context:
            context_analysis['session_info']['id'] = context['session_id']
        
        # 最近活動Analyze
        if 'recent_events' in context:
            recent = context['recent_events']
            context_analysis['recent_activity'] = {
                'event_count': len(recent),
                'event_types': list(set(e.get('type', '') for e in recent)),
                'tools_used': list(set(e.get('tool', '') for e in recent if e.get('tool')))
            }
        
        # 統計InformationAnalyze
        if 'stats' in context:
            stats = context['stats']
            context_analysis['session_stats'] = {
                'total_events': sum(stats.values()) if isinstance(stats, dict) else 0,
                'most_used_tools': self._get_top_tools(stats.get('tools', {}))
            }
        
        return context_analysis
    
    def _get_top_tools(self, tool_stats: Dict[str, int]) -> List[Dict[str, Any]]:
        """獲取最常用的Tool"""
        if not tool_stats:
            return []
        
        sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1], reverse=True)
        return [{'tool': tool, 'count': count} for tool, count in sorted_tools[:3]]
    
    def _trend_analysis(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Trend analysis"""
        return {
            'analysis_type': 'trend',
            'time_period': parameters.get('period', 'session'),
            'trends': {
                'tool_usage_trend': 'increasing',  # 模擬Data
                'file_modification_trend': 'stable',
                'complexity_trend': 'decreasing'
            },
            'insights': [
                "Tool使用頻率呈上升趨勢",
                "File修改活動保持穩定",
                "代碼複雜度有所改善"
            ]
        }
    
    def _pattern_analysis(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Pattern analysis"""
        patterns = []
        
        # AnalyzeEvent模式
        if context.get('recent_events'):
            recent = context['recent_events']
            
            # Detection重複Operation模式
            event_types = [e.get('type') for e in recent[-5:]]
            if len(set(event_types)) < len(event_types):
                patterns.append({
                    'type': 'repetitive_operations',
                    'description': 'Detection到重複Operation模式',
                    'confidence': 0.8
                })
            
            # DetectionTool切換模式
            tools = [e.get('tool') for e in recent[-3:] if e.get('tool')]
            if len(set(tools)) == len(tools) and len(tools) > 1:
                patterns.append({
                    'type': 'tool_switching',
                    'description': 'Detection到Tool快速切換模式',
                    'confidence': 0.7
                })
        
        # AnalyzeFileOperation模式
        if event.file_paths:
            file_types = [Path(fp).suffix for fp in event.file_paths]
            if len(set(file_types)) == 1:
                patterns.append({
                    'type': 'single_file_type_focus',
                    'description': f'專注於 {file_types[0]} File',
                    'confidence': 0.9
                })
        
        return {
            'analysis_type': 'pattern',
            'patterns_detected': patterns,
            'pattern_count': len(patterns),
            'insights': [p['description'] for p in patterns]
        }
    
    def _performance_analysis(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Performance analysis"""
        return {
            'analysis_type': 'performance',
            'metrics': {
                'response_time': 'fast',      # 模擬Data
                'resource_usage': 'low',
                'error_rate': 'minimal',
                'throughput': 'optimal'
            },
            'bottlenecks': [],
            'recommendations': [
                "當前性能表現良好",
                "建議Continue監控資源使用情況"
            ]
        }
    
    def _usage_analysis(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Usage analysis"""
        usage_stats = {
            'current_session': {
                'duration': self._estimate_session_duration(context),
                'activity_level': self._estimate_activity_level(context),
                'productivity_score': self._calculate_productivity_score(context)
            },
            'tool_preferences': self._analyze_tool_preferences(context),
            'workflow_patterns': self._analyze_workflow_patterns(context)
        }
        
        return {
            'analysis_type': 'usage',
            'stats': usage_stats,
            'insights': self._generate_usage_insights(usage_stats)
        }
    
    def _estimate_session_duration(self, context: Dict[str, Any]) -> str:
        """估計Session持續Time"""
        # 簡化實現，實際應基於Time戳計算
        return "估計 30 分鐘"
    
    def _estimate_activity_level(self, context: Dict[str, Any]) -> str:
        """估計活動水平"""
        recent_events = context.get('recent_events', [])
        if len(recent_events) > 10:
            return 'high'
        elif len(recent_events) > 5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_productivity_score(self, context: Dict[str, Any]) -> float:
        """計算生產力分數"""
        # 簡化的生產力計算
        stats = context.get('stats', {})
        if not stats:
            return 0.5
        
        # 基於Event type計算分數
        productive_events = stats.get('PostToolUse', 0)
        total_events = sum(stats.values()) if isinstance(stats, dict) else 1
        
        return min(1.0, productive_events / total_events)
    
    def _analyze_tool_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AnalyzeTool偏好"""
        tool_stats = context.get('stats', {}).get('tools', {})
        
        if not tool_stats:
            return {'preferred_tools': [], 'diversity_score': 0}
        
        sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1], reverse=True)
        total_usage = sum(tool_stats.values())
        
        return {
            'preferred_tools': sorted_tools[:3],
            'diversity_score': len(tool_stats) / max(1, total_usage),
            'specialization': sorted_tools[0][1] / total_usage if sorted_tools else 0
        }
    
    def _analyze_workflow_patterns(self, context: Dict[str, Any]) -> List[str]:
        """Analyze工作流模式"""
        patterns = []
        recent_events = context.get('recent_events', [])
        
        if len(recent_events) < 3:
            return patterns
        
        # Detection編輯-Test循環
        tools = [e.get('tool') for e in recent_events[-5:]]
        if 'Edit' in tools and ('Test' in tools or 'Bash' in tools):
            patterns.append('edit_test_cycle')
        
        # Detection研究模式
        if 'Read' in tools and 'Grep' in tools:
            patterns.append('research_pattern')
        
        return patterns
    
    def _generate_usage_insights(self, usage_stats: Dict[str, Any]) -> List[str]:
        """Generate使用洞察"""
        insights = []
        
        activity_level = usage_stats['current_session']['activity_level']
        if activity_level == 'high':
            insights.append("當前Session活動水平較高，注意適當休息")
        
        productivity = usage_stats['current_session']['productivity_score']
        if productivity > 0.7:
            insights.append("生產力表現良好，保持當前節奏")
        elif productivity < 0.3:
            insights.append("建議Optimize工作流程以提升效率")
        
        return insights
    
    def _impact_analysis(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Impact analysis"""
        impact = {
            'immediate_impact': self._assess_immediate_impact(event),
            'potential_risks': self._assess_risks(event),
            'benefits': self._assess_benefits(event),
            'recommendations': []
        }
        
        # Generate建議
        if impact['potential_risks']:
            impact['recommendations'].append("建議Evaluate並緩解識別的風險")
        
        if impact['benefits']:
            impact['recommendations'].append("充分利用已識別的優勢")
        
        return {
            'analysis_type': 'impact',
            'assessment': impact,
            'overall_impact_score': self._calculate_impact_score(impact)
        }
    
    def _assess_immediate_impact(self, event: HookEvent) -> List[str]:
        """Evaluate直接影響"""
        impacts = []
        
        if event.tool_name == 'Write':
            impacts.append("新增了代碼或文檔")
        elif event.tool_name == 'Edit':
            impacts.append("修改了現有代碼")
        elif event.tool_name == 'Delete':
            impacts.append("Delete了File或Content")
        
        if len(event.file_paths) > 1:
            impacts.append("影響多files")
        
        return impacts
    
    def _assess_risks(self, event: HookEvent) -> List[str]:
        """Evaluate風險"""
        risks = []
        
        if event.tool_name in ['Delete', 'MultiEdit'] and len(event.file_paths) > 3:
            risks.append("批量修改可能引入Error")
        
        if event.metadata.get('estimated_complexity') == 'complex':
            risks.append("複雜Operation可能需要額外Test")
        
        return risks
    
    def _assess_benefits(self, event: HookEvent) -> List[str]:
        """Evaluate收益"""
        benefits = []
        
        if event.metadata.get('estimated_intent') == 'optimize':
            benefits.append("可能改善代碼性能或結構")
        
        if event.tool_name in ['Write', 'Edit'] and any('.md' in fp for fp in event.file_paths):
            benefits.append("改善了文檔Quality")
        
        return benefits
    
    def _calculate_impact_score(self, impact: Dict[str, Any]) -> float:
        """計算影響分數"""
        positive_score = len(impact['benefits']) * 0.3
        negative_score = len(impact['potential_risks']) * 0.2
        base_score = len(impact['immediate_impact']) * 0.1
        
        return max(0, min(1, base_score + positive_score - negative_score))