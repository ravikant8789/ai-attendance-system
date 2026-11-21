import base64
from pathlib import Path

ASSETS_DIR = Path(__file__).parent

def get_asset_path(filename: str) -> str:
    return str(ASSETS_DIR / filename)

def get_asset_base64(filename: str) -> str:
    path = ASSETS_DIR / filename
    if path.exists():
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        ext = path.suffix.lstrip(".").lower()
        return f"data:image/{ext};base64,{encoded}"
    return ""
