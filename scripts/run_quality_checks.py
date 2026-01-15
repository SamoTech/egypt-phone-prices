#!/usr/bin/env python3
"""
Code quality checker script.
Runs all code quality tools and generates a summary report.
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*70}")
    print(f"Running {description}...")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️  {description} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run all code quality checks."""
    print("🔍 Starting Code Quality Checks...")
    
    results = {}
    
    # Run tests
    results['tests'] = run_command(
        'python -m pytest tests/ -v --tb=short --maxfail=5',
        'Test Suite'
    )
    
    # Run flake8
    results['flake8'] = run_command(
        'python -m flake8 engine/ scrapers/ utils/ --statistics --count',
        'Flake8 Linter'
    )
    
    # Run pylint
    results['pylint'] = run_command(
        'python -m pylint engine/ scrapers/ utils/ --score=yes --exit-zero',
        'Pylint Linter'
    )
    
    # Run mypy
    results['mypy'] = run_command(
        'python -m mypy engine/ --ignore-missing-imports',
        'MyPy Type Checker'
    )
    
    # Run bandit
    results['bandit'] = run_command(
        'python -m bandit -r engine/ scrapers/ utils/ -ll',
        'Bandit Security Scanner'
    )
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, status in results.items():
        icon = "✅" if status else "⚠️"
        print(f"{icon} {check.upper()}: {'PASSED' if status else 'HAS ISSUES'}")
    
    print(f"\n📈 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All quality checks passed!")
        return 0
    else:
        print("\n⚠️  Some quality checks have issues. Review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
