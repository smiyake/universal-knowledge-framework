"""
Claude Code同期機能のテストケース
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from universal_knowledge.ai.claude_code_sync import (
    ClaudeCodeSync,
    ClaudeTask,
    TaskStatus,
    TaskPriority,
    sync_from_claude_cli,
    get_tasks_for_claude
)


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリ作成"""
    return tmp_path


@pytest.fixture
def sample_tasks():
    """サンプルタスクデータ"""
    return [
        {
            "id": "task-001",
            "content": "UKF統合機能の実装",
            "status": "in_progress",
            "priority": "high"
        },
        {
            "id": "task-002",
            "content": "テストケースの作成",
            "status": "pending",
            "priority": "medium"
        },
        {
            "id": "task-003",
            "content": "ドキュメント更新",
            "status": "completed",
            "priority": "low"
        }
    ]


@pytest.fixture
def claude_sync(temp_dir):
    """ClaudeCodeSync インスタンス"""
    vault_path = temp_dir / "knowledge"
    cache_file = temp_dir / ".claude-task-cache.json"
    return ClaudeCodeSync(vault_path=vault_path, cache_file=cache_file, auto_commit=False)


class TestClaudeTask:
    """ClaudeTaskモデルのテスト"""
    
    def test_task_creation(self):
        """タスク作成テスト"""
        task = ClaudeTask(
            id="test-001",
            content="テストタスク",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH
        )
        
        assert task.id == "test-001"
        assert task.content == "テストタスク"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
    
    def test_task_to_dict(self):
        """タスクの辞書変換テスト"""
        task = ClaudeTask(
            id="test-001",
            content="テストタスク",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM
        )
        
        data = task.to_dict()
        assert data["id"] == "test-001"
        assert data["content"] == "テストタスク"
        assert data["status"] == "in_progress"
        assert data["priority"] == "medium"
    
    def test_task_from_dict(self):
        """辞書からタスク生成テスト"""
        data = {
            "id": "test-001",
            "content": "テストタスク",
            "status": "completed",
            "priority": "low"
        }
        
        task = ClaudeTask.from_dict(data)
        assert task.id == "test-001"
        assert task.content == "テストタスク"
        assert task.status == TaskStatus.COMPLETED
        assert task.priority == TaskPriority.LOW


class TestClaudeCodeSync:
    """ClaudeCodeSync機能のテスト"""
    
    def test_initialization(self, temp_dir):
        """初期化テスト"""
        sync = ClaudeCodeSync(vault_path=temp_dir / "knowledge")
        assert sync.vault_path == temp_dir / "knowledge"
        assert sync.cache_file.name == ".claude-task-cache.json"
        assert sync.auto_commit == True
    
    def test_sync_from_claude(self, claude_sync, sample_tasks):
        """Claude → Knowledge Base同期テスト"""
        claude_sync.sync_from_claude(sample_tasks)
        
        # キャッシュファイル確認
        assert claude_sync.cache_file.exists()
        
        # タスクファイル確認
        task_file = claude_sync.vault_path / claude_sync.task_file_name
        assert task_file.exists()
        
        # タスクファイル内容確認
        content = task_file.read_text(encoding='utf-8')
        assert "UKF統合機能の実装" in content
        assert "テストケースの作成" in content
        assert "ドキュメント更新" in content
        assert "進行中タスク" in content
        assert "未完了タスク" in content
        assert "完了タスク" in content
    
    def test_sync_to_claude(self, claude_sync, sample_tasks):
        """Knowledge Base → Claude同期テスト"""
        # まず同期してタスクファイルを作成
        claude_sync.sync_from_claude(sample_tasks)
        
        # タスクを取得
        tasks = claude_sync.sync_to_claude()
        
        assert len(tasks) >= 3  # 最低限のタスク数
        assert all(isinstance(task, dict) for task in tasks)
        assert all("id" in task and "content" in task for task in tasks)
    
    def test_cache_operations(self, claude_sync, sample_tasks):
        """キャッシュ操作テスト"""
        # タスクをモデルに変換
        claude_tasks = [ClaudeTask.from_dict(task) for task in sample_tasks]
        
        # キャッシュに保存
        claude_sync._save_to_cache(claude_tasks)
        assert claude_sync.cache_file.exists()
        
        # キャッシュから読み込み
        cache_data = claude_sync._load_cache()
        assert "tasks" in cache_data
        assert len(cache_data["tasks"]) == 3
        assert cache_data["tasks"][0]["content"] == "UKF統合機能の実装"
    
    def test_markdown_generation(self, claude_sync):
        """マークダウン生成テスト"""
        tasks = [
            ClaudeTask("1", "タスク1", TaskStatus.COMPLETED, TaskPriority.HIGH),
            ClaudeTask("2", "タスク2", TaskStatus.IN_PROGRESS, TaskPriority.MEDIUM),
            ClaudeTask("3", "タスク3", TaskStatus.PENDING, TaskPriority.LOW)
        ]
        
        content = claude_sync._generate_task_markdown(
            [tasks[0]],  # completed
            [tasks[1]],  # in_progress
            [tasks[2]]   # pending
        )
        
        assert "# タスク管理" in content
        assert "## 🔄 進行中タスク" in content
        assert "## 📋 未完了タスク" in content
        assert "## ✅ 完了タスク" in content
        assert "タスク1" in content
        assert "タスク2" in content
        assert "タスク3" in content
    
    def test_sync_log_creation(self, claude_sync, sample_tasks):
        """同期ログ作成テスト"""
        claude_tasks = [ClaudeTask.from_dict(task) for task in sample_tasks]
        
        claude_sync._log_sync_operation(claude_tasks, "from_claude")
        
        log_file = claude_sync.vault_path / claude_sync.sync_log_dir / claude_sync.sync_log_file
        assert log_file.exists()
        
        content = log_file.read_text(encoding='utf-8')
        assert "同期実行" in content
        assert "from_claude" in content
    
    @patch('subprocess.run')
    def test_auto_commit(self, mock_run, claude_sync, sample_tasks):
        """Git自動コミットテスト"""
        # auto_commitを有効に
        claude_sync.auto_commit = True
        
        # 同期実行
        claude_sync.sync_from_claude(sample_tasks)
        
        # Git コマンドが呼ばれたことを確認
        assert mock_run.call_count >= 2  # add と commit
        
        # Git add コマンドの確認
        add_call = mock_run.call_args_list[0]
        assert add_call[0][0][0] == "git"
        assert add_call[0][0][1] == "add"
        
        # Git commit コマンドの確認
        commit_call = mock_run.call_args_list[1]
        assert commit_call[0][0][0] == "git"
        assert commit_call[0][0][1] == "commit"
    
    def test_get_sync_status(self, claude_sync):
        """同期状態取得テスト"""
        status = claude_sync.get_sync_status()
        
        assert "last_sync" in status
        assert "total_tasks" in status
        assert "cache_file" in status
        assert "vault_path" in status
        assert "auto_commit" in status
        
        assert status["auto_commit"] == False
        assert str(claude_sync.cache_file) in status["cache_file"]
    
    def test_empty_tasks_sync(self, claude_sync):
        """空タスクリストの同期テスト"""
        claude_sync.sync_from_claude([])
        
        # キャッシュファイルは作成されない
        assert not claude_sync.cache_file.exists()
        
        # タスクファイルも作成されない
        task_file = claude_sync.vault_path / claude_sync.task_file_name
        assert not task_file.exists()


