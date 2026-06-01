"""Check that the local ASR runtime dependencies can be imported."""

from __future__ import annotations

import importlib
from importlib import metadata


REQUIRED_MODULES = [
    ("numpy", "numpy"),
    ("torch", "torch"),
    ("torchaudio", "torchaudio"),
    ("modelscope", "modelscope"),
    ("funasr", "funasr"),
]


def package_version(distribution_name: str) -> str:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return "unknown"


def main() -> None:
    missing: list[str] = []
    for module_name, distribution_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            missing.append(f"{module_name}: {error}")
            continue
        print(f"OK {module_name} {package_version(distribution_name)}")

    if missing:
        print("")
        print("Missing or broken ASR dependencies:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(1)

    print("")
    print("ASR dependency import check passed.")


if __name__ == "__main__":
    main()
