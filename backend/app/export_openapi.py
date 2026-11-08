"""Writes the OpenAPI schema for frontend type generation (no server needed).

Usage (from backend/): uv run python -m app.export_openapi [output-path]
"""

import json
import sys
from pathlib import Path

from .db import REPO_ROOT
from .main import create_app

DEFAULT_OUTPUT = REPO_ROOT / "src" / "frontend" / "api" / "openapi.json"


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(create_app(":memory:").openapi(), indent=2) + "\n")
    print(f"Wrote {output.relative_to(REPO_ROOT) if output.is_relative_to(REPO_ROOT) else output}")


if __name__ == "__main__":
    main()
