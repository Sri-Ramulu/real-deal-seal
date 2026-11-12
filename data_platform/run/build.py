"""Build the warehouse from landing. Usage: python data_platform/run/build.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdsp.runner import GateFailed, build  # noqa: E402

if __name__ == "__main__":
    try:
        build()
    except GateFailed as e:
        print("RED:", e, file=sys.stderr)
        sys.exit(1)
