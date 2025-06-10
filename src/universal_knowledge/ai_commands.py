"""
AI CLIコマンド統合モジュール

後方互換性を保持しながら、AI機能をCLIに統合します。
"""

import click
import sys
from pathlib import Path
from typing import Optional

from .ai_migration import AIMigrationSystem, MigrationStrategy
from .ai.session_tracker import SessionTracker
from .ai.claude_manager import ClaudeManager
from .ai.auto_updater import AutoUpdateManager


class AICommands:
    """AI機能CLIコマンドクラス"""
    
    def __init__(self):
        self.ai_system = AIMigrationSystem()
        self.session_tracker = SessionTracker()
        self.claude_manager = ClaudeManager()
        self.auto_updater = AutoUpdateManager()

    def create_cli_group(self) -> click.Group:
        """AI CLIコマンドグループを作成"""
        
        @click.group(name='ai')
        def ai_group():
            """🤖 AI駆動ドキュメント変換・解析・開発支援機能"""
            pass
        
        # 既存のサブコマンド
        ai_group.add_command(self._create_analyze_command())
        ai_group.add_command(self._create_migrate_command())
        ai_group.add_command(self._create_plan_command())
        ai_group.add_command(self._create_report_command())
        
        # 新機能サブコマンド
        ai_group.add_command(self._create_session_group())
        ai_group.add_command(self._create_claude_group())
        
        return ai_group

    def _create_analyze_command(self) -> click.Command:
        """解析コマンド"""
        
        @click.command()
        @click.argument('project_path', type=click.Path(exists=True, file_okay=False))
        @click.option('--output', '-o', help='解析結果出力ファイル')
        @click.option('--format', 'output_format', 
                     type=click.Choice(['markdown', 'json', 'text']),
                     default='markdown', help='出力形式')
        @click.option('--verbose', '-v', is_flag=True, help='詳細表示')
        def analyze(project_path: str, output: Optional[str], 
                   output_format: str, verbose: bool):
            """📊 プロジェクト構造とコンテンツを解析"""
            
            try:
                click.echo(f"🔍 プロジェクト解析開始: {project_path}")
                
                # クイック解析実行
                analysis_report = self.ai_system.quick_analyze(project_path)
                
                # 詳細解析
                if verbose:
                    click.echo("\n📈 詳細解析中...")
                    project_analysis = self.ai_system.analyze_project(project_path)
                    
                    click.echo(f"\n📊 詳細結果:")
                    click.echo(f"  ファイル数: {project_analysis.total_files:,}")
                    click.echo(f"  総サイズ: {self.ai_system._format_size(project_analysis.total_size)}")
                    click.echo(f"  平均品質: {project_analysis.quality_average:.1f}/100")
                    
                    # ファイルタイプ分布
                    click.echo(f"\n📂 ファイルタイプ分布:")
                    for file_type, count in sorted(
                        project_analysis.file_types.items(), 
                        key=lambda x: x[1], reverse=True
                    ):
                        percentage = (count / project_analysis.total_files) * 100
                        click.echo(f"  {file_type}: {count} ({percentage:.1f}%)")
                
                # 出力
                if output:
                    if output_format == 'json':
                        # JSON形式での出力
                        import json
                        analysis_data = self.ai_system.analyze_project(project_path)
                        with open(output, 'w', encoding='utf-8') as f:
                            json.dump({
                                'root_path': analysis_data.root_path,
                                'total_files': analysis_data.total_files,
                                'total_size': analysis_data.total_size,
                                'file_types': analysis_data.file_types,
                                'frameworks': analysis_data.frameworks,
                                'quality_average': analysis_data.quality_average
                            }, f, ensure_ascii=False, indent=2)
                    else:
                        with open(output, 'w', encoding='utf-8') as f:
                            f.write(analysis_report)
                    
                    click.echo(f"📄 解析結果保存: {output}")
                else:
                    click.echo(f"\n{analysis_report}")
                
                click.echo("✅ プロジェクト解析完了")
                
            except Exception as e:
                click.echo(f"❌ 解析エラー: {e}", err=True)
                sys.exit(1)
        
        return analyze

    def _create_migrate_command(self) -> click.Command:
        """マイグレーションコマンド"""
        
        @click.command()
        @click.argument('source_path', type=click.Path(exists=True, file_okay=False))
        @click.option('--target', '-t', help='出力先ディレクトリ')
        @click.option('--strategy', type=click.Choice(['conservative', 'aggressive', 'selective', 'hybrid']),
                     default='conservative', help='マイグレーション戦略')
        @click.option('--ai-enhancement', is_flag=True, default=True,
                     help='AI品質向上を適用')
        @click.option('--dry-run', is_flag=True, help='実行せずに計画のみ表示')
        @click.option('--force', is_flag=True, help='確認なしで実行')
        def migrate(source_path: str, target: Optional[str], strategy: str,
                   ai_enhancement: bool, dry_run: bool, force: bool):
            """🚀 AI駆動プロジェクトマイグレーション"""
            
            try:
                if not target:
                    target = f"{source_path}_migrated"
                
                click.echo(f"🤖 AI駆動マイグレーション開始")
                click.echo(f"  ソース: {source_path}")
                click.echo(f"  ターゲット: {target}")
                click.echo(f"  戦略: {strategy}")
                
                if dry_run:
                    click.echo("\n📋 ドライラン: 計画のみ表示")
                    
                    # 解析と計画
                    analysis = self.ai_system.analyze_project(source_path)
                    strategy_enum = MigrationStrategy(strategy)
                    plan = self.ai_system.create_migration_plan(analysis, strategy_enum)
                    plan.target_path = target
                    
                    click.echo(f"\n📊 マイグレーション計画:")
                    click.echo(f"  プロジェクト: {plan.project_name}")
                    click.echo(f"  ファイル数: {plan.file_count}")
                    click.echo(f"  予想時間: {plan.estimated_duration//60}時間{plan.estimated_duration%60}分")
                    click.echo(f"  バックアップ: {'有' if plan.backup_required else '無'}")
                    
                    return
                
                # 実行確認
                if not force:
                    if not click.confirm(f"\nマイグレーションを実行しますか？"):
                        click.echo("❌ マイグレーションを中止しました")
                        return
                
                # マイグレーション実行
                click.echo("\n🔄 マイグレーション実行中...")
                
                with click.progressbar(length=100, label='処理中') as bar:
                    # 簡易版マイグレーション実行
                    report = self.ai_system.migrate_project(source_path, target, strategy)
                    bar.update(100)
                
                click.echo(f"\n✅ マイグレーション完了!")
                click.echo(f"📁 結果ディレクトリ: {target}")
                
                # レポート表示
                lines = report.split('\n')
                for line in lines[:15]:  # 最初の15行を表示
                    if line.strip():
                        click.echo(line)
                
                if len(lines) > 15:
                    click.echo(f"... (残り{len(lines)-15}行)")
                
            except Exception as e:
                click.echo(f"❌ マイグレーションエラー: {e}", err=True)
                sys.exit(1)
        
        return migrate

    def _create_plan_command(self) -> click.Command:
        """計画作成コマンド"""
        
        @click.command()
        @click.argument('project_path', type=click.Path(exists=True, file_okay=False))
        @click.option('--strategy', type=click.Choice(['conservative', 'aggressive', 'selective', 'hybrid']),
                     default='conservative', help='マイグレーション戦略')
        @click.option('--output', '-o', help='計画出力ファイル')
        def plan(project_path: str, strategy: str, output: Optional[str]):
            """📋 マイグレーション計画を作成"""
            
            try:
                click.echo(f"📋 マイグレーション計画作成: {project_path}")
                
                # 解析と計画
                with click.progressbar(length=100, label='解析中') as bar:
                    analysis = self.ai_system.analyze_project(project_path)
                    bar.update(50)
                    
                    strategy_enum = MigrationStrategy(strategy)
                    plan = self.ai_system.create_migration_plan(analysis, strategy_enum)
                    bar.update(100)
                
                # 計画表示
                click.echo(f"\n📊 マイグレーション計画:")
                click.echo(f"  プロジェクト: {plan.project_name}")
                click.echo(f"  戦略: {plan.strategy.value}")
                click.echo(f"  ファイル数: {plan.file_count}")
                click.echo(f"  予想時間: {plan.estimated_duration//60}時間{plan.estimated_duration%60}分")
                click.echo(f"  バックアップ: {'必要' if plan.backup_required else '不要'}")
                
                # 推奨事項
                click.echo(f"\n💡 推奨事項:")
                if analysis.quality_average < 50:
                    click.echo("  - 品質向上の余地が大きいため、AI強化をお勧めします")
                if analysis.total_files > 500:
                    click.echo("  - 大量ファイルのため、段階的な移行をお勧めします")
                if 'obsidian' in analysis.frameworks:
                    click.echo("  - Obsidianプロジェクトが検出されました")
                
                # 計画保存
                if output:
                    import json
                    plan_data = {
                        'project_name': plan.project_name,
                        'source_path': plan.source_path,
                        'target_path': plan.target_path,
                        'strategy': plan.strategy.value,
                        'estimated_duration': plan.estimated_duration,
                        'file_count': plan.file_count,
                        'backup_required': plan.backup_required
                    }
                    
                    with open(output, 'w', encoding='utf-8') as f:
                        json.dump(plan_data, f, ensure_ascii=False, indent=2)
                    
                    click.echo(f"📄 計画保存: {output}")
                
                click.echo("✅ 計画作成完了")
                
            except Exception as e:
                click.echo(f"❌ 計画作成エラー: {e}", err=True)
                sys.exit(1)
        
        return plan

    def _create_report_command(self) -> click.Command:
        """レポート生成コマンド"""
        
        @click.command()
        @click.argument('project_path', type=click.Path(exists=True, file_okay=False))
        @click.option('--output', '-o', help='レポート出力ファイル')
        @click.option('--format', 'output_format',
                     type=click.Choice(['markdown', 'json', 'html']),
                     default='markdown', help='出力形式')
        def report(project_path: str, output: Optional[str], output_format: str):
            """📊 プロジェクトレポートを生成"""
            
            try:
                click.echo(f"📊 レポート生成: {project_path}")
                
                # 解析実行
                with click.progressbar(length=100, label='解析中') as bar:
                    analysis = self.ai_system.analyze_project(project_path)
                    bar.update(70)
                    
                    report_content = self.ai_system.quick_analyze(project_path)
                    bar.update(100)
                
                # フォーマット別出力
                if output_format == 'json':
                    import json
                    import datetime
                    report_data = {
                        'timestamp': str(datetime.datetime.now()),
                        'project_path': analysis.root_path,
                        'total_files': analysis.total_files,
                        'total_size': analysis.total_size,
                        'file_types': analysis.file_types,
                        'frameworks': analysis.frameworks,
                        'quality_average': analysis.quality_average
                    }
                    final_content = json.dumps(report_data, ensure_ascii=False, indent=2)
                
                elif output_format == 'html':
                    import datetime
                    final_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Project Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4f8; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Project Analysis Report</h1>
        <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="metrics">
        <div class="metric">📁 Files: {analysis.total_files:,}</div>
        <div class="metric">💾 Size: {self.ai_system._format_size(analysis.total_size)}</div>
        <div class="metric">⭐ Quality: {analysis.quality_average:.1f}/100</div>
    </div>
    <pre>{report_content}</pre>
