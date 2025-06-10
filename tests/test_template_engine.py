"""
動的テンプレートエンジンのテスト
Tests for Dynamic Template Engine
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.universal_knowledge.templates import DynamicTemplateEngine, TemplateManager


class TestDynamicTemplateEngine:
    """DynamicTemplateEngineのテストクラス"""
    
    def setup_method(self):
        """テストメソッドのセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = DynamicTemplateEngine(self.temp_dir)
    
    def test_generate_context_aware_template_basic(self):
        """基本的なコンテキスト認識テンプレート生成のテスト"""
        project_context = {
            "name": "Test Project",
            "type": "basic",
            "path": "/test/path"
        }
        
        result = self.engine.generate_context_aware_template(
            "session", project_context, "ja", "markdown"
        )
        
        assert "Test Project" in result
        assert "セッション記録" in result or "Session Record" in result
        assert "Universal Knowledge Framework" in result
    
    def test_build_template_context(self):
        """テンプレートコンテキスト構築のテスト"""
        project_context = {
            "name": "Test Project",
            "type": "web-development",
            "tech_stack": ["JavaScript", "React"],
            "team_size": 3
        }
        
        context = self.engine._build_template_context(project_context, "ja")
        
        assert context["project_name"] == "Test Project"
        assert context["project_type"] == "web-development"
        assert context["tech_stack"] == ["JavaScript", "React"]
        assert context["team_size"] == 3
        assert context["language"] == "ja"
        assert "date" in context
        assert "time" in context
    
    def test_get_localized_strings(self):
        """ローカライズされた文字列取得のテスト"""
        ja_strings = self.engine._get_localized_strings("ja")
        en_strings = self.engine._get_localized_strings("en")
        
        assert ja_strings["project"] == "プロジェクト"
        assert en_strings["project"] == "Project"
        assert ja_strings["overview"] == "概要"
        assert en_strings["overview"] == "Overview"
    
    def test_fallback_template_generation(self):
        """フォールバックテンプレート生成のテスト"""
        context = {
            "project_name": "Fallback Test",
            "date": "2025-01-01",
            "time": "12:00:00",
            "timestamp": "2025-01-01 12:00:00",
            "language": "ja",
            "project_type": "basic",
            "strings": self.engine._get_localized_strings("ja")
        }
        
        # Markdown fallback
        md_result = self.engine._generate_markdown_fallback("test", context, context["strings"])
        assert "Fallback Test" in md_result
        assert "概要" in md_result
        
        # JSON fallback
        json_result = self.engine._generate_json_fallback("test", context)
        json_data = json.loads(json_result)
        assert json_data["project"] == "Fallback Test"
        assert json_data["type"] == "test"
    
    def test_validate_template_valid(self):
        """有効なテンプレートの検証テスト"""
        # Create a valid template file
        template_content = """# {{ project_name }}

**Date:** {{ date }}

## Content
{{ description_prompt }}
"""
        template_file = self.temp_dir / "valid_template.jinja2"
        template_file.write_text(template_content, encoding='utf-8')
        
        result = self.engine.validate_template(template_file)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "metadata" in result
    
    def test_validate_template_invalid(self):
        """無効なテンプレートの検証テスト"""
        # Create an invalid template file with syntax error
        template_content = """# {{ project_name

**Date:** {{ date }}
"""
        template_file = self.temp_dir / "invalid_template.jinja2"
        template_file.write_text(template_content, encoding='utf-8')
        
        result = self.engine.validate_template(template_file)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_template_nonexistent(self):
        """存在しないテンプレートの検証テスト"""
        nonexistent_file = self.temp_dir / "nonexistent.jinja2"
        
        result = self.engine.validate_template(nonexistent_file)
        
        assert result["valid"] is False
        assert any("not found" in error for error in result["errors"])


