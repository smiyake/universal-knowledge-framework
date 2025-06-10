"""Development Pattern Learning - 開発パターン学習・推奨システム"""

import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

from .session_tracker import SimpleGitUtils
from .session_tracker import SessionTracker


class PatternLearner:
    """開発パターン学習・推奨システム"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.patterns_dir = self.project_path / ".ukf" / "patterns"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        
        self.git_utils = SimpleGitUtils(self.project_path)
        self.session_tracker = SessionTracker(self.project_path)
        self.logger = logging.getLogger(__name__)
        
        # パターンデータベースファイル
        self.patterns_db = self.patterns_dir / "learned_patterns.json"
        self.usage_stats = self.patterns_dir / "usage_stats.json"
        
    def learn_from_sessions(self, sessions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """セッション履歴からパターン学習"""
        if sessions is None:
            sessions = self.session_tracker.list_sessions(limit=100)
        
        patterns = defaultdict(list)
        
        for session in sessions:
            if session['status'] != 'completed':
                continue
                
            session_patterns = self._extract_session_patterns(session)
            
            for pattern_type, pattern_data in session_patterns.items():
                patterns[pattern_type].extend(pattern_data)
        
        # パターン分析・統合
        learned_patterns = self._analyze_patterns(patterns)
        
        # 既存パターンとマージ
        self._merge_patterns(learned_patterns)
        
        return learned_patterns
    
    def learn_from_git_history(self, limit: int = 200) -> Dict[str, Any]:
        """Git履歴からパターン学習"""
        try:
            commits = self.git_utils.get_recent_commits(limit)
            patterns = defaultdict(list)
            
            for commit in commits:
                commit_patterns = self._extract_commit_patterns(commit)
                
                for pattern_type, pattern_data in commit_patterns.items():
                    patterns[pattern_type].extend(pattern_data)
            
            learned_patterns = self._analyze_patterns(patterns)
            self._merge_patterns(learned_patterns)
            
            return learned_patterns
            
        except Exception as e:
            self.logger.error(f"Git履歴学習エラー: {e}")
            return {}
    
    def learn_from_codebase(self) -> Dict[str, Any]:
        """コードベース構造からパターン学習"""
        patterns = defaultdict(list)
        
        # ファイル構造パターン
        file_patterns = self._analyze_file_structure()
        patterns["file_structure"].extend(file_patterns)
        
        # コーディングパターン
        coding_patterns = self._analyze_code_patterns()
        patterns["coding_style"].extend(coding_patterns)
        
        # 設定パターン
        config_patterns = self._analyze_config_patterns()
        patterns["configuration"].extend(config_patterns)
        
        learned_patterns = self._analyze_patterns(patterns)
        self._merge_patterns(learned_patterns)
        
        return learned_patterns
    
    def get_recommendations(self, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """開発パターン推奨"""
        patterns_data = self._load_patterns()
        if not patterns_data:
            return []
        
        context = context or self._get_current_context()
        recommendations = []
        
        for pattern_id, pattern in patterns_data.items():
            relevance_score = self._calculate_relevance(pattern, context)
            
            if relevance_score > 0.3:  # 閾値
                recommendations.append({
                    "pattern_id": pattern_id,
                    "name": pattern["name"],
                    "description": pattern["description"],
                    "relevance_score": relevance_score,
                    "usage_count": pattern.get("usage_count", 0),
                    "last_used": pattern.get("last_used"),
                    "tags": pattern.get("tags", []),
                    "examples": pattern.get("examples", [])[:3]  # 最大3例
                })
        
        # スコア順でソート
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return recommendations[:10]  # 上位10件
    
    def track_pattern_usage(self, pattern_id: str, context: Dict[str, Any] = None):
        """パターン使用履歴記録"""
        usage_data = self._load_usage_stats()
        
        if pattern_id not in usage_data:
            usage_data[pattern_id] = {
                "usage_count": 0,
                "first_used": datetime.now(timezone.utc).isoformat(),
                "contexts": []
            }
        
        usage_data[pattern_id]["usage_count"] += 1
        usage_data[pattern_id]["last_used"] = datetime.now(timezone.utc).isoformat()
        
        if context:
            usage_data[pattern_id]["contexts"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context
            })
            
            # 最新50件のみ保持
            if len(usage_data[pattern_id]["contexts"]) > 50:
                usage_data[pattern_id]["contexts"] = usage_data[pattern_id]["contexts"][-50:]
        
        self._save_usage_stats(usage_data)
        
        # パターンデータベースの使用カウントも更新
        patterns_data = self._load_patterns()
        if pattern_id in patterns_data:
            patterns_data[pattern_id]["usage_count"] = usage_data[pattern_id]["usage_count"]
            patterns_data[pattern_id]["last_used"] = usage_data[pattern_id]["last_used"]
            self._save_patterns(patterns_data)
    
    def get_pattern_analytics(self) -> Dict[str, Any]:
        """パターン分析データ取得"""
        patterns_data = self._load_patterns()
        usage_data = self._load_usage_stats()
        
        if not patterns_data:
            return {"total_patterns": 0, "analytics": {}}
        
        analytics = {
            "total_patterns": len(patterns_data),
            "by_category": defaultdict(int),
            "most_used": [],
            "recent_patterns": [],
            "usage_trends": {}
        }
        
        # カテゴリ別集計
        for pattern in patterns_data.values():
            category = pattern.get("category", "unknown")
            analytics["by_category"][category] += 1
        
        # 使用頻度順
        pattern_usage = [(pid, p.get("usage_count", 0)) for pid, p in patterns_data.items()]
        pattern_usage.sort(key=lambda x: x[1], reverse=True)
        analytics["most_used"] = pattern_usage[:10]
        
        # 最近のパターン
        recent_patterns = [(pid, p) for pid, p in patterns_data.items() if p.get("created_at")]
        recent_patterns.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)
        analytics["recent_patterns"] = [(pid, p["name"]) for pid, p in recent_patterns[:10]]
        
        return analytics
    
    def _extract_session_patterns(self, session: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """セッションからパターン抽出"""
        patterns = defaultdict(list)
        
        # セッションタイプパターン
        session_type = session.get("type", "unknown")
        patterns["session_workflow"].append({
            "name": f"{session_type}_workflow",
            "description": f"{session_type}セッションワークフロー",
            "category": "workflow",
            "session_data": {
                "type": session_type,
                "duration": self._calculate_session_duration(session),
                "files_modified": len(session.get("files_modified", [])),
                "commits": len(session.get("commits", [])),
                "milestones": len(session.get("milestones", []))
            }
        })
        
        # ファイル変更パターン
        modified_files = session.get("files_modified", [])
        if modified_files:
            file_pattern = self._analyze_file_change_pattern(modified_files)
            patterns["file_changes"].append(file_pattern)
        
        # コミットパターン
        commits = session.get("commits", [])
        if commits:
            commit_pattern = self._analyze_commit_pattern(commits)
            patterns["commit_style"].append(commit_pattern)
        
        return patterns
    
    def _extract_commit_patterns(self, commit: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """コミットからパターン抽出"""
        patterns = defaultdict(list)
        
        message = commit.get("message", "")
        files = commit.get("files", [])
        
        # コミットメッセージパターン
        message_pattern = self._analyze_commit_message(message)
        if message_pattern:
            patterns["commit_message"].append(message_pattern)
        
        # ファイル変更パターン
        if files:
            file_pattern = self._analyze_file_change_pattern(files)
            patterns["file_changes"].append(file_pattern)
        
        return patterns
    
    def _analyze_file_structure(self) -> List[Dict[str, Any]]:
        """ファイル構造分析"""
        patterns = []
        
        # ディレクトリ構造パターン
        dir_structure = defaultdict(int)
        file_extensions = Counter()
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and not str(file_path).startswith('.'):
                # ディレクトリレベル
                depth = len(file_path.relative_to(self.project_path).parts) - 1
                dir_structure[depth] += 1
                
                # 拡張子
                if file_path.suffix:
                    file_extensions[file_path.suffix.lower()] += 1
        
        patterns.append({
            "name": "directory_structure",
            "description": "プロジェクトディレクトリ構造",
            "category": "file_structure",
            "data": {
                "depth_distribution": dict(dir_structure),
                "file_extensions": dict(file_extensions.most_common(10))
            }
        })
        
        return patterns
    
    def _analyze_code_patterns(self) -> List[Dict[str, Any]]:
        """コードパターン分析"""
        patterns = []
        
        # Python コードパターン（例）
        python_files = list(self.project_path.rglob("*.py"))
        if python_files:
            python_patterns = self._analyze_python_patterns(python_files[:20])  # サンプル
            patterns.extend(python_patterns)
        
        return patterns
    
    def _analyze_python_patterns(self, python_files: List[Path]) -> List[Dict[str, Any]]:
        """Pythonコードパターン分析"""
        patterns = []
        import_patterns = Counter()
        class_patterns = []
        function_patterns = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # import文パターン
                imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+(\S+)', content, re.MULTILINE)
                for imp in imports:
                    import_patterns[imp.split('.')[0]] += 1
                
                # クラス定義パターン
                classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                class_patterns.extend(classes)
                
                # 関数定義パターン
                functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                function_patterns.extend(functions)
                
            except Exception:
                continue
        
        if import_patterns:
            patterns.append({
                "name": "python_imports",
                "description": "Python import パターン",
                "category": "coding_style",
                "data": {
                    "common_imports": dict(import_patterns.most_common(10)),
                    "class_naming": self._analyze_naming_pattern(class_patterns),
                    "function_naming": self._analyze_naming_pattern(function_patterns)
                }
            })
        
        return patterns
    
    def _analyze_config_patterns(self) -> List[Dict[str, Any]]:
        """設定ファイルパターン分析"""
        patterns = []
        
        config_files = {
            "package.json": "nodejs",
            "requirements.txt": "python",
            "Cargo.toml": "rust",
            "pom.xml": "java",
            "pyproject.toml": "python",
            "Dockerfile": "docker"
        }
        
        found_configs = {}
        for config_file, tech in config_files.items():
            config_path = self.project_path / config_file
            if config_path.exists():
                found_configs[tech] = config_file
        
        if found_configs:
            patterns.append({
                "name": "project_technologies",
                "description": "プロジェクト技術スタック",
                "category": "configuration",
                "data": {
                    "technologies": found_configs,
                    "tech_stack": list(found_configs.keys())
                }
            })
        
        return patterns
    
    def _analyze_patterns(self, raw_patterns: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """パターン分析・統合"""
        analyzed_patterns = {}
        
        for pattern_type, pattern_list in raw_patterns.items():
            if not pattern_list:
                continue
            
            # 類似パターンを統合
            merged_patterns = self._merge_similar_patterns(pattern_list)
            
            for i, pattern in enumerate(merged_patterns):
                pattern_id = f"{pattern_type}_{i}"
                
                analyzed_patterns[pattern_id] = {
                    "name": pattern.get("name", pattern_id),
                    "description": pattern.get("description", ""),
                    "category": pattern.get("category", pattern_type),
                    "pattern_type": pattern_type,
                    "confidence": pattern.get("confidence", 0.5),
                    "frequency": pattern.get("frequency", 1),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "tags": pattern.get("tags", []),
                    "data": pattern.get("data", {}),
                    "usage_count": 0
                }
        
        return analyzed_patterns
    
    def _merge_similar_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """類似パターン統合"""
        if len(patterns) <= 1:
            return patterns
        
        # 簡単な類似性チェック（名前ベース）
        merged = []
        used_indices = set()
        
        for i, pattern in enumerate(patterns):
            if i in used_indices:
                continue
                
            similar_patterns = [pattern]
            pattern_name = pattern.get("name", "")
            
            for j, other_pattern in enumerate(patterns[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                other_name = other_pattern.get("name", "")
                
                # 名前の類似性チェック（簡易版）
                if self._calculate_similarity(pattern_name, other_name) > 0.7:
                    similar_patterns.append(other_pattern)
                    used_indices.add(j)
            
            # 統合されたパターン作成
            merged_pattern = self._create_merged_pattern(similar_patterns)
            merged.append(merged_pattern)
            used_indices.add(i)
        
        return merged
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """文字列類似度計算（簡易版）"""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard係数による類似度
        set1 = set(str1.lower().split('_'))
        set2 = set(str2.lower().split('_'))
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _create_merged_pattern(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """統合パターン作成"""
        base_pattern = patterns[0].copy()
        base_pattern["frequency"] = len(patterns)
        base_pattern["confidence"] = min(1.0, base_pattern.get("confidence", 0.5) + (len(patterns) - 1) * 0.1)
        
        # データ統合
        if "data" in base_pattern and isinstance(base_pattern["data"], dict):
            for pattern in patterns[1:]:
                if "data" in pattern and isinstance(pattern["data"], dict):
                    # 数値データは平均値を取る
                    for key, value in pattern["data"].items():
                        if isinstance(value, (int, float)) and key in base_pattern["data"]:
                            base_pattern["data"][key] = (base_pattern["data"][key] + value) / 2
        
        return base_pattern
    
    def _analyze_file_change_pattern(self, files: List[str]) -> Dict[str, Any]:
        """ファイル変更パターン分析"""
        file_types = Counter()
        directories = Counter()
        
        for file_path in files:
            path_obj = Path(file_path)
            
            # 拡張子
            if path_obj.suffix:
                file_types[path_obj.suffix.lower()] += 1
            
            # ディレクトリ
            if len(path_obj.parts) > 1:
                directories[path_obj.parts[0]] += 1
        
        return {
            "name": "file_change_pattern",
            "description": "ファイル変更パターン",
            "category": "file_changes",
            "data": {
                "file_types": dict(file_types),
                "directories": dict(directories),
                "total_files": len(files)
            }
        }
    
    def _analyze_commit_pattern(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コミットパターン分析"""
        message_prefixes = Counter()
        
        for commit in commits:
            message = commit.get("message", "")
            
            # プリフィックス抽出（feat:, fix:, docs: など）
            prefix_match = re.match(r'^(\w+):', message)
            if prefix_match:
                message_prefixes[prefix_match.group(1)] += 1
        
        return {
            "name": "commit_pattern",
            "description": "コミットメッセージパターン",
            "category": "commit_style",
            "data": {
                "message_prefixes": dict(message_prefixes),
                "total_commits": len(commits)
            }
        }
    
    def _analyze_commit_message(self, message: str) -> Optional[Dict[str, Any]]:
        """コミットメッセージ分析"""
        if not message:
            return None
        
        # 基本的なパターン分析
        patterns = {
            "conventional": bool(re.match(r'^(feat|fix|docs|style|refactor|test|chore):', message)),
            "has_emoji": bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message)),
            "length": len(message),
            "has_body": '\n' in message
        }
        
        return {
            "name": "commit_message_style",
            "description": "コミットメッセージスタイル",
            "category": "commit_style",
            "data": patterns
        }
    
    def _analyze_naming_pattern(self, names: List[str]) -> Dict[str, Any]:
        """命名パターン分析"""
        if not names:
            return {}
        
        patterns = {
            "snake_case": sum(1 for name in names if '_' in name and name.islower()),
            "camel_case": sum(1 for name in names if any(c.isupper() for c in name[1:]) and '_' not in name),
            "pascal_case": sum(1 for name in names if name[0].isupper() and any(c.isupper() for c in name[1:])),
            "average_length": sum(len(name) for name in names) / len(names),
            "total_count": len(names)
        }
        
        return patterns
    
    def _calculate_session_duration(self, session: Dict[str, Any]) -> int:
        """セッション時間計算（分）"""
        start_time = session.get("start_time")
        end_time = session.get("end_time")
        
        if not start_time or not end_time:
            return 0
        
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = (end_dt - start_dt).total_seconds() / 60
            return int(duration)
        except Exception:
            return 0
    
    def _get_current_context(self) -> Dict[str, Any]:
        """現在の開発コンテキスト取得"""
        context = {
            "project_path": str(self.project_path),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Git状態
            context["git_branch"] = self.git_utils.get_current_branch()
            context["modified_files"] = self.git_utils.get_modified_files()
            
            # アクティブセッション
            active_sessions = self.session_tracker.get_active_sessions()
            if active_sessions:
                context["active_session"] = active_sessions[0]["type"]
        except Exception:
            pass
        
        return context
    
    def _calculate_relevance(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> float:
        """パターン関連度計算"""
        relevance = 0.0
        
        # 使用頻度
        usage_count = pattern.get("usage_count", 0)
        relevance += min(0.3, usage_count * 0.01)
        
        # 最近の使用
        last_used = pattern.get("last_used")
        if last_used:
            try:
                last_used_dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - last_used_dt).days
                relevance += max(0, 0.2 - days_ago * 0.01)
            except Exception:
                pass
        
        # カテゴリマッチ
        active_session = context.get("active_session")
        if active_session and pattern.get("category") == active_session:
            relevance += 0.3
        
        # Git状態マッチ
        if context.get("modified_files") and pattern.get("pattern_type") == "file_changes":
            relevance += 0.2
        
        # 基本スコア
        relevance += pattern.get("confidence", 0.5) * 0.2
        
        return min(1.0, relevance)
    
    def _load_patterns(self) -> Dict[str, Dict[str, Any]]:
        """パターンデータベース読み込み"""
        if not self.patterns_db.exists():
            return {}
        
        try:
            with open(self.patterns_db, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"パターン読み込みエラー: {e}")
            return {}
    
    def _save_patterns(self, patterns: Dict[str, Dict[str, Any]]):
        """パターンデータベース保存"""
        try:
            with open(self.patterns_db, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"パターン保存エラー: {e}")
    
    def _merge_patterns(self, new_patterns: Dict[str, Dict[str, Any]]):
        """既存パターンとマージ"""
        existing_patterns = self._load_patterns()
        
        for pattern_id, pattern_data in new_patterns.items():
            if pattern_id in existing_patterns:
                # 既存パターンを更新
                existing_patterns[pattern_id]["frequency"] = existing_patterns[pattern_id].get("frequency", 1) + 1
                existing_patterns[pattern_id]["confidence"] = min(1.0, existing_patterns[pattern_id]["confidence"] + 0.1)
                existing_patterns[pattern_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
            else:
                # 新規パターン追加
                existing_patterns[pattern_id] = pattern_data
        
        self._save_patterns(existing_patterns)
    
    def _load_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """使用統計読み込み"""
        if not self.usage_stats.exists():
            return {}
        
        try:
            with open(self.usage_stats, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"使用統計読み込みエラー: {e}")
            return {}
    
    def _save_usage_stats(self, stats: Dict[str, Dict[str, Any]]):
        """使用統計保存"""
        try:
            with open(self.usage_stats, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"使用統計保存エラー: {e}")