"""
プロジェクト統計情報API - ツール非依存の分析機能
Project Analytics API - Tool-independent analysis functionality
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import time
import mimetypes


class ProjectAnalytics:
    """
    プロジェクト統計情報を収集・分析するAPIクラス
    ツール非依存でプロジェクトの各種メトリクスを提供
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """
        統計分析APIを初期化
        
        Args:
            project_path: プロジェクトパス（デフォルト: 現在のディレクトリ）
        """
        self.project_path = Path(project_path or os.getcwd())
        self.cache = {}
        self.cache_ttl = 300  # 5分間のキャッシュ
        
        # 無視するディレクトリのパターン
        self.ignore_dirs = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'env', 'dist', 'build', '.pytest_cache', '.tox',
            'htmlcov', '.coverage', '*.egg-info', '.mypy_cache'
        }
        
        # ファイルタイプの分類
        self.file_categories = {
            'code': {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', 
                    '.h', '.hpp', '.cs', '.rb', '.go', '.rs', '.swift', '.kt'},
            'docs': {'.md', '.rst', '.txt', '.doc', '.docx', '.pdf'},
            'config': {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.env'},
            'data': {'.csv', '.tsv', '.xls', '.xlsx', '.db', '.sqlite'},
            'web': {'.html', '.css', '.scss', '.sass', '.less'},
            'image': {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'},
            'test': {'.test.py', '.spec.js', '_test.py', '_test.go'}
        }
    
    def get_file_statistics(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        ファイル統計情報を取得
        
        Args:
            use_cache: キャッシュを使用するか
            
        Returns:
            Dict: ファイル統計情報
        """
        cache_key = 'file_statistics'
        if use_cache and self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        start_time = time.time()
        stats = {
            'total_files': 0,
            'total_directories': 0,
            'total_size_bytes': 0,
            'file_types': defaultdict(int),
            'file_categories': defaultdict(int),
            'largest_files': [],
            'directory_sizes': {},
            'processing_time': 0
        }
        
        # ファイルをスキャン
        file_sizes = []
        for path in self._walk_project():
            if path.is_file():
                stats['total_files'] += 1
                size = path.stat().st_size
                stats['total_size_bytes'] += size
                
                # ファイルタイプ統計
                ext = path.suffix.lower()
                stats['file_types'][ext] += 1
                
                # カテゴリ分類
                category = self._categorize_file(path)
                stats['file_categories'][category] += 1
                
                # サイズ情報を保存
                file_sizes.append((str(path.relative_to(self.project_path)), size))
                
            elif path.is_dir():
                stats['total_directories'] += 1
        
        # 最大ファイルを特定
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = [
            {'path': path, 'size': size} 
            for path, size in file_sizes[:10]
        ]
        
        # ディレクトリサイズを計算
        stats['directory_sizes'] = self._calculate_directory_sizes()
        
        # 処理時間
        stats['processing_time'] = time.time() - start_time
        
        # キャッシュに保存
        self._set_cache(cache_key, stats)
        
        return stats
    
    def get_activity_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        プロジェクトのアクティビティパターンを分析
        
        Args:
            days: 分析対象の日数
            
        Returns:
            Dict: アクティビティパターン情報
        """
        cache_key = f'activity_patterns_{days}'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        patterns = {
            'daily_modifications': defaultdict(int),
            'hourly_distribution': defaultdict(int),
            'most_active_files': [],
            'recent_changes': [],
            'growth_rate': {}
        }
        
        cutoff_time = datetime.now() - timedelta(days=days)
        file_modifications = []
        
        # ファイルの変更時刻を収集
        for path in self._walk_project():
            if path.is_file():
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                if mtime >= cutoff_time:
                    date_key = mtime.strftime('%Y-%m-%d')
                    hour_key = mtime.hour
                    
                    patterns['daily_modifications'][date_key] += 1
                    patterns['hourly_distribution'][hour_key] += 1
                    
                    file_modifications.append({
                        'path': str(path.relative_to(self.project_path)),
                        'modified': mtime.isoformat(),
                        'size': path.stat().st_size
                    })
        
        # 最も活発なファイル
        file_mod_count = Counter(fm['path'] for fm in file_modifications)
        patterns['most_active_files'] = [
            {'path': path, 'modifications': count}
            for path, count in file_mod_count.most_common(10)
        ]
        
        # 最近の変更
        file_modifications.sort(key=lambda x: x['modified'], reverse=True)
        patterns['recent_changes'] = file_modifications[:20]
        
        # 成長率計算
        if patterns['daily_modifications']:
            dates = sorted(patterns['daily_modifications'].keys())
            if len(dates) >= 2:
                first_week = sum(patterns['daily_modifications'][d] 
                               for d in dates[:7])
                last_week = sum(patterns['daily_modifications'][d] 
                              for d in dates[-7:])
                
                patterns['growth_rate'] = {
                    'weekly_change': last_week - first_week,
                    'percentage': ((last_week - first_week) / max(first_week, 1)) * 100
                }
        
        self._set_cache(cache_key, patterns)
        return patterns
    
    def get_project_summary(self) -> Dict[str, Any]:
        """
        プロジェクトの総合サマリーを取得
        
        Returns:
            Dict: プロジェクトサマリー
        """
        file_stats = self.get_file_statistics()
        activity = self.get_activity_patterns()
        
        summary = {
            'project_name': self.project_path.name,
            'project_path': str(self.project_path),
            'total_files': file_stats['total_files'],
            'total_directories': file_stats['total_directories'],
            'total_size_mb': round(file_stats['total_size_bytes'] / (1024 * 1024), 2),
            'primary_language': self._detect_primary_language(file_stats['file_types']),
            'last_updated': datetime.now().isoformat(),
            'activity_summary': {
                'recent_files_modified': len(activity['recent_changes']),
                'most_active_hour': max(activity['hourly_distribution'].items(), 
                                      key=lambda x: x[1])[0] if activity['hourly_distribution'] else None,
                'growth_trend': activity['growth_rate'].get('percentage', 0)
            }
        }
        
        return summary
    
    def export_statistics(self, format: str = 'json', output_path: Optional[str] = None) -> str:
        """
        統計情報をエクスポート
        
        Args:
            format: 出力形式 ('json', 'markdown', 'csv')
            output_path: 出力先パス
            
        Returns:
            str: 出力されたファイルパスまたはコンテンツ
        """
        stats = {
            'summary': self.get_project_summary(),
            'file_statistics': self.get_file_statistics(),
            'activity_patterns': self.get_activity_patterns()
        }
        
        if format == 'json':
            content = json.dumps(stats, indent=2, ensure_ascii=False, default=str)
            ext = '.json'
        elif format == 'markdown':
            content = self._format_as_markdown(stats)
            ext = '.md'
        elif format == 'csv':
            content = self._format_as_csv(stats)
            ext = '.csv'
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_path:
            output_file = Path(output_path)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.project_path / f'project_analytics_{timestamp}{ext}'
        
        output_file.write_text(content, encoding='utf-8')
        return str(output_file)
    
    def analyze_file_complexity(self, file_path: str) -> Dict[str, Any]:
        """
        特定ファイルの複雑度を分析
        
        Args:
            file_path: ファイルパス
            
        Returns:
            Dict: ファイル複雑度情報
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stats = {
            'file_path': str(path),
            'size_bytes': path.stat().st_size,
            'lines': 0,
            'characters': 0,
            'last_modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        }
        
        # テキストファイルの場合は行数をカウント
        if self._is_text_file(path):
            try:
                content = path.read_text(encoding='utf-8')
                stats['lines'] = len(content.splitlines())
                stats['characters'] = len(content)
                
                # コードファイルの追加分析
                if path.suffix in self.file_categories['code']:
                    stats['code_metrics'] = self._analyze_code_metrics(content, path.suffix)
                    
            except Exception:
                stats['error'] = 'Could not read file content'
        
        return stats
    
    def _walk_project(self):
        """プロジェクトディレクトリを走査"""
        for root, dirs, files in os.walk(self.project_path):
            root_path = Path(root)
            
            # 無視するディレクトリを除外
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            # ディレクトリを yield
            for dir_name in dirs:
                yield root_path / dir_name
            
            # ファイルを yield
            for file_name in files:
                yield root_path / file_name
    
    def _categorize_file(self, path: Path) -> str:
        """ファイルをカテゴリに分類"""
        ext = path.suffix.lower()

        # テストファイルの特別処理を優先
        test_patterns = self.file_categories.get('test', set())
        for pattern in test_patterns:
            if pattern in path.name:
                return 'test'

        stem_lower = path.stem.lower()
        if stem_lower.startswith('test_') or stem_lower.endswith('_test'):
            return 'test'

        for category, extensions in self.file_categories.items():
            if category == 'test':
                continue
            if ext in extensions:
                return category

        return 'other'
    
    def _calculate_directory_sizes(self) -> Dict[str, int]:
        """ディレクトリサイズを計算"""
        dir_sizes = defaultdict(int)
        
        for path in self._walk_project():
            if path.is_file():
                size = path.stat().st_size
                # 親ディレクトリすべてにサイズを追加
                current = path.parent
                while current != self.project_path.parent:
                    rel_path = str(current.relative_to(self.project_path))
                    if rel_path == '.':
                        rel_path = '/'
                    dir_sizes[rel_path] += size
                    current = current.parent
        
        # 上位10ディレクトリを返す
        sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_dirs[:10])
    
    def _detect_primary_language(self, file_types: Dict[str, int]) -> str:
        """主要なプログラミング言語を検出"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        language_counts = defaultdict(int)
        for ext, count in file_types.items():
            if ext in language_map:
                language_counts[language_map[ext]] += count
        
        if language_counts:
            return max(language_counts.items(), key=lambda x: x[1])[0]
        return 'Unknown'
    
    def _is_text_file(self, path: Path) -> bool:
        """テキストファイルかどうかを判定"""
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type and mime_type.startswith('text'):
            return True
        
        # 拡張子でチェック
        text_extensions = {'.txt', '.md', '.rst', '.log', '.csv', '.json', '.xml', '.yaml', '.yml'}
        if path.suffix.lower() in text_extensions or path.suffix.lower() in self.file_categories['code']:
            return True
        
        return False
    
    def _analyze_code_metrics(self, content: str, suffix: str) -> Dict[str, Any]:
        """コードメトリクスを分析"""
        lines = content.splitlines()
        
        metrics = {
            'total_lines': len(lines),
            'blank_lines': sum(1 for line in lines if not line.strip()),
            'comment_lines': 0,
            'code_lines': 0
        }
        
        # 簡易的なコメント検出
        comment_chars = {
            '.py': '#',
            '.js': '//',
            '.ts': '//',
            '.java': '//',
            '.cpp': '//',
            '.c': '//',
            '.rb': '#',
            '.go': '//',
            '.rs': '//',
            '.swift': '//',
            '.kt': '//'
        }
        
        comment_char = comment_chars.get(suffix, '#')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(comment_char):
                metrics['comment_lines'] += 1
            elif stripped:
                metrics['code_lines'] += 1
        
        return metrics
    
    def _format_as_markdown(self, stats: Dict[str, Any]) -> str:
        """統計情報をMarkdown形式にフォーマット"""
        summary = stats['summary']
        file_stats = stats['file_statistics']
        activity = stats['activity_patterns']
        
        md = f"""# プロジェクト統計レポート: {summary['project_name']}

## 概要
- **プロジェクトパス**: {summary['project_path']}
- **総ファイル数**: {summary['total_files']:,}
- **総ディレクトリ数**: {summary['total_directories']:,}
- **総サイズ**: {summary['total_size_mb']} MB
- **主要言語**: {summary['primary_language']}
- **最終更新**: {summary['last_updated']}

## ファイル統計

### ファイルタイプ別
| 拡張子 | ファイル数 |
|--------|-----------|
"""
        
        for ext, count in sorted(file_stats['file_types'].items(), 
                                key=lambda x: x[1], reverse=True)[:10]:
            md += f"| {ext or 'なし'} | {count:,} |\n"
        
        md += f"""
### カテゴリ別
| カテゴリ | ファイル数 |
|----------|-----------|
"""
        
        for category, count in sorted(file_stats['file_categories'].items(), 
                                    key=lambda x: x[1], reverse=True):
            md += f"| {category} | {count:,} |\n"
        
        md += f"""
### 最大ファイル
| ファイル | サイズ |
|----------|--------|
"""
        
        for file_info in file_stats['largest_files'][:5]:
            size_mb = round(file_info['size'] / (1024 * 1024), 2)
            md += f"| {file_info['path']} | {size_mb} MB |\n"
        
        md += f"""
## アクティビティパターン

### 最近の変更 ({len(activity['recent_changes'])}件)
"""
        
        for change in activity['recent_changes'][:10]:
            md += f"- {change['path']} ({change['modified']})\n"
        
        if activity['growth_rate']:
            md += f"""
### 成長率
- **週間変化**: {activity['growth_rate']['weekly_change']:+d} ファイル
- **成長率**: {activity['growth_rate']['percentage']:+.1f}%
"""
        
        return md
    
    def _format_as_csv(self, stats: Dict[str, Any]) -> str:
        """統計情報をCSV形式にフォーマット"""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # サマリー情報
        writer.writerow(['Project Summary'])
        writer.writerow(['Metric', 'Value'])
        summary = stats['summary']
        for key, value in summary.items():
            if isinstance(value, dict):
                continue
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # ファイルタイプ統計
        writer.writerow(['File Type Statistics'])
        writer.writerow(['Extension', 'Count'])
        for ext, count in stats['file_statistics']['file_types'].items():
            writer.writerow([ext or 'None', count])
        
        return output.getvalue()
    
    def _is_cache_valid(self, key: str) -> bool:
        """キャッシュが有効かチェック"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key]['timestamp']
        return (time.time() - cached_time) < self.cache_ttl
    
    def _set_cache(self, key: str, data: Any) -> None:
        """キャッシュにデータを保存"""
        self.cache[key] = {
            'timestamp': time.time(),
            'data': data
        }