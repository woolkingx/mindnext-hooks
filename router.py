from typing import Dict, Any, List, Optional
import asyncio
import importlib
import inspect
import re

from type_defs import HookResult, RulePayload
from utils.context import get_event
from utils.logger import get_logger
from utils.parsers.shlex_parser import tokenize
from loaders import rules as rules_loader

logger = get_logger("router")

def _event_tool_command(event) -> Optional[str]:
    """Extract tool_input.command from object-first event payload."""
    tool_input = getattr(event, "tool_input", None)
    if tool_input is None:
        return None

    command = getattr(tool_input, "command", None)
    if command is not None:
        return command

    if isinstance(tool_input, dict):
        return tool_input.get("command")

    getter = getattr(tool_input, "get", None)
    if callable(getter):
        return getter("command")

    return None


async def route(rules: List[RulePayload]) -> List[HookResult]:
    """Route event to handlers

    Args:
        rules: Loaded rule list

    Returns:
        List[HookResult]: Processing results from all handlers

    Note: Event is retrieved from global EventContext
    """
    # Get event from global context
    event = get_event()
    event_name = event.hook_event_name

    logger.debug(f"Routing event: {event_name}")

    # Fast path: retrieve rules by event from loader index
    # Fallback to input list for compatibility in tests/custom calls.
    event_rules = rules_loader.get_by_event(event_name) if hasattr(rules_loader, "get_by_event") else []
    if event_rules:
        matched_rules = event_rules
    else:
        matched_rules = [
            rule for rule in rules
            if rule.get('enabled', True) and rule.get('event') == event_name
        ]

    if not matched_rules:
        logger.debug(f"No rules matched for event: {event_name}")
        return []

    logger.info(f"Matched {len(matched_rules)} rules for event: {event_name}")

    # Import handler once per event (single-run optimization)
    try:
        mod = importlib.import_module(f"handlers.{event_name}")
        process_fn = getattr(mod, "process", None)
        if process_fn is None:
            logger.warning(f"Handler {event_name} has no 'process' function")
            return []
    except ImportError as e:
        logger.error(f"Failed to import handler for {event_name}: {e}")
        return []

    # Sort by priority (high to low)
    matched_rules = sorted(
        matched_rules,
        key=lambda r: r.get('priority', 50),
        reverse=True
    )

    # Execute handlers concurrently
    tasks = [_handle_rule(rule, process_fn, event_name) for rule in matched_rules]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            rule_name = matched_rules[i].get('name', 'unknown')
            logger.error(f"Handler failed for rule '{rule_name}': {result}")

    # Filter valid results
    valid_results = [r for r in results if r and not isinstance(r, Exception)]
    logger.debug(f"Returning {len(valid_results)} valid results")
    return valid_results


async def _handle_rule(rule: RulePayload, process_fn, event_name: str) -> HookResult:
    """Handle single rule

    Workflow:
    1. Quick filter (tool)
    2. Detailed match (match)
    3. Call event_handler.process()
    4. Return HookResult
    """
    event = get_event()
    rule_name = rule.get('name', 'unknown')

    logger.debug(f"Processing rule: {rule_name}")

    # Quick filter by tool
    if 'tool' in rule and rule['tool'] != getattr(event, 'tool_name', None):
        logger.debug(f"Rule {rule_name} skipped: tool mismatch")
        return None

    # Detailed match
    if not _matches_rule(rule, event):
        logger.debug(f"Rule {rule_name} skipped: match failed")
        return None

    logger.debug(f"Rule {rule_name} matched, invoking handler")

    # Call event handler
    try:
        # process(rule) - event retrieved from global context
        result = process_fn(rule)
        if inspect.isawaitable(result):
            result = await result

        if result:
            logger.debug(f"Rule {rule_name} returned result")
        return result
    except Exception as e:
        logger.exception(f"Handler {event_name} failed for rule {rule_name}: {e}")
        return None


def _matches_rule(rule: RulePayload, event) -> bool:
    """檢查 event 是否符合 rule 的 match 條件"""
    if 'match' not in rule:
        return True

    match_config = rule['match']

    # 字串：regex 匹配
    if isinstance(match_config, str):
        compiled = rule.get('_match_re')
        command = _event_tool_command(event)
        # 優先匹配 prompt/command 字段
        if hasattr(event, 'prompt'):
            if compiled:
                return bool(compiled.search(event.prompt))
            return bool(re.search(match_config, event.prompt))
        elif command is not None:
            if compiled:
                return bool(compiled.search(command))
            return bool(re.search(match_config, command))
        return False

    # 物件：結構化匹配
    if isinstance(match_config, dict):
        # Bash 專用的結構化匹配
        command = _event_tool_command(event)
        if command is not None:
            return _matches_bash_struct(rule, match_config, command)
        return False

    return True


def _matches_bash_struct(rule: RulePayload, config: Dict[str, Any], command: str) -> bool:
    """Bash 結構化匹配"""
    tokens = tokenize(command)
    first_token = tokens[0] if tokens else ""
    args_tokens = tokens[1:] if len(tokens) > 1 else []

    # cmd 必須匹配
    if 'cmd' in config:
        cmd_re = rule.get('_cmd_re')
        if cmd_re:
            if not first_token or not cmd_re.match(first_token):
                return False
        elif not first_token or not re.match(config['cmd'], first_token):
            return False

    # any_cmd: 複合命令任一
    if 'any_cmd' in config:
        if first_token not in config['any_cmd']:
            return False

    # flags: 必須有的 flags
    if 'flags' in config:
        for flag in config['flags']:
            if f'-{flag}' not in command and f'--{flag}' not in command:
                return False

    # args: args regex
    if 'args' in config:
        # 提取 args (跳過第一個單詞和 flags)
        args_str = ' '.join([p for p in args_tokens if not p.startswith('-')])
        args_re = rule.get('_args_re')
        if args_re:
            if not args_re.search(args_str):
                return False
        elif not re.search(config['args'], args_str):
            return False

    return True