class TestTemplateManager:
    """TemplateManagerのテストクラス"""
    
    def setup_method(self):
        """テストメソッドのセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = TemplateManager(self.temp_dir)
    
    def test_register_custom_template(self):
        """カスタムテンプレート登録のテスト"""
        template_content = "# {{ project_name }}\n\nTest template content"
        metadata = {
            "description": "Test template",
            "author": "Test"
        }
        
        success = self.manager.register_custom_template(
            "test_template", template_content, metadata, "custom"
        )
        
        assert success is True
        assert "test_template" in self.manager._template_registry
        
        # Check if file was created
        template_file = self.manager.custom_templates_dir / "test_template.jinja2"
        assert template_file.exists()
        assert template_file.read_text(encoding='utf-8') == template_content
    
    def test_get_template(self):
        """テンプレート取得のテスト"""
        # Register a template first
        template_content = "Test content"
        metadata = {"description": "Test"}
        self.manager.register_custom_template("test_get", template_content, metadata)
        
        template_info = self.manager.get_template("test_get")
        
        assert template_info is not None
        assert template_info["name"] == "test_get"
        assert template_info["metadata"]["description"] == "Test"
    
    def test_list_templates(self):
        """テンプレート一覧取得のテスト"""
        # Register some templates
        for i in range(3):
            self.manager.register_custom_template(
                f"test_{i}", f"Content {i}", {"type": "test"}, "custom"
            )
        
        templates = self.manager.list_templates()
        custom_templates = [t for t in templates if t.get("type") == "custom"]
        
        assert len(custom_templates) >= 3
        assert any(t["name"] == "test_0" for t in custom_templates)
    
    def test_search_templates(self):
        """テンプレート検索のテスト"""
        # Register templates with different content
        self.manager.register_custom_template(
            "web_template", "React content", {"description": "Web template"}, "custom"
        )
        self.manager.register_custom_template(
            "data_template", "Data analysis", {"description": "Data template"}, "custom"
        )
        
        # Search by name
        results = self.manager.search_templates("web")
        assert len(results) >= 1
        assert any("web" in t["name"].lower() for t in results)
        
        # Search by content
        results = self.manager.search_templates("react")
        assert len(results) >= 1
    
    def test_get_recommended_templates(self):
        """推奨テンプレート取得のテスト"""
        project_context = {
            "type": "web-development",
            "tech_stack": ["JavaScript", "React"],
            "phase": "development"
        }
        
        # Register some templates
        self.manager.register_custom_template(
            "react_session", "React session", {"type": "session"}, "custom"
        )
        self.manager.register_custom_template(
            "general_meeting", "General meeting", {"type": "meeting"}, "custom"
        )
        
        recommendations = self.manager.get_recommended_templates(project_context)
        
        assert len(recommendations) > 0
        # React template should have higher relevance
        react_templates = [t for t in recommendations if "react" in t["name"].lower()]
        if react_templates:
            assert react_templates[0].get("relevance_score", 0) > 0
    
    def test_delete_template(self):
        """テンプレート削除のテスト"""
        # Register a template first
        self.manager.register_custom_template(
            "delete_test", "Delete me", {"description": "Test deletion"}
        )
        
        # Confirm it exists
        assert self.manager.get_template("delete_test") is not None
        
        # Delete it
        success = self.manager.delete_template("delete_test")
        assert success is True
        
        # Confirm it's gone
        assert self.manager.get_template("delete_test") is None
    
    def test_update_template(self):
        """テンプレート更新のテスト"""
        # Register a template first
        original_content = "Original content"
        self.manager.register_custom_template(
            "update_test", original_content, {"description": "Original"}
        )
        
        # Update content
        new_content = "Updated content"
        success = self.manager.update_template("update_test", new_content)
        assert success is True
        
        # Check if content was updated
        template_file = self.manager.custom_templates_dir / "update_test.jinja2"
        assert template_file.read_text(encoding='utf-8') == new_content
        
        # Update metadata
        success = self.manager.update_template(
            "update_test", metadata={"description": "Updated description"}
        )
        assert success is True
        
        template_info = self.manager.get_template("update_test")
        assert template_info["metadata"]["description"] == "Updated description"
    
    def test_import_export_template(self):
        """テンプレートのインポート・エクスポートのテスト"""
        # Create a template file to import
        import_file = self.temp_dir / "import_test.jinja2"
        import_content = "# Imported Template\n\n{{ project_name }}"
        import_file.write_text(import_content, encoding='utf-8')
        
        # Import the template
        success = self.manager.import_template(import_file, "imported_template")
        assert success is True
        
        # Check if it was imported
        template_info = self.manager.get_template("imported_template")
        assert template_info is not None
        assert template_info["type"] == "imported"
        
        # Export the template
        export_file = self.temp_dir / "export_test.jinja2"
        success = self.manager.export_template("imported_template", export_file)
        assert success is True
        assert export_file.exists()
        assert export_file.read_text(encoding='utf-8') == import_content


if __name__ == "__main__":
    pytest.main([__file__])