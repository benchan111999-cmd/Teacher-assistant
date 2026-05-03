import json
import logging
from typing import Any, Optional, List, Dict, Any


logger = logging.getLogger(__name__)


def serialize_json(data: Any) -> Optional[str]:
    """Serialize data to JSON string."""
    if data is None:
        return None
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize JSON: {e}")
        return None


def deserialize_json(data: Optional[str]) -> Any:
    """Deserialize JSON string to data."""
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to deserialize JSON: {e}")
        return None


def serialize_json_list(data: List[Any]) -> List[Optional[str]]:
    """Serialize list of items to JSON strings."""
    return [serialize_json(item) for item in data]


def deserialize_json_list(data: List[Optional[str]]) -> List[Any]:
    """Deserialize list of JSON strings to objects."""
    return [deserialize_json(item) for item in data if item]


def serialize_optional_dict(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """Serialize optional dictionary."""
    return serialize_json(data)


def deserialize_optional_dict(data: Optional[str]) -> Optional[Dict[str, Any]]:
    """Deserialize to optional dictionary."""
    return deserialize_json(data)