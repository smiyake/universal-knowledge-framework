"""
AI駆動ドキュメント変換システム - 統合モジュール

Wikiと同じ階層で管理するため、AI機能を1つのファイルに統合。
シンプルで煩雑にならない設計を重視。
"""

import os
import json
import re
import shutil
import hashlib
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import datetime
import fnmatch


class MigrationStrategy(Enum):
    """マイグレーション戦略"""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    SELECTIVE = "selective"
    HYBRID = "hybrid"


class FrameworkType(Enum):
    """フレームワークタイプ"""
    OBSIDIAN = "obsidian"
    NOTION = "notion"
    UNIVERSAL_KNOWLEDGE = "universal_knowledge"
    GENERIC = "generic"


@dataclass
class FileInfo:
    """ファイル情報"""
    path: str
    size: int
    type: str
    quality_score: float = 0.0


@dataclass
class ProjectAnalysis:
    """プロジェクト解析結果"""
    root_path: str
    total_files: int
    total_size: int
    file_types: Dict[str, int]
    files: List[FileInfo]
    frameworks: List[str]
    quality_average: float


@dataclass
class MigrationPlan:
    """マイグレーション計画"""
    project_name: str
    source_path: str
    target_path: str
    strategy: MigrationStrategy
    estimated_duration: int
    file_count: int
    backup_required: bool


@dataclass
class MigrationResult:
    """マイグレーション結果"""
    success: bool
    source_file: str
    target_file: str
    quality_improvement: float
    processing_time: float


