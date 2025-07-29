#!/usr/bin/env python3
"""
Comprehensive Test Runner for AI System
Runs all tests with proper categorization and reporting
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        print(f"\nSTDOUT:\n{result.stdout}")
    
    if result.stderr:
        print(f"\nSTDERR:\n{result.stderr}")
    
    return result


def run_unit_tests():
    """Run unit tests."""
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '-m', 'unit',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov',
        '--junit-xml=test-results/unit-tests.xml'
    ]
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests():
    """Run integration tests."""
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '-m', 'integration',
        '--junit-xml=test-results/integration-tests.xml'
    ]
    
    return run_command(cmd, "Integration Tests")


def run_performance_tests():
    """Run performance tests."""
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '-m', 'performance',
        '--junit-xml=test-results/performance-tests.xml'
    ]
    
    return run_command(cmd, "Performance Tests")


def run_security_tests():
    """Run security tests."""
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '-m', 'security',
        '--junit-xml=test-results/security-tests.xml'
    ]
    
    return run_command(cmd, "Security Tests")


def run_linting():
    """Run code linting."""
    results = []
    
    # Flake8
    cmd = ['flake8', 'src/', 'tests/', '--max-line-length=120', '--ignore=E203,W503']
    results.append(run_command(cmd, "Flake8 Linting"))
    
    # Black (check only)
    cmd = ['black', '--check', '--diff', 'src/', 'tests/']
    results.append(run_command(cmd, "Black Code Formatting Check"))
    
    # isort (check only)
    cmd = ['isort', '--check-only', '--diff', 'src/', 'tests/']
    results.append(run_command(cmd, "isort Import Sorting Check"))
    
    return results


def run_type_checking():
    """Run type checking with mypy."""
    cmd = ['mypy', 'src/', '--ignore-missing-imports', '--no-strict-optional']
    return run_command(cmd, "MyPy Type Checking")


def run_dependency_check():
    """Check for security vulnerabilities in dependencies."""
    cmd = ['safety', 'check', '--json']
    return run_command(cmd, "Dependency Security Check")


def setup_test_environment():
    """Setup test environment."""
    print("Setting up test environment...")
    
    # Create test results directory
    Path("test-results").mkdir(exist_ok=True)
    
    # Create coverage directory
    Path("htmlcov").mkdir(exist_ok=True)
    
    # Install test dependencies
    cmd = ['pip', 'install', '-r', 'requirements/requirements.txt']
    result = run_command(cmd, "Installing Dependencies")
    
    if result.returncode != 0:
        print("Failed to install dependencies")
        return False
    
    # Install test-specific dependencies
    test_deps = [
        'pytest', 'pytest-cov', 'pytest-asyncio', 'pytest-mock',
        'flake8', 'black', 'isort', 'mypy', 'safety'
    ]
    
    for dep in test_deps:
        cmd = ['pip', 'install', dep]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: Failed to install {dep}")
    
    print("Test environment setup complete")
    return True


def generate_test_report(results):
    """Generate a comprehensive test report."""
    report_path = "test-results/test-report.html"
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI System Test Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .pass { background-color: #d4edda; border-color: #c3e6cb; }
            .fail { background-color: #f8d7da; border-color: #f5c6cb; }
            .warning { background-color: #fff3cd; border-color: #ffeaa7; }
            .code { background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AI System Test Report</h1>
            <p>Generated on: {timestamp}</p>
        </div>
    """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Add summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.returncode == 0)
    failed_tests = total_tests - passed_tests
    
    html_content += f"""
        <div class="section">
            <h2>Test Summary</h2>
            <table>
                <tr><th>Category</th><th>Count</th></tr>
                <tr><td>Total Tests</td><td>{total_tests}</td></tr>
                <tr><td>Passed</td><td>{passed_tests}</td></tr>
                <tr><td>Failed</td><td>{failed_tests}</td></tr>
                <tr><td>Success Rate</td><td>{passed_tests/total_tests*100:.1f}%</td></tr>
            </table>
        </div>
    """
    
    # Add detailed results
    for i, result in enumerate(results):
        status_class = "pass" if result.returncode == 0 else "fail"
        html_content += f"""
        <div class="section {status_class}">
            <h3>Test {i+1}: {result.args[0] if result.args else 'Unknown'}</h3>
            <p><strong>Return Code:</strong> {result.returncode}</p>
            <p><strong>Duration:</strong> {getattr(result, 'duration', 'Unknown')}</p>
            <div class="code">
                <strong>STDOUT:</strong><br>
                <pre>{result.stdout}</pre>
            </div>
            {f'<div class="code"><strong>STDERR:</strong><br><pre>{result.stderr}</pre></div>' if result.stderr else ''}
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"\nTest report generated: {report_path}")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="AI System Test Runner")
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--lint', action='store_true', help='Run linting only')
    parser.add_argument('--type-check', action='store_true', help='Run type checking only')
    parser.add_argument('--deps', action='store_true', help='Check dependencies only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--no-setup', action='store_true', help='Skip environment setup')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only (unit + lint)')
    
    args = parser.parse_args()
    
    # If no specific test type is selected, run all
    if not any([args.unit, args.integration, args.performance, args.security, 
                args.lint, args.type_check, args.deps, args.quick]):
        args.all = True
    
    print("AI System Test Runner")
    print("====================")
    
    # Setup environment unless skipped
    if not args.no_setup:
        if not setup_test_environment():
            print("Failed to setup test environment")
            return 1
    
    results = []
    start_time = time.time()
    
    try:
        # Run selected tests
        if args.unit or args.all or args.quick:
            results.append(run_unit_tests())
        
        if args.integration or args.all:
            results.append(run_integration_tests())
        
        if args.performance or args.all:
            results.append(run_performance_tests())
        
        if args.security or args.all:
            results.append(run_security_tests())
        
        if args.lint or args.all or args.quick:
            results.extend(run_linting())
        
        if args.type_check or args.all:
            results.append(run_type_checking())
        
        if args.deps or args.all:
            results.append(run_dependency_check())
        
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Generate summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Total test categories: {len(results)}")
    
    passed = sum(1 for r in results if r.returncode == 0)
    failed = len(results) - passed
    
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(results)*100:.1f}%" if results else "No tests run")
    
    # Generate detailed report
    generate_test_report(results)
    
    # Return appropriate exit code
    if failed > 0:
        print("\nSome tests failed!")
        return 1
    else:
        print("\nAll tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())