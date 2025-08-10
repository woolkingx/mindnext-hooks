#!/usr/bin/env python3
"""
MindNext Hooks Config Validator
Simple validator that scans actual code and validates config files
"""

import os
import json
import toml
from pathlib import Path
from datetime import datetime
from typing import Set, List, Dict, Any

class ConfigValidator:
    """Simple config validator - scans code and validates TOML configs"""
    
    def __init__(self, hooks_dir: Path = None):
        self.hooks_dir = hooks_dir or Path(__file__).parent.parent
        self.config_dir = self.hooks_dir / "config"
        self.flow_engine_dir = self.hooks_dir / "flow_engine"
        self.actions_dir = self.flow_engine_dir / "actions"
        
    def scan_available_components(self) -> Dict[str, Set[str]]:
        """Scan actual code to find available Events, Rules, Actions"""
        components = {
            'events': set(),
            'rules': set(), 
            'actions': set()
        }
        
        # Import supported events from event_layer
        events_file = self.flow_engine_dir / "event_layer.py"
        if events_file.exists():
            content = events_file.read_text()
            import re
            # Find SUPPORTED_EVENTS definition
            match = re.search(r'SUPPORTED_EVENTS\s*=\s*\{([^}]+)\}', content, re.DOTALL)
            if match:
                events_str = match.group(1)
                events = re.findall(r"['\"](\w+)['\"]", events_str)
                components['events'].update(events)
        
        # Import supported rules from rule_layer
        rules_file = self.flow_engine_dir / "rule_layer.py"  
        if rules_file.exists():
            content = rules_file.read_text()
            # Find SUPPORTED_RULE_TYPES definition
            match = re.search(r'SUPPORTED_RULE_TYPES\s*=\s*\{([^}]+)\}', content, re.DOTALL)
            if match:
                rules_str = match.group(1)
                rules = re.findall(r"['\"](\w+)['\"]", rules_str)
                components['rules'].update(rules)
        
        # Scan actions from actions directory
        if self.actions_dir.exists():
            for action_file in self.actions_dir.glob("action_*.py"):
                if action_file.name != "action_base.py":
                    action_name = action_file.stem.replace("action_", "action.")
                    components['actions'].add(action_name)
        
        return components
    
    def parse_config_references(self) -> Dict[str, Any]:
        """Parse config files to extract used Events, Rules, Actions and detect conflicts"""
        references = {
            'events': set(),
            'rules': set(),
            'actions': set(),
            'mappings': []  # Store all mappings for conflict detection
        }
        
        # Parse all TOML config files
        for config_file in self.config_dir.glob("*.toml"):
            try:
                config = toml.load(config_file)
                
                # Skip disabled configs
                if not config.get('config', {}).get('enable', True):
                    continue
                
                # Extract mappings
                mappings = config.get('mappings', [])
                for mapping in mappings:
                    # Skip disabled mappings
                    if not mapping.get('enable', True):
                        continue
                        
                    # Extract event
                    event = mapping.get('event')
                    if event:
                        references['events'].add(event)
                    
                    # Extract rule
                    rule = mapping.get('rule') 
                    if rule:
                        references['rules'].add(rule)
                    
                    # Extract actions from action_flow
                    action_flow = mapping.get('action_flow', [])
                    for action_ref in action_flow:
                        if isinstance(action_ref, str) and '/' in action_ref:
                            action_type = action_ref.split('/')[0]
                            references['actions'].add(action_type)
                    
                    # Store mapping for conflict detection
                    references['mappings'].append({
                        'file': config_file.name,
                        'event': event,
                        'rule': rule,
                        'condition': mapping.get('condition'),
                        'action_flow': action_flow
                    })
                            
            except Exception as e:
                print(f"⚠️ Error parsing {config_file}: {e}")
        
        return references
    
    def detect_conflicts(self, mappings: List[Dict]) -> List[Dict]:
        """Detect conflicts in rule mappings"""
        conflicts = []
        
        # Group mappings by event+rule+condition
        mapping_groups = {}
        for mapping in mappings:
            # Create unique key for grouping
            key = f"{mapping['event']}:{mapping['rule']}:{str(mapping['condition'])}"
            if key not in mapping_groups:
                mapping_groups[key] = []
            mapping_groups[key].append(mapping)
        
        # Check for conflicts
        for key, group in mapping_groups.items():
            if len(group) > 1:
                # Check if action_flows are different
                action_flows = [str(m['action_flow']) for m in group]
                if len(set(action_flows)) > 1:
                    conflicts.append({
                        'type': 'conflict',
                        'event': group[0]['event'],
                        'rule': group[0]['rule'],
                        'condition': group[0]['condition'],
                        'conflicting_files': [m['file'] for m in group],
                        'conflicting_actions': [m['action_flow'] for m in group]
                    })
        
        return conflicts
    
    def validate_config(self) -> Dict[str, Any]:
        """Main validation function"""
        print("🔍 MindNext Config Validator")
        print("=" * 40)
        
        # Scan actual code
        print("📂 Scanning available components...")
        available = self.scan_available_components()
        
        print(f"   Events: {len(available['events'])}")
        print(f"   Rules: {len(available['rules'])}")  
        print(f"   Actions: {len(available['actions'])}")
        
        # Parse config references
        print("\n📋 Parsing config references...")
        references = self.parse_config_references()
        
        print(f"   Events used: {len(references['events'])}")
        print(f"   Rules used: {len(references['rules'])}")
        print(f"   Actions used: {len(references['actions'])}")
        
        # Validate references
        print("\n✅ Validating references...")
        issues = []
        
        # Check Events
        missing_events = references['events'] - available['events']
        if missing_events:
            issues.append({
                'type': 'error',
                'category': 'events',
                'message': f'Unknown events in config: {list(missing_events)}'
            })
        
        # Check Rules  
        missing_rules = references['rules'] - available['rules']
        if missing_rules:
            issues.append({
                'type': 'error', 
                'category': 'rules',
                'message': f'Unknown rules in config: {list(missing_rules)}'
            })
        
        # Check Actions
        missing_actions = references['actions'] - available['actions'] 
        if missing_actions:
            issues.append({
                'type': 'error',
                'category': 'actions', 
                'message': f'Unknown actions in config: {list(missing_actions)}'
            })
        
        # Check for conflicts
        print("\n🔍 Detecting conflicts...")
        conflicts = self.detect_conflicts(references.get('mappings', []))
        if conflicts:
            print(f"   ⚠️  Found {len(conflicts)} conflict(s)")
            for conflict in conflicts:
                issues.append({
                    'type': 'warning',
                    'category': 'conflict',
                    'message': f"Conflict: {conflict['event']} + {conflict['rule']} + {conflict['condition']} has different actions in {conflict['conflicting_files']}"
                })
        else:
            print("   ✅ No conflicts detected")
        
        # Generate report
        status = "error" if issues else "ok"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'available_components': {
                'events': list(available['events']),
                'rules': list(available['rules']),
                'actions': list(available['actions'])
            },
            'config_references': {
                'events': list(references['events']),
                'rules': list(references['rules']), 
                'actions': list(references['actions'])
            },
            'issues': issues
        }
        
        print(f"\n🎯 Status: {status.upper()}")
        if issues:
            for issue in issues:
                print(f"   ❌ {issue['message']}")
        else:
            print("   ✅ All references are valid")
        
        return report

if __name__ == "__main__":
    validator = ConfigValidator()
    report = validator.validate_config()
    
    # Save report
    report_file = Path(__file__).parent.parent / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: {report_file}")