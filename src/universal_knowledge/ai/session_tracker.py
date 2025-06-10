"""AI Development Session Tracker - Claude Code連携・開発支援"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class SimpleGitUtils:
    """簡易Git操作ユーティリティ"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def get_current_branch(self) -> str:
        try:
            import subprocess
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, cwd=self.project_path)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def get_current_commit(self) -> str:
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.project_path)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def get_status(self) -> Dict[str, Any]:
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_path)
            if result.returncode != 0:
                return {"error": "git status failed"}
            
            modified_files = []
            staged_files = []
            
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                status = line[:2]
                filename = line[3:]
                
                if status[0] in 'MADRC':
                    staged_files.append(filename)
                if status[1] in 'MD':
                    modified_files.append(filename)
            
            return {
                "modified_files": modified_files,
                "staged_files": staged_files
            }
        except:
            return {"error": "git not available"}
    
    def get_staged_files(self) -> List[str]:
        return self.get_status().get("staged_files", [])
    
    def get_modified_files(self) -> List[str]:
        return self.get_status().get("modified_files", [])
    
    def get_commits_since(self, timestamp: str) -> List[Dict[str, Any]]:
        try:
            import subprocess
            result = subprocess.run(['git', 'log', '--since', timestamp, '--oneline'], 
                                  capture_output=True, text=True, cwd=self.project_path)
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1]
                        })
            return commits
        except:
            return []
    
    def get_recent_commits(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            import subprocess
            result = subprocess.run(['git', 'log', f'-{limit}', '--oneline'], 
                                  capture_output=True, text=True, cwd=self.project_path)
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "files": []  # ファイル情報は別途取得が必要
                        })
            return commits
        except:
            return []


