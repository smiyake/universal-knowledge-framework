"""
動的テンプレートエンジン - 状況認識・カスタマイゼーション機能
Dynamic Template Engine - Context Recognition & Customization Features
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from jinja2 import Environment, FileSystemLoader, Template


class DynamicTemplateEngine:
    """
    コンテキスト認識型の動的テンプレートエンジン
    Context-aware dynamic template engine
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        テンプレートエンジンを初期化
        Initialize template engine
        """
        self.base_dir = Path(__file__).parent
        self.templates_dir = templates_dir or self.base_dir / "base_templates"
        self.custom_templates_dir = self.base_dir / "custom_templates"
        
        # Ensure template directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader([str(self.templates_dir), str(self.custom_templates_dir)]),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Template metadata cache
        self._template_metadata: Dict[str, Dict] = {}
        self._load_template_metadata()
    
    def _load_template_metadata(self):
        """テンプレートメタデータを読み込み"""
        metadata_file = self.templates_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self._template_metadata = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load template metadata: {e}")
    
    def generate_context_aware_template(
        self, 
        template_type: str, 
        project_context: Dict[str, Any],
        language: str = "ja",
        output_format: str = "markdown"
    ) -> str:
        """
        コンテキスト認識型のテンプレート生成
        Context-aware template generation
        
        Args:
            template_type: テンプレートの種類 (session, meeting, planning, etc.)
            project_context: プロジェクト情報
            language: 言語 (ja, en)
            output_format: 出力形式 (markdown, json, yaml, html)
        
        Returns:
            生成されたテンプレート文字列
        """
        # Build template context with project information
        template_context = self._build_template_context(project_context, language)
        
        # Select appropriate template based on context
        template_name = self._select_template(template_type, project_context, language, output_format)
        
        try:
            template = self.env.get_template(template_name)
            return template.render(**template_context)
        except Exception as e:
            # Fallback to basic template
            return self._generate_fallback_template(template_type, template_context, language, output_format)
    
    def _build_template_context(self, project_context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """テンプレートコンテキストを構築"""
        context = {
            # 基本情報
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'language': language,
            
            # プロジェクト情報
            'project_name': project_context.get('name', 'Unknown Project'),
            'project_type': project_context.get('type', 'basic'),
            'project_path': project_context.get('path', '.'),
            'project_phase': project_context.get('phase', 'development'),
            
            # 技術スタック情報
            'tech_stack': project_context.get('tech_stack', []),
            'frameworks': project_context.get('frameworks', []),
            'languages': project_context.get('programming_languages', []),
            
            # チーム情報
            'team_size': project_context.get('team_size', 1),
            'team_members': project_context.get('team_members', []),
            
            # カスタムフィールド
            'custom_fields': project_context.get('custom_fields', {}),
            
            # ローカライゼーション
            'strings': self._get_localized_strings(language)
        }
        
        return context
    
    def _select_template(
        self, 
        template_type: str, 
        project_context: Dict[str, Any], 
        language: str, 
        output_format: str
    ) -> str:
        """適切なテンプレートを選択"""
        # Template naming convention: {type}_{language}_{format}.{ext}
        template_candidates = [
            f"{template_type}_{language}_{output_format}.jinja2",
            f"{template_type}_{language}.jinja2",
            f"{template_type}_{output_format}.jinja2",
            f"{template_type}.jinja2",
            f"default_{language}_{output_format}.jinja2",
            f"default_{language}.jinja2",
            f"default.jinja2"
        ]
        
        # Check project-specific templates first
        project_type = project_context.get('type', 'basic')
        project_candidates = [
            f"{project_type}_{template_type}_{language}_{output_format}.jinja2",
            f"{project_type}_{template_type}_{language}.jinja2",
            f"{project_type}_{template_type}.jinja2"
        ]
        
        all_candidates = project_candidates + template_candidates
        
        for candidate in all_candidates:
            try:
                self.env.get_template(candidate)
                return candidate
            except:
                continue
        
        # If no template found, return default
        return "default.jinja2"
    
    def _generate_fallback_template(
        self, 
        template_type: str, 
        context: Dict[str, Any], 
        language: str, 
        output_format: str
    ) -> str:
        """フォールバックテンプレートを生成"""
        strings = context.get('strings', {})
        
        if output_format.lower() == 'markdown':
            return self._generate_markdown_fallback(template_type, context, strings)
        elif output_format.lower() == 'json':
            return self._generate_json_fallback(template_type, context)
        elif output_format.lower() == 'yaml':
            return self._generate_yaml_fallback(template_type, context)
        else:
            return self._generate_markdown_fallback(template_type, context, strings)
    
    def _generate_markdown_fallback(self, template_type: str, context: Dict[str, Any], strings: Dict[str, str]) -> str:
        """Markdownフォールバックテンプレート"""
        title = strings.get(f'{template_type}_title', f'{template_type.title()} Document')
        
        return f"""# {title}

