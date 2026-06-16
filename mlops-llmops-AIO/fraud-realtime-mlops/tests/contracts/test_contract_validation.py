import json
import pathlib
import sys

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from validate_contract_payload import ContractValidationError, validate


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts" / "events" / "card_auth_event" / "v2" / "schema.json"


def load_json(path: pathlib.Path):
    return json.loads(path.read_text())


def test_valid_card_auth_event_v2_passes():
    schema = load_json(SCHEMA)
    payload = load_json(ROOT / "tests" / "fixtures" / "card_auth_event_v2_valid.json")
    validate(schema, payload)


def test_missing_required_field_fails():
    schema = load_json(SCHEMA)
    payload = load_json(ROOT / "tests" / "fixtures" / "card_auth_event_v2_missing_required.json")
    with pytest.raises(ContractValidationError):
        validate(schema, payload)


def test_bad_numeric_range_fails():
    schema = load_json(SCHEMA)
    payload = load_json(ROOT / "tests" / "fixtures" / "card_auth_event_v2_bad_range.json")
    with pytest.raises(ContractValidationError):
        validate(schema, payload)
