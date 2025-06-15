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
from .core.analytics import ProjectAnalytics
from .core.bridge import BridgeManager, StandardDataFormat
from .core.obsidian_adapter import ObsidianAdapter
from .core.updater import UKFUpdater
from .ai_commands import create_ai_cli_group
from .templates import DynamicTemplateEngine, TemplateManager
from .utils import process_logs, DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR


@click.group()
@click.version_option(version="1.1.0")
def main():
    """汎用ナレッジ管理フレームワーク - あらゆるプロジェクトで利用可能な文書管理システム"""
    pass


# AI機能を統合
main.add_command(create_ai_cli_group())


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
def claude():
    """Claude Code連携機能"""
    pass


@claude.command()
@click.option("--tasks-json", "-t", help="タスクJSONデータ (TodoRead出力)")
@click.option("--vault-path", "-v", help="ナレッジベースパス")
@click.option("--auto-commit", is_flag=True, default=True, help="Git自動コミット")
def sync(tasks_json: Optional[str], vault_path: Optional[str], auto_commit: bool):
    """Claude Codeのタスクを同期します"""
    try:
        from .ai.claude_code_sync import ClaudeCodeSync
        
        sync_manager = ClaudeCodeSync(
            vault_path=Path(vault_path) if vault_path else None,
            auto_commit=auto_commit
        )
        
        if tasks_json:
            # タスクJSONが提供された場合
            import json
            tasks = json.loads(tasks_json)
            sync_manager.sync_from_claude(tasks)
            click.echo(f"✅ Claude → Knowledge Base: {len(tasks)}タスクを同期しました")
        else:
            # キャッシュから同期
            cache_data = sync_manager._load_cache()
            tasks = cache_data.get("tasks", [])
            if tasks:
                sync_manager.sync_from_claude(tasks)
                click.echo(f"✅ キャッシュから{len(tasks)}タスクを同期しました")
            else:
                click.echo("⚠️ 同期するタスクがありません")
                click.echo("💡 使用方法: ukf claude sync --tasks-json '<TodoRead出力>'")
                
    except Exception as e:
        click.echo(f"❌ 同期エラー: {e}", err=True)
        sys.exit(1)


@claude.command()
def init():
    """Claude Code連携を初期化します"""
    try:
        from .ai.claude_code_sync import ClaudeCodeSync
        
        sync_manager = ClaudeCodeSync()
        
        # ナレッジベースディレクトリ作成
        sync_manager.vault_path.mkdir(parents=True, exist_ok=True)
        
        # 初期タスクファイル作成
        task_file = sync_manager.vault_path / sync_manager.task_file_name
        if not task_file.exists():
            initial_content = """# タスク管理

Claude Code連携により自動管理されるタスクファイルです。

## 使用方法

1. Claude Codeでタスクを作成・更新
2. `ukf claude sync`コマンドで同期
3. このファイルに反映される

---
*Universal Knowledge Framework - Claude Code Integration*
"""
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(initial_content)
        
        click.echo("✅ Claude Code連携を初期化しました")
        click.echo(f"📁 ナレッジベース: {sync_manager.vault_path}")
        click.echo(f"📝 タスクファイル: {task_file}")
        click.echo("\n🎯 次のステップ:")
        click.echo("1. Claude Codeでタスクを作成")
        click.echo("2. TodoReadでタスクを取得")
        click.echo("3. ukf claude sync --tasks-json '<タスクJSON>' で同期")
        
    except Exception as e:
        click.echo(f"❌ 初期化エラー: {e}", err=True)
        sys.exit(1)


