#!/usr/bin/env python3
"""
Setup script for MindNext Hooks System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text().splitlines() 
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="mindnext-hooks",
    version="3.0.0",
    author="MindNext Development Team",
    author_email="dev@mindnext.org",
    description="A comprehensive three-layer hooks system for Claude Code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mindnext/hooks",
    
    packages=find_packages(),
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Quality Assurance",
    ],
    
    python_requires=">=3.7",
    install_requires=requirements,
    
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
        ],
        'enhanced': [
            'rich>=13.0.0',
            'requests>=2.28.0',
            'slack-sdk>=3.0.0',
        ],
        'ai': [
            'openai>=1.0.0',
            'anthropic>=0.3.0',
        ],
    },
    
    entry_points={
        'console_scripts': [
            'mindnext-hooks=mindnext_hooks:main',
            'mindnext-validator=system_validator:main',
        ],
    },
    
    include_package_data=True,
    package_data={
        '': ['*.json', '*.toml', '*.md', '*.txt'],
        '.': ['claude_settings_example.json'],
        'config': ['*.json'],
        'flow_engine': ['*.py'],
        'flow_engine.actions': ['*.py'],
    },
    
    project_urls={
        'Bug Reports': 'https://github.com/mindnext/hooks/issues',
        'Documentation': 'https://github.com/mindnext/hooks/wiki',
        'Source': 'https://github.com/mindnext/hooks',
    },
    
    keywords=[
        'hooks', 'claude-code', 'automation', 'code-quality', 
        'three-layer-architecture', 'event-driven', 'ai-integration'
    ],
    
    zip_safe=False,
)