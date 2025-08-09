#!/usr/bin/env python3
"""
MindNext Hooks System - Three-Layer Architecture
Event Layer → Rule Layer → Action Flow Layer

A comprehensive, modular, and extensible hooks system for Claude Code.
Designed for global use and easy GitHub distribution.

Architecture:
- Event Layer: Captures and standardizes hook events
- Rule Layer: Matches events to configurable rules with complex conditions
- Action Flow Layer: Executes actions including quality checks, AI analysis, notifications, and memory recording

Core Components:
- Buffer: Event buffering and queuing system
- Cache: High-performance caching for repeated operations
- AI SDK: Integrated AI capabilities for analysis and enhancement

Features:
- 20+ modular action executors
- Comprehensive rule engine with DSL support
- Pipeline-based action flows
- Circuit breakers and rate limiting
- Performance monitoring and statistics
- MindNext Graph integration
- Extensible plugin architecture
"""

import json
import sys
import os
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Setup paths
HOOKS_DIR = Path(__file__).parent
sys.path.insert(0, str(HOOKS_DIR))

# Optional rich console
try:
    from rich.console import Console
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    console = Console()


class MindNextHooksSystem:
    """
    MindNext Hooks System - Three-Layer Architecture
    
    The main entry point for the unified hooks system.
    Handles all Claude Code hook events through a sophisticated three-layer architecture.
    """
    
    def __init__(self, validate_on_startup: bool = None):
        self.hooks_dir = HOOKS_DIR
        self.config_dir = self.hooks_dir / "config"
        
        # Smart validation: only if files changed
        if validate_on_startup is None:
            validate_on_startup = self._should_validate()
            
        if validate_on_startup:
            self._validate_system_configuration()
            self._save_validation_state()
        
        # Initialize Three-Layer Flow Engine
        self.flow_coordinator = None
        self.use_flow_engine = False
        
        try:
            from flow_engine.flow_coordinator import FlowCoordinator
            self.flow_coordinator = FlowCoordinator(str(self.config_dir))
            self.use_flow_engine = True
            console.print("✅ MindNext Three-Layer Flow Engine initialized", style="green")
            
        except Exception as e:
            console.print(f"⚠️ Flow Engine initialization failed: {e}", style="yellow")
            console.print("   Falling back to basic event handling", style="yellow")
            self.use_flow_engine = False
        
        # System statistics
        self.stats = {
            'total_events': 0,
            'successful_events': 0,
            'failed_events': 0,
            'blocked_events': 0,
            'start_time': datetime.now()
        }
    
    def _validate_system_configuration(self) -> bool:
        """
        Validate system configuration on startup using SystemValidator
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            # Import SystemValidator
            import importlib.util
            validator_path = self.hooks_dir / "flow_engine" / "system_validator.py"
            
            if not validator_path.exists():
                console.print("⚠️ SystemValidator not found, skipping validation", style="yellow")
                return True
                
            spec = importlib.util.spec_from_file_location("system_validator", validator_path)
            if spec and spec.loader:
                validator_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(validator_module)
                
                # Create validator instance and run quick check
                validator = validator_module.SystemValidator()
                report = validator.validate_system(quick_check=True, auto_fix=False)
                
                # Check results
                critical_count = report.get('critical_issues_count', 0)
                warnings_count = report.get('warnings_count', 0)
                
                if critical_count == 0:
                    if warnings_count == 0:
                        console.print("✅ System configuration validated successfully", style="green")
                    else:
                        console.print(f"✅ System validated with {warnings_count} minor warnings", style="green")
                    return True
                else:
                    console.print(f"❌ System validation failed: {critical_count} critical issues", style="red")
                    console.print("   Run 'python hooks/flow_engine/system_validator.py --fix' to resolve issues", style="red")
                    
                    # Show critical issues
                    for issue in report.get('critical_issues', [])[:3]:  # Show first 3 issues
                        console.print(f"   • {issue.get('message', 'Unknown issue')}", style="red")
                    
                    return False
                    
        except Exception as e:
            console.print(f"⚠️ System validation error: {e}", style="yellow")
            console.print("   Continuing with startup...", style="yellow")
            return True  # Don't block startup on validation errors
        
        return True
    
    def _should_validate(self) -> bool:
        """Check if validation needed based on file changes"""
        state_file = self.hooks_dir / ".validation_state"
        config_files = list(self.config_dir.glob("*.toml")) + list(self.config_dir.glob("*.json"))
        
        try:
            # Calculate current hash
            current_hash = ""
            for f in sorted(config_files):
                if f.exists():
                    current_hash += hashlib.sha256(f.read_bytes()).hexdigest()
            
            # Check against saved hash
            if state_file.exists():
                saved_hash = state_file.read_text().strip()
                return current_hash != saved_hash
            
            return True  # First run
            
        except Exception:
            return True  # Error = validate
    
    def _save_validation_state(self):
        """Save current file state"""
        try:
            state_file = self.hooks_dir / ".validation_state"
            config_files = list(self.config_dir.glob("*.toml")) + list(self.config_dir.glob("*.json"))
            
            current_hash = ""
            for f in sorted(config_files):
                if f.exists():
                    current_hash += hashlib.sha256(f.read_bytes()).hexdigest()
            
            state_file.write_text(current_hash)
        except Exception:
            pass  # Silent fail
    
    async def process_hook_event(self, event_type: str, event_data: Dict[str, Any]) -> int:
        """
        Process a hook event through the Three-Layer Architecture
        
        Args:
            event_type: The type of hook event (UserPromptSubmit, PostToolUse, etc.)
            event_data: The event data payload
        
        Returns:
            Exit code (0=success, 2=block operation)
        """
        start_time = datetime.now()
        self.stats['total_events'] += 1
        
        try:
            if self.use_flow_engine and self.flow_coordinator:
                # Process through Three-Layer Architecture
                result = await self.flow_coordinator.process_hook_event(event_type, event_data)
                
                if result.get('success'):
                    processing_time = result.get('processing_time', 0)
                    actions_executed = result.get('actions_executed', 0)
                    rules_matched = len(result.get('rules_matched', []))
                    
                    console.print(
                        f"✅ [{event_type}] Processed in {processing_time:.3f}s | "
                        f"{rules_matched} rules → {actions_executed} actions",
                        style="green"
                    )
                    
                    # Check for blocking results
                    results = result.get('results', [])
                    for action_result in results:
                        if (action_result.get('action_id') == 'block_operation' or 
                            not action_result.get('success', True)):
                            console.print("🛑 Operation blocked by rule", style="red")
                            self.stats['blocked_events'] += 1
                            return 2
                    
                    self.stats['successful_events'] += 1
                    return 0
                else:
                    error_msg = result.get('error', 'Unknown error')
                    console.print(f"❌ [{event_type}] Processing failed: {error_msg}", style="red")
                    self.stats['failed_events'] += 1
                    return self._fallback_process(event_type, event_data)
                    
            else:
                # Fallback processing
                return self._fallback_process(event_type, event_data)
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            console.print(f"❌ [{event_type}] System error: {e}", style="red")
            self.stats['failed_events'] += 1
            return 0  # Don't block on system errors
    
    def _fallback_process(self, event_type: str, event_data: Dict[str, Any]) -> int:
        """Fallback processing when Flow Engine is not available"""
        # Stop events should be completely silent
        if event_type == "Stop":
            return 0
            
        console.print(f"🔄 [{event_type}] Using fallback processing", style="yellow")
        
        # Basic event acknowledgment
        if event_type == "SessionStart":
            console.print("🌟 Welcome to MindNext Hooks System!", style="cyan")
            console.print("   Three-Layer Architecture: Event → Rule → Action", style="cyan")
            
        elif event_type == "UserPromptSubmit":
            prompt = event_data.get('user_prompt', '')
            if prompt and len(prompt) > 100:
                console.print("💡 Long prompt detected - consider using AI enhancement", style="blue")
                
        elif event_type == "PostToolUse":
            tool_name = event_data.get('tool_name', '')
            if tool_name in ['Write', 'Edit', 'MultiEdit']:
                console.print("📝 Code modification detected - quality check recommended", style="blue")
        
        return 0
    
    # === Management and Statistics Methods ===
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        # Create serializable stats copy
        serializable_stats = self.stats.copy()
        serializable_stats['start_time'] = self.stats['start_time'].isoformat()
        
        status = {
            'system': {
                'status': 'operational' if self.use_flow_engine else 'fallback',
                'uptime_seconds': uptime,
                'flow_engine_enabled': self.use_flow_engine
            },
            'statistics': serializable_stats,
            'performance': {
                'success_rate': (
                    self.stats['successful_events'] / max(1, self.stats['total_events'])
                ),
                'block_rate': (
                    self.stats['blocked_events'] / max(1, self.stats['total_events'])
                ),
                'events_per_minute': (
                    self.stats['total_events'] / max(1, uptime / 60)
                )
            }
        }
        
        if self.use_flow_engine and self.flow_coordinator:
            status['flow_engine'] = self.flow_coordinator.get_system_status()
            
        return status
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get rule execution statistics"""
        if self.use_flow_engine and self.flow_coordinator:
            return self.flow_coordinator.get_rule_statistics()
        return {'error': 'Flow Engine not available'}
    
    def get_action_statistics(self) -> Dict[str, Any]:
        """Get action execution statistics"""
        if self.use_flow_engine and self.flow_coordinator:
            return self.flow_coordinator.get_action_statistics()
        return {'error': 'Flow Engine not available'}
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule"""
        if self.use_flow_engine and self.flow_coordinator:
            return self.flow_coordinator.enable_rule(rule_id)
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule"""
        if self.use_flow_engine and self.flow_coordinator:
            return self.flow_coordinator.disable_rule(rule_id)
        return False
    
    def reload_configuration(self) -> Dict[str, Any]:
        """Reload all system configuration"""
        if self.use_flow_engine and self.flow_coordinator:
            result = self.flow_coordinator.reload_configuration()
            console.print("🔄 Configuration reloaded", style="green")
            return result
        return {'success': False, 'error': 'Flow Engine not available'}
    
    async def test_system(self) -> Dict[str, Any]:
        """Run comprehensive system test"""
        console.print("🧪 Running MindNext Hooks System Test...", style="cyan")
        
        test_events = [
            {
                'type': 'UserPromptSubmit',
                'data': {
                    'hook_event_name': 'UserPromptSubmit',
                    'user_prompt': 'Test the MindNext Three-Layer Flow Engine system'
                }
            },
            {
                'type': 'PostToolUse',
                'data': {
                    'hook_event_name': 'PostToolUse',
                    'tool_name': 'Write',
                    'tool_input': {
                        'file_path': '/test/sample.py',
                        'content': 'print("Hello, MindNext Three-Layer Architecture!")'
                    },
                    'env': {'CLAUDE_FILE_PATHS': '/test/sample.py'}
                }
            }
        ]
        
        results = []
        for test_event in test_events:
            try:
                result_code = await self.process_hook_event(
                    test_event['type'],
                    test_event['data']
                )
                results.append({
                    'event_type': test_event['type'],
                    'success': result_code == 0,
                    'result_code': result_code
                })
            except Exception as e:
                results.append({
                    'event_type': test_event['type'],
                    'success': False,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r.get('success', False))
        
        console.print(
            f"✅ System test completed: {success_count}/{len(results)} events successful",
            style="green" if success_count == len(results) else "yellow"
        )
        
        return {
            'overall_success': success_count == len(results),
            'test_results': results,
            'system_status': self.get_system_status()
        }
    
    def export_report(self) -> str:
        """Export comprehensive system report"""
        if self.use_flow_engine and self.flow_coordinator:
            report_result = self.flow_coordinator.export_execution_report('json')
            if report_result.get('success'):
                return report_result['report_path']
        
        # Fallback: export basic report
        report_dir = Path("/root/Dev/mindnext/record")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"hooks_system_report_{timestamp}.json"
        
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'system_status': self.get_system_status(),
            'message': 'Basic report - Flow Engine not available'
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return str(report_path)


async def main():
    """Main entry point for MindNext Hooks System"""
    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            # Check for special commands
            if sys.argv[1] == '--test':
                system = MindNextHooksSystem()
                test_result = await system.test_system()
                print(json.dumps(test_result, indent=2))
                return
                
            elif sys.argv[1] == '--status':
                system = MindNextHooksSystem()
                status = system.get_system_status()
                print(json.dumps(status, indent=2))
                return
                
            elif sys.argv[1] == '--export-report':
                system = MindNextHooksSystem()
                report_path = system.export_report()
                print(f"Report exported to: {report_path}")
                return
            
            # Check if it's an event type
            event_type_arg = sys.argv[1]
            valid_events = [
                'UserPromptSubmit', 'PreToolUse', 'PostToolUse',
                'Notification', 'Stop', 'SubagentStop', 
                'PreCompact', 'SessionStart'
            ]
            
            if event_type_arg in valid_events:
                # Read actual event data from stdin
                stdin_data = sys.stdin.read()
                if stdin_data:
                    hook_input = json.loads(stdin_data)
                    hook_input['hook_event_name'] = event_type_arg
                else:
                    hook_input = {'hook_event_name': event_type_arg}
            else:
                # Try to parse as JSON
                hook_input = json.loads(sys.argv[1])
        else:
            # Read from stdin
            hook_input = json.loads(sys.stdin.read())
        
        # Extract event type
        event_type = hook_input.get('hook_event_name', '')
        if not event_type:
            console.print("❌ No event type specified", style="red")
            sys.exit(0)
        
        # Create system instance and process event
        system = MindNextHooksSystem()
        exit_code = await system.process_hook_event(event_type, hook_input)
        
        sys.exit(exit_code)
        
    except json.JSONDecodeError as e:
        console.print(f"❌ JSON parsing error: {e}", style="red")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ MindNext Hooks System error: {e}", style="red")
        sys.exit(0)


def run_sync_main():
    """Synchronous wrapper for the async main function"""
    asyncio.run(main())


if __name__ == '__main__':
    run_sync_main()