@claude.command()
def status():
    """Claude Code同期状態を確認します"""
    try:
        from .ai.claude_code_sync import ClaudeCodeSync
        
        sync_manager = ClaudeCodeSync()
        status = sync_manager.get_sync_status()
        
        click.echo("🔍 Claude Code同期状態:")
        click.echo(f"📁 ナレッジベース: {status['vault_path']}")
        click.echo(f"📝 キャッシュファイル: {status['cache_file']}")
        click.echo(f"🕒 最終同期: {status['last_sync']}")
        click.echo(f"📊 タスク数: {status['total_tasks']}")
        click.echo(f"🔄 自動コミット: {'有効' if status['auto_commit'] else '無効'}")
        
        # キャッシュ確認
        if Path(status['cache_file']).exists():
            click.echo("\n✅ キャッシュファイルが存在します")
        else:
            click.echo("\n⚠️ キャッシュファイルが存在しません")
            click.echo("💡 Claude Codeでタスクを同期してください")
        
    except Exception as e:
        click.echo(f"❌ 状態確認エラー: {e}", err=True)
        sys.exit(1)


@claude.command()
@click.option("--vault-path", "-v", help="ナレッジベースパス")
def export(vault_path: Optional[str]):
    """ナレッジベースのタスクをClaude Code形式でエクスポート"""
    try:
        from .ai.claude_code_sync import ClaudeCodeSync
        import json
        
        sync_manager = ClaudeCodeSync(
            vault_path=Path(vault_path) if vault_path else None
        )
        
        tasks = sync_manager.sync_to_claude()
        
        if tasks:
            # JSON形式で出力（TodoWrite用）
            output = json.dumps(tasks, ensure_ascii=False, indent=2)
            click.echo(output)
            
            click.echo(f"\n✅ {len(tasks)}タスクをエクスポートしました", err=True)
            click.echo("💡 出力をコピーしてClaude CodeのTodoWriteで使用してください", err=True)
        else:
            click.echo("⚠️ エクスポートするタスクがありません")
            
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}", err=True)
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


@main.group()
def stats():
    """プロジェクト統計情報"""
    pass


@stats.command()
@click.option("--path", "-p", default=None, help="プロジェクトパス (デフォルト: 現在のディレクトリ)")
@click.option("--no-cache", is_flag=True, help="キャッシュを使用しない")
def files(path: Optional[str], no_cache: bool):
    """ファイル統計情報を表示"""
    try:
        analytics = ProjectAnalytics(path)
        stats = analytics.get_file_statistics(use_cache=not no_cache)
        
        click.echo(f"📊 ファイル統計 - {analytics.project_path.name}")
        click.echo(f"📁 総ファイル数: {stats['total_files']:,}")
        click.echo(f"📂 総ディレクトリ数: {stats['total_directories']:,}")
        click.echo(f"💾 総サイズ: {stats['total_size_bytes'] / (1024*1024):.1f} MB")
        click.echo(f"⏱️  処理時間: {stats['processing_time']:.2f}秒")
        
        click.echo("\n📈 ファイルタイプ別 (上位10):")
        for ext, count in sorted(stats['file_types'].items(), 
                                key=lambda x: x[1], reverse=True)[:10]:
            click.echo(f"  {ext or 'なし'}: {count:,}")
        
        click.echo("\n📊 カテゴリ別:")
        for category, count in sorted(stats['file_categories'].items(),
                                    key=lambda x: x[1], reverse=True):
            click.echo(f"  {category}: {count:,}")
            
    except Exception as e:
        click.echo(f"❌ ファイル統計エラー: {e}", err=True)
        sys.exit(1)


@stats.command()
@click.option("--path", "-p", default=None, help="プロジェクトパス")
@click.option("--days", "-d", default=30, help="分析対象の日数")
def activity(path: Optional[str], days: int):
    """プロジェクトアクティビティを表示"""
    try:
        analytics = ProjectAnalytics(path)
        activity = analytics.get_activity_patterns(days)
        
        click.echo(f"🔥 アクティビティパターン ({days}日間) - {analytics.project_path.name}")
        
        if activity['recent_changes']:
            click.echo(f"\n📝 最近の変更 ({len(activity['recent_changes'])}件):")
            for change in activity['recent_changes'][:10]:
                click.echo(f"  {change['path']} ({change['modified'][:10]})")
        
        if activity['most_active_files']:
            click.echo(f"\n🎯 最も活発なファイル:")
            for file_info in activity['most_active_files'][:5]:
                click.echo(f"  {file_info['path']}: {file_info['modifications']}回")
        
        if activity['growth_rate']:
            growth = activity['growth_rate']
            click.echo(f"\n📈 成長率:")
            click.echo(f"  週間変化: {growth['weekly_change']:+d}ファイル")
            click.echo(f"  成長率: {growth['percentage']:+.1f}%")
            
    except Exception as e:
        click.echo(f"❌ アクティビティ分析エラー: {e}", err=True)
        sys.exit(1)