class SessionTracker:
    """AI開発セッション追跡管理"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.sessions_dir = self.project_path / ".ukf" / "ai_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.git_utils = SimpleGitUtils(self.project_path)
        self.logger = logging.getLogger(__name__)
        
    def start_session(self, session_type: str = "implementation", 
                     description: str = "", context: Dict[str, Any] = None) -> str:
        """AI開発セッション開始"""
        session_id = str(uuid.uuid4())[:8]
        
        # Git状態取得
        git_status = self._get_git_context()
        
        session_data = {
            "session_id": session_id,
            "type": session_type,
            "description": description,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "status": "active",
            "project_path": str(self.project_path),
            "git_context": git_status,
            "context": context or {},
            "files_modified": [],
            "commits": [],
            "milestones": [],
            "notes": []
        }
        
        session_file = self.sessions_dir / f"session_{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"AI開発セッション開始: {session_id} ({session_type})")
        return session_id
    
    def end_session(self, session_id: str, summary: str = "") -> bool:
        """AI開発セッション終了"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            self.logger.error(f"セッションが見つかりません: {session_id}")
            return False
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # セッション終了データ更新
        session_data.update({
            "end_time": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "summary": summary,
            "final_git_context": self._get_git_context()
        })
        
        # 変更ファイル検出
        modified_files = self._detect_modified_files(session_data["git_context"])
        session_data["files_modified"] = modified_files
        
        # コミット履歴取得
        commits = self._get_session_commits(session_data["start_time"])
        session_data["commits"] = commits
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"AI開発セッション終了: {session_id}")
        return True
    
    def add_milestone(self, session_id: str, milestone: str, 
                     context: Dict[str, Any] = None) -> bool:
        """セッションマイルストーン追加"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            self.logger.error(f"セッションが見つかりません: {session_id}")
            return False
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        milestone_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": milestone,
            "context": context or {},
            "git_state": self._get_git_context()
        }
        
        session_data["milestones"].append(milestone_data)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def add_note(self, session_id: str, note: str, note_type: str = "general") -> bool:
        """セッションノート追加"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            self.logger.error(f"セッションが見つかりません: {session_id}")
            return False
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        note_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": note_type,
            "content": note,
        }
        
        session_data["notes"].append(note_data)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッション情報取得"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_sessions(self, status: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """セッション一覧取得"""
        sessions = []
        
        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                if status and session_data.get("status") != status:
                    continue
                
                sessions.append(session_data)
            except Exception as e:
                self.logger.error(f"セッションファイル読み込みエラー: {session_file} - {e}")
        
        # 開始時間でソート（新しい順）
        sessions.sort(key=lambda x: x["start_time"], reverse=True)
        
        return sessions[:limit]
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """アクティブセッション取得"""
        return self.list_sessions(status="active")
    
    def _get_git_context(self) -> Dict[str, Any]:
        """Git状態取得"""
        try:
            return {
                "current_branch": self.git_utils.get_current_branch(),
                "commit_hash": self.git_utils.get_current_commit(),
                "status": self.git_utils.get_status(),
                "staged_files": self.git_utils.get_staged_files(),
                "modified_files": self.git_utils.get_modified_files()
            }
        except Exception as e:
            self.logger.error(f"Git状態取得エラー: {e}")
            return {"error": str(e)}
    
    def _detect_modified_files(self, initial_git_context: Dict[str, Any]) -> List[str]:
        """変更ファイル検出"""
        try:
            current_modified = self.git_utils.get_modified_files()
            initial_modified = initial_git_context.get("modified_files", [])
            
            # 新しく変更されたファイル
            new_modified = list(set(current_modified) - set(initial_modified))
            return new_modified
        except Exception as e:
            self.logger.error(f"変更ファイル検出エラー: {e}")
            return []
    
    def _get_session_commits(self, start_time: str) -> List[Dict[str, Any]]:
        """セッション期間のコミット取得"""
        try:
            # ISO形式の時間をGitの形式に変換
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            start_timestamp = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            commits = self.git_utils.get_commits_since(start_timestamp)
            return commits
        except Exception as e:
            self.logger.error(f"コミット履歴取得エラー: {e}")
            return []
    
    def generate_session_report(self, session_id: str) -> str:
        """セッションレポート生成"""
        session_data = self.get_session(session_id)
        if not session_data:
            return f"セッション {session_id} が見つかりません"
        
        report_lines = [
            f"# AI開発セッションレポート",
            f"",
            f"**セッションID**: {session_data['session_id']}",
            f"**タイプ**: {session_data['type']}",
            f"**説明**: {session_data.get('description', 'なし')}",
            f"**開始時間**: {session_data['start_time']}",
            f"**終了時間**: {session_data.get('end_time', '実行中')}",
            f"**ステータス**: {session_data['status']}",
            f"",
            f"## 変更ファイル ({len(session_data.get('files_modified', []))}件)",
        ]
        
        for file_path in session_data.get('files_modified', []):
            report_lines.append(f"- {file_path}")
        
        report_lines.extend([
            f"",
            f"## コミット履歴 ({len(session_data.get('commits', []))}件)",
        ])
        
        for commit in session_data.get('commits', []):
            report_lines.append(f"- {commit.get('hash', '')[:8]} {commit.get('message', '')}")
        
        if session_data.get('milestones'):
            report_lines.extend([
                f"",
                f"## マイルストーン ({len(session_data['milestones'])}件)",
            ])
            
            for milestone in session_data['milestones']:
                timestamp = milestone['timestamp'][:19]
                report_lines.append(f"- {timestamp}: {milestone['description']}")
        
        if session_data.get('notes'):
            report_lines.extend([
                f"",
                f"## ノート ({len(session_data['notes'])}件)",
            ])
            
            for note in session_data['notes']:
                timestamp = note['timestamp'][:19]
                note_type = note.get('type', 'general')
                report_lines.append(f"- [{note_type}] {timestamp}: {note['content']}")
        
        if session_data.get('summary'):
            report_lines.extend([
                f"",
                f"## サマリー",
                f"{session_data['summary']}"
            ])
        
        return '\n'.join(report_lines)