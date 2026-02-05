"""Rule Loading — One-time load and index by event

Responsibilities:
- Load rules from v2/config/rules/*.md
- Normalize field names (alias → official)
- Provide event query interface
- Validate rules during loading
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger("loaders.rules")

RULES_DIR = Path(__file__).parent.parent / "config" / "rules"
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n?', re.DOTALL)

_rules_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None
_rules_by_event_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None


def _parse_rule_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Parse single rule file with validation

    Returns:
        Rule dict or None (if parse failed, disabled, or validation failed)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read rule file {filepath.name}: {e}")
        return None

    # Parse frontmatter
    match = FRONTMATTER_RE.match(content)
    if not match:
        logger.warning(f"Rule file missing frontmatter: {filepath.name}")
        return None

    try:
        rule = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        logger.error(f"YAML parse failed ({filepath.name}): {e}")
        return None

    if not isinstance(rule, dict):
        logger.error(f"Frontmatter is not a dict: {filepath.name}")
        return None

    # Check enabled early (skip disabled rules)
    if not rule.get('enabled', True):
        logger.debug(f"Rule disabled: {filepath.name}")
        return None

    # Validate rule
    from .validator import validate_rule
    passed, errors = validate_rule(rule, filepath.name)
    if not passed:
        error_msg = '; '.join(errors) if errors else 'Unknown validation error'
        logger.warning(f"Rule validation failed for {filepath.name}: {error_msg}")
        return None

    logger.debug(f"Rule loaded: {rule.get('name', filepath.name)}")

    # Add source info
    rule['_filepath'] = filepath.name
    rule['_source'] = str(filepath)

    # Precompile match regex for single-run performance
    match_config = rule.get('match')
    if isinstance(match_config, str):
        try:
            rule['_match_re'] = re.compile(match_config)
        except re.error as e:
            logger.warning(f"Invalid regex in {filepath.name}: {e}")
            return None
    elif isinstance(match_config, dict):
        if 'cmd' in match_config and isinstance(match_config['cmd'], str):
            try:
                rule['_cmd_re'] = re.compile(match_config['cmd'])
            except re.error as e:
                logger.warning(f"Invalid cmd regex in {filepath.name}: {e}")
                return None
        if 'args' in match_config and isinstance(match_config['args'], str):
            try:
                rule['_args_re'] = re.compile(match_config['args'])
            except re.error as e:
                logger.warning(f"Invalid args regex in {filepath.name}: {e}")
                return None

    # Body content (after frontmatter)
    body = content[match.end():].strip()
    if body:
        rule['_body'] = body

    return rule


def _load_all() -> List[Dict[str, Any]]:
    """Load all rules (frontmatter only)

    Returns:
        [rule1, rule2, ...] flat list, sorted by priority
    """
    rules: List[Dict[str, Any]] = []

    if not RULES_DIR.exists():
        logger.warning(f"Rules directory not found: {RULES_DIR}")
        return rules

    logger.debug(f"Loading rules from: {RULES_DIR}")

    total_files = 0
    for filepath in RULES_DIR.glob('*.md'):
        # Skip RULES.md (documentation)
        if filepath.name == 'RULES.md':
            continue

        total_files += 1
        rule = _parse_rule_file(filepath)
        if rule:
            rules.append(rule)

    # Sort by priority (high to low)
    rules.sort(key=lambda r: -r.get('priority', 0))

    logger.info(f"Successfully loaded {len(rules)}/{total_files} rules")

    return rules


def load() -> List[Dict[str, Any]]:
    """Load all rules (called once during router initialization)

    Returns:
        Rule list (sorted by priority)
    """
    global _rules_cache
    if _rules_cache is not None:
        logger.debug("Using cached rules")
        return _rules_cache

    _rules_cache = _load_all()
    return _rules_cache


def get_by_event(event_name: str) -> List[Dict[str, Any]]:
    """Get rules for a specific event (cached index)."""
    global _rules_by_event_cache
    if _rules_by_event_cache is None:
        index: Dict[str, List[Dict[str, Any]]] = {}
        for rule in load():
            event = rule.get("event")
            if not isinstance(event, str):
                continue
            index.setdefault(event, []).append(rule)
        _rules_by_event_cache = index
    return _rules_by_event_cache.get(event_name, [])


def reload():
    """Clear cache and force reload"""
    global _rules_cache, _rules_by_event_cache
    logger.info("Clearing rules cache")
    _rules_cache = None
    _rules_by_event_cache = None