@stats.command()
@click.option("--path", "-p", default=None, help="プロジェクトパス")
def summary(path: Optional[str]):
    """プロジェクトサマリーを表示"""
    try:
        analytics = ProjectAnalytics(path)
        summary = analytics.get_project_summary()
        
        click.echo(f"📋 プロジェクトサマリー")
        click.echo(f"🏷️  名前: {summary['project_name']}")
        click.echo(f"📁 パス: {summary['project_path']}")
        click.echo(f"📊 ファイル数: {summary['total_files']:,}")
        click.echo(f"📂 ディレクトリ数: {summary['total_directories']:,}")
        click.echo(f"💾 サイズ: {summary['total_size_mb']} MB")
        click.echo(f"🔤 主要言語: {summary['primary_language']}")
        click.echo(f"🕒 最終更新: {summary['last_updated'][:19]}")
        
        activity_summary = summary['activity_summary']
        click.echo(f"\n🎯 アクティビティ:")
        click.echo(f"  最近の変更: {activity_summary['recent_files_modified']}件")
        if activity_summary['most_active_hour'] is not None:
            click.echo(f"  最活発時間: {activity_summary['most_active_hour']}時")
        click.echo(f"  成長トレンド: {activity_summary['growth_trend']:+.1f}%")
        
    except Exception as e:
        click.echo(f"❌ サマリー生成エラー: {e}", err=True)
        sys.exit(1)


@stats.command()
@click.option("--path", "-p", default=None, help="プロジェクトパス")
@click.option("--format", "-f", default="json", 
              type=click.Choice(['json', 'markdown', 'csv']),
              help="出力形式")
@click.option("--output", "-o", default=None, help="出力ファイルパス")
def export(path: Optional[str], format: str, output: Optional[str]):
    """統計情報をエクスポート"""
    try:
        analytics = ProjectAnalytics(path)
        output_file = analytics.export_statistics(format, output)
        
        click.echo(f"📤 統計情報をエクスポートしました")
        click.echo(f"📁 ファイル: {output_file}")
        click.echo(f"📄 形式: {format}")
        
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}", err=True)
        sys.exit(1)


@stats.command()
@click.argument("file_path")
@click.option("--project-path", "-p", default=None, help="プロジェクトパス")
def analyze(file_path: str, project_path: Optional[str]):
    """特定ファイルの詳細分析"""
    try:
        analytics = ProjectAnalytics(project_path)
        analysis = analytics.analyze_file_complexity(file_path)
        
        click.echo(f"🔍 ファイル分析: {analysis['file_path']}")
        click.echo(f"💾 サイズ: {analysis['size_bytes']:,} bytes")
        click.echo(f"🕒 最終更新: {analysis['last_modified'][:19]}")
        
        if 'lines' in analysis:
            click.echo(f"📝 行数: {analysis['lines']:,}")
            click.echo(f"🔤 文字数: {analysis['characters']:,}")
        
        if 'code_metrics' in analysis:
            metrics = analysis['code_metrics']
            click.echo(f"\n📊 コードメトリクス:")
            click.echo(f"  総行数: {metrics['total_lines']:,}")
            click.echo(f"  コード行: {metrics['code_lines']:,}")
            click.echo(f"  コメント行: {metrics['comment_lines']:,}")
            click.echo(f"  空行: {metrics['blank_lines']:,}")
            
    except Exception as e:
        click.echo(f"❌ ファイル分析エラー: {e}", err=True)
        sys.exit(1)


@main.group()
def template():
    """テンプレート管理"""
    pass


