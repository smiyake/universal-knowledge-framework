"""
Pytest設定ファイル
Configuration file for pytest
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_project_dir():
    """一時プロジェクトディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_git_config():
    """Gitの設定済み状態をモック"""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "name_set": True,
        "email_set": True
    }