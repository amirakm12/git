#!/usr/bin/env python3
"""
IGED Installation Test
Verifies that all dependencies are properly installed
"""

import sys
import importlib
from pathlib import Path

def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: OK")
        return True
    except ImportError as e:
        print(f"❌ {description}: FAILED - {e}")
        return False

def test_core_dependencies():
    """Test core dependencies"""
    print("🔧 Testing core dependencies...")
    core_tests = [
        ("cryptography", "Cryptography"),
        ("flask", "Flask"),
        ("flask_cors", "Flask-CORS"),
        ("requests", "Requests")
    ]
    
    all_passed = True
    for module, description in core_tests:
        if not test_import(module, description):
            all_passed = False
    
    return all_passed

def test_voice_dependencies():
    """Test voice recognition dependencies"""
    print("\n🎤 Testing voice recognition dependencies...")
    voice_tests = [
        ("speech_recognition", "SpeechRecognition"),
        ("whisper", "Whisper"),
        ("pyaudio", "PyAudio")
    ]
    
    all_passed = True
    for module, description in voice_tests:
        if not test_import(module, description):
            print(f"⚠️ Voice feature may not work without {description}")
            all_passed = False
    
    return all_passed

def test_data_analysis_dependencies():
    """Test data analysis dependencies"""
    print("\n📊 Testing data analysis dependencies...")
    data_tests = [
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("matplotlib", "Matplotlib"),
        ("seaborn", "Seaborn")
    ]
    
    all_passed = True
    for module, description in data_tests:
        if not test_import(module, description):
            print(f"⚠️ Data analysis features may not work without {description}")
            all_passed = False
    
    return all_passed

def test_security_dependencies():
    """Test security dependencies"""
    print("\n🔒 Testing security dependencies...")
    security_tests = [
        ("nmap", "Python-Nmap"),
        ("psutil", "psutil")
    ]
    
    all_passed = True
    for module, description in security_tests:
        if not test_import(module, description):
            print(f"⚠️ Security features may not work without {description}")
            all_passed = False
    
    return all_passed

def test_build_dependencies():
    """Test build dependencies"""
    print("\n🔨 Testing build dependencies...")
    build_tests = [
        ("PyInstaller", "PyInstaller"),
        ("setuptools", "setuptools"),
        ("wheel", "wheel")
    ]
    
    all_passed = True
    for module, description in build_tests:
        if not test_import(module, description):
            print(f"⚠️ Build features may not work without {description}")
            all_passed = False
    
    return all_passed

def test_iged_modules():
    """Test IGED internal modules"""
    print("\n🤖 Testing IGED modules...")
    
    iged_tests = [
        ("core.encryption", "Encryption Manager"),
        ("core.command_parser", "Command Parser"),
        ("core.memory_engine", "Memory Engine"),
        ("core.voice_pipeline", "Voice Pipeline"),
        ("agents.orchestrator", "Orchestrator"),
        ("agents.codegen_agent.main", "CodeGen Agent"),
        ("agents.secops.main", "SecOps Agent"),
        ("agents.data_miner.main", "DataMiner Agent")
    ]
    
    all_passed = True
    for module, description in iged_tests:
        if not test_import(module, description):
            print(f"❌ IGED module {description} failed to load")
            all_passed = False
    
    return all_passed

def test_directories():
    """Test if required directories exist"""
    print("\n📁 Testing directories...")
    
    required_dirs = [
        "config",
        "memory", 
        "logs",
        "output",
        "output/data_analysis",
        "output/security",
        "output/network_intelligence",
        "output/remote_control"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory {directory}: OK")
        else:
            print(f"❌ Directory {directory}: MISSING")
            all_exist = False
    
    return all_exist

def test_encryption_key():
    """Test if encryption key exists"""
    print("\n🔐 Testing encryption...")
    
    key_path = Path("config/secret.key")
    if key_path.exists():
        print("✅ Encryption key: OK")
        return True
    else:
        print("❌ Encryption key: MISSING")
        return False

def test_python_version():
    """Test Python version"""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}: OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro}: TOO OLD (3.8+ required)")
        return False

def main():
    """Main test function"""
    print("🧪 IGED Installation Test")
    print("=" * 40)
    
    # Test Python version
    if not test_python_version():
        print("\n❌ Python version check failed")
        sys.exit(1)
    
    # Test dependencies
    core_ok = test_core_dependencies()
    voice_ok = test_voice_dependencies()
    data_ok = test_data_analysis_dependencies()
    security_ok = test_security_dependencies()
    build_ok = test_build_dependencies()
    
    # Test IGED modules
    iged_ok = test_iged_modules()
    
    # Test directories and encryption
    dirs_ok = test_directories()
    encryption_ok = test_encryption_key()
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 Test Summary:")
    print(f"Core Dependencies: {'✅' if core_ok else '❌'}")
    print(f"Voice Dependencies: {'✅' if voice_ok else '⚠️'}")
    print(f"Data Analysis: {'✅' if data_ok else '⚠️'}")
    print(f"Security Dependencies: {'✅' if security_ok else '⚠️'}")
    print(f"Build Dependencies: {'✅' if build_ok else '⚠️'}")
    print(f"IGED Modules: {'✅' if iged_ok else '❌'}")
    print(f"Directories: {'✅' if dirs_ok else '❌'}")
    print(f"Encryption: {'✅' if encryption_ok else '❌'}")
    
    if core_ok and iged_ok and dirs_ok and encryption_ok:
        print("\n🎉 All critical components are working!")
        print("✅ IGED is ready to launch")
        print("\n🚀 Run: python launcher.py")
    else:
        print("\n⚠️ Some components have issues")
        if not core_ok:
            print("❌ Core dependencies failed - run: install_deps.bat")
        if not iged_ok:
            print("❌ IGED modules failed - check installation")
        if not dirs_ok:
            print("❌ Directories missing - run: install_deps.bat")
        if not encryption_ok:
            print("❌ Encryption key missing - run: install_deps.bat")

if __name__ == "__main__":
    main() 