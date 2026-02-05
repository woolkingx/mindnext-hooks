"""Event object layer built from JSON Schema object trees.

Pipeline:
raw payload -> schema object tree projector -> typed event dataclass
"""
import json
from dataclasses import dataclass, field, make_dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List


@dataclass
class TreeNode:
    """Runtime object-tree node compiled from JSON schema."""

    node_type: str = "any"
    required: List[str] = field(default_factory=list)
    properties: Dict[str, "TreeNode"] = field(default_factory=dict)
    items: Optional["TreeNode"] = None
    enum: Optional[List[Any]] = None
    const: Optional[Any] = None
    additional_properties: bool = True


@dataclass
class TreeObject:
    """Attribute-first object wrapper for projected schema objects."""

    _data: Dict[str, Any]

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key, value in self._data.items():
            out[key] = _to_plain(value)
        return out


def _to_plain(value: Any) -> Any:
    if isinstance(value, TreeObject):
        return value.to_dict()
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def _load_schemas() -> Dict[str, Dict[str, Any]]:
    """Load all event schemas from v2/config/schema/*.json."""
    schema_dir = Path(__file__).parent.parent / "config" / "schema"
    schemas: Dict[str, Dict[str, Any]] = {}
    for schema_file in schema_dir.glob("*.json"):
        with open(schema_file, "r", encoding="utf-8") as f:
            schemas[schema_file.stem] = json.load(f)
    return schemas


def _json_type_to_python(field_def: Dict[str, Any]):
    """Map JSON schema type to Python hint."""
    field_type = field_def.get("type", "string")
    if field_type == "string":
        return Optional[str]
    if field_type == "boolean":
        return Optional[bool]
    if field_type == "object":
        return Optional[Dict[str, Any]]
    if field_type == "array":
        return Optional[list]
    if field_type == "integer":
        return Optional[int]
    if field_type == "number":
        return Optional[float]
    return Optional[Any]


def _build_tree(defn: Dict[str, Any]) -> TreeNode:
    """Compile schema definition into TreeNode."""
    node_type = defn.get("type", "any")
    node = TreeNode(
        node_type=node_type,
        required=list(defn.get("required", [])),
        enum=defn.get("enum"),
        const=defn.get("const"),
        additional_properties=defn.get("additionalProperties", True),
    )

    if node_type == "object":
        for name, child in defn.get("properties", {}).items():
            node.properties[name] = _build_tree(child)
    elif node_type == "array" and isinstance(defn.get("items"), dict):
        node.items = _build_tree(defn["items"])

    return node


def _build_schema_registry():
    """Build event class + event tree registries from schemas."""
    schemas = _load_schemas()
    event_classes: Dict[str, Any] = {}
    event_trees: Dict[str, TreeNode] = {}

    for event_name, schema in schemas.items():
        event_def = schema.get("definitions", {}).get("event")
        if not isinstance(event_def, dict):
            continue

        properties = event_def.get("properties", {})
        fields = []
        for field_name, field_def in properties.items():
            fields.append((field_name, _json_type_to_python(field_def), None))

        event_class = make_dataclass(
            event_name,
            fields,
            namespace={"event_type": lambda self, name=event_name: name},
        )
        event_classes[event_name] = event_class
        event_trees[event_name] = _build_tree(event_def)

    return event_classes, event_trees


def _project(node: TreeNode, value: Any, path: str = "") -> Any:
    """Project raw data by object tree (whitelist + required checks)."""
    if node.node_type == "object":
        if not isinstance(value, dict):
            raise ValueError(f"Expected object at '{path or '$'}'")

        projected: Dict[str, Any] = {}

        for req in node.required:
            if req not in value:
                raise ValueError(f"Missing required field: '{(path + '.' + req).strip('.')}'")

        for key, child in node.properties.items():
            if key in value:
                child_path = f"{path}.{key}" if path else key
                projected[key] = _project(child, value[key], child_path)
            else:
                projected[key] = None

        if node.additional_properties:
            for key, raw in value.items():
                if key not in projected:
                    projected[key] = raw

        return projected

    if node.node_type == "array":
        if not isinstance(value, list):
            raise ValueError(f"Expected array at '{path or '$'}'")
        if node.items is None:
            return value
        return [_project(node.items, item, f"{path}[]") for item in value]

    # scalar / any
    if node.const is not None and value != node.const:
        raise ValueError(f"Field '{path or '$'}' must be constant '{node.const}'")
    if node.enum is not None and value not in node.enum:
        raise ValueError(f"Field '{path or '$'}' must be one of {node.enum}")
    return value


def _materialize(node: TreeNode, value: Any, root: bool = False) -> Any:
    """Convert projected dict/list into nested TreeObject instances."""
    if node.node_type == "object" and isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, raw in value.items():
            child = node.properties.get(key)
            if child is not None:
                out[key] = _materialize(child, raw, root=False)
            elif isinstance(raw, dict):
                out[key] = TreeObject({k: _to_plain(v) for k, v in raw.items()})
            elif isinstance(raw, list):
                out[key] = [_to_plain(v) for v in raw]
            else:
                out[key] = raw
        if root:
            return out
        return TreeObject(out)

    if node.node_type == "array" and isinstance(value, list):
        if node.items is None:
            return value
        return [_materialize(node.items, item, root=False) for item in value]

    return value


# Global registries (compiled once)
EVENT_CLASSES, EVENT_TREES = _build_schema_registry()


def project_event(event_name: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Project raw payload to schema-aligned object by event tree."""
    tree = EVENT_TREES.get(event_name)
    if tree is None:
        raise ValueError(f"Unknown event type: {event_name}")
    projected = _project(tree, raw_data)
    return _materialize(tree, projected, root=True)


def from_dict(data: Dict[str, Any]):
    """Convert raw payload dict into typed event object via schema tree."""
    event_name = data.get("hook_event_name")
    if not event_name:
        raise ValueError("Missing 'hook_event_name' in payload")

    event_class = EVENT_CLASSES.get(event_name)
    if event_class is None:
        raise ValueError(f"Unknown event type: {event_name}")

    projected = project_event(event_name, data)
    try:
        return event_class(**projected)
    except TypeError as e:
        raise TypeError(f"Invalid payload for {event_name}: {e}")
