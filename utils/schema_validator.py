"""
Schema 驗證器
根據 config/schema/ 中的 JSON Schema 驗證 events/responses/rules
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
try:
    import jsonschema
    from jsonschema import validate, ValidationError, RefResolver
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


SCHEMA_DIR = Path(__file__).parent.parent / "config" / "schema"


class SchemaValidator:
    """Schema 驗證器 (三段式 schema)"""

    def __init__(self):
        # 載入所有 schema (event_name.json)
        self.schemas: Dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self):
        """載入所有 JSON schema"""
        if not SCHEMA_DIR.exists():
            return

        for schema_file in SCHEMA_DIR.glob("*.json"):
            event_name = schema_file.stem
            with open(schema_file) as f:
                schema = json.load(f)
                self.schemas[event_name] = schema

    def validate_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        驗證 event payload

        Args:
            event_data: 從 stdin 讀取的 JSON

        Returns:
            錯誤訊息,若無錯誤返回 None
        """
        if not HAS_JSONSCHEMA:
            return None

        event_name = event_data.get('hook_event_name')
        if not event_name:
            return "Missing 'hook_event_name' in event data"

        schema = self.schemas.get(event_name)
        if not schema:
            return f"No schema found for event: {event_name}"

        # 使用 definitions.event 子 schema
        event_schema = schema.get('definitions', {}).get('event')
        if not event_schema:
            return f"No event schema found in {event_name}.json"

        try:
            validate(instance=event_data, schema=event_schema)
            return None
        except ValidationError as e:
            return f"Event validation failed: {e.message}"

    def validate_response(self, event_name: str, response_data: Dict[str, Any]) -> Optional[str]:
        """
        驗證 response 格式

        Args:
            event_name: 事件名稱
            response_data: 輸出的 JSON

        Returns:
            錯誤訊息,若無錯誤返回 None
        """
        if not HAS_JSONSCHEMA:
            return None

        schema = self.schemas.get(event_name)
        if not schema:
            return f"No schema found for event: {event_name}"

        # 使用 definitions.response 子 schema
        response_schema = schema.get('definitions', {}).get('response')
        if not response_schema:
            return f"No response schema found in {event_name}.json"

        try:
            validate(instance=response_data, schema=response_schema)
            return None
        except ValidationError as e:
            return f"Response validation failed: {e.message}"

    def validate_rule(self, rule_config: Dict[str, Any]) -> Optional[str]:
        """
        驗證 rule 配置

        Args:
            rule_config: rule 的 YAML frontmatter

        Returns:
            錯誤訊息,若無錯誤返回 None
        """
        if not HAS_JSONSCHEMA:
            return None

        event_type = rule_config.get('event')
        if not event_type:
            return "Missing 'event' in rule config"

        schema = self.schemas.get(event_type)
        if not schema:
            return f"No schema found for event: {event_type}"

        # 使用 definitions.rule 子 schema
        rule_schema = schema.get('definitions', {}).get('rule')
        if not rule_schema:
            return f"No rule schema found in {event_type}.json"

        try:
            validate(instance=rule_config, schema=rule_schema)
            return None
        except ValidationError as e:
            return f"Rule validation failed: {e.message}"


# 全局 validator 實例
_validator: Optional[SchemaValidator] = None


def get_validator() -> SchemaValidator:
    """取得全局 validator 實例"""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator


def validate_event(event_data: Dict[str, Any]) -> Optional[str]:
    """驗證 event (便捷函數)"""
    return get_validator().validate_event(event_data)


def validate_response(event_name: str, response_data: Dict[str, Any]) -> Optional[str]:
    """驗證 response (便捷函數)"""
    return get_validator().validate_response(event_name, response_data)


def validate_rule(rule_config: Dict[str, Any]) -> Optional[str]:
    """驗證 rule (便捷函數)"""
    return get_validator().validate_rule(rule_config)
