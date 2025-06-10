from setuptools import setup, find_packages

setup(
    name="universal-knowledge-framework",
    version="1.0.0",
    description="あらゆるプロジェクトで利用可能な汎用ナレッジ管理フレームワーク",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="株式会社CGin財 (CGin-Zai Co., Ltd.)",
    url="https://github.com/smiyake/universal-knowledge-framework",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "universal_knowledge": [
            "templates/**/",
            "templates/**/*",
        ],
    },
    install_requires=[
        "click>=8.0.0",
        "gitpython>=3.1.0",
        "pyyaml>=6.0",
        "jinja2>=3.0.0",
        "pathlib2>=2.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0", 
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "ai": [
            "openai>=1.0.0",
            "sentence-transformers>=2.0.0",
            "numpy>=1.20.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ukf=universal_knowledge.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="知識管理 文書管理 Claude Obsidian プロジェクト管理 テンプレート",
)