class AIMigrationSystem:
    """AI駆動マイグレーションシステム - 統合クラス"""
    
    def __init__(self):
        self.supported_extensions = {
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json',
            '.yaml': 'yaml',
            '.py': 'python',
            '.js': 'javascript'
        }
        
        self.framework_indicators = {
            'obsidian': ['.obsidian/', 'manifest.json'],
            'notion': ['Notion_DB_', 'export_'],
            'generic': []
        }

    def analyze_project(self, project_path: str) -> ProjectAnalysis:
        """プロジェクト解析"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise ValueError(f"プロジェクトパス '{project_path}' が存在しません")
        
        files = []
        file_types = {}
        total_size = 0
        quality_scores = []
        
        # ファイルスキャン
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size
                    total_size += file_size
                    
                    file_ext = file_path.suffix.lower()
                    file_type = self.supported_extensions.get(file_ext, 'unknown')
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                    
                    # 簡易品質評価
                    quality_score = self._quick_quality_assessment(file_path, file_type)
                    quality_scores.append(quality_score)
                    
                    file_info = FileInfo(
                        path=str(file_path.relative_to(project_path)),
                        size=file_size,
                        type=file_type,
                        quality_score=quality_score
                    )
                    files.append(file_info)
                    
                except (OSError, PermissionError):
                    continue
        
        # フレームワーク検出
        frameworks = self._detect_frameworks(project_path)
        
        return ProjectAnalysis(
            root_path=str(project_path),
            total_files=len(files),
            total_size=total_size,
            file_types=file_types,
            files=files,
            frameworks=frameworks,
            quality_average=sum(quality_scores) / len(quality_scores) if quality_scores else 0
        )

    def _quick_quality_assessment(self, file_path: Path, file_type: str) -> float:
        """簡易品質評価"""
        try:
            if file_type == 'markdown':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                score = 50.0  # ベーススコア
                
                # タイトルの存在
                if re.search(r'^# ', content, re.MULTILINE):
                    score += 15
                
                # セクション構造
                headers = re.findall(r'^#{2,6} ', content, re.MULTILINE)
                if len(headers) >= 2:
                    score += 10
                
                # コードブロック
                if '```' in content:
                    score += 10
                
                # 適切な長さ
                word_count = len(content.split())
                if 100 <= word_count <= 2000:
                    score += 15
                
                return min(score, 100.0)
            
            else:
                return 60.0  # デフォルトスコア
                
        except Exception:
            return 40.0

    def _detect_frameworks(self, project_path: Path) -> List[str]:
        """フレームワーク検出"""
        detected = []
        
        for framework, indicators in self.framework_indicators.items():
            for indicator in indicators:
                if (project_path / indicator).exists() or \
                   any(indicator in f.name for f in project_path.rglob('*')):
                    detected.append(framework)
                    break
        
        return detected or ['generic']

    def create_migration_plan(self, analysis: ProjectAnalysis, strategy: MigrationStrategy = MigrationStrategy.CONSERVATIVE) -> MigrationPlan:
        """マイグレーション計画作成"""
        
        # 戦略別設定
        strategy_configs = {
            MigrationStrategy.CONSERVATIVE: {'files_per_hour': 20, 'backup': True},
            MigrationStrategy.AGGRESSIVE: {'files_per_hour': 50, 'backup': True},
            MigrationStrategy.SELECTIVE: {'files_per_hour': 15, 'backup': True},
            MigrationStrategy.HYBRID: {'files_per_hour': 30, 'backup': True}
        }
        
        config = strategy_configs[strategy]
        estimated_hours = max(1, analysis.total_files / config['files_per_hour'])
        
        return MigrationPlan(
            project_name=Path(analysis.root_path).name,
            source_path=analysis.root_path,
            target_path=f"{analysis.root_path}_migrated",
            strategy=strategy,
            estimated_duration=int(estimated_hours * 60),  # 分単位
            file_count=analysis.total_files,
            backup_required=config['backup']
        )

    def execute_migration(self, plan: MigrationPlan, ai_enhancement: bool = True) -> List[MigrationResult]:
        """マイグレーション実行"""
        results = []
        
        # 出力ディレクトリ作成
        target_path = Path(plan.target_path)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # バックアップ作成
        if plan.backup_required:
            self._create_backup(plan.source_path)
        
        # ファイル変換
        source_path = Path(plan.source_path)
        for file_path in source_path.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    result = self._convert_file(file_path, source_path, target_path, ai_enhancement)
                    results.append(result)
                except Exception as e:
                    # エラーの場合も記録
                    error_result = MigrationResult(
                        success=False,
                        source_file=str(file_path.relative_to(source_path)),
                        target_file="",
                        quality_improvement=0,
                        processing_time=0
                    )
                    results.append(error_result)
        
        return results

    def _convert_file(self, source_file: Path, source_root: Path, target_root: Path, ai_enhancement: bool) -> MigrationResult:
        """単一ファイル変換"""
        start_time = datetime.datetime.now()
        
        relative_path = source_file.relative_to(source_root)
        target_file = target_root / relative_path
        
        # ディレクトリ作成
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # ファイル読み込み
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(source_file, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # 品質向上処理
        original_quality = self._quick_quality_assessment(source_file, source_file.suffix.lower())
        enhanced_content = self._enhance_content(content, source_file, ai_enhancement)
        
        # ファイル書き込み
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        # 変換後品質評価
        improved_quality = self._quick_quality_assessment(target_file, target_file.suffix.lower())
        
        processing_time = (datetime.datetime.now() - start_time).total_seconds()
        
        return MigrationResult(
            success=True,
            source_file=str(relative_path),
            target_file=str(target_file.relative_to(target_root)),
            quality_improvement=improved_quality - original_quality,
            processing_time=processing_time
        )

    def _enhance_content(self, content: str, file_path: Path, ai_enhancement: bool) -> str:
        """コンテンツ品質向上"""
        if file_path.suffix.lower() != '.md':
            return content  # Markdown以外はそのまま
        
        enhanced = content
        
        # 基本的な改善
        if not re.search(r'^# ', enhanced, re.MULTILINE):
            # タイトル追加
            title = file_path.stem.replace('_', ' ').title()
            enhanced = f"# {title}\n\n{enhanced}"
        
        # フロントマター追加
        if not enhanced.startswith('---'):
            frontmatter = f"""---
