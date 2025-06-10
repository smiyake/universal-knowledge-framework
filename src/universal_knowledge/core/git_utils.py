"""
Git操作のユーティリティモジュール
Git Utilities Module - Improved error handling and user guidance
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict


class GitManager:
    """Gitリポジトリ管理とエラーハンドリングを改善したクラス"""
    
    def __init__(self):
        """GitManagerを初期化"""
        self.git_config = self._check_git_installation()
    
    def _check_git_installation(self) -> bool:
        """Gitのインストール状況を確認"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_git_config(self) -> Tuple[bool, Dict[str, str]]:
        """
        Git設定の確認
        
        Returns:
            Tuple[bool, Dict]: (設定完了状況, 設定情報)
        """
        if not self.git_config:
            return False, {"error": "Gitがインストールされていません"}
        
        try:
            # グローバル設定確認
            name_result = subprocess.run(['git', 'config', '--global', 'user.name'], 
                                       capture_output=True, text=True, timeout=5)
            email_result = subprocess.run(['git', 'config', '--global', 'user.email'], 
                                        capture_output=True, text=True, timeout=5)
            
            name = name_result.stdout.strip()
            email = email_result.stdout.strip()
            
            config_info = {
                "name": name,
                "email": email,
                "name_set": bool(name),
                "email_set": bool(email)
            }
            
            # 両方設定されているかチェック
            is_configured = bool(name and email)
            
            return is_configured, config_info
            
        except subprocess.TimeoutExpired:
            return False, {"error": "Git設定確認がタイムアウトしました"}
        except Exception as e:
            return False, {"error": f"Git設定確認エラー: {e}"}
    
    def setup_git_config_interactive(self) -> bool:
        """
        インタラクティブなGit設定
        
        Returns:
            bool: 設定成功
        """
        print("\n🔧 Git設定が不完全です。設定を行います。")
        print("📝 この設定は今後のコミットで使用されます。")
        
        try:
            # ユーザー名入力
            current_name = self._get_current_git_config('user.name')
            name_prompt = f"Git user.name ({current_name}): " if current_name else "Git user.name: "
            user_name = input(name_prompt).strip()
            
            if not user_name and current_name:
                user_name = current_name
            elif not user_name:
                user_name = input("ユーザー名を入力してください: ").strip()
                if not user_name:
                    print("❌ ユーザー名が必要です")
                    return False
            
            # メールアドレス入力
            current_email = self._get_current_git_config('user.email')
            email_prompt = f"Git user.email ({current_email}): " if current_email else "Git user.email: "
            user_email = input(email_prompt).strip()
            
            if not user_email and current_email:
                user_email = current_email
            elif not user_email:
                user_email = input("メールアドレスを入力してください: ").strip()
                if not user_email:
                    print("❌ メールアドレスが必要です")
                    return False
            
            # 設定適用
            subprocess.run(['git', 'config', '--global', 'user.name', user_name], 
                         check=True, timeout=10)
            subprocess.run(['git', 'config', '--global', 'user.email', user_email], 
                         check=True, timeout=10)
            
            print(f"✅ Git設定完了")
            print(f"   ユーザー名: {user_name}")
            print(f"   メール: {user_email}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git設定エラー: {e}")
            return False
        except KeyboardInterrupt:
            print("\n❌ 設定がキャンセルされました")
            return False
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            return False
    
    def _get_current_git_config(self, key: str) -> Optional[str]:
        """現在のGit設定値を取得"""
        try:
            result = subprocess.run(['git', 'config', '--global', key], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def initialize_repository(self, project_path: Path, initial_commit_message: str = "Initial commit 🚀") -> bool:
        """
        安全なGitリポジトリ初期化
        
        Args:
            project_path: プロジェクトパス
            initial_commit_message: 初期コミットメッセージ
            
        Returns:
            bool: 初期化成功
        """
        if not self.git_config:
            print("⚠️ Gitが利用できません。手動でGitリポジトリを初期化してください。")
            return False
        
        # Git設定確認
        is_configured, config_info = self.check_git_config()
        
        if not is_configured:
            print(f"\n⚠️ Git設定に問題があります:")
            if "error" in config_info:
                print(f"   エラー: {config_info['error']}")
                return False
            
            if not config_info.get("name_set"):
                print("   - user.name が設定されていません")
            if not config_info.get("email_set"):
                print("   - user.email が設定されていません")
            
            # 自動設定を提案
            setup_now = input("\n今すぐGit設定を行いますか？ (Y/n): ").strip().lower()
            if setup_now in ['', 'y', 'yes']:
                if not self.setup_git_config_interactive():
                    print("❌ Git設定に失敗しました。手動で設定してください:")
                    print("   git config --global user.name \"Your Name\"")
                    print("   git config --global user.email \"your.email@example.com\"")
                    return False
            else:
                print("ℹ️ Git初期化をスキップします。")
                print("💡 後で手動でGitリポジトリを初期化できます:")
                print(f"   cd {project_path}")
                print("   git init")
                print("   git add .")
                print(f"   git commit -m \"{initial_commit_message}\"")
                return False
        
        # Git初期化実行
        try:
            original_cwd = Path.cwd()
            
            # プロジェクトディレクトリに移動
            import os
            os.chdir(project_path)
            
            # Git初期化
            subprocess.run(['git', 'init'], check=True, timeout=10)
            
            # デフォルトブランチ名設定
            try:
                subprocess.run(['git', 'config', 'init.defaultBranch', 'main'], 
                             check=True, timeout=5)
                subprocess.run(['git', 'branch', '-m', 'main'], 
                             check=True, timeout=5)
            except subprocess.CalledProcessError:
                # デフォルトブランチ設定に失敗しても続行
                pass
            
            # ファイル追加
            subprocess.run(['git', 'add', '.'], check=True, timeout=30)
            
            # 初期コミット
            subprocess.run(['git', 'commit', '-m', initial_commit_message], 
                         check=True, timeout=30)
            
            print("✅ Gitリポジトリを初期化しました")
            
            # 元のディレクトリに戻る
            os.chdir(original_cwd)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git初期化でエラーが発生しましたが、プロジェクト作成は完了しました")
            print(f"   エラー詳細: {e}")
            print(f"💡 手動でGit初期化を行ってください:")
            print(f"   cd {project_path}")
            print("   git init")
            print("   git add .")
            print(f"   git commit -m \"{initial_commit_message}\"")
            
            # 元のディレクトリに戻る
            try:
                import os
                os.chdir(original_cwd)
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"❌ 予期しないエラーが発生しました: {e}")
            return False
    
    def print_git_help(self) -> None:
        """Git設定のヘルプ情報を表示"""
        print("\n📚 Git設定について")
        print("="*50)
        print("Gitの基本設定は以下のコマンドで行えます:")
        print()
        print("# グローバル設定（推奨）")
        print("git config --global user.name \"Your Name\"")
        print("git config --global user.email \"your.email@example.com\"")
        print()
        print("# 現在の設定確認")
        print("git config --list")
        print()
        print("詳細: https://git-scm.com/book/ja/v2/使い始める-最初のGitの構成")