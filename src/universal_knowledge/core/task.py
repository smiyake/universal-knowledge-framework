"""
タスク管理マネージャー - タスク作成・管理のコアクラス
Task Manager - Core class for task creation and management
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class TaskManager:
    """
    汎用タスク管理システム
    プロジェクトのタスク作成・進捗管理を行う
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """
        タスクマネージャーを初期化
        
        Args:
            project_path: プロジェクトパス（デフォルト: 現在のディレクトリ）
        """
        self.project_path = Path(project_path or ".")
        self.config_path = self.project_path / ".ukf"
        self.tasks_path = self.config_path / "tasks.json"
        
        # 設定ディレクトリ作成
        self.config_path.mkdir(exist_ok=True)
        
        # タスクファイル初期化
        if not self.tasks_path.exists():
            self._initialize_tasks_file()
    
    def add_task(self, content: str, priority: str = "medium") -> str:
        """
        新しいタスクを追加
        
        Args:
            content: タスク内容
            priority: 優先度 (high, medium, low)
            
        Returns:
            str: 作成されたタスクID
        """
        try:
            task_id = str(uuid.uuid4())[:8]
            
            task = {
                "id": task_id,
                "content": content,
                "status": "pending",
                "priority": priority,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            tasks = self._load_tasks()
            tasks.append(task)
            self._save_tasks(tasks)
            
            return task_id
            
        except Exception as e:
            raise Exception(f"タスク追加に失敗しました: {e}")
    
    def list_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        タスク一覧を取得
        
        Args:
            status_filter: 状態フィルタ (pending, in_progress, completed)
            
        Returns:
            List[Dict]: タスク一覧
        """
        try:
            tasks = self._load_tasks()
            
            if status_filter:
                tasks = [task for task in tasks if task["status"] == status_filter]
            
            # 優先度と作成日時でソート
            priority_order = {"high": 0, "medium": 1, "low": 2}
            tasks.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["created_at"]))
            
            return tasks
            
        except Exception as e:
            raise Exception(f"タスク一覧取得に失敗しました: {e}")
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        タスクの状態を更新
        
        Args:
            task_id: タスクID
            status: 新しい状態
            
        Returns:
            bool: 更新成功可否
        """
        try:
            tasks = self._load_tasks()
            
            for task in tasks:
                if task["id"] == task_id:
                    task["status"] = status
                    task["updated_at"] = datetime.now().isoformat()
                    
                    if status == "completed":
                        task["completed_at"] = datetime.now().isoformat()
                    
                    self._save_tasks(tasks)
                    return True
            
            raise ValueError(f"タスクID '{task_id}' が見つかりません")
            
        except Exception as e:
            raise Exception(f"タスク状態更新に失敗しました: {e}")
    
    def complete_task(self, task_id: str) -> bool:
        """
        タスクを完了にする
        
        Args:
            task_id: タスクID
            
        Returns:
            bool: 完了成功可否
        """
        return self.update_task_status(task_id, "completed")
    
    def start_task(self, task_id: str) -> bool:
        """
        タスクを開始する
        
        Args:
            task_id: タスクID
            
        Returns:
            bool: 開始成功可否
        """
        return self.update_task_status(task_id, "in_progress")
    
    def delete_task(self, task_id: str) -> bool:
        """
        タスクを削除
        
        Args:
            task_id: タスクID
            
        Returns:
            bool: 削除成功可否
        """
        try:
            tasks = self._load_tasks()
            
            original_length = len(tasks)
            tasks = [task for task in tasks if task["id"] != task_id]
            
            if len(tasks) == original_length:
                raise ValueError(f"タスクID '{task_id}' が見つかりません")
            
            self._save_tasks(tasks)
            return True
            
        except Exception as e:
            raise Exception(f"タスク削除に失敗しました: {e}")
    
    def get_task_stats(self) -> Dict[str, Any]:
        """
        タスク統計を取得
        
        Returns:
            Dict: タスク統計情報
        """
        try:
            tasks = self._load_tasks()
            
            stats = {
                "total": len(tasks),
                "pending": len([t for t in tasks if t["status"] == "pending"]),
                "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
                "completed": len([t for t in tasks if t["status"] == "completed"]),
                "high_priority": len([t for t in tasks if t["priority"] == "high"]),
                "medium_priority": len([t for t in tasks if t["priority"] == "medium"]),
                "low_priority": len([t for t in tasks if t["priority"] == "low"])
            }
            
            if stats["total"] > 0:
                stats["completion_rate"] = round((stats["completed"] / stats["total"]) * 100, 1)
            else:
                stats["completion_rate"] = 0.0
            
            return stats
            
        except Exception as e:
            raise Exception(f"タスク統計取得に失敗しました: {e}")
    
    def export_tasks(self, format_type: str = "markdown") -> str:
        """
        タスクをエクスポート
        
        Args:
            format_type: エクスポート形式 (markdown, json, csv)
            
        Returns:
            str: エクスポートされた内容
        """
        try:
            tasks = self._load_tasks()
            
            if format_type == "markdown":
                return self._export_as_markdown(tasks)
            elif format_type == "json":
                return json.dumps(tasks, indent=2, ensure_ascii=False)
            elif format_type == "csv":
                return self._export_as_csv(tasks)
            else:
                raise ValueError(f"未対応の形式: {format_type}")
                
        except Exception as e:
            raise Exception(f"タスクエクスポートに失敗しました: {e}")
    
    def _load_tasks(self) -> List[Dict[str, Any]]:
        """タスクファイルを読み込み"""
        try:
            with open(self.tasks_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """タスクファイルに保存"""
        with open(self.tasks_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    def _initialize_tasks_file(self) -> None:
        """タスクファイルを初期化"""
        self._save_tasks([])
    
    def _export_as_markdown(self, tasks: List[Dict[str, Any]]) -> str:
        """タスクをMarkdown形式でエクスポート"""
        content = "# タスク一覧\n\n"
        
        # 状態別でグループ化
        statuses = {
            "pending": "⏳ 未着手",
            "in_progress": "🔄 進行中", 
            "completed": "✅ 完了"
        }
        
        for status, emoji_title in statuses.items():
            status_tasks = [t for t in tasks if t["status"] == status]
            if status_tasks:
                content += f"## {emoji_title}\n\n"
                for task in status_tasks:
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    content += f"- {priority_emoji.get(task['priority'], '⚪')} [{task['id']}] {task['content']}\n"
                content += "\n"
        
        return content
    
    def _export_as_csv(self, tasks: List[Dict[str, Any]]) -> str:
        """タスクをCSV形式でエクスポート"""
        content = "ID,内容,状態,優先度,作成日時,更新日時\n"
        
        for task in tasks:
            content += f'"{task["id"]}","{task["content"]}","{task["status"]}","{task["priority"]}","{task["created_at"]}","{task["updated_at"]}"\n'
        
        return content