**{strings.get('project', 'Project')}:** {context['project_name']}
**{strings.get('date', 'Date')}:** {context['date']}
**{strings.get('time', 'Time')}:** {context['time']}

## {strings.get('overview', 'Overview')}

{strings.get('description_prompt', 'Please add description here...')}

## {strings.get('details', 'Details')}

{strings.get('details_prompt', 'Please add details here...')}

## {strings.get('notes', 'Notes')}

{strings.get('notes_prompt', 'Please add notes here...')}

---
*{strings.get('generated_by', 'Generated by')} Universal Knowledge Framework - {context['timestamp']}*
"""
    
    def _generate_json_fallback(self, template_type: str, context: Dict[str, Any]) -> str:
        """JSONフォールバックテンプレート"""
        data = {
            "type": template_type,
            "project": context['project_name'],
            "timestamp": context['timestamp'],
            "data": {
                "title": f"{template_type.title()} Document",
                "description": "",
                "details": "",
                "notes": ""
            },
            "metadata": {
                "generated_by": "Universal Knowledge Framework",
                "language": context['language'],
                "project_type": context['project_type']
            }
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _generate_yaml_fallback(self, template_type: str, context: Dict[str, Any]) -> str:
        """YAMLフォールバックテンプレート"""
        data = {
            "type": template_type,
            "project": context['project_name'],
            "timestamp": context['timestamp'],
            "data": {
                "title": f"{template_type.title()} Document",
                "description": "",
                "details": "",
                "notes": ""
            },
            "metadata": {
                "generated_by": "Universal Knowledge Framework",
                "language": context['language'],
                "project_type": context['project_type']
            }
        }
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def _get_localized_strings(self, language: str) -> Dict[str, str]:
        """ローカライズされた文字列を取得"""
        strings = {
            'ja': {
                'project': 'プロジェクト',
                'date': '日付',
                'time': '時刻',
                'overview': '概要',
                'details': '詳細',
                'notes': 'メモ',
                'session_title': 'セッション記録',
                'meeting_title': '会議記録',
                'planning_title': '計画書',
                'task_title': 'タスク',
                'description_prompt': 'ここに説明を追加してください...',
                'details_prompt': 'ここに詳細を追加してください...',
                'notes_prompt': 'ここにメモを追加してください...',
                'generated_by': '生成者'
            },
            'en': {
                'project': 'Project',
                'date': 'Date', 
                'time': 'Time',
                'overview': 'Overview',
                'details': 'Details',
                'notes': 'Notes',
                'session_title': 'Session Record',
                'meeting_title': 'Meeting Record',
                'planning_title': 'Planning Document',
                'task_title': 'Task',
                'description_prompt': 'Please add description here...',
                'details_prompt': 'Please add details here...',
                'notes_prompt': 'Please add notes here...',
                'generated_by': 'Generated by'
            }
        }
        
        return strings.get(language, strings['en'])
    
    def get_available_templates(self) -> Dict[str, List[str]]:
        """利用可能なテンプレート一覧を取得"""
        templates = {'base': [], 'custom': []}
        
        # Base templates
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.jinja2"):
                templates['base'].append(template_file.stem)
        
        # Custom templates
        if self.custom_templates_dir.exists():
            for template_file in self.custom_templates_dir.glob("*.jinja2"):
                templates['custom'].append(template_file.stem)
        
        return templates
    
    def validate_template(self, template_path: Union[str, Path]) -> Dict[str, Any]:
        """テンプレートの妥当性を検証"""
        template_path = Path(template_path)
        
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            # Check if file exists
            if not template_path.exists():
                result['errors'].append(f"Template file not found: {template_path}")
                return result
            
            # Try to parse template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            template = self.env.from_string(template_content)
            
            # Basic syntax validation
            try:
                template.render()
                result['valid'] = True
            except Exception as e:
                # Try with sample context
                sample_context = self._build_template_context({
                    'name': 'Sample Project',
                    'type': 'basic',
                    'path': '.'
                }, 'ja')
                
                try:
                    template.render(**sample_context)
                    result['valid'] = True
                except Exception as render_error:
                    result['errors'].append(f"Template rendering error: {render_error}")
            
            # Extract metadata if available
            result['metadata'] = {
                'file_size': template_path.stat().st_size,
                'last_modified': datetime.fromtimestamp(template_path.stat().st_mtime).isoformat(),
                'name': template_path.stem
            }
            
        except Exception as e:
            result['errors'].append(f"Template validation error: {e}")
        
        return result