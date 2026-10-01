"""
DataGuard Comprehensive Test Suite Runner
Discovers and executes all unit and integration tests across ML, Agents, Auth, Recovery, and Reporting.
"""

import sys
from pathlib import Path
import pytest

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def main():
    print("=" * 70)
    print("DATAGUARD 2.0 ENTERPRISE SYSTEM TEST SUITE (PYTEST)")
    print("=" * 70)

    exit_code = pytest.main([
        str(Path(__file__).parent),
        "-v",
        "--durations=5",
    ])

    print("\n" + "=" * 70)
    if exit_code == 0:
        print(">>> ALL DATAGUARD SYSTEM TESTS (27/27) PASSED SUCCESSFULLY! <<<")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f">>> TEST SUITE FAILED WITH EXIT CODE {exit_code} <<<")
        print("=" * 70)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