title: "{file_path.stem.replace('_', ' ').title()}"
created: {datetime.datetime.now().isoformat()}
tags: []
---

"""
            enhanced = frontmatter + enhanced
        
        # AI品質向上（簡略版）
        if ai_enhancement:
            # 略語展開
            enhanced = re.sub(r'\bAPI\b', 'Application Programming Interface (API)', enhanced)
            enhanced = re.sub(r'\bUI\b', 'User Interface (UI)', enhanced)
        
        return enhanced

    def _create_backup(self, source_path: str) -> str:
        """バックアップ作成"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{Path(source_path).name}_backup_{timestamp}.zip"
        backup_path = Path(source_path).parent / backup_name
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in Path(source_path).rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_path)
                    zipf.write(file_path, arcname)
        
        return str(backup_path)

    def generate_migration_report(self, results: List[MigrationResult]) -> str:
        """マイグレーションレポート生成"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_improvement = sum(r.quality_improvement for r in successful)
        avg_improvement = total_improvement / len(successful) if successful else 0
        
        report = f"""# マイグレーションレポート

## 概要
- 処理日時: {datetime.datetime.now().isoformat()}
- 総ファイル数: {len(results)}
- 成功: {len(successful)}
- 失敗: {len(failed)}
- 平均品質向上: {avg_improvement:.1f}ポイント

## 大幅改善ファイル
"""
        
        # 上位改善ファイル
        top_improved = sorted(successful, key=lambda r: r.quality_improvement, reverse=True)[:10]
        for result in top_improved:
            if result.quality_improvement > 5:
                report += f"- {result.source_file}: +{result.quality_improvement:.1f}ポイント\n"
        
        if failed:
            report += f"\n## 失敗ファイル\n"
            for result in failed[:10]:
                report += f"- {result.source_file}\n"
        
        return report

    def quick_analyze(self, project_path: str) -> str:
        """クイック解析"""
        analysis = self.analyze_project(project_path)
        
        report = f"""# プロジェクト解析結果

## 基本情報
- ファイル数: {analysis.total_files:,}
- 総サイズ: {self._format_size(analysis.total_size)}
- 平均品質: {analysis.quality_average:.1f}/100
- 検出フレームワーク: {', '.join(analysis.frameworks)}

## ファイルタイプ分布
"""
        
        for file_type, count in sorted(analysis.file_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / analysis.total_files) * 100
            report += f"- {file_type}: {count} ({percentage:.1f}%)\n"
        
        # 推奨事項
        report += f"\n## 推奨マイグレーション戦略\n"
        if analysis.quality_average < 50:
            report += "- 戦略: CONSERVATIVE (段階的改善重視)\n"
        elif analysis.total_files > 500:
            report += "- 戦略: HYBRID (バランス重視)\n"
        else:
            report += "- 戦略: AGGRESSIVE (高速処理)\n"
        
        return report

    def _format_size(self, size_bytes: int) -> str:
        """サイズフォーマット"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


# モジュール レベル関数（簡易アクセス用）
def analyze_project(project_path: str) -> str:
    """プロジェクト解析（簡易版）"""
    system = AIMigrationSystem()
    return system.quick_analyze(project_path)


def migrate_project(source_path: str, target_path: str = None, strategy: str = "conservative") -> str:
    """プロジェクトマイグレーション（簡易版）"""
    system = AIMigrationSystem()
    
    # 解析
    analysis = system.analyze_project(source_path)
    
    # 計画
    strategy_enum = MigrationStrategy(strategy)
    plan = system.create_migration_plan(analysis, strategy_enum)
    if target_path:
        plan.target_path = target_path
    
    # 実行
    results = system.execute_migration(plan)
    
    return system.generate_migration_report(results)


# CLI統合用のエクスポート
__all__ = [
    'AIMigrationSystem',
    'MigrationStrategy', 
    'ProjectAnalysis',
    'MigrationPlan',
    'MigrationResult',
    'analyze_project',
    'migrate_project'
]