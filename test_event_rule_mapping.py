#!/usr/bin/env python3
"""
Test event to rule mapping
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from flow_engine.event_layer import EventProcessor, SUPPORTED_EVENTS
from flow_engine.rule_layer import RuleEngine
from flow_engine.flow_coordinator import FlowCoordinator

def test_event_rule_mapping():
    """Test if all 8 events can correctly map to rules"""
    
    # Initialize components
    event_processor = EventProcessor()
    rule_engine = RuleEngine(config_dir=str(Path(__file__).parent / "config"))
    
    print("Testing Event → Rule Mapping")
    print("=" * 40)
    
    # Test each supported event
    for event_type in SUPPORTED_EVENTS:
        print(f"\n📌 Event: {event_type}")
        
        # Create a test event
        test_data = {
            'user_prompt': 'test 記錄 搜索',  # Include keywords to trigger rules
            'tool_name': 'TestTool',
            'tool_input': {'test': 'data'}
        }
        
        # Process event
        event = event_processor.process_hook_event(event_type, test_data)
        
        # Find matching rules
        matched_rules = rule_engine.match_rules(event)
        
        if matched_rules:
            print(f"   ✅ Found {len(matched_rules)} matching rule(s):")
            for rule in matched_rules:
                print(f"      - {rule.id}: {rule.name[:50]}")
        else:
            print(f"   ⚠️  No matching rules found")
    
    print("\n" + "=" * 40)
    print("Summary:")
    print(f"Total events tested: {len(SUPPORTED_EVENTS)}")
    print(f"Total rules loaded: {len(rule_engine.rules)}")

if __name__ == "__main__":
    test_event_rule_mapping()