#!/usr/bin/env python3
"""
知識圧縮モジュール - プロジェクト知識を圧縮・要約

Claude Codeのトークン使用量を削減するため、プロジェクト情報を効率的に圧縮します。
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import yaml


class KnowledgeCompressor:
    """プロジェクト知識を圧縮・要約するクラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        self.config = self._load_config(config_path)
        self.ignored_patterns = self._get_ignored_patterns()
    
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """設定ファイルを読み込み"""
        default_config = {
            "knowledge_compression": {
                "output_file": "PROJECT_KNOWLEDGE_MAP.md",
                "max_tokens": 5000,
                "update_frequency": "on_commit",
                "sections": [
                    {
                        "name": "current_state",
                        "sources": ["logs", "test_results", "docker_status"]
                    },
                    {
                        "name": "architecture",
                        "sources": ["src/", "docs/"]
                    },
                    {
                        "name": "tasks",
                        "sources": [".claude-task-cache.json", "TODO.md"]
                    }
                ],
                "claude_code_optimization": {
                    "enabled": True,
                    "priority_order": [
                        "errors_and_issues",
                        "current_tasks",
                        "recent_changes",
                        "architecture_summary"
                    ]
                }
            }
        }
        
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
                
                # マージ
                return {**default_config, **user_config}
        
        return default_config
    
    def _get_ignored_patterns(self) -> Set[str]:
        """無視するパターンを取得"""
        patterns = {
            '__pycache__', '.git', '.pytest_cache', 'node_modules',
            'venv', '.venv', 'env', '.env', '.mypy_cache',
            '*.pyc', '*.pyo', '.DS_Store', 'Thumbs.db'
        }
        return patterns
    
    def compress_project(self, 
                        project_path: Path,
                        max_tokens: int = 5000,
                        format: str = "claude-code") -> str:
        """プロジェクト全体を分析して圧縮された知識マップを生成
        
        Args:
            project_path: プロジェクトパス
            max_tokens: 最大トークン数
            format: 出力フォーマット
            
        Returns:
            圧縮された知識マップ
        """
        # プロジェクト分析
        state = self.analyze_project_state(project_path)
        
        # 重要度でフィルタリング
        filtered = self.filter_by_importance(state, max_tokens)
        
        # フォーマット別に出力
        if format == "claude-code":
            return self.format_for_claude_code(filtered)
        elif format == "mindmap":
            return self.format_as_mindmap(filtered)
        else:
            return self.format_as_markdown(filtered)
    
    def analyze_project_state(self, project_path: Path) -> Dict:
        """プロジェクトの現在状態を分析
        
        Returns:
            プロジェクト状態の辞書
        """
        state = {
            "project_info": self._get_project_info(project_path),
            "current_errors": self._find_current_errors(project_path),
            "architecture": self._analyze_architecture(project_path),
            "recent_changes": self._get_recent_changes(project_path),
            "tasks": self._get_current_tasks(project_path),
            "dependencies": self._analyze_dependencies(project_path),
            "test_status": self._get_test_status(project_path),
            "docker_status": self._get_docker_status(project_path)
        }
        
        return state
    
    def _get_project_info(self, project_path: Path) -> Dict:
        """プロジェクト基本情報を取得"""
        info = {
            "name": project_path.name,
            "path": str(project_path),
            "type": self._detect_project_type(project_path)
        }
        
        # README/CLAUDE.mdから情報抽出
        for readme_name in ['CLAUDE.md', 'README.md', 'readme.md']:
            readme_path = project_path / readme_name
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # 最初の1000文字
                    # プロジェクト概要を抽出
                    if '概要' in content or 'Overview' in content:
                        info['description'] = self._extract_description(content)
                    break
        
        return info
    
    def _detect_project_type(self, project_path: Path) -> str:
        """プロジェクトタイプを検出"""
        # ファイルパターンでプロジェクトタイプを判定
        if (project_path / 'package.json').exists():
            return 'node/javascript'
        elif (project_path / 'requirements.txt').exists() or (project_path / 'pyproject.toml').exists():
            return 'python'
        elif (project_path / 'go.mod').exists():
            return 'go'
        elif (project_path / 'Cargo.toml').exists():
            return 'rust'
        elif (project_path / 'pom.xml').exists():
            return 'java/maven'
        else:
            return 'unknown'
    
    def _extract_description(self, content: str) -> str:
        """READMEから説明を抽出"""
        lines = content.split('\n')
        description_lines = []
        in_description = False
        
        for line in lines:
            if '概要' in line or 'Overview' in line:
                in_description = True
                continue
            elif in_description and line.startswith('#'):
                break
            elif in_description and line.strip():
                description_lines.append(line.strip())
        
        return ' '.join(description_lines[:3])  # 最初の3行
    
    def _find_current_errors(self, project_path: Path) -> List[Dict]:
        """現在のエラー・問題を検出"""
        errors = []
        
        # ログファイルからエラーを抽出
        log_patterns = ['*.log', 'logs/*.log', 'test-reports/*.txt']
        for pattern in log_patterns:
            for log_file in project_path.glob(pattern):
                if log_file.is_file():
                    errors.extend(self._extract_errors_from_file(log_file))
        
        # Dockerコンテナのステータス確認
        docker_errors = self._check_docker_errors()
        errors.extend(docker_errors)
        
        # 最新のエラーのみ保持（重複排除）
        unique_errors = []
        seen = set()
        for error in sorted(errors, key=lambda x: x.get('timestamp', ''), reverse=True):
            key = (error['type'], error['message'][:50])
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
                if len(unique_errors) >= 10:  # 最大10個
                    break
        
        return unique_errors
    
    def _extract_errors_from_file(self, file_path: Path) -> List[Dict]:
        """ファイルからエラーを抽出"""
        errors = []
        error_keywords = ['ERROR', 'FAILED', 'Exception', 'Error:', 'fail']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-100:]  # 最後の100行
                
                for i, line in enumerate(lines):
                    for keyword in error_keywords:
                        if keyword in line:
                            errors.append({
                                'type': keyword,
                                'file': file_path.name,
                                'line': i + 1,
                                'message': line.strip()[:200],
                                'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                            break
        except Exception:
            pass
        
        return errors
    
    def _check_docker_errors(self) -> List[Dict]:
        """Dockerコンテナのエラーをチェック"""
        errors = []
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) == 2:
                            name, status = parts
                            if 'Exited' in status or 'Error' in status:
                                errors.append({
                                    'type': 'Docker',
                                    'container': name,
                                    'message': f"Container {name} is not running: {status}",
                                    'timestamp': datetime.now().isoformat()
                                })
        except Exception:
            pass
        
        return errors
    
    def _analyze_architecture(self, project_path: Path) -> Dict:
        """プロジェクトアーキテクチャを分析"""
        architecture = {
            'structure': self._get_directory_structure(project_path),
            'main_files': self._find_main_files(project_path),
            'services': self._detect_services(project_path),
            'databases': self._detect_databases(project_path)
        }
        
        return architecture
    
    def _get_directory_structure(self, project_path: Path, max_depth: int = 3) -> Dict:
        """ディレクトリ構造を取得（重要部分のみ）"""
        def _build_tree(path: Path, depth: int = 0) -> Optional[Dict]:
            if depth >= max_depth:
                return None
            
            tree = {
                'name': path.name,
                'type': 'directory' if path.is_dir() else 'file',
                'children': []
            }
            
            if path.is_dir():
                # 重要なディレクトリのみ展開
                important_dirs = {'src', 'app', 'api', 'services', 'components', 'tests', 'docs'}
                
                for child in sorted(path.iterdir()):
                    # 無視パターンをスキップ
                    if any(pattern in str(child) for pattern in self.ignored_patterns):
                        continue
                    
                    if child.is_dir():
                        if child.name in important_dirs or depth < 2:
                            child_tree = _build_tree(child, depth + 1)
                            if child_tree:
                                tree['children'].append(child_tree)
                    elif depth < 2:  # 浅い階層のファイルは含める
                        tree['children'].append({
                            'name': child.name,
                            'type': 'file'
                        })
            
            return tree
        
        return _build_tree(project_path)
    
    def _find_main_files(self, project_path: Path) -> List[Dict]:
        """主要ファイルを検出"""
        main_files = []
        
        # エントリーポイントパターン
        entry_patterns = [
            'main.py', 'app.py', 'index.js', 'index.ts', 'main.go',
            'server.py', 'server.js', 'api.py', 'app.js'
        ]
        
        for pattern in entry_patterns:
            for file_path in project_path.rglob(pattern):
                if not any(ignored in str(file_path) for ignored in self.ignored_patterns):
                    main_files.append({
                        'path': str(file_path.relative_to(project_path)),
                        'type': 'entry_point',
                        'size': file_path.stat().st_size
                    })
        
        # 設定ファイル
        config_patterns = [
            'config.py', 'settings.py', 'config.json', 'config.yaml',
            '.env.example', 'docker-compose.yml', 'Makefile'
        ]
        
        for pattern in config_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.exists():
                    main_files.append({
                        'path': str(file_path.relative_to(project_path)),
                        'type': 'config',
                        'size': file_path.stat().st_size
                    })
        
        return main_files
    
    def _detect_services(self, project_path: Path) -> List[Dict]:
        """マイクロサービスやAPIを検出"""
        services = []
        
        # docker-compose.ymlから抽出
        compose_file = project_path / 'docker-compose.yml'
        if compose_file.exists():
            try:
                with open(compose_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    if content and 'services' in content:
                        for service_name, config in content['services'].items():
                            services.append({
                                'name': service_name,
                                'type': 'docker',
                                'ports': config.get('ports', [])
                            })
            except Exception:
                pass
        
        # FastAPI/Flaskアプリを検出
        for py_file in project_path.rglob('*.py'):
            if any(ignored in str(py_file) for ignored in self.ignored_patterns):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read(1000)
                    if 'FastAPI()' in content or 'Flask(__name__)' in content:
                        services.append({
                            'name': py_file.stem,
                            'type': 'api',
                            'file': str(py_file.relative_to(project_path))
                        })
            except Exception:
                pass
        
        return services
    
    def _detect_databases(self, project_path: Path) -> List[str]:
        """使用データベースを検出"""
        databases = set()
        
        # 環境変数やコンフィグから検出
        patterns = [
            ('DATABASE_URL', 'postgresql'),
            ('MONGO_URL', 'mongodb'),
            ('REDIS_URL', 'redis'),
            ('MYSQL_', 'mysql'),
            ('TIMESCALE', 'timescaledb')
        ]
        
        for file_name in ['.env', '.env.example', 'docker-compose.yml']:
            file_path = project_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern, db_type in patterns:
                            if pattern in content:
                                databases.add(db_type)
                except Exception:
                    pass
        
        return list(databases)
    
    def _get_recent_changes(self, project_path: Path) -> List[Dict]:
        """最近の変更を取得"""
        changes = []
        
        try:
            # Git logから最近のコミットを取得
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            changes.append({
                                'commit': parts[0],
                                'message': parts[1]
                            })
        except Exception:
            pass
        
        # 最近変更されたファイル
        recent_files = []
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not any(ignored in str(file_path) for ignored in self.ignored_patterns):
                try:
                    mtime = file_path.stat().st_mtime
                    if mtime > (datetime.now().timestamp() - 86400):  # 24時間以内
                        recent_files.append({
                            'path': str(file_path.relative_to(project_path)),
                            'modified': datetime.fromtimestamp(mtime).isoformat()
                        })
                except Exception:
                    pass
        
        # 最新5ファイルのみ
        recent_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            'commits': changes[:5],
            'files': recent_files[:5]
        }
    
    def _get_current_tasks(self, project_path: Path) -> List[Dict]:
        """現在のタスクを取得"""
        tasks = []
        
        # .claude-task-cache.jsonから読み込み
        cache_file = project_path / '.claude-task-cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tasks.extend(data.get('tasks', []))
            except Exception:
                pass
        
        # TODO.mdから読み込み
        todo_file = project_path / 'TODO.md'
        if todo_file.exists():
            try:
                with open(todo_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip().startswith('- [ ]'):
                            tasks.append({
                                'content': line.strip()[6:],
                                'status': 'pending',
                                'priority': 'medium'
                            })
            except Exception:
                pass
        
        return tasks
    
    def _analyze_dependencies(self, project_path: Path) -> Dict:
        """依存関係を分析"""
        deps = {}
        
        # Python
        req_file = project_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    deps['python'] = [line.strip() for line in f if line.strip() and not line.startswith('#')][:10]
            except Exception:
                pass
        
        # Node.js
        package_file = project_path / 'package.json'
        if package_file.exists():
            try:
                with open(package_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps['node'] = list(data.get('dependencies', {}).keys())[:10]
            except Exception:
                pass
        
        return deps
    
    def _get_test_status(self, project_path: Path) -> Dict:
        """テスト状態を取得"""
        status = {
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # pytest結果を探す
        for report_file in project_path.glob('**/pytest_*.xml'):
            # XMLパース（簡易版）
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'failures=' in content:
                        # 簡易的な抽出
                        pass
            except Exception:
                pass
        
        return status
    
    def _get_docker_status(self, project_path: Path) -> List[Dict]:
        """Dockerコンテナの状態を取得"""
        containers = []
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            containers.append({
                                'name': parts[0],
                                'status': parts[1],
                                'ports': parts[2] if len(parts) > 2 else ''
                            })
        except Exception:
            pass
        
        return containers
    
    def filter_by_importance(self, state: Dict, max_tokens: int) -> Dict:
        """重要度に基づいてフィルタリング
        
        Args:
            state: プロジェクト状態
            max_tokens: 最大トークン数
            
        Returns:
            フィルタリングされた状態
        """
        # Claude Code用の優先順位
        priority_config = self.config['knowledge_compression']['claude_code_optimization']['priority_order']
        
        filtered = {}
        estimated_tokens = 0
        
        # 優先順位に従って追加
        priority_mapping = {
            'errors_and_issues': 'current_errors',
            'current_tasks': 'tasks',
            'recent_changes': 'recent_changes',
            'architecture_summary': 'architecture'
        }
        
        for priority_key in priority_config:
            if priority_key in priority_mapping:
                state_key = priority_mapping[priority_key]
                if state_key in state:
                    # トークン数を推定（簡易版: 1文字 = 0.25トークン）
                    content = json.dumps(state[state_key], ensure_ascii=False)
                    tokens = len(content) * 0.25
                    
                    if estimated_tokens + tokens <= max_tokens:
                        filtered[state_key] = state[state_key]
                        estimated_tokens += tokens
        
        # 基本情報は常に含める
        filtered['project_info'] = state.get('project_info', {})
        
        return filtered
    
    def format_for_claude_code(self, state: Dict) -> str:
        """Claude Code用にフォーマット
        
        Args:
            state: フィルタリングされた状態
            
        Returns:
            Claude Code用に最適化されたMarkdown
        """
        lines = [
            "# 🧠 プロジェクト知識マップ（Claude Code用）",
            "",
            "> このファイルは、Claude Codeが効率的に開発するための「圧縮された知識ベース」です。",
            "> 全ファイルを読む代わりに、まずこのファイルを読んでください。",
            ""
        ]
        
        # プロジェクト情報
        if 'project_info' in state:
            info = state['project_info']
            lines.extend([
                "## 📍 現在地",
                "",
                "### プロジェクト概要",
                f"- **名称**: {info.get('name', 'Unknown')}",
                f"- **タイプ**: {info.get('type', 'Unknown')}",
            ])
            if 'description' in info:
                lines.append(f"- **説明**: {info['description']}")
            lines.append("")
        
        # 現在のエラー・問題
        if 'current_errors' in state and state['current_errors']:
            lines.extend([
                "### 🚨 現在の問題",
                "```yaml",
                "critical:"
            ])
            
            for error in state['current_errors'][:5]:
                lines.append(f"  - {error['type']}: {error['message'][:100]}")
            
            lines.extend(["", "```", ""])
        
        # アーキテクチャ
        if 'architecture' in state:
            arch = state['architecture']
            lines.extend([
                "## 🏗️ アーキテクチャ",
                ""
            ])
            
            # ディレクトリ構造（簡易版）
            if 'structure' in arch:
                lines.extend([
                    "### ディレクトリ構造（重要部分のみ）",
                    "```"
                ])
                lines.extend(self._format_tree(arch['structure']))
                lines.extend(["```", ""])
            
            # サービス
            if 'services' in arch and arch['services']:
                lines.extend([
                    "### 主要サービス",
                    "```yaml"
                ])
                for service in arch['services']:
                    lines.append(f"- {service['name']}: {service['type']}")
                lines.extend(["```", ""])
            
            # データベース
            if 'databases' in arch and arch['databases']:
                lines.append(f"### データベース: {', '.join(arch['databases'])}")
                lines.append("")
        
        # 現在のタスク
        if 'tasks' in state and state['tasks']:
            lines.extend([
                "## 🎯 現在のタスク",
                ""
            ])
            
            # 優先度別に分類
            high_tasks = [t for t in state['tasks'] if t.get('priority') == 'high']
            medium_tasks = [t for t in state['tasks'] if t.get('priority') == 'medium']
            
            if high_tasks:
                lines.append("### 🔴 High Priority")
                for task in high_tasks[:3]:
                    lines.append(f"- {task['content']}")
                lines.append("")
            
            if medium_tasks:
                lines.append("### 🟡 Medium Priority")
                for task in medium_tasks[:3]:
                    lines.append(f"- {task['content']}")
                lines.append("")
        
        # 最近の変更
        if 'recent_changes' in state:
            changes = state['recent_changes']
            lines.extend([
                "## 📝 最近の変更",
                ""
            ])
            
            if 'commits' in changes and changes['commits']:
                lines.append("### 最新コミット")
                for commit in changes['commits'][:3]:
                    lines.append(f"- {commit['commit']}: {commit['message']}")
                lines.append("")
            
            if 'files' in changes and changes['files']:
                lines.append("### 最近更新されたファイル")
                for file in changes['files'][:5]:
                    lines.append(f"- {file['path']} ({file['modified'][:10]})")
                lines.append("")
        
        # フッター
        lines.extend([
            "---",
            f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "次回更新: `ukf knowledge compress` で実行"
        ])
        
        return '\n'.join(lines)
    
    def _format_tree(self, tree: Dict, prefix: str = "") -> List[str]:
        """ツリー構造をフォーマット"""
        lines = []
        
        if tree['type'] == 'directory':
            lines.append(f"{prefix}{tree['name']}/")
            for i, child in enumerate(tree.get('children', [])):
                is_last = i == len(tree['children']) - 1
                child_prefix = prefix + ("└── " if is_last else "├── ")
                next_prefix = prefix + ("    " if is_last else "│   ")
                
                if child['type'] == 'directory':
                    lines.extend(self._format_tree(child, child_prefix))
                else:
                    lines.append(f"{child_prefix}{child['name']}")
        
        return lines
    
    def format_as_mindmap(self, state: Dict) -> str:
        """マインドマップ形式でフォーマット"""
        # TODO: マインドマップ形式の実装
        return "# Mind Map Format\n\nNot implemented yet."
    
    def format_as_markdown(self, state: Dict) -> str:
        """標準Markdown形式でフォーマット"""
        return self.format_for_claude_code(state)  # 暫定的に同じ形式を使用
