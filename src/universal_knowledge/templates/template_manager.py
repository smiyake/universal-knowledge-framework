"""
テンプレート管理システム
Template Management System
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .dynamic_engine import DynamicTemplateEngine


class TemplateManager:
    """
    カスタムテンプレート管理システム
    Custom template management system
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        テンプレートマネージャーを初期化
        Initialize template manager
        """
        self.base_dir = Path(__file__).parent
        self.templates_dir = templates_dir or self.base_dir / "base_templates"
        self.custom_templates_dir = self.base_dir / "custom_templates"
        self.user_templates_dir = Path.home() / ".ukf" / "templates"
        
        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize template engine
        self.engine = DynamicTemplateEngine(self.templates_dir)
        
        # Template registry
        self.template_registry_file = self.user_templates_dir / "registry.json"
        self._template_registry: Dict[str, Dict] = {}
        self._load_template_registry()
    
    def _load_template_registry(self):
        """テンプレートレジストリを読み込み"""
        if self.template_registry_file.exists():
            try:
                with open(self.template_registry_file, 'r', encoding='utf-8') as f:
                    self._template_registry = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load template registry: {e}")
                self._template_registry = {}
    
    def _save_template_registry(self):
        """テンプレートレジストリを保存"""
        try:
            with open(self.template_registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._template_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save template registry: {e}")
    
    def register_custom_template(
        self, 
        name: str, 
        template_content: str, 
        metadata: Dict[str, Any],
        template_type: str = "custom"
    ) -> bool:
        """
        カスタムテンプレートを登録
        Register custom template
        
        Args:
            name: テンプレート名
            template_content: テンプレート内容
            metadata: テンプレートメタデータ
            template_type: テンプレートタイプ
        
        Returns:
            登録成功したかどうか
        """
        try:
            # Generate template filename
            template_filename = f"{name}.jinja2"
            template_path = self.custom_templates_dir / template_filename
            
            # Write template file
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # Register in registry
            self._template_registry[name] = {
                'name': name,
                'type': template_type,
                'path': str(template_path),
                'filename': template_filename,
                'metadata': metadata,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_template_registry()
            return True
            
        except Exception as e:
            print(f"Error registering template '{name}': {e}")
            return False
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """テンプレート情報を取得"""
        return self._template_registry.get(name)
    
    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        テンプレート一覧を取得
        Get list of templates
        
        Args:
            template_type: フィルタするテンプレートタイプ
        
        Returns:
            テンプレート一覧
        """
        templates = []
        
        # Custom templates from registry
        for template_info in self._template_registry.values():
            if template_type is None or template_info.get('type') == template_type:
                templates.append(template_info)
        
        # Base templates
        base_templates = self._get_base_templates()
        for template_info in base_templates:
            if template_type is None or template_info.get('type') == 'base':
                templates.append(template_info)
        
        return sorted(templates, key=lambda x: x.get('name', ''))
    
    def _get_base_templates(self) -> List[Dict[str, Any]]:
        """ベーステンプレート一覧を取得"""
        templates = []
        
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.jinja2"):
                templates.append({
                    'name': template_file.stem,
                    'type': 'base',
                    'path': str(template_file),
                    'filename': template_file.name,
                    'metadata': {
                        'size': template_file.stat().st_size,
                        'last_modified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
                    }
                })
        
        return templates
    
    def get_recommended_templates(self, project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        プロジェクトコンテキストに基づいて推奨テンプレートを取得
        Get recommended templates based on project context
        
        Args:
            project_context: プロジェクト情報
        
        Returns:
            推奨テンプレート一覧
        """
        recommended = []
        project_type = project_context.get('type', 'basic')
        tech_stack = project_context.get('tech_stack', [])
        phase = project_context.get('phase', 'development')
        
        # Score templates based on relevance
        all_templates = self.list_templates()
        
        for template in all_templates:
            score = self._calculate_template_relevance(template, project_context)
            if score > 0:
                template['relevance_score'] = score
                recommended.append(template)
        
        # Sort by relevance score
        recommended.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return recommended[:10]  # Return top 10 recommendations
    
    def _calculate_template_relevance(self, template: Dict[str, Any], context: Dict[str, Any]) -> float:
        """テンプレートの関連性スコアを計算"""
        score = 0.0
        
        template_name = template.get('name', '').lower()
        template_metadata = template.get('metadata', {})
        
        project_type = context.get('type', '').lower()
        tech_stack = [tech.lower() for tech in context.get('tech_stack', [])]
        phase = context.get('phase', '').lower()
        
        # Project type matching
        if project_type in template_name:
            score += 3.0
        
        # Technology stack matching
        for tech in tech_stack:
            if tech in template_name:
                score += 2.0
        
        # Phase matching
        if phase in template_name:
            score += 1.5
        
        # Common template types
        common_types = ['session', 'meeting', 'planning', 'task', 'report']
        for common_type in common_types:
            if common_type in template_name:
                score += 1.0
        
        # Custom templates get bonus
        if template.get('type') == 'custom':
            score += 0.5
        
        return score
    
    def delete_template(self, name: str) -> bool:
        """
        カスタムテンプレートを削除
        Delete custom template
        
        Args:
            name: テンプレート名
        
        Returns:
            削除成功したかどうか
        """
        if name not in self._template_registry:
            return False
        
        try:
            template_info = self._template_registry[name]
            template_path = Path(template_info['path'])
            
            # Remove file if it exists
            if template_path.exists():
                template_path.unlink()
            
            # Remove from registry
            del self._template_registry[name]
            self._save_template_registry()
            
            return True
            
        except Exception as e:
            print(f"Error deleting template '{name}': {e}")
            return False
    
    def update_template(
        self, 
        name: str, 
        template_content: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        テンプレートを更新
        Update template
        
        Args:
            name: テンプレート名
            template_content: 新しいテンプレート内容
            metadata: 新しいメタデータ
        
        Returns:
            更新成功したかどうか
        """
        if name not in self._template_registry:
            return False
        
        try:
            template_info = self._template_registry[name]
            
            # Update content if provided
            if template_content is not None:
                template_path = Path(template_info['path'])
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)
            
            # Update metadata if provided
            if metadata is not None:
                template_info['metadata'].update(metadata)
            
            template_info['updated_at'] = datetime.now().isoformat()
            self._save_template_registry()
            
            return True
            
        except Exception as e:
            print(f"Error updating template '{name}': {e}")
            return False
    
    def export_template(self, name: str, output_path: Path) -> bool:
        """
        テンプレートをエクスポート
        Export template
        
        Args:
            name: テンプレート名
            output_path: エクスポート先パス
        
        Returns:
            エクスポート成功したかどうか
        """
        template_info = self.get_template(name)
        if not template_info:
            return False
        
        try:
            source_path = Path(template_info['path'])
            if source_path.exists():
                shutil.copy2(source_path, output_path)
                return True
            return False
            
        except Exception as e:
            print(f"Error exporting template '{name}': {e}")
            return False
    
    def import_template(self, template_path: Path, name: Optional[str] = None) -> bool:
        """
        テンプレートをインポート
        Import template
        
        Args:
            template_path: インポート元テンプレートパス
            name: テンプレート名（省略時はファイル名を使用）
        
        Returns:
            インポート成功したかどうか
        """
        if not template_path.exists():
            return False
        
        try:
            # Read template content
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Use filename as name if not provided
            template_name = name or template_path.stem
            
            # Create metadata
            metadata = {
                'imported_from': str(template_path),
                'original_size': template_path.stat().st_size,
                'import_date': datetime.now().isoformat()
            }
            
            return self.register_custom_template(
                template_name, 
                template_content, 
                metadata, 
                "imported"
            )
            
        except Exception as e:
            print(f"Error importing template from '{template_path}': {e}")
            return False
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """
        テンプレートを検索
        Search templates
        
        Args:
            query: 検索クエリ
        
        Returns:
            検索結果テンプレート一覧
        """
        query = query.lower()
        results = []
        
        all_templates = self.list_templates()
        
        for template in all_templates:
            # Search in name
            if query in template.get('name', '').lower():
                template['match_type'] = 'name'
                results.append(template)
                continue
            
            # Search in metadata
            metadata = template.get('metadata', {})
            metadata_str = json.dumps(metadata).lower()
            if query in metadata_str:
                template['match_type'] = 'metadata'
                results.append(template)
                continue
            
            # Search in template content (for custom templates)
            if template.get('type') in ['custom', 'imported']:
                try:
                    template_path = Path(template['path'])
                    if template_path.exists():
                        with open(template_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                        if query in content:
                            template['match_type'] = 'content'
                            results.append(template)
                except:
                    pass
        
        return results