@template.command()
@click.argument("template_type")
@click.option("--context", default="auto", help="プロジェクトコンテキスト (auto, manual)")
@click.option("--language", "-l", default="ja", type=click.Choice(['ja', 'en']), help="言語")
@click.option("--format", "-f", default="markdown", 
              type=click.Choice(['markdown', 'json', 'yaml', 'html']), help="出力形式")
@click.option("--output", "-o", default=None, help="出力ファイルパス")
@click.argument("project_path", default=".", required=False)
def generate(template_type: str, context: str, language: str, format: str, output: Optional[str], project_path: str):
    """コンテキスト認識テンプレートを生成します"""
    try:
        click.echo(f"🎯 テンプレート生成: {template_type}")
        
        # Get project context
        if context == "auto":
            project_manager = ProjectManager()
            project_context = project_manager.detect_project_context(Path(project_path))
        else:
            project_context = {"name": "Manual Project", "type": "basic", "path": project_path}
        
        # Generate template
        engine = DynamicTemplateEngine()
        template_content = engine.generate_context_aware_template(
            template_type, project_context, language, format
        )
        
        # Output result
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            click.echo(f"✅ テンプレートを保存しました: {output_path}")
        else:
            click.echo(f"📄 生成されたテンプレート:\n")
            click.echo(template_content)
        
    except Exception as e:
        click.echo(f"❌ テンプレート生成エラー: {e}", err=True)
        sys.exit(1)


