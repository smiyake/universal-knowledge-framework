"""
ナレッジ管理マネージャー - 文書同期・管理のコアクラス
Knowledge Manager - Core class for document synchronization and management
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
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
            # Obsidianボルト自動検出
            if not obsidian_vault:
                obsidian_vault = self._detect_obsidian_vault()
            
            if not obsidian_vault:
                raise ValueError("Obsidianボルトが見つかりません。パスを指定してください。")
            
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
    
    def _detect_obsidian_vault(self) -> Optional[str]:
        """
        Obsidianボルトを自動検出
        
        Returns:
            Optional[str]: 検出されたボルトパス
        """
        # 一般的なObsidianボルトの場所を検索
        common_paths = [
            Path.home() / "Documents" / "Obsidian",
            Path.home() / "Obsidian",
            self.project_path / "docs",
            self.project_path / "knowledge",
            self.project_path / ".obsidian"
        ]
        
        for path in common_paths:
            if path.exists() and (path / ".obsidian").exists():
                return str(path)
        
        return None
    
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