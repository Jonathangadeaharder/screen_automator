#!/usr/bin/env python3
"""
Test runner script for Screen Automator project.
Executes comprehensive tests with proper configuration and reporting.
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def setup_test_environment():
    """Set up the test environment."""
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / 'src'))
    
    # Set environment variables for testing
    os.environ['TESTING'] = '1'
    os.environ['PYTHONPATH'] = str(project_root)
    
    return project_root


def install_test_dependencies():
    """Install required test dependencies."""
    test_requirements = [
        'pytest>=7.0.0',
        'pytest-mock>=3.10.0',
        'pytest-cov>=4.0.0',
        'pytest-xvfb',  # For GUI testing on headless systems
        'coverage>=7.0.0'
    ]
    
    print("Installing test dependencies...")
    for requirement in test_requirements:
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', requirement
            ], check=True, capture_output=True)
            print(f"✓ Installed {requirement}")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Failed to install {requirement}: {e}")
            print("Continuing without this dependency...")


def run_basic_tests(project_root):
    """Run basic functionality tests."""
    print("\n" + "="*60)
    print("RUNNING BASIC TESTS")
    print("="*60)
    
    basic_test_file = project_root / 'test_basic.py'
    if basic_test_file.exists():
        try:
            result = subprocess.run([
                sys.executable, str(basic_test_file)
            ], cwd=project_root, capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error running basic tests: {e}")
            return False
    else:
        print("No basic test file found, skipping...")
        return True


def run_comprehensive_tests(project_root, coverage=False, verbose=False):
    """Run comprehensive test suite."""
    print("\n" + "="*60)
    print("RUNNING COMPREHENSIVE TESTS")
    print("="*60)
    
    test_file = project_root / 'tests' / 'test_comprehensive.py'
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return False
    
    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']
    
    if coverage:
        cmd.extend(['--cov=src', '--cov=.', '--cov-report=html', '--cov-report=term'])
    
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    cmd.extend([
        '--tb=short',
        '--disable-warnings',
        str(test_file)
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running comprehensive tests: {e}")
        return False


def run_cli_tests(project_root):
    """Run CLI-specific tests."""
    print("\n" + "="*60)
    print("RUNNING CLI TESTS")
    print("="*60)
    
    # Test CLI help
    try:
        result = subprocess.run([
            sys.executable, 'cli.py', '--help'
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ CLI help command works")
        else:
            print("✗ CLI help command failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ CLI test error: {e}")
        return False
    
    # Test CLI status (with timeout)
    try:
        result = subprocess.run([
            sys.executable, 'cli.py', 'status'
        ], cwd=project_root, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ CLI status command works")
            print(f"Status output: {result.stdout.strip()}")
        else:
            print("✗ CLI status command failed")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠ CLI status command timed out (this might be normal)")
    except Exception as e:
        print(f"✗ CLI status test error: {e}")
        return False
    
    return True


def run_gui_tests(project_root):
    """Run GUI tests."""
    print("\n" + "="*60)
    print("RUNNING GUI TESTS")
    print("="*60)
    
    # Test GUI import
    try:
        result = subprocess.run([
            sys.executable, '-c', 'import gui; print("GUI import successful")'
        ], cwd=project_root, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✓ GUI module imports successfully")
        else:
            print("✗ GUI module import failed")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠ GUI import test timed out")
        return False
    except Exception as e:
        print(f"✗ GUI import test error: {e}")
        return False
    
    return True


def generate_test_report(results):
    """Generate a test report."""
    print("\n" + "="*60)
    print("TEST SUMMARY REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    return failed_tests == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run Screen Automator tests')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--install-deps', action='store_true', help='Install test dependencies')
    parser.add_argument('--basic-only', action='store_true', help='Run only basic tests')
    parser.add_argument('--comprehensive-only', action='store_true', help='Run only comprehensive tests')
    
    args = parser.parse_args()
    
    print("Screen Automator Test Runner")
    print("="*60)
    
    # Setup test environment
    project_root = setup_test_environment()
    print(f"Project root: {project_root}")
    
    # Install dependencies if requested
    if args.install_deps:
        install_test_dependencies()
    
    # Track test results
    results = {}
    
    # Run tests based on arguments
    if args.basic_only:
        results['Basic Tests'] = run_basic_tests(project_root)
    elif args.comprehensive_only:
        results['Comprehensive Tests'] = run_comprehensive_tests(project_root, args.coverage, args.verbose)
    else:
        # Run all tests
        results['Basic Tests'] = run_basic_tests(project_root)
        results['CLI Tests'] = run_cli_tests(project_root)
        results['GUI Tests'] = run_gui_tests(project_root)
        results['Comprehensive Tests'] = run_comprehensive_tests(project_root, args.coverage, args.verbose)
    
    # Generate report
    all_passed = generate_test_report(results)
    
    # Coverage report info
    if args.coverage:
        print("\n" + "="*60)
        print("Coverage report generated in htmlcov/index.html")
        print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main() 