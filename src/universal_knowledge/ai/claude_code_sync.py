"""
Claude Code Integration - TodoRead/TodoWrite同期機能
Universal Knowledge Framework の Claude Code 連携モジュール
"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import logging
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    """タスクステータス定義"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(Enum):
    """タスク優先度定義"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ClaudeTask:
    """Claude Codeタスクのデータモデル"""
    id: str
    content: str
    status: TaskStatus
    priority: TaskPriority
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClaudeTask':
        """辞書から生成"""
        data['status'] = TaskStatus(data['status'])
        data['priority'] = TaskPriority(data['priority'])
        return cls(**data)


class ClaudeCodeSync:
    """Claude Code公式同期機能 - 汎用実装"""
    
    def __init__(self, 
                 vault_path: Optional[Path] = None,
                 cache_file: Optional[Path] = None,
                 auto_commit: bool = True,
                 log_level: str = "INFO"):
        """
        初期化
        
        Args:
            vault_path: ナレッジベースのパス（デフォルト: ./knowledge）
            cache_file: キャッシュファイルパス（デフォルト: ./.claude-task-cache.json）
            auto_commit: Git自動コミットを有効にするか
            log_level: ログレベル
        """
        self.vault_path = Path(vault_path or "./knowledge")
        self.cache_file = Path(cache_file or "./.claude-task-cache.json")
        self.auto_commit = auto_commit
        
        # ロギング設定
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level))
        
        # カスタマイズ可能な設定
        self.task_file_name = "タスク管理.md"
        self.sync_log_dir = "同期ログ"
        self.sync_log_file = "Claude-タスク同期履歴.md"
        
        # コールバック関数
        self._on_sync_complete: Optional[Callable] = None
        self._on_task_update: Optional[Callable] = None
    
    def sync_from_claude(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Claude CodeのTodoReadからタスクを取得して同期
        
        Args:
            tasks: TodoReadで取得したタスクリスト
        """
        if not tasks:
            self.logger.warning("同期するタスクがありません")
            return
        
        # タスクをモデルに変換
        claude_tasks = [ClaudeTask.from_dict(task) for task in tasks]
        
        # キャッシュに保存
        self._save_to_cache(claude_tasks)
        
        # ナレッジベースに同期
        self._sync_to_knowledge_base(claude_tasks)
        
        # 同期ログ記録
        self._log_sync_operation(claude_tasks, "from_claude")
        
        # Git自動コミット（有効な場合）
        if self.auto_commit:
            self._auto_commit_changes("Claude → Knowledge Base")
        
        # コールバック実行
        if self._on_sync_complete:
            self._on_sync_complete(claude_tasks)
        
        self.logger.info(f"Claude → Knowledge Base: {len(tasks)}タスクを同期")
    
    def sync_to_claude(self) -> List[Dict[str, Any]]:
        """
        ナレッジベースのタスクをClaude CodeのTodoWrite形式に変換
        
        Returns:
            TodoWrite用のタスクリスト
        """
        # ナレッジベースからタスクを読み込み
        tasks = self._read_tasks_from_knowledge_base()
        
        # Claude Code形式に変換
        claude_format_tasks = [task.to_dict() for task in tasks]
        
        # キャッシュ更新
        self._save_to_cache(tasks)
        
        # 同期ログ記録
        self._log_sync_operation(tasks, "to_claude")
        
        self.logger.info(f"Knowledge Base → Claude: {len(tasks)}タスクを準備")
        
        return claude_format_tasks
    
    def enable_realtime_sync(self, 
                           sync_interval: int = 300,
                           watch_files: bool = True) -> None:
        """
        リアルタイム双方向同期を有効化
        
        Args:
            sync_interval: 同期間隔（秒）
            watch_files: ファイル変更監視を有効にするか
        """
        # TODO: 実装予定
        # - ファイル監視によるトリガー
        # - 定期的なポーリング
        # - WebSocket/SSEによるリアルタイム通信
        raise NotImplementedError("リアルタイム同期は今後実装予定です")
    
    def set_on_sync_complete(self, callback: Callable) -> None:
        """同期完了時のコールバック設定"""
        self._on_sync_complete = callback
    
    def set_on_task_update(self, callback: Callable) -> None:
        """タスク更新時のコールバック設定"""
        self._on_task_update = callback
    
    def get_sync_status(self) -> Dict[str, Any]:
        """同期状態を取得"""
        cache_data = self._load_cache()
        
        return {
            "last_sync": cache_data.get("last_sync", "未同期"),
            "total_tasks": len(cache_data.get("tasks", [])),
            "cache_file": str(self.cache_file),
            "vault_path": str(self.vault_path),
            "auto_commit": self.auto_commit
        }
    
    def _save_to_cache(self, tasks: List[ClaudeTask]) -> None:
        """タスクをキャッシュに保存"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "tasks": [task.to_dict() for task in tasks],
            "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        self.logger.debug(f"キャッシュに{len(tasks)}タスクを保存")
    
    def _load_cache(self) -> Dict[str, Any]:
        """キャッシュからデータを読み込み"""
        if not self.cache_file.exists():
            return {"tasks": []}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"キャッシュ読み込みエラー: {e}")
            return {"tasks": []}
    
    def _sync_to_knowledge_base(self, tasks: List[ClaudeTask]) -> None:
        """ナレッジベースにタスクを同期"""
        # タスクファイルパス
        task_file = self.vault_path / self.task_file_name
        
        # ディレクトリ作成
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # タスクをステータス別に分類
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        
        # マークダウン生成
        content = self._generate_task_markdown(
            completed_tasks, in_progress_tasks, pending_tasks
        )
        
        # ファイル更新
        self._update_or_create_file(task_file, content)
    
    def _read_tasks_from_knowledge_base(self) -> List[ClaudeTask]:
        """ナレッジベースからタスクを読み込み"""
        task_file = self.vault_path / self.task_file_name
        
        if not task_file.exists():
            return []
        
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # マークダウンからタスクを抽出（簡易実装）
        tasks = []
        task_pattern = r'- \[([ x>])\] #(\w+) \*\*(.*?)\*\*'
        
        for match in re.finditer(task_pattern, content):
            status_char, task_id, content_text = match.groups()
            
            # ステータス判定
            if status_char == 'x':
                status = TaskStatus.COMPLETED
            elif status_char == '>':
                status = TaskStatus.IN_PROGRESS
            else:
                status = TaskStatus.PENDING
            
            # タスク作成（優先度は簡易的にmediumとする）
            task = ClaudeTask(
                id=task_id,
                content=content_text,
                status=status,
                priority=TaskPriority.MEDIUM
            )
            tasks.append(task)
        
        return tasks
    
    def _generate_task_markdown(self, 
                              completed: List[ClaudeTask],
                              in_progress: List[ClaudeTask],
                              pending: List[ClaudeTask]) -> str:
        """タスクのマークダウンを生成"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sections = [
            f"# タスク管理",
            f"",
            f"最終更新: {timestamp} (Claude Code 自動同期)",
            f"",
        ]
        
        # 進行中タスク
        if in_progress:
            sections.extend([
                "## 🔄 進行中タスク",
                ""
            ])
            for task in in_progress:
                sections.append(f"- [>] #{task.id} **{task.content}**")
            sections.append("")
        
        # 未完了タスク
        if pending:
            sections.extend([
                "## 📋 未完了タスク",
                ""
            ])
            for task in pending:
                priority_emoji = {
                    TaskPriority.HIGH: "🔴",
                    TaskPriority.MEDIUM: "🟡",
                    TaskPriority.LOW: "🟢"
                }[task.priority]
                sections.append(
                    f"- [ ] #{task.id} **{task.content}** {priority_emoji} {task.priority.value}"
                )
            sections.append("")
        
        # 完了タスク
        if completed:
            sections.extend([
                "## ✅ 完了タスク",
                ""
            ])
            for task in completed:
                sections.append(f"- [x] #{task.id} **{task.content}**")
            sections.append("")
        
        # サマリー
        total = len(completed) + len(in_progress) + len(pending)
        sections.extend([
            "---",
            "",
            "## 📊 サマリー",
            "",
            f"- **総タスク数**: {total}",
            f"- **完了**: {len(completed)}",
            f"- **進行中**: {len(in_progress)}",
            f"- **未完了**: {len(pending)}",
            f"- **完了率**: {len(completed) / total * 100:.1f}%" if total > 0 else "- **完了率**: 0%"
        ])
        
        return '\n'.join(sections)
    
    def _update_or_create_file(self, file_path: Path, content: str) -> None:
        """ファイルを更新または作成"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.debug(f"ファイルを更新: {file_path}")
    
    def _log_sync_operation(self, 
                          tasks: List[ClaudeTask],
                          direction: str) -> None:
        """同期操作をログに記録"""
        log_dir = self.vault_path / self.sync_log_dir
        log_file = log_dir / self.sync_log_file
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログエントリ作成
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [
            f"",
            f"## {timestamp} - 同期実行 ({direction})",
            f"",
            f"- **完了**: {len([t for t in tasks if t.status == TaskStatus.COMPLETED])}タスク",
            f"- **進行中**: {len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])}タスク",
            f"- **未完了**: {len([t for t in tasks if t.status == TaskStatus.PENDING])}タスク",
            f"- **合計**: {len(tasks)}タスク",
            f"",
            f"---"
        ]
        
        # 既存のログに追記
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = "# Claude Code 同期履歴\n"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(existing_content + '\n'.join(log_entry) + '\n')
    
    def _auto_commit_changes(self, message: str) -> None:
        """Git自動コミット"""
        try:
            # 変更をステージング
            subprocess.run(
                ["git", "add", str(self.vault_path)],
                check=True,
                cwd=self.vault_path.parent
            )
            
            # コミット
            commit_message = f"auto: {message} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                cwd=self.vault_path.parent
            )
            
            self.logger.info("Git自動コミット完了")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Git自動コミット失敗: {e}")


# 便利な関数
def sync_from_claude_cli(tasks_json: str, vault_path: Optional[str] = None) -> None:
    """CLI用: Claude Codeからタスクを同期"""
    try:
        tasks = json.loads(tasks_json) if isinstance(tasks_json, str) else tasks_json
        sync = ClaudeCodeSync(vault_path=Path(vault_path) if vault_path else None)
        sync.sync_from_claude(tasks)
    except Exception as e:
        logging.error(f"同期エラー: {e}")
        raise


def get_tasks_for_claude(vault_path: Optional[str] = None) -> str:
    """CLI用: Claude Code向けにタスクをJSON形式で取得"""
    try:
        sync = ClaudeCodeSync(vault_path=Path(vault_path) if vault_path else None)
        tasks = sync.sync_to_claude()
        return json.dumps(tasks, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"タスク取得エラー: {e}")
        raise