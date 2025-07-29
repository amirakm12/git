"""
Setup configuration for the AI System
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements/requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-system",
    version="1.0.0",
    author="AI System Development Team",
    author_email="team@aisystem.dev",
    description="Comprehensive Multi-Agent AI System with Kernel Integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ai-system/ai-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.8.0",
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
        "gpu": [
            "torch-audio==2.1.2+cu118",
            "torch-vision==0.16.2+cu118",
        ],
        "voice": [
            "SpeechRecognition>=3.10.0",
            "pyttsx3>=2.90",
            "pyaudio>=0.2.11",
        ],
        "quantum": [
            "qiskit>=0.45.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "ai-system=src.main:run_system",
            "ai-system-config=src.core.config:main",
            "ai-system-dashboard=src.ui.dashboard:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.json", "*.yaml", "*.yml"],
        "templates": ["*.html"],
        "static": ["*.css", "*.js", "*.png", "*.jpg", "*.ico"],
    },
    zip_safe=False,
    keywords=[
        "artificial intelligence",
        "multi-agent system",
        "machine learning",
        "system monitoring",
        "kernel integration",
        "automation",
        "orchestration",
        "rag",
        "vector database",
        "speculative decoding",
        "sensor fusion",
        "voice interface",
        "dashboard",
        "security monitoring"
    ],
    project_urls={
        "Bug Reports": "https://github.com/ai-system/ai-system/issues",
        "Source": "https://github.com/ai-system/ai-system",
        "Documentation": "https://ai-system.readthedocs.io/",
    },
)