</body>
</html>"""
                else:
                    final_content = report_content
                
                # 出力
                if output:
                    with open(output, 'w', encoding='utf-8') as f:
                        f.write(final_content)
                    click.echo(f"📄 レポート保存: {output}")
                else:
                    click.echo(f"\n{final_content}")
                
                click.echo("✅ レポート生成完了")
                
            except Exception as e:
                click.echo(f"❌ レポート生成エラー: {e}", err=True)
                sys.exit(1)
        
        return report

    def _create_session_group(self) -> click.Group:
        """セッション管理コマンドグループ"""
        
        @click.group(name='session')
        def session_group():
            """📝 AI開発セッション管理"""
            pass
        
        @session_group.command()
        @click.option('--type', '-t', default='implementation', 
                     type=click.Choice(['implementation', 'debugging', 'refactoring', 'research']),
                     help='セッションタイプ')
        @click.option('--description', '-d', default='', help='セッション説明')
        @click.argument('project_path', default='.', required=False)
        def start(type: str, description: str, project_path: str):
            """AI開発セッション開始"""
            try:
                project_path_obj = Path(project_path)
                tracker = SessionTracker(project_path_obj)
                
                session_id = tracker.start_session(type, description)
                click.echo(f"✅ セッション開始: {session_id}")
                click.echo(f"📁 プロジェクト: {project_path_obj.resolve()}")
                click.echo(f"🎯 タイプ: {type}")
                if description:
                    click.echo(f"📝 説明: {description}")
                    
            except Exception as e:
                click.echo(f"❌ セッション開始エラー: {e}", err=True)
                sys.exit(1)
        
        @session_group.command()
        @click.argument('session_id')
        @click.option('--summary', '-s', default='', help='セッションサマリー')
        def end(session_id: str, summary: str):
            """AI開発セッション終了"""
            try:
                tracker = SessionTracker()
                success = tracker.end_session(session_id, summary)
                
                if success:
                    click.echo(f"✅ セッション終了: {session_id}")
                    if summary:
                        click.echo(f"📄 サマリー: {summary}")
                else:
                    click.echo(f"❌ セッション {session_id} が見つかりません", err=True)
                    sys.exit(1)
                    
            except Exception as e:
                click.echo(f"❌ セッション終了エラー: {e}", err=True)
                sys.exit(1)
        
        @session_group.command()
        @click.option('--status', type=click.Choice(['active', 'completed']), help='ステータスフィルター')
        @click.option('--limit', '-n', default=10, help='表示件数')
        def list(status: Optional[str], limit: int):
            """セッション一覧表示"""
            try:
                tracker = SessionTracker()
                sessions = tracker.list_sessions(status, limit)
                
                if not sessions:
                    click.echo("📭 セッションがありません")
                    return
                
                click.echo(f"📋 セッション一覧 ({len(sessions)}件)")
                for session in sessions:
                    status_emoji = "🟢" if session['status'] == 'active' else "🔵"
                    click.echo(f"{status_emoji} {session['session_id']} - {session['type']}")
                    click.echo(f"    📅 {session['start_time'][:19]}")
                    if session.get('description'):
                        click.echo(f"    📝 {session['description']}")
                    
            except Exception as e:
                click.echo(f"❌ セッション一覧エラー: {e}", err=True)
                sys.exit(1)
        
        @session_group.command()
        @click.argument('session_id')
        def report(session_id: str):
            """セッションレポート生成"""
            try:
                tracker = SessionTracker()
                report_content = tracker.generate_session_report(session_id)
                
                if "が見つかりません" in report_content:
                    click.echo(f"❌ {report_content}", err=True)
                    sys.exit(1)
                
                click.echo(report_content)
                
            except Exception as e:
                click.echo(f"❌ レポート生成エラー: {e}", err=True)
                sys.exit(1)
        
        @session_group.command()
        @click.argument('session_id')
        @click.argument('milestone')
        def milestone(session_id: str, milestone: str):
            """セッションマイルストーン追加"""
            try:
                tracker = SessionTracker()
                success = tracker.add_milestone(session_id, milestone)
                
                if success:
                    click.echo(f"✅ マイルストーン追加: {milestone}")
                else:
                    click.echo(f"❌ セッション {session_id} が見つかりません", err=True)
                    sys.exit(1)
                    
            except Exception as e:
                click.echo(f"❌ マイルストーン追加エラー: {e}", err=True)
                sys.exit(1)
        
        return session_group

    def _create_claude_group(self) -> click.Group:
        """Claude管理コマンドグループ"""
        
        @click.group(name='claude')
        def claude_group():
            """🤖 Claude Code連携・CLAUDE.md管理"""
            pass
        
        @claude_group.command()
        @click.argument('project_path', default='.', required=False)
        @click.option('--force', is_flag=True, help='既存ファイルを上書き')
        def init(project_path: str, force: bool):
            """CLAUDE.md初期化"""
            try:
                project_path_obj = Path(project_path)
                manager = ClaudeManager(project_path_obj)
                
                success = manager.initialize_claude_md(force)
                
                if success:
                    click.echo(f"✅ CLAUDE.md初期化完了: {project_path_obj / 'CLAUDE.md'}")
                else:
                    click.echo("ℹ️ CLAUDE.mdは既に存在します (--force で上書き可能)")
                    
            except Exception as e:
                click.echo(f"❌ 初期化エラー: {e}", err=True)
                sys.exit(1)
        
        @claude_group.command()
        @click.argument('project_path', default='.', required=False)
        @click.option('--auto', is_flag=True, help='自動更新機能を開始')
        def update(project_path: str, auto: bool):
            """CLAUDE.md更新・自動更新開始"""
            try:
                project_path_obj = Path(project_path)
                
                if auto:
                    updater = AutoUpdateManager(project_path_obj)
                    success = updater.start_monitoring()
                    
                    if success:
                        click.echo(f"🔄 CLAUDE.md自動更新開始: {project_path_obj}")
                        click.echo("ファイル変更を監視中... (Ctrl+Cで停止)")
                        
                        try:
                            while updater.is_monitoring():
                                import time
                                time.sleep(1)
                        except KeyboardInterrupt:
                            updater.stop_monitoring()
                            click.echo("\n✅ 自動更新を停止しました")
                    else:
                        click.echo("❌ 自動更新開始に失敗しました", err=True)
                        sys.exit(1)
                else:
                    manager = ClaudeManager(project_path_obj)
                    context = {"manual_update": True}
                    success = manager.update_development_context(context)
                    
                    if success:
                        click.echo(f"✅ CLAUDE.md更新完了: {project_path_obj / 'CLAUDE.md'}")
                    else:
                        click.echo("❌ 更新に失敗しました", err=True)
                        sys.exit(1)
                        
            except Exception as e:
                click.echo(f"❌ 更新エラー: {e}", err=True)
                sys.exit(1)
        
        @claude_group.command()
        @click.argument('project_path', default='.', required=False)
        def optimize(project_path: str):
            """CLAUDE.md最適化"""
            try:
                project_path_obj = Path(project_path)
                manager = ClaudeManager(project_path_obj)
                
                result = manager.optimize_claude_md()
                
                if "error" in result:
                    click.echo(f"❌ {result['error']}", err=True)
                    sys.exit(1)
                
                click.echo("✅ CLAUDE.md最適化完了")
                for optimization in result['optimizations']:
                    click.echo(f"  - {optimization}")
                
                sections_count = result.get('sections_count', 0)
                click.echo(f"📊 セクション数: {sections_count}")
                
            except Exception as e:
                click.echo(f"❌ 最適化エラー: {e}", err=True)
                sys.exit(1)
        
        @claude_group.command()
        @click.argument('project_path', default='.', required=False)
        def validate(project_path: str):
            """CLAUDE.md検証"""
            try:
                project_path_obj = Path(project_path)
                manager = ClaudeManager(project_path_obj)
                
                result = manager.validate_claude_md()
                
                if result['valid']:
                    click.echo("✅ CLAUDE.mdは有効です")
                else:
                    click.echo("❌ CLAUDE.mdに問題があります")
                    for error in result['errors']:
                        click.echo(f"  エラー: {error}")
                
                if result['warnings']:
                    for warning in result['warnings']:
                        click.echo(f"  警告: {warning}")
                
                click.echo(f"📊 セクション数: {result['sections_count']}")
                click.echo(f"💾 ファイルサイズ: {result['file_size']} bytes")
                
            except Exception as e:
                click.echo(f"❌ 検証エラー: {e}", err=True)
                sys.exit(1)
        
        @claude_group.command()
        @click.argument('pattern_name')
        @click.argument('description')
        @click.option('--example', '-e', default='', help='使用例')
        @click.option('--tags', '-t', default='', help='タグ (カンマ区切り)')
        @click.argument('project_path', default='.', required=False)
        def pattern(pattern_name: str, description: str, example: str, tags: str, project_path: str):
            """開発パターン追加"""
            try:
                project_path_obj = Path(project_path)
                manager = ClaudeManager(project_path_obj)
                
                tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
                
                success = manager.add_development_pattern(pattern_name, description, example, tags_list)
                
                if success:
                    click.echo(f"✅ 開発パターン追加: {pattern_name}")
                else:
                    click.echo("❌ パターン追加に失敗しました", err=True)
                    sys.exit(1)
                    
            except Exception as e:
                click.echo(f"❌ パターン追加エラー: {e}", err=True)
                sys.exit(1)
        
        return claude_group


# モジュールレベルでのエクスポート
def create_ai_cli_group() -> click.Group:
    """AI CLI コマンドグループを作成"""
    ai_commands = AICommands()
    return ai_commands.create_cli_group()


__all__ = ['AICommands', 'create_ai_cli_group']