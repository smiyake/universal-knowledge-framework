#!/usr/bin/env python3
"""
汎用ナレッジ管理フレームワーク CLI
Universal Knowledge Framework Command Line Interface
"""

import click
import os
import sys
from pathlib import Path
from typing import Optional

from .core.manager import KnowledgeManager
from .core.project import ProjectManager
from .core.task import TaskManager


@click.group()
@click.version_option(version="1.0.0")
def main():
    """汎用ナレッジ管理フレームワーク - あらゆるプロジェクトで利用可能な文書管理システム"""
    pass


@main.command()
@click.option("--name", "-n", required=True, help="プロジェクト名")
@click.option("--type", "-t", default="basic", 
              type=click.Choice(['basic', 'web-development', 'data-science', 'business', 'research', 'personal']),
              help="プロジェクトタイプ")
@click.option("--path", "-p", default=None, help="作成パス (デフォルト: 現在のディレクトリ)")
@click.option("--skip-git", is_flag=True, help="Git初期化をスキップ")
def create_project(name: str, type: str, path: Optional[str], skip_git: bool):
    """新しいプロジェクトを作成します"""
    try:
        click.echo(f"🚀 プロジェクト '{name}' を作成しています...")
        click.echo(f"📁 タイプ: {type}")
        
        project_manager = ProjectManager()
        project_path = project_manager.create_project(name, type, path)
        
        click.echo(f"\n✅ プロジェクト '{name}' を作成しました")
        click.echo(f"📍 場所: {project_path}")
        click.echo(f"📁 タイプ: {type}")
        click.echo("")
        click.echo("🎯 次のステップ:")
        click.echo(f"   cd {project_path}")
        click.echo("   ukf sync start")
        click.echo("")
        click.echo("📚 詳細な使用方法: ukf --help")
        
    except PermissionError:
        click.echo("❌ プロジェクト作成に失敗しました", err=True)
        click.echo("", err=True)
        click.echo("🔍 原因: 書き込み権限がありません", err=True)
        click.echo("💡 解決策:", err=True)
        click.echo("  1. 書き込み権限のあるディレクトリを選択してください", err=True)
        click.echo("  2. 管理者権限で実行してください", err=True)
        click.echo("  3. パス指定オプション -p を使用してください", err=True)
        click.echo("", err=True)
        click.echo("🔧 例: ukf create-project -n myproject -p ~/Documents", err=True)
        sys.exit(1)
        
    except FileNotFoundError as e:
        click.echo("❌ プロジェクト作成に失敗しました", err=True)
        click.echo("", err=True)
        click.echo("🔍 原因: 指定されたパスが存在しません", err=True)
        click.echo("💡 解決策:", err=True)
        click.echo("  1. 親ディレクトリが存在することを確認してください", err=True)
        click.echo("  2. 正しいパスを指定してください", err=True)
        click.echo("", err=True)
        click.echo(f"🔧 エラー詳細: {e}", err=True)
        sys.exit(1)
        
    except Exception as e:
        click.echo("❌ プロジェクト作成に失敗しました", err=True)
        click.echo("", err=True)
        click.echo(f"🔍 原因: {e}", err=True)
        click.echo("💡 解決策:", err=True)
        click.echo("  1. 再度実行してみてください", err=True)
        click.echo("  2. パス名に特殊文字が含まれていないか確認してください", err=True)
        click.echo("  3. ディスク容量を確認してください", err=True)
        click.echo("", err=True)
        click.echo("📚 詳細なヘルプ: ukf create-project --help", err=True)
        click.echo("🐛 問題が解決しない場合: https://github.com/smiyake/universal-knowledge-framework/issues", err=True)
        sys.exit(1)


@main.group()
def sync():
    """文書同期管理"""
    pass


@sync.command()
@click.option("--obsidian-vault", "-v", help="Obsidianボルトパス")
def start(obsidian_vault: Optional[str]):
    """文書同期を開始します"""
    try:
        knowledge_manager = KnowledgeManager()
        knowledge_manager.start_sync(obsidian_vault)
        click.echo("✅ 文書同期を開始しました")
    except Exception as e:
        click.echo(f"❌ 同期開始エラー: {e}", err=True)
        sys.exit(1)


@sync.command()
def stop():
    """文書同期を停止します"""
    try:
        knowledge_manager = KnowledgeManager()
        knowledge_manager.stop_sync()
        click.echo("✅ 文書同期を停止しました")
    except Exception as e:
        click.echo(f"❌ 同期停止エラー: {e}", err=True)
        sys.exit(1)


@sync.command()
def status():
    """同期状態を確認します"""
    try:
        knowledge_manager = KnowledgeManager()
        status = knowledge_manager.get_sync_status()
        if status["active"]:
            click.echo("🟢 文書同期: アクティブ")
            click.echo(f"   Obsidianボルト: {status['vault_path']}")
            click.echo(f"   最終同期: {status['last_sync']}")
        else:
            click.echo("🔴 文書同期: 停止中")
    except Exception as e:
        click.echo(f"❌ 状態確認エラー: {e}", err=True)
        sys.exit(1)


@main.group()
def task():
    """タスク管理"""
    pass


@task.command()
@click.argument("content")
@click.option("--priority", "-p", default="medium",
              type=click.Choice(['high', 'medium', 'low']),
              help="優先度")
def add(content: str, priority: str):
    """新しいタスクを追加します"""
    try:
        task_manager = TaskManager()
        task_id = task_manager.add_task(content, priority)
        click.echo(f"✅ タスクを追加しました (ID: {task_id})")
    except Exception as e:
        click.echo(f"❌ タスク追加エラー: {e}", err=True)
        sys.exit(1)


@task.command()
@click.option("--status", "-s", 
              type=click.Choice(['pending', 'in_progress', 'completed']),
              help="状態フィルタ")
def list(status: Optional[str]):
    """タスク一覧を表示します"""
    try:
        task_manager = TaskManager()
        tasks = task_manager.list_tasks(status)
        
        if not tasks:
            click.echo("📝 タスクがありません")
            return
            
        for task in tasks:
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄', 
                'completed': '✅'
            }
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }
            click.echo(f"{status_emoji[task['status']]} {priority_emoji[task['priority']]} [{task['id']}] {task['content']}")
            
    except Exception as e:
        click.echo(f"❌ タスク一覧エラー: {e}", err=True)
        sys.exit(1)


@task.command()
@click.argument("task_id")
def complete(task_id: str):
    """タスクを完了にします"""
    try:
        task_manager = TaskManager()
        task_manager.complete_task(task_id)
        click.echo(f"✅ タスク {task_id} を完了しました")
    except Exception as e:
        click.echo(f"❌ タスク完了エラー: {e}", err=True)
        sys.exit(1)


@main.command()
def version():
    """バージョン情報を表示します"""
    click.echo("汎用ナレッジ管理フレームワーク v1.0.0")
    click.echo("Universal Knowledge Framework")


if __name__ == "__main__":
    main()