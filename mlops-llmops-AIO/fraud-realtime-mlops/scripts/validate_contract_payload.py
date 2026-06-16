import argparse
import json
import pathlib
from typing import Any


TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "object": dict,
}


class ContractValidationError(ValueError):
    pass


def _validate_type(expected: str, value: Any, path: str) -> None:
    if expected == "integer" and isinstance(value, bool):
        raise ContractValidationError(f"{path} expected integer, got bool")
    py_type = TYPE_MAP.get(expected)
    if py_type is None:
        raise ContractValidationError(f"Unsupported schema type at {path}: {expected}")
    if not isinstance(value, py_type):
        raise ContractValidationError(f"{path} expected {expected}, got {type(value).__name__}")


def validate(schema: dict[str, Any], payload: dict[str, Any], path: str = "$") -> None:
    if schema.get("type") != "object":
        raise ContractValidationError("Top-level schema type must be object")

    for field in schema.get("required", []):
        if field not in payload:
            raise ContractValidationError(f"Missing required field: {path}.{field}")

    properties = schema.get("properties", {})
    for key, value in payload.items():
        if key not in properties:
            continue
        field_schema = properties[key]
        field_path = f"{path}.{key}"
        expected_type = field_schema.get("type")
        if expected_type:
            _validate_type(expected_type, value, field_path)

        if "enum" in field_schema and value not in field_schema["enum"]:
            raise ContractValidationError(f"{field_path} value {value!r} not in enum {field_schema['enum']}")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")
            if minimum is not None and value < minimum:
                raise ContractValidationError(f"{field_path} value {value} < minimum {minimum}")
            if maximum is not None and value > maximum:
                raise ContractValidationError(f"{field_path} value {value} > maximum {maximum}")

        if expected_type == "object":
            validate(field_schema, value, field_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True)
    parser.add_argument("--payload", required=True)
    args = parser.parse_args()

    schema = json.loads(pathlib.Path(args.schema).read_text())
    payload = json.loads(pathlib.Path(args.payload).read_text())
    validate(schema, payload)
    print("contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
