"""
UKF更新システム - 自動更新・アップグレード機能
UKF Update System - Automatic update and upgrade functionality
"""

import os
import subprocess
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tempfile
import logging

from .git_utils import GitManager


class UKFUpdater:
    """UKF自動更新システム"""
    
    def __init__(self, ukf_path: Optional[Path] = None):
        """
        UKF更新システムを初期化
        
        Args:
            ukf_path: UKFプロジェクトパス（自動検出も可能）
        """
        self.ukf_path = self._detect_ukf_path(ukf_path)
        self.git_manager = GitManager()
        self.logger = logging.getLogger(__name__)
        
        # 更新設定
        self.backup_dir = self.ukf_path / ".backup"
        self.backup_dir.mkdir(exist_ok=True)
        
        # リポジトリ情報
        self.repository_url = "https://github.com/smiyake/universal-knowledge-framework.git"
        self.branch = "main"
    
    def _detect_ukf_path(self, provided_path: Optional[Path]) -> Path:
        """UKFプロジェクトパスを検出"""
        if provided_path and provided_path.exists():
            return provided_path
        
        # 環境変数から検出
        if "UKF_PATH" in os.environ:
            ukf_env_path = Path(os.environ["UKF_PATH"])
            if ukf_env_path.exists():
                return ukf_env_path
        
        # pip show で検出を試行
        try:
            result = subprocess.run(
                ['pip', 'show', '-f', 'universal-knowledge-framework'], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Location:'):
                        location = line.split(':', 1)[1].strip()
                        ukf_path = Path(location) / 'universal_knowledge'
                        if ukf_path.exists():
                            return ukf_path.parent
        except:
            pass
        
        # 現在のディレクトリから上方向に検索
        current = Path.cwd()
        while current != current.parent:
            if (current / "src" / "universal_knowledge").exists():
                return current
            current = current.parent
        
        # デフォルトパス
        default_path = Path.home() / "universal-knowledge-framework"
        if default_path.exists():
            return default_path
        
        raise FileNotFoundError("UKFプロジェクトパスが見つかりません。--path で指定するか、UKF_PATH環境変数を設定してください。")
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        利用可能な更新をチェック
        
        Returns:
            Dict: 更新情報
        """
        try:
            current_version = self._get_current_version()
            remote_version = self._get_remote_version()
            
            updates_available = current_version != remote_version
            
            return {
                "updates_available": updates_available,
                "current_version": current_version,
                "remote_version": remote_version,
                "current_commit": self._get_current_commit(),
                "remote_commit": self._get_remote_commit(),
                "check_time": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"更新チェックエラー: {e}")
            return {
                "updates_available": None,
                "error": str(e),
                "check_time": datetime.now().isoformat()
            }
    
    def update(self, target_version: Optional[str] = None, 
               force: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """
        UKFを更新
        
        Args:
            target_version: 対象バージョン（Noneで最新版）
            force: 強制更新
            dry_run: 実際には更新せず、手順のみ表示
            
        Returns:
            Dict: 更新結果
        """
        update_info = {
            "success": False,
            "start_time": datetime.now().isoformat(),
            "target_version": target_version or "latest",
            "dry_run": dry_run,
            "steps": [],
            "backup_created": False,
            "error": None
        }
        
        try:
            # 1. 事前チェック
            self._add_step(update_info, "事前チェック開始")
            if not self._pre_update_checks(force):
                raise Exception("事前チェックに失敗しました")
            
            # 2. バックアップ作成
            self._add_step(update_info, "バックアップ作成")
            if not dry_run:
                backup_path = self._create_backup()
                update_info["backup_path"] = str(backup_path)
                update_info["backup_created"] = True
            else:
                self._add_step(update_info, "[DRY RUN] バックアップ作成をスキップ")
            
            # 3. リモート更新を取得
            self._add_step(update_info, "リモート更新取得")
            if not dry_run:
                self._fetch_remote_updates()
            else:
                self._add_step(update_info, "[DRY RUN] git fetch をスキップ")
            
            # 4. 更新適用
            self._add_step(update_info, "更新適用")
            if not dry_run:
                self._apply_updates(target_version)
            else:
                self._add_step(update_info, "[DRY RUN] git pull をスキップ")
            
            # 5. 依存関係更新
            self._add_step(update_info, "依存関係更新")
            if not dry_run:
                self._update_dependencies()
            else:
                self._add_step(update_info, "[DRY RUN] pip install をスキップ")
            
            # 6. 更新後チェック
            self._add_step(update_info, "更新後チェック")
            if not dry_run:
                self._post_update_checks()
            else:
                self._add_step(update_info, "[DRY RUN] 更新後チェックをスキップ")
            
            update_info["success"] = True
            update_info["end_time"] = datetime.now().isoformat()
            
            if not dry_run:
                self._add_step(update_info, "✅ 更新完了")
            else:
                self._add_step(update_info, "✅ DRY RUN完了")
            
        except Exception as e:
            update_info["error"] = str(e)
            update_info["end_time"] = datetime.now().isoformat()
            self._add_step(update_info, f"❌ 更新エラー: {e}")
            
            # エラー時はバックアップから復元を提案
            if update_info["backup_created"] and not dry_run:
                self._add_step(update_info, f"💡 復元方法: ukf update rollback --backup {update_info['backup_path']}")
        
        return update_info
    
    def rollback(self, backup_path: str) -> Dict[str, Any]:
        """
        バックアップから復元
        
        Args:
            backup_path: バックアップディレクトリパス
            
        Returns:
            Dict: 復元結果
        """
        rollback_info = {
            "success": False,
            "start_time": datetime.now().isoformat(),
            "backup_path": backup_path,
            "steps": []
        }
        
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                raise FileNotFoundError(f"バックアップが見つかりません: {backup_path}")
            
            self._add_step(rollback_info, "バックアップからの復元開始")
            
            # 現在の状態をバックアップ
            current_backup = self._create_backup()
            rollback_info["current_backup"] = str(current_backup)
            
            # バックアップから復元
            self._restore_from_backup(backup_dir)
            
            # 依存関係を再インストール
            self._update_dependencies()
            
            rollback_info["success"] = True
            rollback_info["end_time"] = datetime.now().isoformat()
            self._add_step(rollback_info, "✅ 復元完了")
            
        except Exception as e:
            rollback_info["error"] = str(e)
            rollback_info["end_time"] = datetime.now().isoformat()
            self._add_step(rollback_info, f"❌ 復元エラー: {e}")
        
        return rollback_info
    
    def _get_current_version(self) -> str:
        """現在のバージョンを取得"""
        try:
            # __init__.py からバージョン取得
            init_file = self.ukf_path / "src" / "universal_knowledge" / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('__version__'):
                            return line.split('=')[1].strip().strip('"\'')
            
            # Git コミットハッシュをバージョンとして使用
            return self._get_current_commit()[:8]
        except:
            return "unknown"
    
    def _get_remote_version(self) -> str:
        """リモートの最新バージョンを取得"""
        try:
            # リモートの __init__.py をチェック
            result = subprocess.run([
                'git', 'show', f'origin/{self.branch}:src/universal_knowledge/__init__.py'
            ], capture_output=True, text=True, cwd=self.ukf_path, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('__version__'):
                        return line.split('=')[1].strip().strip('"\'')
            
            # リモートのコミットハッシュを使用
            return self._get_remote_commit()[:8]
        except:
            return "unknown"
    
    def _get_current_commit(self) -> str:
        """現在のコミットハッシュを取得"""
        try:
            result = subprocess.run([
                'git', 'rev-parse', 'HEAD'
            ], capture_output=True, text=True, cwd=self.ukf_path, timeout=5)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _get_remote_commit(self) -> str:
        """リモートの最新コミットハッシュを取得"""
        try:
            result = subprocess.run([
                'git', 'rev-parse', f'origin/{self.branch}'
            ], capture_output=True, text=True, cwd=self.ukf_path, timeout=5)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _pre_update_checks(self, force: bool) -> bool:
        """更新前チェック"""
        # Git設定確認
        is_configured, config_info = self.git_manager.check_git_config()
        if not is_configured and not force:
            raise Exception("Git設定が不完全です。--force を使用するか、Git設定を完了してください。")
        
        # 作業ディレクトリの状態確認
        try:
            result = subprocess.run([
                'git', 'status', '--porcelain'
            ], capture_output=True, text=True, cwd=self.ukf_path, timeout=10)
            
            if result.stdout.strip() and not force:
                raise Exception("未コミットの変更があります。コミットするか --force を使用してください。")
        except subprocess.TimeoutExpired:
            if not force:
                raise Exception("Git状態確認がタイムアウトしました。")
        
        return True
    
    def _create_backup(self) -> Path:
        """バックアップを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        # 重要なディレクトリとファイルをバックアップ
        important_paths = [
            "src",
            "pyproject.toml",
            "requirements.txt",
            "README.md"
        ]
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for path_name in important_paths:
            source_path = self.ukf_path / path_name
            if source_path.exists():
                dest_path = backup_path / path_name
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
        
        # バックアップ情報ファイル作成
        backup_info = {
            "created_at": datetime.now().isoformat(),
            "ukf_path": str(self.ukf_path),
            "commit": self._get_current_commit(),
            "version": self._get_current_version()
        }
        
        with open(backup_path / "backup_info.json", 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        return backup_path
    
    def _fetch_remote_updates(self) -> None:
        """リモート更新を取得"""
        subprocess.run([
            'git', 'fetch', 'origin'
        ], check=True, cwd=self.ukf_path, timeout=30)
    
    def _apply_updates(self, target_version: Optional[str]) -> None:
        """更新を適用"""
        if target_version:
            # 特定バージョンにチェックアウト
            subprocess.run([
                'git', 'checkout', target_version
            ], check=True, cwd=self.ukf_path, timeout=30)
        else:
            # 最新版に更新
            subprocess.run([
                'git', 'pull', 'origin', self.branch
            ], check=True, cwd=self.ukf_path, timeout=30)
    
    def _update_dependencies(self) -> None:
        """依存関係を更新"""
        # requirements.txt が存在する場合
        req_file = self.ukf_path / "requirements.txt"
        if req_file.exists():
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(req_file)
            ], check=True, timeout=300)
        
        # パッケージを再インストール
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-e', str(self.ukf_path)
        ], check=True, timeout=300)
    
    def _post_update_checks(self) -> None:
        """更新後チェック"""
        # UKFコマンドが動作するかチェック
        try:
            result = subprocess.run([
                'ukf', 'version'
            ], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception("更新後のUKFコマンドが正常に動作しません")
        except FileNotFoundError:
            raise Exception("UKFコマンドが見つかりません。インストールを確認してください。")
    
    def _restore_from_backup(self, backup_path: Path) -> None:
        """バックアップから復元"""
        # バックアップ情報確認
        backup_info_file = backup_path / "backup_info.json"
        if backup_info_file.exists():
            with open(backup_info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            self.logger.info(f"バックアップ情報: {backup_info}")
        
        # ファイルを復元
        important_paths = ["src", "pyproject.toml", "requirements.txt"]
        
        for path_name in important_paths:
            backup_item = backup_path / path_name
            target_item = self.ukf_path / path_name
            
            if backup_item.exists():
                if target_item.exists():
                    if target_item.is_dir():
                        shutil.rmtree(target_item)
                    else:
                        target_item.unlink()
                
                if backup_item.is_dir():
                    shutil.copytree(backup_item, target_item)
                else:
                    shutil.copy2(backup_item, target_item)
    
    def _add_step(self, info: Dict[str, Any], message: str) -> None:
        """ステップ情報を追加"""
        step = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        info["steps"].append(step)
        self.logger.info(message)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """利用可能なバックアップ一覧を取得"""
        backups = []
        
        for backup_dir in self.backup_dir.glob("backup_*"):
            if backup_dir.is_dir():
                backup_info_file = backup_dir / "backup_info.json"
                
                backup_data = {
                    "path": str(backup_dir),
                    "name": backup_dir.name,
                    "created_at": "unknown",
                    "version": "unknown",
                    "commit": "unknown"
                }
                
                if backup_info_file.exists():
                    try:
                        with open(backup_info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                        backup_data.update(info)
                    except:
                        pass
                
                backups.append(backup_data)
        
        # 作成日時でソート（新しい順）
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """古いバックアップを削除"""
        backups = self.list_backups()
        deleted_count = 0
        
        for backup in backups[keep_count:]:
            try:
                backup_path = Path(backup["path"])
                shutil.rmtree(backup_path)
                deleted_count += 1
                self.logger.info(f"古いバックアップを削除: {backup_path}")
            except Exception as e:
                self.logger.error(f"バックアップ削除エラー: {e}")
        
        return deleted_count