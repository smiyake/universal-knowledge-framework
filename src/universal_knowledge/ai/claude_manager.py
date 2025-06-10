"""Claude Context Manager - CLAUDE.md管理・最適化支援"""

import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

# Git utilities will be imported from session_tracker to avoid duplication


class ClaudeManager:
    """Claude Code連携・CLAUDE.md管理"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.claude_md_path = self.project_path / "CLAUDE.md"
        # Git utilities will be added when needed
        self.logger = logging.getLogger(__name__)
        
        # CLAUDE.mdテンプレート
        self.template_sections = {
            "project_overview": "# プロジェクト概要",
            "development_context": "# 開発コンテキスト",  
            "ai_instructions": "# AI開発指示",
            "patterns": "# 開発パターン",
            "commands": "# よく使うコマンド",
            "notes": "# 開発ノート",
            "history": "# 開発履歴"
        }
    
    def initialize_claude_md(self, force: bool = False) -> bool:
        """CLAUDE.md初期化"""
        if self.claude_md_path.exists() and not force:
            self.logger.info("CLAUDE.mdが既に存在します")
            return False
        
        # プロジェクト情報取得
        project_info = self._analyze_project_context()
        
        # テンプレート生成
        content = self._generate_initial_content(project_info)
        
        # ファイル作成
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"CLAUDE.mdを初期化しました: {self.claude_md_path}")
        return True
    
    def update_development_context(self, context: Dict[str, Any]) -> bool:
        """開発コンテキスト更新"""
        if not self.claude_md_path.exists():
            self.initialize_claude_md()
        
        content = self._read_claude_md()
        
        # 開発コンテキストセクション更新  
        context_section = self._build_context_section(context)
        content = self._update_section(content, "development_context", context_section)
        
        # ファイル書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info("開発コンテキストを更新しました")
        return True
    
    def add_development_pattern(self, pattern_name: str, pattern_description: str, 
                              example: str = "", tags: List[str] = None) -> bool:
        """開発パターン追加"""
        if not self.claude_md_path.exists():
            self.initialize_claude_md()
        
        content = self._read_claude_md()
        
        # パターンエントリ作成
        pattern_entry = self._create_pattern_entry(
            pattern_name, pattern_description, example, tags or []
        )
        
        # パターンセクションに追加
        content = self._append_to_section(content, "patterns", pattern_entry)
        
        # ファイル書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"開発パターンを追加しました: {pattern_name}")
        return True
    
    def add_command(self, command: str, description: str, usage: str = "") -> bool:
        """よく使うコマンド追加"""
        if not self.claude_md_path.exists():
            self.initialize_claude_md()
        
        content = self._read_claude_md()
        
        # コマンドエントリ作成
        command_entry = f"\n### {description}\n```bash\n{command}\n```\n"
        if usage:
            command_entry += f"\n使用例: {usage}\n"
        
        # コマンドセクションに追加
        content = self._append_to_section(content, "commands", command_entry)
        
        # ファイル書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"コマンドを追加しました: {command}")
        return True
    
    def add_development_note(self, note: str, category: str = "general") -> bool:
        """開発ノート追加"""
        if not self.claude_md_path.exists():
            self.initialize_claude_md()
        
        content = self._read_claude_md()
        
        # ノートエントリ作成
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        note_entry = f"\n## {timestamp} - {category}\n{note}\n"
        
        # ノートセクションに追加
        content = self._append_to_section(content, "notes", note_entry)
        
        # ファイル書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"開発ノートを追加しました: {category}")
        return True
    
    def log_development_history(self, session_id: str, summary: str, 
                               changes: List[str] = None) -> bool:
        """開発履歴記録"""
        if not self.claude_md_path.exists():
            self.initialize_claude_md()
        
        content = self._read_claude_md()
        
        # 履歴エントリ作成
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        history_entry = f"\n## {timestamp} - セッション {session_id}\n{summary}\n"
        
        if changes:
            history_entry += "\n変更ファイル:\n"
            for change in changes:
                history_entry += f"- {change}\n"
        
        # 履歴セクションに追加
        content = self._append_to_section(content, "history", history_entry)
        
        # ファイル書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"開発履歴を記録しました: {session_id}")
        return True
    
    def optimize_claude_md(self) -> Dict[str, Any]:
        """CLAUDE.md最適化"""
        if not self.claude_md_path.exists():
            return {"error": "CLAUDE.mdが存在しません"}
        
        content = self._read_claude_md()
        
        # 最適化処理
        optimizations = []
        
        # 1. 重複セクション削除
        content, removed_duplicates = self._remove_duplicate_sections(content)
        if removed_duplicates > 0:
            optimizations.append(f"重複セクション {removed_duplicates}件を削除")
        
        # 2. 空セクション削除
        content, removed_empty = self._remove_empty_sections(content)
        if removed_empty > 0:
            optimizations.append(f"空セクション {removed_empty}件を削除")
        
        # 3. セクション順序整理
        content = self._reorder_sections(content)
        optimizations.append("セクション順序を整理")
        
        # 4. 古い履歴のアーカイブ（100件超過時）
        content, archived_entries = self._archive_old_history(content)
        if archived_entries > 0:
            optimizations.append(f"古い履歴 {archived_entries}件をアーカイブ")
        
        # ファイル書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = {
            "optimizations": optimizations,
            "file_size_before": self.claude_md_path.stat().st_size,
            "file_size_after": len(content.encode('utf-8')),
            "sections_count": len(self._extract_sections(content))
        }
        
        self.logger.info(f"CLAUDE.mdを最適化しました: {len(optimizations)}件の最適化")
        return result
    
    def validate_claude_md(self) -> Dict[str, Any]:
        """CLAUDE.md検証"""
        if not self.claude_md_path.exists():
            return {"valid": False, "errors": ["CLAUDE.mdが存在しません"]}
        
        content = self._read_claude_md()
        errors = []
        warnings = []
        
        # 基本構造チェック
        sections = self._extract_sections(content)
        
        # 必須セクションチェック
        required_sections = ["project_overview", "development_context"]
        for section in required_sections:
            if section not in [s[0] for s in sections]:
                errors.append(f"必須セクション '{self.template_sections[section]}' が見つかりません")
        
        # セクション内容チェック
        for section_id, section_title in sections:
            if len(section_title.strip()) == 0:
                warnings.append(f"空のセクションがあります: {section_id}")
        
        # ファイルサイズチェック
        file_size = self.claude_md_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB
            warnings.append(f"ファイルサイズが大きいです: {file_size / 1024 / 1024:.1f}MB")
        
        # マークダウン構文チェック
        syntax_errors = self._check_markdown_syntax(content)
        errors.extend(syntax_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sections_count": len(sections),
            "file_size": file_size,
            "last_modified": datetime.fromtimestamp(
                self.claude_md_path.stat().st_mtime
            ).isoformat()
        }
    
    def _read_claude_md(self) -> str:
        """CLAUDE.md読み込み"""
        try:
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"CLAUDE.md読み込みエラー: {e}")
            return ""
    
    def _analyze_project_context(self) -> Dict[str, Any]:
        """プロジェクトコンテキスト分析"""
        context = {
            "name": self.project_path.name,
            "path": str(self.project_path),
            "git_info": {},
            "languages": [],
            "frameworks": [],
            "files_count": 0
        }
        
        # Git情報
        try:
            context["git_info"] = {
                "current_branch": self.git_utils.get_current_branch(),
                "remote_url": self.git_utils.get_remote_url()
            }
        except Exception:
            pass
        
        # ファイル分析
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and not str(file_path).startswith('.'):
                context["files_count"] += 1
                
                # 言語検出
                suffix = file_path.suffix.lower()
                if suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
                    lang = suffix[1:]
                    if lang not in context["languages"]:
                        context["languages"].append(lang)
        
        return context
    
    def _generate_initial_content(self, project_info: Dict[str, Any]) -> str:
        """初期コンテンツ生成"""
        lines = [
            "# CLAUDE.md - AI開発アシスタント設定",
            "",
            "このファイルはClaude Codeとの開発セッションを効率化するための設定ファイルです。",
            "",
            "# プロジェクト概要",
            f"**プロジェクト名**: {project_info['name']}",
            f"**パス**: {project_info['path']}",
            f"**ファイル数**: {project_info['files_count']}",
            "",
            "## 技術スタック",
        ]
        
        if project_info['languages']:
            lines.append(f"**言語**: {', '.join(project_info['languages'])}")
        
        if project_info['git_info'].get('current_branch'):
            lines.extend([
                "",
                "## Git情報",
                f"**ブランチ**: {project_info['git_info']['current_branch']}",
            ])
        
        lines.extend([
            "",
            "# 開発コンテキスト",
            "",
            "## 現在の開発状況",
            "プロジェクト初期化完了",
            "",
            "## 開発目標",
            "- 基本機能実装",
            "- テスト整備",
            "",
            "# AI開発指示",
            "",
            "## コーディング規約",
            "- PythonのPEP8準拠",
            "- 適切なコメント・ドキュメント記述",
            "- テストコード作成",
            "",
            "## 開発フロー",
            "1. 機能設計・実装",
            "2. テスト作成・実行",
            "3. コードレビュー",
            "4. ドキュメント更新",
            "",
            "# 開発パターン",
            "",
            "# よく使うコマンド",
            "",
            "# 開発ノート",
            "",
            "# 開発履歴",
            "",
            f"## {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} - プロジェクト初期化",
            "CLAUDE.mdファイルを作成し、AI開発環境を初期化しました。",
        ])
        
        return '\n'.join(lines)
    
    def _build_context_section(self, context: Dict[str, Any]) -> str:
        """コンテキストセクション構築"""
        lines = ["# 開発コンテキスト", ""]
        
        if context.get("current_task"):
            lines.extend([
                "## 現在のタスク",
                context["current_task"],
                ""
            ])
        
        if context.get("recent_changes"):
            lines.extend([
                "## 最近の変更",
            ])
            for change in context["recent_changes"]:
                lines.append(f"- {change}")
            lines.append("")
        
        if context.get("next_steps"):
            lines.extend([
                "## 次のステップ",
            ])
            for step in context["next_steps"]:
                lines.append(f"- {step}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _create_pattern_entry(self, name: str, description: str, 
                             example: str, tags: List[str]) -> str:
        """パターンエントリ作成"""
        lines = [f"\n## {name}"]
        
        if tags:
            tags_str = " ".join([f"`{tag}`" for tag in tags])
            lines.append(f"**タグ**: {tags_str}")
        
        lines.extend([
            "", description, ""
        ])
        
        if example:
            lines.extend([
                "**例**:",
                "```",
                example,
                "```",
                ""
            ])
        
        return '\n'.join(lines)
    
    def _extract_sections(self, content: str) -> List[Tuple[str, str]]:
        """セクション抽出"""
        sections = []
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('# ') and not line.startswith('# CLAUDE.md'):
                if current_section:
                    sections.append((current_section, '\n'.join(current_content)))
                current_section = line[2:].strip().lower().replace(' ', '_')
                current_content = [line]
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _update_section(self, content: str, section_id: str, new_content: str) -> str:
        """セクション更新"""
        sections = self._extract_sections(content)
        updated_sections = []
        section_updated = False
        
        for sid, scontent in sections:
            if sid == section_id:
                updated_sections.append(new_content)
                section_updated = True
            else:
                updated_sections.append(scontent)
        
        if not section_updated:
            updated_sections.append(new_content)
        
        return '\n\n'.join(updated_sections)
    
    def _append_to_section(self, content: str, section_id: str, new_entry: str) -> str:
        """セクションに追加"""
        sections = self._extract_sections(content)
        updated_sections = []
        section_found = False
        
        for sid, scontent in sections:
            if sid == section_id:
                updated_sections.append(scontent + new_entry)
                section_found = True
            else:
                updated_sections.append(scontent)
        
        if not section_found:
            # セクションが存在しない場合は作成
            section_title = self.template_sections.get(section_id, f"# {section_id}")
            updated_sections.append(section_title + new_entry)
        
        return '\n\n'.join(updated_sections)
    
    def _remove_duplicate_sections(self, content: str) -> Tuple[str, int]:
        """重複セクション削除"""
        sections = self._extract_sections(content)
        seen_sections = set()
        unique_sections = []
        removed_count = 0
        
        for sid, scontent in sections:
            if sid not in seen_sections:
                seen_sections.add(sid)
                unique_sections.append(scontent)
            else:
                removed_count += 1
        
        return '\n\n'.join(unique_sections), removed_count
    
    def _remove_empty_sections(self, content: str) -> Tuple[str, int]:
        """空セクション削除"""
        sections = self._extract_sections(content)
        non_empty_sections = []
        removed_count = 0
        
        for sid, scontent in sections:
            lines = [line.strip() for line in scontent.split('\n') if line.strip()]
            if len(lines) > 1:  # タイトル行以外に内容がある
                non_empty_sections.append(scontent)
            else:
                removed_count += 1
        
        return '\n\n'.join(non_empty_sections), removed_count
    
    def _reorder_sections(self, content: str) -> str:
        """セクション順序整理"""
        sections = self._extract_sections(content)
        section_order = [
            "project_overview", "development_context", "ai_instructions",
            "patterns", "commands", "notes", "history"
        ]
        
        ordered_sections = []
        section_dict = {sid: scontent for sid, scontent in sections}
        
        # 定義済み順序で並べる
        for section_id in section_order:
            if section_id in section_dict:
                ordered_sections.append(section_dict[section_id])
        
        # その他のセクション追加
        for sid, scontent in sections:
            if sid not in section_order:
                ordered_sections.append(scontent)
        
        return '\n\n'.join(ordered_sections)
    
    def _archive_old_history(self, content: str) -> Tuple[str, int]:
        """古い履歴アーカイブ"""
        # 履歴セクション内のエントリを100件に制限
        sections = self._extract_sections(content)
        archived_count = 0
        
        for i, (sid, scontent) in enumerate(sections):
            if sid == "history":
                # 履歴エントリを分析
                history_entries = re.findall(r'\n## \d{4}-\d{2}-\d{2}.*?(?=\n## \d{4}-\d{2}-\d{2}|\Z)', 
                                            scontent, re.DOTALL)
                
                if len(history_entries) > 100:
                    # 最新100件のみ保持
                    kept_entries = history_entries[-100:]
                    archived_count = len(history_entries) - 100
                    
                    new_content = scontent.split('\n')[0] + '\n'  # タイトル行
                    new_content += '\n'.join(kept_entries)
                    
                    sections[i] = (sid, new_content)
                
                break
        
        return '\n\n'.join([scontent for sid, scontent in sections]), archived_count
    
    def _check_markdown_syntax(self, content: str) -> List[str]:
        """マークダウン構文チェック"""
        errors = []
        lines = content.split('\n')
        
        # 基本的な構文チェック
        for i, line in enumerate(lines, 1):
            # 不正なヘッダー
            if line.startswith('#') and not re.match(r'^#{1,6}\s+', line):
                if line.strip() != '#':
                    errors.append(f"行 {i}: 不正なヘッダー形式: '{line[:20]}...'")
            
            # 不完全なコードブロック
            if line.strip() == '```' and i < len(lines):
                # 対応する終了タグを探す
                found_end = False
                for j in range(i, len(lines)):
                    if lines[j].strip() == '```':
                        found_end = True
                        break
                if not found_end:
                    errors.append(f"行 {i}: 閉じられていないコードブロック")
        
        return errors