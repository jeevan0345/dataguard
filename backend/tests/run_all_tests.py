"""
DataGuard Comprehensive Test Suite Runner
Discovers and executes all unit and integration tests across ML, Agents, Auth, Recovery, and Reporting.
"""

import unittest
import sys

def main():
    print("=" * 70)
    print("DATAGUARD 2.0 ENTERPRISE SYSTEM TEST SUITE")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    if result.wasSuccessful():
        print(">>> ALL DATAGUARD SYSTEM TESTS PASSED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print(">>> TESTS FAILED <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