class TestCLIFunctions:
    """CLI用関数のテスト"""
    
    def test_sync_from_claude_cli(self, temp_dir, sample_tasks):
        """CLI同期関数テスト"""
        vault_path = temp_dir / "knowledge"
        tasks_json = json.dumps(sample_tasks)
        
        sync_from_claude_cli(tasks_json, str(vault_path))
        
        # タスクファイルが作成されたことを確認
        task_file = vault_path / "タスク管理.md"
        assert task_file.exists()
    
    def test_get_tasks_for_claude(self, temp_dir, sample_tasks):
        """Claude向けタスク取得テスト"""
        vault_path = temp_dir / "knowledge"
        
        # まずタスクを同期
        sync = ClaudeCodeSync(vault_path=vault_path, auto_commit=False)
        sync.sync_from_claude(sample_tasks)
        
        # タスクを取得
        tasks_json = get_tasks_for_claude(str(vault_path))
        tasks = json.loads(tasks_json)
        
        assert isinstance(tasks, list)
        assert len(tasks) >= 3
    
    def test_error_handling(self, temp_dir):
        """エラーハンドリングテスト"""
        # 無効なJSON
        with pytest.raises(Exception):
            sync_from_claude_cli("invalid json", str(temp_dir))
        
        # 存在しないパスからの取得
        non_existent = temp_dir / "non_existent"
        result = get_tasks_for_claude(str(non_existent))
        tasks = json.loads(result)
        assert tasks == []  # 空リストが返される


class TestIntegration:
    """統合テスト"""
    
    def test_full_sync_cycle(self, temp_dir, sample_tasks):
        """完全な同期サイクルテスト"""
        vault_path = temp_dir / "knowledge"
        
        # 1. Claude → Knowledge Base
        sync1 = ClaudeCodeSync(vault_path=vault_path, auto_commit=False)
        sync1.sync_from_claude(sample_tasks)
        
        # 2. Knowledge Base → Claude
        tasks_for_claude = sync1.sync_to_claude()
        
        # 3. 別インスタンスで再同期
        sync2 = ClaudeCodeSync(vault_path=vault_path, auto_commit=False)
        sync2.sync_from_claude(tasks_for_claude)
        
        # 両方のタスクファイルが同じ内容であることを確認
        task_file = vault_path / "タスク管理.md"
        content = task_file.read_text(encoding='utf-8')
        
        assert "UKF統合機能の実装" in content
        assert "テストケースの作成" in content
        assert "ドキュメント更新" in content
    
    def test_callback_functionality(self, claude_sync, sample_tasks):
        """コールバック機能テスト"""
        callback_called = False
        callback_tasks = None
        
        def on_sync_complete(tasks):
            nonlocal callback_called, callback_tasks
            callback_called = True
            callback_tasks = tasks
        
        claude_sync.set_on_sync_complete(on_sync_complete)
        claude_sync.sync_from_claude(sample_tasks)
        
        assert callback_called
        assert len(callback_tasks) == 3
        assert callback_tasks[0].content == "UKF統合機能の実装"