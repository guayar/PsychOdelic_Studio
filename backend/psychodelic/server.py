"""Start serwera. Domyslnie tylko 127.0.0.1 (zmiana wymaga jawnej zmiany PSYCHODELIC_HOST)."""
import os

import uvicorn

from .app import create_app


def main():
    host = os.environ.get("PSYCHODELIC_HOST", "127.0.0.1")
    port = int(os.environ.get("PSYCHODELIC_PORT", "8765"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