@template.command()
@click.argument("name")
@click.option("--type", "-t", default="custom", help="テンプレートタイプ")
@click.option("--file", "-f", default=None, help="テンプレートファイルパス")
@click.option("--content", "-c", default=None, help="テンプレート内容")
def create(name: str, type: str, file: Optional[str], content: Optional[str]):
    """カスタムテンプレートを作成します"""
    try:
        manager = TemplateManager()
        
        # Get template content
        if file:
            template_path = Path(file)
            if not template_path.exists():
                click.echo(f"❌ ファイルが見つかりません: {file}", err=True)
                sys.exit(1)
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        elif content:
            template_content = content
        else:
            click.echo("❌ --file または --content のいずれかを指定してください", err=True)
            sys.exit(1)
        
        # Create metadata
        metadata = {
            "type": type,
            "created_by": "ukf-cli",
            "description": f"Custom template: {name}"
        }
        
        if manager.register_custom_template(name, template_content, metadata, type):
            click.echo(f"✅ カスタムテンプレート '{name}' を作成しました")
        else:
            click.echo(f"❌ テンプレート作成に失敗しました", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ テンプレート作成エラー: {e}", err=True)
        sys.exit(1)


@template.command()
@click.option("--filter", "-f", default=None, help="テンプレートタイプフィルタ")
@click.option("--search", "-s", default=None, help="検索クエリ")
def list(filter: Optional[str], search: Optional[str]):
    """テンプレート一覧を表示します"""
    try:
        manager = TemplateManager()
        
        if search:
            templates = manager.search_templates(search)
            click.echo(f"🔍 検索結果: '{search}'")
        else:
            templates = manager.list_templates(filter)
            if filter:
                click.echo(f"📋 テンプレート一覧 (フィルタ: {filter})")
            else:
                click.echo("📋 テンプレート一覧")
        
        if not templates:
            click.echo("📝 テンプレートがありません")
            return
        
        for template in templates:
            type_emoji = {"base": "🏗️", "custom": "🎨", "imported": "📥"}.get(template.get("type"), "📄")
            click.echo(f"{type_emoji} {template['name']} ({template.get('type', 'unknown')})")
            if template.get('metadata'):
                desc = template['metadata'].get('description', '')
                if desc:
                    click.echo(f"    {desc}")
        
    except Exception as e:
        click.echo(f"❌ テンプレート一覧エラー: {e}", err=True)
        sys.exit(1)


@template.command()
@click.argument("template_path")
def validate(template_path: str):
    """テンプレートの妥当性を検証します"""
    try:
        engine = DynamicTemplateEngine()
        result = engine.validate_template(template_path)
        
        click.echo(f"🔍 テンプレート検証: {template_path}")
        
        if result['valid']:
            click.echo("✅ テンプレートは有効です")
        else:
            click.echo("❌ テンプレートに問題があります")
            for error in result['errors']:
                click.echo(f"  エラー: {error}")
        
        if result['warnings']:
            for warning in result['warnings']:
                click.echo(f"  警告: {warning}")
        
        if result['metadata']:
            metadata = result['metadata']
            click.echo(f"📊 メタデータ:")
            click.echo(f"  ファイルサイズ: {metadata.get('file_size', 0)} bytes")
            click.echo(f"  最終更新: {metadata.get('last_modified', 'Unknown')}")
        
    except Exception as e:
        click.echo(f"❌ テンプレート検証エラー: {e}", err=True)
        sys.exit(1)


@template.command()
@click.argument("project_path", default=".", required=False)
@click.option("--limit", "-n", default=5, help="推奨テンプレート数")
def recommend(project_path: str, limit: int):
    """プロジェクトに適したテンプレートを推奨します"""
    try:
        # Get project context
        project_manager = ProjectManager()
        project_context = project_manager.detect_project_context(Path(project_path))
        
        # Get recommendations
        manager = TemplateManager()
        recommendations = manager.get_recommended_templates(project_context)
        
        click.echo(f"🎯 プロジェクト '{project_context.get('name', 'Unknown')}' への推奨テンプレート:")
        click.echo(f"📁 プロジェクトタイプ: {project_context.get('type', 'unknown')}")
        
        if not recommendations:
            click.echo("📝 推奨テンプレートがありません")
            return
        
        for i, template in enumerate(recommendations[:limit], 1):
            score = template.get('relevance_score', 0)
            type_emoji = {"base": "🏗️", "custom": "🎨", "imported": "📥"}.get(template.get("type"), "📄")
            click.echo(f"{i}. {type_emoji} {template['name']} (関連度: {score:.1f})")
            if template.get('metadata', {}).get('description'):
                click.echo(f"    {template['metadata']['description']}")
        
    except Exception as e:
        click.echo(f"❌ テンプレート推奨エラー: {e}", err=True)
        sys.exit(1)


@template.command()
@click.argument("name")
def delete(name: str):
    """カスタムテンプレートを削除します"""
    try:
        manager = TemplateManager()
        
        if manager.delete_template(name):
            click.echo(f"✅ テンプレート '{name}' を削除しました")
        else:
            click.echo(f"❌ テンプレート '{name}' が見つかりません", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ テンプレート削除エラー: {e}", err=True)
        sys.exit(1)


@main.group()
def bridge():
    """ブリッジアダプター管理 - 外部ツール連携"""
    pass


@bridge.command()
def list():
    """利用可能なアダプター一覧を表示"""
    try:
        bridge_manager = BridgeManager()
        adapters = bridge_manager.list_adapters()
        
        if not adapters:
            click.echo("📭 登録済みアダプターがありません")
            click.echo("\n🔧 利用可能なアダプター:")
            click.echo("  - obsidian: Obsidianボルト連携")
            return
        
        click.echo("📋 登録済みアダプター:")
        status = bridge_manager.get_adapter_status()
        
        for adapter_name in adapters:
            adapter_status = status.get(adapter_name, {})
            connected = adapter_status.get('connected', False)
            status_emoji = "🟢" if connected else "🔴"
            click.echo(f"  {status_emoji} {adapter_name}")
            
            if connected and 'info' in adapter_status:
                info = adapter_status['info']
                if 'vault_path' in info:
                    click.echo(f"    📁 ボルト: {info['vault_path']}")
                    
    except Exception as e:
        click.echo(f"❌ アダプター一覧エラー: {e}", err=True)
        sys.exit(1)


@bridge.command()
@click.argument("adapter_name")
@click.option("--vault-path", "-v", help="Obsidianボルトパス (obsidianアダプター用)")
@click.option("--project-path", "-p", default=None, help="プロジェクトパス (デフォルト: 現在のディレクトリ)")
@click.option("--create-vault", is_flag=True, help="ボルトが存在しない場合作成")
def connect(adapter_name: str, vault_path: Optional[str], project_path: Optional[str], create_vault: bool):
    """アダプターに接続"""
    try:
        bridge_manager = BridgeManager(project_path)
        
        if adapter_name == "obsidian":
            # Obsidianアダプターを登録・接続
            obsidian_adapter = ObsidianAdapter()
            bridge_manager.register_adapter(obsidian_adapter)
            
            config = {
                'project_path': project_path or Path.cwd(),
                'create_if_missing': create_vault
            }
            
            if vault_path:
                config['vault_path'] = vault_path
            
            success = bridge_manager.connect_adapter("obsidian", config)
            
            if success:
                click.echo(f"✅ {adapter_name} アダプターに接続しました")
                
                # プロジェクトデータを同期
                project_data = StandardDataFormat.create_project_data(
                    project_path or Path.cwd()
                )
                
                sync_results = bridge_manager.sync_all(project_data)
                if sync_results.get("obsidian"):
                    click.echo("📁 プロジェクトデータを同期しました")
                else:
                    click.echo("⚠️ データ同期に失敗しました")
            else:
                click.echo(f"❌ {adapter_name} アダプターへの接続に失敗しました", err=True)
                sys.exit(1)
        else:
            click.echo(f"❌ 未対応のアダプター: {adapter_name}", err=True)
            click.echo("利用可能なアダプター: obsidian")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ アダプター接続エラー: {e}", err=True)
        sys.exit(1)


@bridge.command()
@click.argument("adapter_name", required=False)
def disconnect(adapter_name: Optional[str]):
    """アダプターから切断 (アダプター名省略時は全て切断)"""
    try:
        bridge_manager = BridgeManager()
        
        if adapter_name:
            # 特定のアダプターを切断
            success = bridge_manager.disconnect_adapter(adapter_name)
            if success:
                click.echo(f"✅ {adapter_name} アダプターから切断しました")
            else:
                click.echo(f"❌ {adapter_name} アダプターが見つかりません", err=True)
                sys.exit(1)
        else:
            # 全アダプターを切断
            adapters = bridge_manager.list_adapters()
            disconnected = 0
            
            for name in adapters:
                if bridge_manager.disconnect_adapter(name):
                    disconnected += 1
            
            click.echo(f"✅ {disconnected}個のアダプターから切断しました")
            
    except Exception as e:
        click.echo(f"❌ アダプター切断エラー: {e}", err=True)
        sys.exit(1)


@bridge.command()
@click.option("--project-path", "-p", default=None, help="プロジェクトパス")
def sync(project_path: Optional[str]):
    """接続済みアダプターでプロジェクトデータを同期"""
    try:
        bridge_manager = BridgeManager(project_path)
        adapters = bridge_manager.list_adapters()
        
        if not adapters:
            click.echo("📭 登録済みアダプターがありません")
            click.echo("使用方法: ukf bridge connect obsidian")
            return
        
        # プロジェクトデータ作成
        project_data = StandardDataFormat.create_project_data(
            project_path or Path.cwd()
        )
        
        # 全アダプターで同期
        sync_results = bridge_manager.sync_all(project_data)
        
        click.echo("🔄 データ同期結果:")
        for adapter_name, success in sync_results.items():
            status_emoji = "✅" if success else "❌"
            click.echo(f"  {status_emoji} {adapter_name}")
        
        successful_syncs = sum(sync_results.values())
        total_adapters = len(sync_results)
        
        click.echo(f"\n📊 {successful_syncs}/{total_adapters} アダプターで同期完了")
        
    except Exception as e:
        click.echo(f"❌ データ同期エラー: {e}", err=True)
        sys.exit(1)


@bridge.command()
def status():
    """ブリッジアダプターの状態を表示"""
    try:
        bridge_manager = BridgeManager()
        status = bridge_manager.get_adapter_status()
        
        if not status:
            click.echo("📭 登録済みアダプターがありません")
            return
        
        click.echo("🔍 ブリッジアダプター状態:")
        
        for adapter_name, adapter_status in status.items():
            connected = adapter_status.get('connected', False)
            status_emoji = "🟢" if connected else "🔴"
            
            click.echo(f"\n{status_emoji} {adapter_name}")
            click.echo(f"  接続状態: {'接続済み' if connected else '切断'}")
            
            if 'info' in adapter_status:
                info = adapter_status['info']
                click.echo(f"  タイプ: {info.get('type', '不明')}")
                
                if 'vault_path' in info:
                    click.echo(f"  ボルトパス: {info['vault_path']}")
                    click.echo(f"  ボルト存在: {'はい' if info.get('vault_exists') else 'いいえ'}")
                    
            if 'error' in adapter_status:
                click.echo(f"  エラー: {adapter_status['error']}")
                
            click.echo(f"  最終確認: {adapter_status['last_check'][:19]}")
            
    except Exception as e:
        click.echo(f"❌ 状態確認エラー: {e}", err=True)
        sys.exit(1)


@bridge.command()
@click.option("--format", "-f", default="json",
              type=click.Choice(['json', 'yaml']),
              help="エクスポート形式")
@click.option("--output", "-o", default=None, help="出力ファイルパス")
@click.option("--project-path", "-p", default=None, help="プロジェクトパス")
def export(format: str, output: Optional[str], project_path: Optional[str]):
    """プロジェクトデータを標準形式でエクスポート"""
    try:
        # プロジェクトデータ作成
        project_data = StandardDataFormat.create_project_data(
            project_path or Path.cwd()
        )
        
        # 出力パス決定
        if not output:
            project_name = project_data.name.replace(' ', '_').lower()
            output = f"{project_name}_export.{format}"
        
        # エクスポート実行
        if format == "json":
            success = StandardDataFormat.export_to_json(project_data, output)
        else:
            # YAML対応は将来実装
            click.echo("❌ YAML形式は未対応です", err=True)
            sys.exit(1)
        
        if success:
            click.echo(f"✅ プロジェクトデータをエクスポートしました")
            click.echo(f"📁 ファイル: {output}")
            click.echo(f"📊 ファイル数: {len(project_data.files)}")
            click.echo(f"📝 タスク数: {len(project_data.tasks)}")
        else:
            click.echo("❌ エクスポートに失敗しました", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ エクスポートエラー: {e}", err=True)
        sys.exit(1)


@main.group()
def update():
    """UKF更新・アップグレード"""
    pass


@update.command()
@click.option("--version", "-v", default=None, help="対象バージョン (デフォルト: 最新)")
@click.option("--force", is_flag=True, help="強制更新 (未コミット変更を無視)")
@click.option("--dry-run", is_flag=True, help="実行せず手順のみ表示")
@click.option("--ukf-path", default=None, help="UKFプロジェクトパス")
def run(version: Optional[str], force: bool, dry_run: bool, ukf_path: Optional[str]):
    """UKFを最新版に更新します"""
    try:
        updater = UKFUpdater(Path(ukf_path) if ukf_path else None)
        
        if dry_run:
            click.echo("🔍 DRY RUN モード - 実際の更新は行いません")
        
        click.echo("🚀 UKF更新を開始します...")
        
        # 更新チェック
        update_check = updater.check_for_updates()
        
        if update_check.get("error"):
            click.echo(f"❌ 更新チェックエラー: {update_check['error']}", err=True)
            sys.exit(1)
        
        if not update_check.get("updates_available") and not force:
            click.echo("✅ 既に最新版です")
            click.echo(f"現在のバージョン: {update_check['current_version']}")
            return
        
        click.echo(f"📊 現在のバージョン: {update_check['current_version']}")
        click.echo(f"📈 最新バージョン: {update_check['remote_version']}")
        
        # 更新実行
        result = updater.update(version, force, dry_run)
        
        # 結果表示
        if result["success"]:
            click.echo("\n✅ 更新完了!")
            if not dry_run:
                click.echo("🎯 新機能を試してみてください:")
                click.echo("   ukf stats summary")
                click.echo("   ukf ai session start")
                click.echo("   ukf template recommend")
        else:
            click.echo(f"\n❌ 更新エラー: {result.get('error', '不明なエラー')}", err=True)
            if result.get("backup_created"):
                click.echo(f"💡 復元方法: ukf update rollback --backup {result['backup_path']}")
            sys.exit(1)
        
        # ステップ詳細表示
        if dry_run or result.get("error"):
            click.echo("\n📋 実行ステップ:")
            for step in result["steps"]:
                click.echo(f"  {step['message']}")
                
    except Exception as e:
        click.echo(f"❌ 更新システムエラー: {e}", err=True)
        sys.exit(1)


@update.command()
@click.option("--backup", "-b", required=True, help="バックアップディレクトリパス")
def rollback(backup: str):
    """バックアップから復元します"""
    try:
        updater = UKFUpdater()
        
        click.echo(f"🔄 バックアップから復元中: {backup}")
        
        result = updater.rollback(backup)
        
        if result["success"]:
            click.echo("✅ 復元完了!")
        else:
            click.echo(f"❌ 復元エラー: {result.get('error', '不明なエラー')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 復元システムエラー: {e}", err=True)
        sys.exit(1)


@update.command()
def check():
    """更新の有無をチェックします"""
    try:
        updater = UKFUpdater()
        
        click.echo("🔍 更新チェック中...")
        
        result = updater.check_for_updates()
        
        if result.get("error"):
            click.echo(f"❌ チェックエラー: {result['error']}", err=True)
            sys.exit(1)
        
        click.echo(f"📊 現在のバージョン: {result['current_version']}")
        click.echo(f"📈 リモートバージョン: {result['remote_version']}")
        
        if result["updates_available"]:
            click.echo("🆙 更新が利用可能です!")
            click.echo("実行コマンド: ukf update run")
        else:
            click.echo("✅ 最新版です")
            
    except Exception as e:
        click.echo(f"❌ チェックシステムエラー: {e}", err=True)
        sys.exit(1)


@update.command()
def backups():
    """利用可能なバックアップ一覧を表示します"""
    try:
        updater = UKFUpdater()
        
        backup_list = updater.list_backups()
        
        if not backup_list:
            click.echo("📝 バックアップがありません")
            return
        
        click.echo("📋 利用可能なバックアップ:")
        for backup in backup_list:
            created = backup["created_at"][:19] if backup["created_at"] != "unknown" else "不明"
            version = backup["version"]
            click.echo(f"  📁 {backup['name']}")
            click.echo(f"     作成日時: {created}")
            click.echo(f"     バージョン: {version}")
            click.echo(f"     パス: {backup['path']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ バックアップリストエラー: {e}", err=True)
        sys.exit(1)


@update.command()
@click.option("--keep", default=5, help="保持するバックアップ数")
def cleanup(keep: int):
    """古いバックアップを削除します"""
    try:
        updater = UKFUpdater()
        
        deleted_count = updater.cleanup_old_backups(keep)
        
        click.echo(f"🗑️  {deleted_count}個の古いバックアップを削除しました")
        click.echo(f"📁 {keep}個のバックアップを保持中")
        
    except Exception as e:
        click.echo(f"❌ クリーンアップエラー: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--input-dir", "-i", default=DEFAULT_INPUT_DIR, help="Claude JSONログディレクトリ")
@click.option("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR, help="出力先Markdownディレクトリ")
@click.option("--include-short", is_flag=True, help="短いメッセージも含める")
def claude2md(input_dir: str, output_dir: str, include_short: bool):
    """ClaudeログをMarkdown形式に変換します"""
    try:
        process_logs(Path(input_dir), Path(output_dir), exclude_short=not include_short)
        click.echo("✅ Claudeログを変換しました")
    except Exception as e:
        click.echo(f"❌ 変換エラー: {e}", err=True)
        sys.exit(1)


@main.command()
def version():
    """バージョン情報を表示します"""
    click.echo("汎用ナレッジ管理フレームワーク v1.1.0")
    click.echo("Universal Knowledge Framework")


if __name__ == "__main__":
    main()