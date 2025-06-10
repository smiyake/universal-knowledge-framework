"""
Obsidian Bridge Adapter - Obsidian連携アダプター
Obsidian Integration Adapter for Universal Knowledge Framework
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .bridge import ToolAdapter, StandardProjectData


class ObsidianAdapter(ToolAdapter):
    """
    Obsidian用ブリッジアダプター
    Obsidianボルトとプロジェクトデータの同期を行う
    """
    
    def __init__(self):
        super().__init__("obsidian")
        self.vault_path: Optional[Path] = None
        self.project_path: Optional[Path] = None
        self.obsidian_config_path: Optional[Path] = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Obsidianボルトに接続
        
        Args:
            config: 接続設定
                - vault_path: ボルトパス
                - project_path: プロジェクトパス
                - create_if_missing: ボルトが存在しない場合作成するか
                
        Returns:
            bool: 接続成功可否
        """
        try:
            vault_path = config.get('vault_path')
            project_path = config.get('project_path', Path.cwd())
            create_if_missing = config.get('create_if_missing', True)
            
            if not vault_path:
                # デフォルトボルトパス（プロジェクト内のknowledgeディレクトリ）
                vault_path = Path(project_path) / "knowledge"
            
            self.vault_path = Path(vault_path)
            self.project_path = Path(project_path)
            self.obsidian_config_path = self.vault_path / ".obsidian"
            
            # ボルトディレクトリの確認・作成
            if not self.vault_path.exists() and create_if_missing:
                self.vault_path.mkdir(parents=True, exist_ok=True)
                self._initialize_obsidian_vault()
            elif not self.vault_path.exists():
                return False
            
            # .obsidianディレクトリの確認・作成
            if not self.obsidian_config_path.exists() and create_if_missing:
                self._initialize_obsidian_vault()
            
            self._config = config
            self._connected = True
            
            print(f"✅ Obsidianボルトに接続しました: {self.vault_path}")
            return True
            
        except Exception as e:
            print(f"❌ Obsidian接続エラー: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Obsidianボルトから切断
        
        Returns:
            bool: 切断成功可否
        """
        try:
            self.vault_path = None
            self.project_path = None
            self.obsidian_config_path = None
            self._connected = False
            self._config = {}
            
            print("✅ Obsidianボルトから切断しました")
            return True
            
        except Exception as e:
            print(f"❌ Obsidian切断エラー: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        接続状態を確認
        
        Returns:
            bool: 接続状態
        """
        return (self._connected and 
                self.vault_path is not None and 
                self.vault_path.exists() and
                self.obsidian_config_path is not None and
                self.obsidian_config_path.exists())
    
    def sync_data(self, project_data: StandardProjectData) -> bool:
        """
        プロジェクトデータをObsidianボルトに同期
        
        Args:
            project_data: 同期するプロジェクトデータ
            
        Returns:
            bool: 同期成功可否
        """
        if not self.is_connected():
            return False
        
        try:
            # プロジェクト概要ファイル作成/更新
            self._sync_project_overview(project_data)
            
            # タスクファイル作成/更新
            self._sync_tasks(project_data)
            
            # ファイル構造マップ作成/更新
            self._sync_file_structure(project_data)
            
            # メタデータ同期
            self._sync_metadata(project_data)
            
            print(f"✅ Obsidianボルトに同期完了: {len(project_data.files)}ファイル")
            return True
            
        except Exception as e:
            print(f"❌ Obsidian同期エラー: {e}")
            return False
    
    def export_data(self) -> Optional[StandardProjectData]:
        """
        Obsidianボルトからデータをエクスポート
        
        Returns:
            Optional[StandardProjectData]: エクスポートされたデータ
        """
        if not self.is_connected():
            return None
        
        try:
            # ボルト内のファイル情報収集
            files = []
            for file_path in self.vault_path.rglob("*.md"):
                if not any(part.startswith('.') for part in file_path.parts):
                    relative_path = file_path.relative_to(self.vault_path)
                    files.append({
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            
            # タスク情報読み込み
            tasks = self._load_tasks_from_vault()
            
            # メタデータ読み込み
            metadata = self._load_metadata_from_vault()
            
            return StandardProjectData(
                name=metadata.get('name', self.vault_path.name),
                description=metadata.get('description', ''),
                path=str(self.project_path) if self.project_path else str(self.vault_path),
                type=metadata.get('type', 'obsidian'),
                created_at=metadata.get('created_at', datetime.now().isoformat()),
                last_modified=datetime.now().isoformat(),
                metadata=metadata,
                files=files,
                tasks=tasks,
                tags=metadata.get('tags', [])
            )
            
        except Exception as e:
            print(f"❌ Obsidianエクスポートエラー: {e}")
            return None
    
    def import_data(self, data: StandardProjectData) -> bool:
        """
        StandardProjectDataをObsidianボルトにインポート
        
        Args:
            data: インポートするデータ
            
        Returns:
            bool: インポート成功可否
        """
        if not self.is_connected():
            return False
        
        return self.sync_data(data)
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Obsidianツール情報を取得
        
        Returns:
            Dict[str, Any]: ツール情報
        """
        info = {
            "name": "Obsidian",
            "type": "knowledge_management",
            "version": "1.0.0",
            "adapter_version": "1.0.0",
            "supported_formats": ["markdown", "json"],
            "features": [
                "note_taking",
                "linking",
                "graph_view",
                "task_management"
            ]
        }
        
        if self.is_connected():
            info.update({
                "vault_path": str(self.vault_path),
                "project_path": str(self.project_path),
                "connected": True,
                "vault_exists": self.vault_path.exists(),
                "config_exists": self.obsidian_config_path.exists()
            })
        else:
            info["connected"] = False
        
        return info
    
    def _initialize_obsidian_vault(self) -> None:
        """Obsidianボルトを初期化"""
        try:
            # .obsidianディレクトリ作成
            self.obsidian_config_path.mkdir(parents=True, exist_ok=True)
            
            # 基本設定ファイル作成
            self._create_obsidian_config()
            
            # ボルト用ディレクトリ構造作成
            self._create_vault_structure()
            
            print(f"📁 Obsidianボルトを初期化しました: {self.vault_path}")
            
        except Exception as e:
            print(f"⚠️ Obsidianボルト初期化エラー: {e}")
    
    def _create_obsidian_config(self) -> None:
        """Obsidian設定ファイルを作成"""
        # app.json
        app_config = {
            "legacyEditor": False,
            "livePreview": True,
            "defaultViewMode": "source",
            "theme": "obsidian",
            "translucency": False,
            "alwaysUpdateLinks": True
        }
        
        with open(self.obsidian_config_path / "app.json", "w", encoding="utf-8") as f:
            json.dump(app_config, f, indent=2, ensure_ascii=False)
        
        # workspace.json
        workspace_config = {
            "main": {
                "id": "main",
                "type": "split",
                "children": [
                    {
                        "id": "editor",
                        "type": "leaf",
                        "state": {
                            "type": "markdown",
                            "state": {
                                "file": "00_Overview/プロジェクト概要.md",
                                "mode": "source"
                            }
                        }
                    }
                ]
            },
            "left": {
                "id": "left",
                "type": "split",
                "children": [
                    {
                        "id": "file-explorer",
                        "type": "leaf",
                        "state": {
                            "type": "file-explorer",
                            "state": {}
                        }
                    }
                ],
                "collapsed": False
            },
            "right": {
                "id": "right",
                "type": "split",
                "children": [
                    {
                        "id": "outline",
                        "type": "leaf",
                        "state": {
                            "type": "outline",
                            "state": {}
                        }
                    }
                ],
                "collapsed": False
            },
            "active": "editor",
            "lastOpenFiles": ["00_Overview/プロジェクト概要.md"]
        }
        
        with open(self.obsidian_config_path / "workspace.json", "w", encoding="utf-8") as f:
            json.dump(workspace_config, f, indent=2, ensure_ascii=False)
    
    def _create_vault_structure(self) -> None:
        """ボルト用ディレクトリ構造を作成"""
        directories = [
            "00_Overview",
            "01_Requirements",
            "02_Design", 
            "03_Implementation",
            "04_Testing",
            "05_Deployment",
            "99_Archives"
        ]
        
        for dir_name in directories:
            (self.vault_path / dir_name).mkdir(exist_ok=True)
    
    def _sync_project_overview(self, project_data: StandardProjectData) -> None:
        """プロジェクト概要を同期"""
        overview_dir = self.vault_path / "00_Overview"
        overview_dir.mkdir(exist_ok=True)
        
        overview_content = f"""# {project_data.name}

## プロジェクト概要
{project_data.description}

## 基本情報
- **プロジェクトタイプ**: {project_data.type}
- **作成日**: {project_data.created_at[:10]}
- **最終更新**: {project_data.last_modified[:10]}
- **ファイル数**: {len(project_data.files)}

## タグ
{' '.join(f'#{tag}' for tag in project_data.tags) if project_data.tags else 'なし'}

## 関連リンク
- [[タスク管理]] - プロジェクトタスクの一覧
- [[ファイル構造]] - プロジェクトファイル構造
- [[進捗管理]] - 開発進捗の追跡

---
*このファイルは Universal Knowledge Framework により自動生成されました*
*最終同期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(overview_dir / "プロジェクト概要.md", "w", encoding="utf-8") as f:
            f.write(overview_content)
    
    def _sync_tasks(self, project_data: StandardProjectData) -> None:
        """タスクを同期"""
        tasks_dir = self.vault_path / "03_Implementation"
        tasks_dir.mkdir(exist_ok=True)
        
        if not project_data.tasks:
            tasks_content = """# タスク管理

## 現在のタスク
タスクはまだ登録されていません。

## 完了したタスク
なし

---
*このファイルは Universal Knowledge Framework により自動生成されました*
"""
        else:
            pending_tasks = [t for t in project_data.tasks if t.get('status') == 'pending']
            in_progress_tasks = [t for t in project_data.tasks if t.get('status') == 'in_progress']
            completed_tasks = [t for t in project_data.tasks if t.get('status') == 'completed']
            
            tasks_content = f"""# タスク管理

## 進行中のタスク
{self._format_tasks(in_progress_tasks) if in_progress_tasks else '現在進行中のタスクはありません'}

## 待機中のタスク
{self._format_tasks(pending_tasks) if pending_tasks else '待機中のタスクはありません'}

## 完了したタスク
{self._format_tasks(completed_tasks) if completed_tasks else '完了したタスクはありません'}

---
*このファイルは Universal Knowledge Framework により自動生成されました*
*最終同期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(tasks_dir / "タスク管理.md", "w", encoding="utf-8") as f:
            f.write(tasks_content)
    
    def _sync_file_structure(self, project_data: StandardProjectData) -> None:
        """ファイル構造を同期"""
        overview_dir = self.vault_path / "00_Overview"
        overview_dir.mkdir(exist_ok=True)
        
        # ファイルを種類別に分類
        file_categories = {}
        for file_info in project_data.files:
            ext = Path(file_info["path"]).suffix.lower()
            if ext not in file_categories:
                file_categories[ext] = []
            file_categories[ext].append(file_info)
        
        structure_content = f"""# ファイル構造

## 概要
- **総ファイル数**: {len(project_data.files)}
- **プロジェクトパス**: `{project_data.path}`

## ファイル種別
"""
        
        for ext, files in sorted(file_categories.items()):
            ext_name = ext if ext else "拡張子なし"
            structure_content += f"\n### {ext_name} ({len(files)}ファイル)\n"
            
            for file_info in sorted(files, key=lambda x: x["path"])[:10]:  # 最大10ファイル表示
                size_kb = file_info["size"] / 1024
                structure_content += f"- `{file_info['path']}` ({size_kb:.1f}KB)\n"
            
            if len(files) > 10:
                structure_content += f"- ... その他 {len(files) - 10} ファイル\n"
        
        structure_content += f"""
---
*このファイルは Universal Knowledge Framework により自動生成されました*
*最終同期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(overview_dir / "ファイル構造.md", "w", encoding="utf-8") as f:
            f.write(structure_content)
    
    def _sync_metadata(self, project_data: StandardProjectData) -> None:
        """メタデータを同期"""
        metadata_file = self.obsidian_config_path / "ukf-metadata.json"
        
        metadata = {
            "project_data": project_data.to_dict(),
            "sync_info": {
                "last_sync": datetime.now().isoformat(),
                "sync_source": "universal-knowledge-framework",
                "adapter_version": "1.0.0"
            }
        }
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _format_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        """タスクをMarkdown形式でフォーマット"""
        if not tasks:
            return "なし"
        
        formatted = ""
        for task in tasks:
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢'
            }.get(task.get('priority', 'medium'), '⚪')
            
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅'
            }.get(task.get('status', 'pending'), '❓')
            
            formatted += f"- {status_emoji} {priority_emoji} {task.get('content', '')}\n"
        
        return formatted
    
    def _load_tasks_from_vault(self) -> List[Dict[str, Any]]:
        """ボルトからタスク情報を読み込み"""
        try:
            metadata_file = self.obsidian_config_path / "ukf-metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                return metadata.get("project_data", {}).get("tasks", [])
        except Exception:
            pass
        return []
    
    def _load_metadata_from_vault(self) -> Dict[str, Any]:
        """ボルトからメタデータを読み込み"""
        try:
            metadata_file = self.obsidian_config_path / "ukf-metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                return metadata.get("project_data", {}).get("metadata", {})
        except Exception:
            pass
        return {}