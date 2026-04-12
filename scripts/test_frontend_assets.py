import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app


def main() -> int:
    client = TestClient(app)
    checks = [
        "/",
        "/static/src/app.js",
        "/static/src/views.js",
        "/static/src/api.js",
        "/static/src/state.js",
        "/static/assets/styles.css",
    ]

    for path in checks:
        response = client.get(path)
        print(path, response.status_code)
        if response.status_code != 200:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
