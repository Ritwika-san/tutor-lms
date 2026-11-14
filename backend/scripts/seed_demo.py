from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.demo_seed import seed_demo


def main() -> None:
    stored_count = seed_demo()
    print(
        "Demo seed complete: users=2, courses=1, enrollments=1, "
        f"materials=1, vectors={stored_count}."
    )


if __name__ == "__main__":
    main()
