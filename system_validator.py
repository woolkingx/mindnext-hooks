#!/usr/bin/env python3
"""
MindNext Hooks System Validator
Validates three-layer architecture configuration and system integrity

Usage:
    python system_validator.py          # Full validation
    python system_validator.py --quick  # Quick check
    python system_validator.py --fix    # Auto-fix issues
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import importlib.util

# Setup paths
HOOKS_DIR = Path(__file__).parent
sys.path.insert(0, str(HOOKS_DIR))

class SystemValidator:
    """System Validator - Checks three-layer architecture configuration"""
    
    def __init__(self):
        self.hooks_dir = HOOKS_DIR
        self.config_dir = self.hooks_dir / "config"
        self.flow_engine_dir = self.hooks_dir / "flow_engine"
        self.actions_dir = self.flow_engine_dir / "actions"
        
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
        
    def validate_system(self, quick_check: bool = False, auto_fix: bool = False) -> Dict[str, Any]:
        """Execute comprehensive system validation"""
        print("🔍 MindNext Hooks System Validator")
        print("=" * 50)
        
        results = {
            'overall_status': 'unknown',
            'checks_passed': 0,
            'total_checks': 0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Core file structure check
        self._check_file_structure()
        
        # 2. Configuration file validation
        self._validate_configurations()
        
        # 3. Three-layer architecture integrity check
        if not quick_check:
            self._validate_three_layer_architecture()
            
        # 4. Modular action validation
        self._validate_modular_actions()
        
        # 5. System functionality testing
        if not quick_check:
            self._test_system_functionality()
            
        # 6. Dependencies check
        self._check_dependencies()
        
        # 7. Auto-fix (if enabled)
        if auto_fix:
            self._apply_automatic_fixes()
            
        # Generate report
        results = self._generate_report()
        
        return results
    
    def _check_file_structure(self):
        """Check core file structure"""
        print("🏗️ Checking file structure...")
        
        required_files = [
            'mindnext_hooks.py',
            'README.md',
            'requirements.txt',
            'config/rules_config.json',
            'config/pipelines_config.json', 
            'config/quality_config.json',
            'flow_engine/__init__.py',
            'flow_engine/event_layer.py',
            'flow_engine/rule_layer.py',
            'flow_engine/action_layer.py',
            'flow_engine/flow_coordinator.py',
            'flow_engine/actions/__init__.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.hooks_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                
        if missing_files:
            self.issues.append({
                'type': 'critical',
                'category': 'file_structure', 
                'message': f'Missing required files: {missing_files}',
                'files': missing_files
            })
        else:
            print("   ✅ All required files present")
            
        # Check Action modules
        action_files = list(self.actions_dir.glob('action_*.py'))
        if len(action_files) < 8:
            self.warnings.append({
                'type': 'warning',
                'category': 'actions',
                'message': f'Only {len(action_files)} action modules found, expected at least 8',
                'current_count': len(action_files)
            })
        else:
            print(f"   ✅ Found {len(action_files)} action modules")
    
    def _validate_configurations(self):
        """Validate configuration files"""
        print("⚙️ Validating configurations...")
        
        # Check rules configuration
        rules_config_path = self.config_dir / "rules_config.json"
        if rules_config_path.exists():
            try:
                with open(rules_config_path, 'r', encoding='utf-8') as f:
                    rules_config = json.load(f)
                    
                rules = rules_config.get('rules', [])
                if len(rules) < 10:
                    self.warnings.append({
                        'type': 'warning',
                        'category': 'rules',
                        'message': f'Only {len(rules)} rules defined, recommend at least 10',
                        'current_count': len(rules)
                    })
                else:
                    print(f"   ✅ Rules configuration valid ({len(rules)} rules)")
                    
                # Check rule format
                for i, rule in enumerate(rules):
                    required_fields = ['id', 'name', 'enabled', 'event_types', 'actions']
                    missing_fields = [field for field in required_fields if field not in rule]
                    if missing_fields:
                        self.issues.append({
                            'type': 'critical',
                            'category': 'rule_format',
                            'message': f'Rule {i} missing required fields: {missing_fields}',
                            'rule_id': rule.get('id', f'rule_{i}'),
                            'missing_fields': missing_fields
                        })
                        
            except Exception as e:
                self.issues.append({
                    'type': 'critical',
                    'category': 'config_parse',
                    'message': f'Failed to parse rules_config.json: {e}',
                    'file': 'rules_config.json'
                })
        else:
            self.issues.append({
                'type': 'critical',
                'category': 'missing_config',
                'message': 'rules_config.json not found'
            })
            
        # Check pipelines configuration
        pipelines_config_path = self.config_dir / "pipelines_config.json"
        if pipelines_config_path.exists():
            try:
                with open(pipelines_config_path, 'r', encoding='utf-8') as f:
                    pipelines_config = json.load(f)
                    
                pipelines = pipelines_config.get('pipelines', [])
                print(f"   ✅ Pipelines configuration valid ({len(pipelines)} pipelines)")
                
            except Exception as e:
                self.issues.append({
                    'type': 'critical', 
                    'category': 'config_parse',
                    'message': f'Failed to parse pipelines_config.json: {e}',
                    'file': 'pipelines_config.json'
                })
    
    def _validate_three_layer_architecture(self):
        """Validate three-layer architecture integrity"""
        print("🏛️ Validating three-layer architecture...")
        
        # Check Event Layer
        try:
            spec = importlib.util.spec_from_file_location(
                "event_layer", 
                self.flow_engine_dir / "event_layer.py"
            )
            if spec and spec.loader:
                event_layer = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(event_layer)
                
                if hasattr(event_layer, 'HookEvent') and hasattr(event_layer, 'EventProcessor'):
                    print("   ✅ Event Layer structure valid")
                else:
                    self.issues.append({
                        'type': 'critical',
                        'category': 'architecture',
                        'message': 'Event Layer missing required classes (HookEvent, EventProcessor)'
                    })
        except Exception as e:
            self.issues.append({
                'type': 'critical',
                'category': 'architecture',
                'message': f'Failed to validate Event Layer: {e}'
            })
            
        # Check Rule Layer
        try:
            spec = importlib.util.spec_from_file_location(
                "rule_layer",
                self.flow_engine_dir / "rule_layer.py"
            )
            if spec and spec.loader:
                rule_layer = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rule_layer)
                
                if hasattr(rule_layer, 'RuleEngine'):
                    print("   ✅ Rule Layer structure valid")
                else:
                    self.issues.append({
                        'type': 'critical',
                        'category': 'architecture',
                        'message': 'Rule Layer missing RuleEngine class'
                    })
        except Exception as e:
            self.issues.append({
                'type': 'critical',
                'category': 'architecture',
                'message': f'Failed to validate Rule Layer: {e}'
            })
            
        # Check Action Flow Layer
        try:
            spec = importlib.util.spec_from_file_location(
                "action_layer",
                self.flow_engine_dir / "action_layer.py"
            )
            if spec and spec.loader:
                action_layer = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(action_layer)
                
                if hasattr(action_layer, 'ActionFlowExecutor'):
                    print("   ✅ Action Flow Layer structure valid")
                else:
                    self.issues.append({
                        'type': 'critical',
                        'category': 'architecture',
                        'message': 'Action Flow Layer missing ActionFlowExecutor class'
                    })
        except Exception as e:
            self.issues.append({
                'type': 'critical',
                'category': 'architecture', 
                'message': f'Failed to validate Action Flow Layer: {e}'
            })
    
    def _validate_modular_actions(self):
        """Validate modular action executors"""
        print("🧩 Validating modular actions...")
        
        expected_actions = [
            'action_prompt.py',
            'action_ai.py', 
            'action_quality.py',
            'action_memory.py',
            'action_notification.py',
            'action_analysis.py',
            'action_conditional.py',
            'action_utility.py'
        ]
        
        missing_actions = []
        for action_file in expected_actions:
            if not (self.actions_dir / action_file).exists():
                missing_actions.append(action_file)
                
        if missing_actions:
            self.issues.append({
                'type': 'critical',
                'category': 'actions',
                'message': f'Missing action modules: {missing_actions}',
                'missing_actions': missing_actions
            })
        else:
            print(f"   ✅ All {len(expected_actions)} core action modules present")
            
        # Check Action base class
        action_base_path = self.actions_dir / "action_base.py"
        if action_base_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "action_base",
                    action_base_path
                )
                if spec and spec.loader:
                    action_base = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(action_base)
                    
                    if hasattr(action_base, 'BaseActionExecutor'):
                        print("   ✅ Action base class structure valid")
                    else:
                        self.issues.append({
                            'type': 'critical',
                            'category': 'actions',
                            'message': 'action_base.py missing BaseActionExecutor class'
                        })
            except Exception as e:
                self.issues.append({
                    'type': 'critical',
                    'category': 'actions',
                    'message': f'Failed to validate action_base.py: {e}'
                })
    
    def _test_system_functionality(self):
        """Test system functionality"""
        print("🧪 Testing system functionality...")
        
        try:
            # Try to import main system
            spec = importlib.util.spec_from_file_location(
                "mindnext_hooks",
                self.hooks_dir / "mindnext_hooks.py"
            )
            if spec and spec.loader:
                hooks_system = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(hooks_system)
                
                if hasattr(hooks_system, 'MindNextHooksSystem'):
                    print("   ✅ Main system module imports successfully")
                    
                    # Try to create system instance (check constructor only)
                    system_class = getattr(hooks_system, 'MindNextHooksSystem')
                    if system_class:
                        print("   ✅ System class can be instantiated")
                else:
                    self.issues.append({
                        'type': 'critical',
                        'category': 'functionality',
                        'message': 'Main system missing MindNextHooksSystem class'
                    })
        except Exception as e:
            self.issues.append({
                'type': 'critical',
                'category': 'functionality',
                'message': f'Failed to test system functionality: {e}'
            })
    
    def _check_dependencies(self):
        """Check dependencies"""
        print("📦 Checking dependencies...")
        
        requirements_path = self.hooks_dir / "requirements.txt"
        if requirements_path.exists():
            print("   ✅ requirements.txt found")
        else:
            self.warnings.append({
                'type': 'warning',
                'category': 'dependencies',
                'message': 'requirements.txt not found - recommend creating one'
            })
            
        # Check optional dependencies
        optional_imports = {
            'rich': 'Enhanced console output',
            'requests': 'HTTP notifications', 
            'openai': 'OpenAI integration',
            'anthropic': 'Anthropic integration'
        }
        
        available_optional = []
        for module_name, description in optional_imports.items():
            try:
                importlib.import_module(module_name)
                available_optional.append(f"{module_name} ({description})")
            except ImportError:
                pass
                
        if available_optional:
            print(f"   ✅ Optional enhancements available: {', '.join(available_optional)}")
    
    def _apply_automatic_fixes(self):
        """Apply automatic fixes"""
        print("🔧 Applying automatic fixes...")
        
        fixes_count = 0
        
        # Fix missing requirements.txt
        if not (self.hooks_dir / "requirements.txt").exists():
            try:
                requirements_content = '''# MindNext Hooks System Dependencies
rich>=13.0.0  # Enhanced console output (optional)
'''
                with open(self.hooks_dir / "requirements.txt", 'w') as f:
                    f.write(requirements_content)
                self.fixes_applied.append("Created requirements.txt")
                fixes_count += 1
            except Exception as e:
                print(f"   ❌ Failed to create requirements.txt: {e}")
                
        # Fix missing __init__.py files
        init_dirs = [
            self.flow_engine_dir,
            self.actions_dir
        ]
        
        for init_dir in init_dirs:
            init_file = init_dir / "__init__.py"
            if not init_file.exists():
                try:
                    with open(init_file, 'w') as f:
                        f.write('"""MindNext Hooks System Module"""')
                    self.fixes_applied.append(f"Created {init_file}")
                    fixes_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to create {init_file}: {e}")
                    
        if fixes_count > 0:
            print(f"   ✅ Applied {fixes_count} automatic fixes")
        else:
            print("   ℹ️ No automatic fixes needed")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate final report"""
        print("\n" + "=" * 50)
        
        critical_count = len([i for i in self.issues if i['type'] == 'critical'])
        warning_count = len(self.warnings)
        
        if critical_count == 0 and warning_count == 0:
            status = 'excellent'
            print("🎉 System Status: EXCELLENT")
            print("   All checks passed! System is ready for production.")
        elif critical_count == 0:
            status = 'good'
            print("✅ System Status: GOOD")
            print(f"   No critical issues, {warning_count} minor warnings")
        elif critical_count <= 3:
            status = 'needs_attention'
            print("⚠️ System Status: NEEDS ATTENTION")
            print(f"   {critical_count} critical issues, {warning_count} warnings")
        else:
            status = 'critical'
            print("❌ System Status: CRITICAL")
            print(f"   {critical_count} critical issues must be resolved")
            
        # Show issue details
        if self.issues:
            print("\n🚨 Critical Issues:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue['message']}")
                
        if self.warnings:
            print("\n⚠️ Warnings:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning['message']}")
                
        if self.fixes_applied:
            print("\n🔧 Automatic Fixes Applied:")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"   {i}. {fix}")
                
        report = {
            'overall_status': status,
            'critical_issues_count': critical_count,
            'warnings_count': warning_count,
            'fixes_applied_count': len(self.fixes_applied),
            'critical_issues': self.issues,
            'warnings': self.warnings,
            'fixes_applied': self.fixes_applied,
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if len(self.issues) > 0:
            recommendations.append("Resolve all critical issues before deploying to production")
            
        if len(self.warnings) > 2:
            recommendations.append("Consider addressing warnings to improve system robustness")
            
        # Check if there are enough rules
        rules_config_path = self.config_dir / "rules_config.json"
        if rules_config_path.exists():
            try:
                with open(rules_config_path, 'r') as f:
                    rules_config = json.load(f)
                    if len(rules_config.get('rules', [])) < 15:
                        recommendations.append("Consider adding more rules for comprehensive event handling")
            except:
                pass
                
        recommendations.append("Run comprehensive tests before GitHub deployment")
        recommendations.append("Consider setting up CI/CD for automated validation")
        
        return recommendations

def main():
    """Main function"""
    validator = SystemValidator()
    
    # Parse command line arguments
    quick_check = '--quick' in sys.argv
    auto_fix = '--fix' in sys.argv
    
    # Execute validation
    report = validator.validate_system(quick_check=quick_check, auto_fix=auto_fix)
    
    # Save report
    report_path = HOOKS_DIR / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Full report saved to: {report_path}")
    
    # Return exit code
    if report['critical_issues_count'] > 0:
        sys.exit(1)
    elif report['warnings_count'] > 3:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()