"""
GitUtilsのテストケース
Test cases for Git utilities
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from universal_knowledge.core.git_utils import GitManager


class TestGitManager:
    """GitManagerクラスのテストケース"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.git_manager = GitManager()
    
    def test_check_git_installation_success(self):
        """Git インストール確認 - 成功ケース"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            git_manager = GitManager()
            assert git_manager.git_config is True
    
    def test_check_git_installation_failure(self):
        """Git インストール確認 - 失敗ケース"""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            git_manager = GitManager()
            assert git_manager.git_config is False
    
    def test_check_git_config_complete(self):
        """Git設定確認 - 完全設定済みケース"""
        with patch('subprocess.run') as mock_run:
            # Name設定済み
            mock_run.side_effect = [
                MagicMock(stdout="Test User", returncode=0),
                MagicMock(stdout="test@example.com", returncode=0)
            ]
            
            self.git_manager.git_config = True
            is_configured, config_info = self.git_manager.check_git_config()
            
            assert is_configured is True
            assert config_info["name"] == "Test User"
            assert config_info["email"] == "test@example.com"
            assert config_info["name_set"] is True
            assert config_info["email_set"] is True
    
    def test_check_git_config_incomplete(self):
        """Git設定確認 - 不完全設定ケース"""
        with patch('subprocess.run') as mock_run:
            # Name未設定、Email設定済み
            mock_run.side_effect = [
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout="test@example.com", returncode=0)
            ]
            
            self.git_manager.git_config = True
            is_configured, config_info = self.git_manager.check_git_config()
            
            assert is_configured is False
            assert config_info["name"] == ""
            assert config_info["email"] == "test@example.com"
            assert config_info["name_set"] is False
            assert config_info["email_set"] is True
    
    def test_check_git_config_no_git(self):
        """Git設定確認 - Git未インストールケース"""
        self.git_manager.git_config = False
        is_configured, config_info = self.git_manager.check_git_config()
        
        assert is_configured is False
        assert "error" in config_info
        assert "インストール" in config_info["error"]
    
    @patch('builtins.input')
    @patch('subprocess.run')
    def test_setup_git_config_interactive_success(self, mock_run, mock_input):
        """インタラクティブGit設定 - 成功ケース"""
        # ユーザー入力をシミュレート
        mock_input.side_effect = ["Test User", "test@example.com"]
        
        # Git設定コマンドをシミュレート
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=1),  # 既存設定なし
            MagicMock(stdout="", returncode=1),  # 既存設定なし
            MagicMock(returncode=0),  # 設定成功
            MagicMock(returncode=0)   # 設定成功
        ]
        
        result = self.git_manager.setup_git_config_interactive()
        assert result is True
    
    @patch('builtins.input')
    def test_setup_git_config_interactive_cancelled(self, mock_input):
        """インタラクティブGit設定 - キャンセルケース"""
        # KeyboardInterruptをシミュレート
        mock_input.side_effect = KeyboardInterrupt()
        
        result = self.git_manager.setup_git_config_interactive()
        assert result is False
    
    def test_initialize_repository_no_git(self):
        """リポジトリ初期化 - Git未インストールケース"""
        self.git_manager.git_config = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            result = self.git_manager.initialize_repository(project_path)
            
            assert result is False
    
    @patch('subprocess.run')
    @patch('builtins.input')
    def test_initialize_repository_success(self, mock_input, mock_run):
        """リポジトリ初期化 - 成功ケース"""
        # Git設定済みをシミュレート
        mock_run.side_effect = [
            MagicMock(stdout="Test User", returncode=0),  # name確認
            MagicMock(stdout="test@example.com", returncode=0),  # email確認
            MagicMock(returncode=0),  # git init
            MagicMock(returncode=0),  # branch設定
            MagicMock(returncode=0),  # branch rename
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0)   # git commit
        ]
        
        self.git_manager.git_config = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # 一時ファイル作成（コミット対象）
            (project_path / "test.txt").write_text("test")
            
            result = self.git_manager.initialize_repository(project_path)
            assert result is True
    
    @patch('subprocess.run')
    def test_initialize_repository_git_error(self, mock_run):
        """リポジトリ初期化 - Gitコマンドエラーケース"""
        # Git設定済みだがコマンドエラー
        mock_run.side_effect = [
            MagicMock(stdout="Test User", returncode=0),  # name確認
            MagicMock(stdout="test@example.com", returncode=0),  # email確認
            subprocess.CalledProcessError(1, 'git init')  # git initエラー
        ]
        
        self.git_manager.git_config = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            result = self.git_manager.initialize_repository(project_path)
            
            assert result is False
    
    def test_print_git_help(self, capsys):
        """Gitヘルプ表示テスト"""
        self.git_manager.print_git_help()
        
        captured = capsys.readouterr()
        assert "Git設定について" in captured.out
        assert "git config --global" in captured.out
        assert "https://git-scm.com" in captured.out


if __name__ == "__main__":
    pytest.main([__file__])