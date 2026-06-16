import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from validate_config import main


def test_prod_config_validates():
    cfg = pathlib.Path(__file__).resolve().parents[1] / "configs" / "prod" / "assistant.yaml"
    assert main(str(cfg)) == 0
