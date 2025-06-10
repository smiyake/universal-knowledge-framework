"""CLAUDE.md Auto-updater - 自動更新機能"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Dummy classes for when watchdog is not available
    class FileSystemEventHandler:
        def on_modified(self, event): pass
        def on_created(self, event): pass
        def on_deleted(self, event): pass
    
    class Observer:
        def __init__(self): self._running = False
        def schedule(self, *args, **kwargs): pass
        def start(self): self._running = True
        def stop(self): self._running = False
        def join(self): pass
        def is_alive(self): return self._running

from .claude_manager import ClaudeManager
from .session_tracker import SessionTracker
from .session_tracker import SimpleGitUtils


class ClaudeAutoUpdater(FileSystemEventHandler):
    """CLAUDE.md自動更新ハンドラー"""
    
    def __init__(self, project_path: Optional[Path] = None, 
                 update_interval: int = 30):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.claude_manager = ClaudeManager(self.project_path)
        self.session_tracker = SessionTracker(self.project_path)
        self.git_utils = SimpleGitUtils(self.project_path)
        self.logger = logging.getLogger(__name__)
        
        self.update_interval = update_interval
        self.last_update = 0
        self.pending_changes = set()
        
    def on_modified(self, event):
        """ファイル変更イベント処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # CLAUDE.md自体の変更は無視
        if file_path.name == "CLAUDE.md":
            return
            
        # 隠しファイル・ディレクトリは無視
        if any(part.startswith('.') for part in file_path.parts):
            return
            
        # 重要なファイルのみ追跡
        if self._is_important_file(file_path):
            self.pending_changes.add(str(file_path.relative_to(self.project_path)))
            self._schedule_update()
    
    def on_created(self, event):
        """ファイル作成イベント処理"""
        self.on_modified(event)
    
    def on_deleted(self, event):
        """ファイル削除イベント処理"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._is_important_file(file_path):
                self.pending_changes.add(f"[削除] {file_path.relative_to(self.project_path)}")
                self._schedule_update()
    
    def _is_important_file(self, file_path: Path) -> bool:
        """重要ファイル判定"""
        # プログラムファイル
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php'}
        if file_path.suffix.lower() in code_extensions:
            return True
            
        # 設定ファイル
        config_files = {'package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml', 
                       'Dockerfile', 'docker-compose.yml', 'Makefile'}
        if file_path.name in config_files:
            return True
            
        # ドキュメントファイル
        doc_extensions = {'.md', '.rst', '.txt'}
        if file_path.suffix.lower() in doc_extensions and file_path.name != "CLAUDE.md":
            return True
            
        return False
    
    def _schedule_update(self):
        """更新スケジュール"""
        current_time = time.time()
        
        # 最後の更新から指定時間経過後に更新
        if current_time - self.last_update >= self.update_interval:
            self._perform_update()
        
    def _perform_update(self):
        """更新実行"""
        if not self.pending_changes:
            return
            
        try:
            # 現在の開発コンテキスト構築
            context = self._build_development_context()
            
            # CLAUDE.md更新
            self.claude_manager.update_development_context(context)
            
            # アクティブセッションがあれば更新
            active_sessions = self.session_tracker.get_active_sessions()
            for session in active_sessions:
                session_id = session['session_id']
                changes_list = list(self.pending_changes)
                
                # セッションに変更を記録
                self.session_tracker.add_note(
                    session_id, 
                    f"ファイル変更検出: {', '.join(changes_list[:5])}{'...' if len(changes_list) > 5 else ''}",
                    "auto_update"
                )
            
            self.pending_changes.clear()
            self.last_update = time.time()
            
            self.logger.info(f"CLAUDE.md自動更新完了: {len(context.get('recent_changes', []))}件の変更")
            
        except Exception as e:
            self.logger.error(f"CLAUDE.md自動更新エラー: {e}")
    
    def _build_development_context(self) -> Dict[str, Any]:
        """開発コンテキスト構築"""
        context = {}
        
        # 最近の変更
        if self.pending_changes:
            context["recent_changes"] = list(self.pending_changes)
        
        # Git状態
        try:
            git_status = self.git_utils.get_status()
            if git_status.get("modified_files") or git_status.get("staged_files"):
                context["git_status"] = git_status
        except Exception:
            pass
        
        # アクティブセッション情報
        active_sessions = self.session_tracker.get_active_sessions()
        if active_sessions:
            session = active_sessions[0]  # 最新のアクティブセッション
            context["current_task"] = f"セッション {session['session_id']}: {session.get('description', '')}"
        
        return context


class AutoUpdateManager:
    """自動更新管理"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.observer = None
        self.event_handler = None
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self, update_interval: int = 30) -> bool:
        """監視開始"""
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("watchdogライブラリが利用できません。自動監視は無効です。")
            return False
            
        try:
            if self.observer:
                self.logger.warning("監視は既に開始されています")
                return False
            
            self.event_handler = ClaudeAutoUpdater(self.project_path, update_interval)
            self.observer = Observer()
            
            # プロジェクトディレクトリを監視
            self.observer.schedule(
                self.event_handler, 
                str(self.project_path), 
                recursive=True
            )
            
            self.observer.start()
            self.logger.info(f"CLAUDE.md自動更新監視を開始しました: {self.project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"監視開始エラー: {e}")
            return False
    
    def stop_monitoring(self):
        """監視停止"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
                self.event_handler = None
                self.logger.info("CLAUDE.md自動更新監視を停止しました")
            
        except Exception as e:
            self.logger.error(f"監視停止エラー: {e}")
    
    def is_monitoring(self) -> bool:
        """監視状態確認"""
        return self.observer is not None and self.observer.is_alive()
    
    def get_status(self) -> Dict[str, Any]:
        """監視状態取得"""
        return {
            "monitoring": self.is_monitoring(),
            "project_path": str(self.project_path),
            "pending_changes": len(self.event_handler.pending_changes) if self.event_handler else 0,
            "last_update": self.event_handler.last_update if self.event_handler else 0
        }
    
    def force_update(self) -> bool:
        """強制更新"""
        if not self.event_handler:
            return False
            
        try:
            self.event_handler._perform_update()
            return True
        except Exception as e:
            self.logger.error(f"強制更新エラー: {e}")
            return False