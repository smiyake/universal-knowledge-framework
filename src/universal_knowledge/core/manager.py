"""
ナレッジ管理マネージャー - 文書同期・管理のコアクラス
Knowledge Manager - Core class for document synchronization and management
"""

import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime


class KnowledgeManager:
    """
    汎用ナレッジ管理システムの中核クラス
    Claude-Obsidian連携による文書同期・管理を行う
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """
        ナレッジマネージャーを初期化
        
        Args:
            project_path: プロジェクトパス（デフォルト: 現在のディレクトリ）
        """
        self.project_path = Path(project_path or os.getcwd())
        self.config_path = self.project_path / ".ukf"
        self.sync_config_path = self.config_path / "sync_config.json"
        
        # 設定ディレクトリ作成
        self.config_path.mkdir(exist_ok=True)
    
    def start_sync(self, obsidian_vault: Optional[str] = None) -> bool:
        """
        文書同期を開始
        
        Args:
            obsidian_vault: Obsidianボルトパス
            
        Returns:
            bool: 開始成功可否
        """
        try:
            # Obsidianボルト設定
            if not obsidian_vault:
                # 既存ボルトを検出
                available_vaults = self.detect_existing_vaults()
                
                if available_vaults:
                    # ユーザーに選択を促す
                    selected_vault_path = self.prompt_vault_selection(available_vaults)
                    
                    if selected_vault_path == "CANCEL":
                        return False
                    elif selected_vault_path:
                        # 選択されたボルトの設定をコピー
                        self.copy_obsidian_settings(selected_vault_path)
                        # プロジェクト内のdocsディレクトリをボルトとして使用
                        obsidian_vault = str(self.project_path / "docs")
                    else:
                        # 新規作成
                        obsidian_vault = str(self.project_path / "docs")
                        print("📁 新規Obsidianボルトを作成します")
                else:
                    # 既存ボルトなし - 新規作成
                    obsidian_vault = str(self.project_path / "docs")
                    print("📁 新規Obsidianボルトを作成します")
            
            # プロジェクト専用ボルトのディレクトリ作成
            vault_path = Path(obsidian_vault)
            vault_path.mkdir(parents=True, exist_ok=True)
            
            # .obsidianディレクトリが存在しない場合は作成
            obsidian_dir = vault_path / ".obsidian"
            if not obsidian_dir.exists():
                obsidian_dir.mkdir(parents=True, exist_ok=True)
                
                # 基本設定ファイルを作成
                self._create_basic_obsidian_config(obsidian_dir)
            
            # 同期設定保存
            sync_config = {
                "active": True,
                "vault_path": str(obsidian_vault),
                "project_path": str(self.project_path),
                "started_at": datetime.now().isoformat(),
                "last_sync": datetime.now().isoformat()
            }
            
            with open(self.sync_config_path, "w", encoding="utf-8") as f:
                json.dump(sync_config, f, indent=2, ensure_ascii=False)
            
            # 初回同期実行
            self._perform_sync()
            
            print(f"✅ 文書同期を開始しました")
            print(f"📁 Obsidianボルト: {obsidian_vault}")
            
            return True
            
        except Exception as e:
            raise Exception(f"同期開始に失敗しました: {e}")
    
    def stop_sync(self) -> bool:
        """
        文書同期を停止
        
        Returns:
            bool: 停止成功可否
        """
        try:
            if self.sync_config_path.exists():
                with open(self.sync_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                config["active"] = False
                config["stopped_at"] = datetime.now().isoformat()
                
                with open(self.sync_config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            raise Exception(f"同期停止に失敗しました: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        同期状態を取得
        
        Returns:
            Dict: 同期状態情報
        """
        try:
            if not self.sync_config_path.exists():
                return {"active": False, "vault_path": None, "last_sync": None}
            
            with open(self.sync_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            return config
            
        except Exception as e:
            raise Exception(f"同期状態の取得に失敗しました: {e}")
    
    def detect_existing_vaults(self) -> List[Dict[str, str]]:
        """
        既存のObsidianボルトを検出
        
        Returns:
            List[Dict]: 検出されたボルト情報のリスト
        """
        vaults = []
        
        # 一般的なObsidianボルトの場所を検索
        search_paths = [
            Path.home() / "Documents" / "Obsidian",
            Path.home() / "Documents",
            Path.home() / "Obsidian",
            Path.home() / "vaults",
            Path.home(),
        ]
        
        for base_path in search_paths:
            if not base_path.exists():
                continue
                
            # ディレクトリを再帰的に検索（深度2まで）
            for path in base_path.rglob("*"):
                if path.is_dir() and (path / ".obsidian").exists():
                    # 既に見つけたパスの親子関係をチェック
                    is_duplicate = False
                    for existing_vault in vaults:
                        existing_path = Path(existing_vault["path"])
                        if path == existing_path or path in existing_path.parents or existing_path in path.parents:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        vaults.append({
                            "name": path.name,
                            "path": str(path),
                            "config_exists": (path / ".obsidian").exists()
                        })
        
        return vaults

    def _detect_obsidian_vault(self) -> Optional[str]:
        """
        Obsidianボルトを自動検出（後方互換性のため保持）
        
        Returns:
            Optional[str]: 検出されたボルトパス
        """
        vaults = self.detect_existing_vaults()
        return vaults[0]["path"] if vaults else None
    
    def _perform_sync(self) -> bool:
        """
        実際の同期処理を実行
        
        Returns:
            bool: 同期成功可否
        """
        try:
            # TODO: Claude-Obsidian同期ロジック実装
            # - プロジェクトドキュメントをObsidianフォーマットに変換
            # - タスク情報の同期
            # - 進捗情報の更新
            
            # 現在は基本的な設定更新のみ
            if self.sync_config_path.exists():
                with open(self.sync_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                config["last_sync"] = datetime.now().isoformat()
                
                with open(self.sync_config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            raise Exception(f"同期処理に失敗しました: {e}")
    
    def create_knowledge_structure(self) -> bool:
        """
        ナレッジ構造を作成
        
        Returns:
            bool: 作成成功可否
        """
        try:
            # 基本的なナレッジ構造ディレクトリを作成
            knowledge_dirs = [
                "docs",
                "docs/planning", 
                "docs/progress",
                "docs/references",
                "docs/templates"
            ]
            
            for dir_name in knowledge_dirs:
                (self.project_path / dir_name).mkdir(parents=True, exist_ok=True)
            
            # 基本的なドキュメントファイルを作成
            self._create_basic_docs()
            
            return True
            
        except Exception as e:
            raise Exception(f"ナレッジ構造作成に失敗しました: {e}")
    
    def _create_basic_docs(self) -> None:
        """基本的なドキュメントファイルを作成"""
        docs_path = self.project_path / "docs"
        
        # プロジェクト概要
        project_overview = """# プロジェクト概要

## 目的

## 技術スタック

## 開発フェーズ

## メンバー

## 関連リンク
"""
        
        # 進捗管理
        progress_doc = """# 進捗管理

## 現在のタスク

## 完了したタスク

## 今後の予定

## 課題・問題点
"""
        
        # 計画書
        planning_doc = """# 計画書

## 要件定義

## アーキテクチャ設計

## 開発計画

## リスク管理
"""
        
        with open(docs_path / "プロジェクト概要.md", "w", encoding="utf-8") as f:
            f.write(project_overview)
        
        with open(docs_path / "progress" / "進捗管理.md", "w", encoding="utf-8") as f:
            f.write(progress_doc)
        
        with open(docs_path / "planning" / "計画書.md", "w", encoding="utf-8") as f:
            f.write(planning_doc)
    
    def _create_basic_obsidian_config(self, obsidian_dir: Path) -> None:
        """
        基本的なObsidian設定ファイルを作成
        
        Args:
            obsidian_dir: .obsidianディレクトリのパス
        """
        try:
            # 基本的なapp.json設定
            app_config = {
                "legacyEditor": False,
                "livePreview": True,
                "defaultViewMode": "source",
                "theme": "obsidian",
                "translucency": False
            }
            
            with open(obsidian_dir / "app.json", "w", encoding="utf-8") as f:
                json.dump(app_config, f, indent=2, ensure_ascii=False)
            
            # 基本的なworkspace.json設定
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
                                    "file": "プロジェクト概要.md",
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
                                "state": {
                                    "file": "プロジェクト概要.md"
                                }
                            }
                        }
                    ],
                    "collapsed": False
                },
                "active": "editor",
                "lastOpenFiles": ["プロジェクト概要.md"]
            }
            
            with open(obsidian_dir / "workspace.json", "w", encoding="utf-8") as f:
                json.dump(workspace_config, f, indent=2, ensure_ascii=False)
            
            # プロジェクト固有設定
            project_config = {
                "projectName": self.project_path.name,
                "createdAt": datetime.now().isoformat(),
                "framework": "universal-knowledge-framework",
                "configSource": "new"
            }
            
            with open(obsidian_dir / "project-config.json", "w", encoding="utf-8") as f:
                json.dump(project_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Obsidian基本設定作成に失敗しました: {e}")
    
    def copy_obsidian_settings(self, source_vault_path: str, target_path: Optional[str] = None) -> bool:
        """
        既存Obsidianボルトの設定をプロジェクト用にコピー
        
        Args:
            source_vault_path: コピー元のボルトパス
            target_path: コピー先パス（デフォルト: プロジェクト/docs）
            
        Returns:
            bool: コピー成功可否
        """
        try:
            source_obsidian = Path(source_vault_path) / ".obsidian"
            if not source_obsidian.exists():
                raise ValueError(f"Obsidian設定が見つかりません: {source_obsidian}")
            
            # ターゲットパス決定
            if target_path is None:
                target_path = self.project_path / "docs"
            else:
                target_path = Path(target_path)
            
            target_obsidian = target_path / ".obsidian"
            
            # ターゲットディレクトリ作成
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 既存設定がある場合はバックアップ
            if target_obsidian.exists():
                backup_path = target_path / f".obsidian.backup.{int(time.time())}"
                shutil.move(str(target_obsidian), str(backup_path))
                print(f"既存設定をバックアップしました: {backup_path}")
            
            # 設定ディレクトリをコピー
            shutil.copytree(str(source_obsidian), str(target_obsidian))
            
            # プロジェクト固有の調整
            self._adjust_workspace_for_project(target_obsidian)
            
            print(f"✅ Obsidian設定をコピーしました")
            print(f"📁 プロジェクト専用ボルト: {target_path}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Obsidian設定コピーに失敗しました: {e}")
    
    def _adjust_workspace_for_project(self, obsidian_config_path: Path) -> None:
        """
        プロジェクト固有のワークスペース調整
        
        Args:
            obsidian_config_path: .obsidianディレクトリのパス
        """
        try:
            workspace_file = obsidian_config_path / "workspace.json"
            
            if workspace_file.exists():
                with open(workspace_file, "r", encoding="utf-8") as f:
                    workspace = json.load(f)
                
                # プロジェクト用のワークスペース設定に調整
                # サイドバーを整理してプロジェクト構造に最適化
                if "leftRibbon" in workspace:
                    workspace["leftRibbon"]["collapsed"] = False
                
                if "rightRibbon" in workspace:
                    workspace["rightRibbon"]["collapsed"] = False
                
                # ファイルエクスプローラーをデフォルト表示
                if "left" in workspace:
                    workspace["left"]["collapsed"] = False
                
                with open(workspace_file, "w", encoding="utf-8") as f:
                    json.dump(workspace, f, indent=2, ensure_ascii=False)
            
            # プロジェクト固有の設定ファイル作成
            project_config = {
                "projectName": self.project_path.name,
                "createdAt": datetime.now().isoformat(),
                "framework": "universal-knowledge-framework"
            }
            
            project_config_file = obsidian_config_path / "project-config.json"
            with open(project_config_file, "w", encoding="utf-8") as f:
                json.dump(project_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # 調整に失敗しても致命的ではないので警告のみ
            print(f"⚠️ ワークスペース調整に失敗しました: {e}")
    
    def prompt_vault_selection(self, available_vaults: List[Dict[str, str]]) -> Optional[str]:
        """
        ユーザーにボルト選択を促す
        
        Args:
            available_vaults: 利用可能なボルトのリスト
            
        Returns:
            Optional[str]: 選択されたボルトパス
        """
        if not available_vaults:
            return None
        
        print("\n📂 既存のObsidianボルトが見つかりました:")
        for i, vault in enumerate(available_vaults, 1):
            print(f"  {i}. {vault['name']} ({vault['path']})")
        
        print(f"  {len(available_vaults) + 1}. 新規作成（設定コピーなし）")
        print(f"  {len(available_vaults) + 2}. キャンセル")
        
        while True:
            try:
                choice = input(f"\n選択してください (1-{len(available_vaults) + 2}): ").strip()
                
                if not choice:
                    continue
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(available_vaults):
                    selected_vault = available_vaults[choice_num - 1]
                    
                    # コピー確認
                    confirm = input(f"\n'{selected_vault['name']}' の設定をプロジェクトにコピーしますか？ (Y/n): ").strip().lower()
                    if confirm in ['', 'y', 'yes']:
                        return selected_vault["path"]
                    else:
                        continue
                        
                elif choice_num == len(available_vaults) + 1:
                    # 新規作成
                    return None
                    
                elif choice_num == len(available_vaults) + 2:
                    # キャンセル
                    print("同期設定をキャンセルしました")
                    return "CANCEL"
                    
                else:
                    print("無効な選択です")
                    
            except (ValueError, KeyboardInterrupt):
                print("\n同期設定をキャンセルしました")
                return "CANCEL"