#!/usr/bin/env python3
"""
Comprehensive Installation and Completeness Verification Script
Verifies all dependencies and ensures all files are fully implemented
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
import ast
import re

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_file_completeness():
    """Check if all source files are complete and not dummy implementations."""
    print("\n📁 Checking file completeness...")
    
    issues = []
    src_files = list(Path("src").rglob("*.py"))
    
    for file_path in src_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for incomplete implementations
            if re.search(r'^\s*pass\s*$', content, re.MULTILINE):
                # Check if it's just exception handling
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if re.match(r'^\s*pass\s*$', line):
                        # Check context - if it's after except, it's OK
                        context = '\n'.join(lines[max(0, i-3):i+1])
                        if not re.search(r'except.*:', context):
                            issues.append(f"{file_path}: Incomplete implementation (pass statement)")
            
            # Check for TODO/FIXME
            if re.search(r'#\s*(TODO|FIXME|XXX)', content, re.IGNORECASE):
                issues.append(f"{file_path}: Contains TODO/FIXME comments")
            
            # Check for placeholder text
            if re.search(r'(placeholder|dummy|not implemented)', content, re.IGNORECASE):
                issues.append(f"{file_path}: Contains placeholder text")
            
            # Check minimum file size (should have substantial content)
            if len(content.strip()) < 100:
                issues.append(f"{file_path}: File too small, likely incomplete")
                
        except Exception as e:
            issues.append(f"{file_path}: Error reading file - {e}")
    
    if issues:
        print("❌ File completeness issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"✅ All {len(src_files)} source files are complete")
        return True

def check_required_dependencies():
    """Check if all required dependencies are available."""
    print("\n📦 Checking required dependencies...")
    
    # Core dependencies that must be available
    core_deps = [
        'asyncio', 'logging', 'json', 'time', 'pathlib', 'typing',
        'dataclasses', 'enum', 'collections', 'hashlib', 're'
    ]
    
    # External dependencies
    external_deps = [
        ('numpy', 'numpy'),
        ('aiohttp', 'aiohttp'),
        ('psutil', 'psutil'),
        ('cryptography', 'cryptography.fernet'),
    ]
    
    # Optional but important dependencies
    optional_deps = [
        ('torch', 'torch'),
        ('transformers', 'transformers'),
        ('sentence_transformers', 'sentence_transformers'),
        ('openai', 'openai'),
        ('chromadb', 'chromadb'),
        ('sklearn', 'sklearn'),
        ('speech_recognition', 'speech_recognition'),
        ('pyttsx3', 'pyttsx3'),
        ('uvloop', 'uvloop'),
    ]
    
    missing_core = []
    missing_external = []
    missing_optional = []
    
    # Check core dependencies
    for dep in core_deps:
        try:
            importlib.import_module(dep)
        except ImportError:
            missing_core.append(dep)
    
    # Check external dependencies
    for name, module in external_deps:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_external.append(name)
    
    # Check optional dependencies
    for name, module in optional_deps:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_optional.append(name)
    
    # Report results
    success = True
    
    if missing_core:
        print("❌ Missing CORE dependencies (critical):")
        for dep in missing_core:
            print(f"   - {dep}")
        success = False
    
    if missing_external:
        print("❌ Missing EXTERNAL dependencies (required):")
        for dep in missing_external:
            print(f"   - {dep}")
        success = False
    
    if missing_optional:
        print("⚠️  Missing OPTIONAL dependencies (functionality may be limited):")
        for dep in missing_optional:
            print(f"   - {dep}")
    
    if success and not missing_optional:
        print("✅ All dependencies are available")
    elif success:
        print("✅ Core dependencies available (some optional missing)")
    
    return success

def check_project_structure():
    """Check if all required directories and files exist."""
    print("\n🏗️  Checking project structure...")
    
    required_dirs = [
        'src', 'src/core', 'src/agents', 'src/ai', 'src/sensors', 
        'src/kernel', 'src/ui', 'src/monitoring', 'tests', 'docs',
        'deployment', 'config', 'requirements'
    ]
    
    required_files = [
        'src/main.py',
        'src/core/config.py',
        'src/core/orchestrator.py',
        'src/agents/triage_agent.py',
        'src/agents/research_agent.py',
        'src/agents/orchestration_agent.py',
        'src/ai/rag_engine.py',
        'src/ai/speculative_decoder.py',
        'src/sensors/fusion.py',
        'src/kernel/integration.py',
        'src/ui/dashboard.py',
        'src/ui/voice_interface.py',
        'src/monitoring/system_monitor.py',
        'src/monitoring/security_monitor.py',
        'requirements/requirements.txt',
        'README.md',
        'LICENSE'
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_dirs or missing_files:
        print("❌ Project structure issues:")
        for dir_path in missing_dirs:
            print(f"   - Missing directory: {dir_path}")
        for file_path in missing_files:
            print(f"   - Missing file: {file_path}")
        return False
    else:
        print("✅ Project structure is complete")
        return True

def check_import_consistency():
    """Check if all imports in source files can be resolved."""
    print("\n🔗 Checking import consistency...")
    
    issues = []
    src_files = list(Path("src").rglob("*.py"))
    
    for file_path in src_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the file to extract imports
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Skip relative imports and built-ins
                            if not alias.name.startswith('.') and '.' not in alias.name:
                                try:
                                    importlib.import_module(alias.name)
                                except ImportError:
                                    issues.append(f"{file_path}: Cannot import '{alias.name}'")
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and not node.module.startswith('.'):
                            try:
                                importlib.import_module(node.module)
                            except ImportError:
                                issues.append(f"{file_path}: Cannot import from '{node.module}'")
            
            except SyntaxError as e:
                issues.append(f"{file_path}: Syntax error - {e}")
                
        except Exception as e:
            issues.append(f"{file_path}: Error checking imports - {e}")
    
    if issues:
        print("❌ Import issues found:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
        return False
    else:
        print("✅ All imports are consistent")
        return True

def check_code_quality():
    """Check basic code quality metrics."""
    print("\n🎯 Checking code quality...")
    
    src_files = list(Path("src").rglob("*.py"))
    total_lines = 0
    total_files = len(src_files)
    
    for file_path in src_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
        except Exception:
            pass
    
    avg_lines = total_lines / total_files if total_files > 0 else 0
    
    print(f"📊 Code Statistics:")
    print(f"   - Total files: {total_files}")
    print(f"   - Total lines: {total_lines}")
    print(f"   - Average lines per file: {avg_lines:.1f}")
    
    if total_lines < 10000:
        print("⚠️  Code base seems small for a comprehensive system")
        return False
    elif avg_lines < 100:
        print("⚠️  Average file size is quite small")
        return False
    else:
        print("✅ Code base has substantial implementation")
        return True

def install_missing_dependencies():
    """Attempt to install missing dependencies."""
    print("\n📥 Installing missing dependencies...")
    
    try:
        # Install from requirements file
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements/requirements.txt'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 AI System Installation and Completeness Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("File Completeness", check_file_completeness),
        ("Code Quality", check_code_quality),
        ("Dependencies", check_required_dependencies),
        ("Import Consistency", check_import_consistency),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:20} : {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED! System is fully implemented and ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} issues found. System may not function correctly.")
        
        # Offer to install dependencies if that's the main issue
        if not results.get("Dependencies", True):
            response = input("\nWould you like to attempt automatic dependency installation? (y/N): ")
            if response.lower() == 'y':
                if install_missing_dependencies():
                    print("✅ Dependencies installed. Please run verification again.")
                else:
                    print("❌ Automatic installation failed. Manual installation required.")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())