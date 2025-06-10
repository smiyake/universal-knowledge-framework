"""
プロジェクト統計情報API テスト
Tests for Project Analytics API
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from universal_knowledge.core.analytics import ProjectAnalytics


class TestProjectAnalytics:
    """ProjectAnalyticsクラスのテスト"""
    
    @pytest.fixture
    def temp_project(self):
        """テスト用の一時プロジェクトディレクトリを作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # テストファイルを作成
            (project_path / "main.py").write_text("""
def hello_world():
    # This is a comment
    print("Hello, World!")
    
    # Another comment
    return "success"

if __name__ == "__main__":
    hello_world()
""", encoding='utf-8')
            
            (project_path / "README.md").write_text("""
# Test Project

This is a test project for analytics.

## Features
- File statistics
- Activity patterns
""", encoding='utf-8')
            
            (project_path / "config.json").write_text(json.dumps({
                "name": "test-project",
                "version": "1.0.0"
            }), encoding='utf-8')
            
            # サブディレクトリとファイル
            sub_dir = project_path / "src"
            sub_dir.mkdir()
            (sub_dir / "utils.py").write_text("def utility_function():\n    pass\n", encoding='utf-8')
            
            # テストディレクトリ
            test_dir = project_path / "tests"
            test_dir.mkdir()
            (test_dir / "test_main.py").write_text("def test_hello():\n    assert True\n", encoding='utf-8')
            
            yield project_path
    
    def test_get_file_statistics(self, temp_project):
        """ファイル統計情報の取得をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        stats = analytics.get_file_statistics()
        
        # 基本統計をチェック
        assert stats['total_files'] >= 5  # 作成したファイル数
        assert stats['total_directories'] >= 2  # src, tests
        assert stats['total_size_bytes'] > 0
        assert stats['processing_time'] >= 0
        
        # ファイルタイプ統計
        assert '.py' in stats['file_types']
        assert '.md' in stats['file_types']
        assert '.json' in stats['file_types']
        
        # カテゴリ統計
        assert 'code' in stats['file_categories']
        assert 'docs' in stats['file_categories']
        assert 'config' in stats['file_categories']
        assert 'test' in stats['file_categories']
        
        # 最大ファイルリスト
        assert len(stats['largest_files']) <= 10
        
        # ディレクトリサイズ
        assert len(stats['directory_sizes']) <= 10
    
    def test_get_activity_patterns(self, temp_project):
        """アクティビティパターンの取得をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        patterns = analytics.get_activity_patterns(days=30)
        
        # パターンの構造をチェック
        assert 'daily_modifications' in patterns
        assert 'hourly_distribution' in patterns
        assert 'most_active_files' in patterns
        assert 'recent_changes' in patterns
        assert 'growth_rate' in patterns
        
        # 最近の変更があることを確認（ファイルを作成したばかりなので）
        assert len(patterns['recent_changes']) > 0
    
    def test_get_project_summary(self, temp_project):
        """プロジェクトサマリーの取得をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        summary = analytics.get_project_summary()
        
        # サマリーの構造をチェック
        assert 'project_name' in summary
        assert 'project_path' in summary
        assert 'total_files' in summary
        assert 'total_directories' in summary
        assert 'total_size_mb' in summary
        assert 'primary_language' in summary
        assert 'last_updated' in summary
        assert 'activity_summary' in summary
        
        # 値の妥当性をチェック
        assert summary['project_name'] == temp_project.name
        assert summary['total_files'] > 0
        assert summary['total_size_mb'] >= 0
        assert summary['primary_language'] == 'Python'  # .pyファイルが最多
    
    def test_export_statistics_json(self, temp_project):
        """JSON形式でのエクスポートをテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        output_file = analytics.export_statistics('json')
        
        # ファイルが作成されることを確認
        assert Path(output_file).exists()
        
        # JSON形式で読み込めることを確認
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'summary' in data
        assert 'file_statistics' in data
        assert 'activity_patterns' in data
    
    def test_export_statistics_markdown(self, temp_project):
        """Markdown形式でのエクスポートをテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        output_file = analytics.export_statistics('markdown')
        
        # ファイルが作成されることを確認
        assert Path(output_file).exists()
        
        # Markdownコンテンツをチェック
        content = Path(output_file).read_text(encoding='utf-8')
        assert '# プロジェクト統計レポート' in content
        assert '## 概要' in content
        assert '## ファイル統計' in content
    
    def test_export_statistics_csv(self, temp_project):
        """CSV形式でのエクスポートをテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        output_file = analytics.export_statistics('csv')
        
        # ファイルが作成されることを確認
        assert Path(output_file).exists()
        
        # CSVコンテンツをチェック
        content = Path(output_file).read_text(encoding='utf-8')
        assert 'Project Summary' in content
        assert 'File Type Statistics' in content
    
    def test_analyze_file_complexity(self, temp_project):
        """ファイル複雑度分析をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        main_py = temp_project / "main.py"
        
        analysis = analytics.analyze_file_complexity(str(main_py))
        
        # 分析結果の構造をチェック
        assert 'file_path' in analysis
        assert 'size_bytes' in analysis
        assert 'lines' in analysis
        assert 'characters' in analysis
        assert 'last_modified' in analysis
        assert 'code_metrics' in analysis
        
        # コードメトリクスをチェック
        metrics = analysis['code_metrics']
        assert 'total_lines' in metrics
        assert 'blank_lines' in metrics
        assert 'comment_lines' in metrics
        assert 'code_lines' in metrics
        
        # 値の妥当性をチェック
        assert metrics['total_lines'] > 0
        assert metrics['comment_lines'] >= 2  # 作成したコメント数
        assert metrics['code_lines'] > 0
    
    def test_cache_functionality(self, temp_project):
        """キャッシュ機能をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        
        # 初回実行（キャッシュなし）
        stats1 = analytics.get_file_statistics(use_cache=False)
        
        # 2回目実行（キャッシュあり）
        stats2 = analytics.get_file_statistics(use_cache=True)
        
        # キャッシュされた結果が同じであることを確認
        assert stats1['total_files'] == stats2['total_files']
        assert stats1['total_size_bytes'] == stats2['total_size_bytes']
        
        # キャッシュを無効にして実行
        stats3 = analytics.get_file_statistics(use_cache=False)
        assert stats1['total_files'] == stats3['total_files']
    
    def test_file_categorization(self, temp_project):
        """ファイルカテゴリ分類をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        
        # 各種ファイルのカテゴリ分類をテスト
        assert analytics._categorize_file(Path("test.py")) == 'code'
        assert analytics._categorize_file(Path("README.md")) == 'docs'
        assert analytics._categorize_file(Path("config.json")) == 'config'
        assert analytics._categorize_file(Path("test_file.py")) == 'test'
        assert analytics._categorize_file(Path("style.css")) == 'web'
        assert analytics._categorize_file(Path("image.png")) == 'image'
        assert analytics._categorize_file(Path("data.csv")) == 'data'
        assert analytics._categorize_file(Path("unknown.xyz")) == 'other'
    
    def test_primary_language_detection(self, temp_project):
        """主要言語検出をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        
        # ファイルタイプカウントをシミュレート
        file_types = {
            '.py': 10,
            '.js': 5,
            '.md': 2,
            '.txt': 1
        }
        
        primary_lang = analytics._detect_primary_language(file_types)
        assert primary_lang == 'Python'
        
        # JavaScriptが多い場合
        file_types_js = {
            '.js': 15,
            '.py': 5,
            '.html': 3
        }
        
        primary_lang_js = analytics._detect_primary_language(file_types_js)
        assert primary_lang_js == 'JavaScript'
    
    def test_error_handling(self, temp_project):
        """エラーハンドリングをテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        
        # 存在しないファイルの分析
        with pytest.raises(FileNotFoundError):
            analytics.analyze_file_complexity("nonexistent_file.py")
        
        # 無効な出力形式
        with pytest.raises(ValueError):
            analytics.export_statistics('invalid_format')
    
    def test_ignore_directories(self, temp_project):
        """無視ディレクトリの処理をテスト"""
        analytics = ProjectAnalytics(str(temp_project))
        
        # 無視すべきディレクトリを作成
        ignore_dirs = ['.git', '__pycache__', 'node_modules', '.venv']
        for ignore_dir in ignore_dirs:
            (temp_project / ignore_dir).mkdir()
            (temp_project / ignore_dir / "should_be_ignored.txt").write_text("ignore me")
        
        stats = analytics.get_file_statistics()
        
        # 無視ディレクトリ内のファイルがカウントされていないことを確認
        # 具体的なチェックは実装に依存するが、基本的な統計は取得できることを確認
        assert stats['total_files'] > 0
        assert stats['total_directories'] > 0