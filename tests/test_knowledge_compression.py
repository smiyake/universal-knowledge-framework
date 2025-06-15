#!/usr/bin/env python3
"""
知識圧縮機能のテスト
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from universal_knowledge.core.compressor import KnowledgeCompressor


class TestKnowledgeCompressor:
    """知識圧縮機能のテスト"""
    
    @pytest.fixture
    def temp_project(self):
        """テスト用の一時プロジェクトを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # プロジェクト構造を作成
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "docs").mkdir()
            
            # サンプルファイル
            (project_path / "README.md").write_text(
                "# Test Project\n\n## 概要\nこれはテストプロジェクトです"
            )
            (project_path / "requirements.txt").write_text("pytest\nclick\n")
            (project_path / "src" / "main.py").write_text(
                "from fastapi import FastAPI\n\napp = FastAPI()\n"
            )
            
            # .claude-task-cache.json
            tasks = {
                "tasks": [
                    {
                        "id": "1",
                        "content": "テストタスク1",
                        "status": "pending",
                        "priority": "high"
                    },
                    {
                        "id": "2",
                        "content": "テストタスク2",
                        "status": "in_progress",
                        "priority": "medium"
                    }
                ]
            }
            (project_path / ".claude-task-cache.json").write_text(
                json.dumps(tasks, ensure_ascii=False)
            )
            
            # ログファイル
            (project_path / "logs").mkdir()
            (project_path / "logs" / "error.log").write_text(
                "2025-01-15 10:00:00 ERROR: Redis connection failed\n"
                "2025-01-15 10:01:00 ERROR: Database timeout\n"
            )
            
            yield project_path
    
    @pytest.fixture
    def compressor(self):
        """コンプレッサーインスタンスを作成"""
        return KnowledgeCompressor()
    
    def test_init_default_config(self, compressor):
        """デフォルト設定での初期化をテスト"""
        assert compressor.config is not None
        assert 'knowledge_compression' in compressor.config
        assert compressor.config['knowledge_compression']['max_tokens'] == 5000
        assert compressor.config['knowledge_compression']['output_file'] == "PROJECT_KNOWLEDGE_MAP.md"
    
    def test_detect_project_type(self, compressor, temp_project):
        """プロジェクトタイプ検出をテスト"""
        # Pythonプロジェクト
        project_type = compressor._detect_project_type(temp_project)
        assert project_type == "python"
        
        # Node.jsプロジェクト
        (temp_project / "package.json").write_text('{"name": "test"}')
        project_type = compressor._detect_project_type(temp_project)
        assert project_type == "node/javascript"
    
    def test_find_current_errors(self, compressor, temp_project):
        """エラー検出をテスト"""
        errors = compressor._find_current_errors(temp_project)
        assert len(errors) > 0
        assert any("Redis" in error['message'] for error in errors)
        assert any("Database" in error['message'] for error in errors)
    
    def test_get_current_tasks(self, compressor, temp_project):
        """タスク取得をテスト"""
        tasks = compressor._get_current_tasks(temp_project)
        assert len(tasks) == 2
        assert tasks[0]['content'] == "テストタスク1"
        assert tasks[0]['priority'] == "high"
        assert tasks[1]['status'] == "in_progress"
    
    def test_analyze_architecture(self, compressor, temp_project):
        """アーキテクチャ分析をテスト"""
        architecture = compressor._analyze_architecture(temp_project)
        
        assert 'structure' in architecture
        assert 'main_files' in architecture
        assert 'services' in architecture
        assert 'databases' in architecture
        
        # main.pyが検出されていることを確認
        main_files = architecture['main_files']
        assert any(file['path'] == 'src/main.py' for file in main_files)
    
    def test_compress_project_claude_code_format(self, compressor, temp_project):
        """プロジェクト圧縮（Claude Code形式）をテスト"""
        result = compressor.compress_project(
            project_path=temp_project,
            max_tokens=5000,
            format="claude-code"
        )
        
        # 基本的なフォーマット確認
        assert "🧠 プロジェクト知識マップ" in result
        assert "Claude Code用" in result
        assert "📍 現在地" in result
        
        # タスク情報が含まれているか
        assert "🎯 現在のタスク" in result
        assert "テストタスク1" in result
        
        # エラー情報が含まれているか
        assert "Redis" in result or "ERROR" in result
    
    def test_filter_by_importance(self, compressor):
        """重要度フィルタリングをテスト"""
        state = {
            'project_info': {'name': 'test'},
            'current_errors': [
                {'type': 'ERROR', 'message': 'Test error 1'},
                {'type': 'ERROR', 'message': 'Test error 2'}
            ],
            'tasks': [
                {'content': 'Task 1', 'priority': 'high'},
                {'content': 'Task 2', 'priority': 'low'}
            ],
            'architecture': {
                'structure': {'name': 'project', 'children': []},
                'services': []
            },
            'recent_changes': {
                'commits': [],
                'files': []
            }
        }
        
        filtered = compressor.filter_by_importance(state, max_tokens=1000)
        
        # 基本情報は常に含まれる
        assert 'project_info' in filtered
        
        # 優先度順に含まれる
        assert 'current_errors' in filtered
        assert 'tasks' in filtered
    
    @patch('subprocess.run')
    def test_check_docker_errors(self, mock_run, compressor):
        """Dockerエラーチェックをテスト"""
        # Dockerコンテナがエラー状態
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test-container\tExited (1) 2 hours ago"
        )
        
        errors = compressor._check_docker_errors()
        assert len(errors) > 0
        assert errors[0]['type'] == 'Docker'
        assert 'test-container' in errors[0]['message']
    
    @patch('subprocess.run')
    def test_get_recent_changes(self, mock_run, compressor, temp_project):
        """最近の変更取得をテスト"""
        # git logのモック
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123 feat: Add new feature\ndef456 fix: Fix bug"
        )
        
        changes = compressor._get_recent_changes(temp_project)
        assert 'commits' in changes
        assert len(changes['commits']) == 2
        assert changes['commits'][0]['message'] == 'feat: Add new feature'
    
    def test_format_tree(self, compressor):
        """ツリーフォーマットをテスト"""
        tree = {
            'name': 'project',
            'type': 'directory',
            'children': [
                {'name': 'src', 'type': 'directory', 'children': []},
                {'name': 'README.md', 'type': 'file'}
            ]
        }
        
        lines = compressor._format_tree(tree)
        assert 'project/' in lines[0]
        assert '├── src/' in ''.join(lines)
        assert '└── README.md' in ''.join(lines)
    
    def test_compress_with_custom_config(self, temp_project):
        """カスタム設定での圧縮をテスト"""
        # カスタム設定ファイルを作成
        config = {
            "knowledge_compression": {
                "max_tokens": 3000,
                "claude_code_optimization": {
                    "enabled": True,
                    "priority_order": [
                        "current_tasks",
                        "errors_and_issues"
                    ]
                }
            }
        }
        
        config_path = temp_project / "test_config.json"
        config_path.write_text(json.dumps(config))
        
        # カスタム設定でコンプレッサーを作成
        compressor = KnowledgeCompressor(config_path)
        assert compressor.config['knowledge_compression']['max_tokens'] == 3000
        
        # 圧縮実行
        result = compressor.compress_project(
            project_path=temp_project,
            max_tokens=3000,
            format="claude-code"
        )
        
        assert result is not None
        assert len(result) > 0
