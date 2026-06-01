from pathlib import Path

from dotenv import load_dotenv


def load_local_env() -> None:
    server_root = Path(__file__).resolve().parents[1]
    load_dotenv(server_root / ".env", override=False)
