"""
プロジェクト管理マネージャー - プロジェクト作成・管理のコアクラス
Project Manager - Core class for project creation and management
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class ProjectManager:
    """
    汎用プロジェクト管理システム
    あらゆるタイプのプロジェクト作成・管理を行う
    """
    
    def __init__(self):
        """プロジェクトマネージャーを初期化"""
        self.templates_path = Path(__file__).parent.parent / "templates"
        self.project_templates_path = Path(__file__).parent.parent.parent.parent / "project_templates"
    
    def create_project(self, name: str, project_type: str = "basic", target_path: Optional[str] = None) -> str:
        """
        新しいプロジェクトを作成
        
        Args:
            name: プロジェクト名
            project_type: プロジェクトタイプ
            target_path: 作成先パス
            
        Returns:
            str: 作成されたプロジェクトパス
        """
        try:
            # プロジェクトパス決定
            if target_path:
                project_path = Path(target_path) / name
            else:
                project_path = Path.cwd() / name
            
            # プロジェクトディレクトリ作成
            project_path.mkdir(parents=True, exist_ok=True)
            
            # テンプレート適用
            self._apply_template(project_path, project_type, name)
            
            # プロジェクト設定ファイル作成
            self._create_project_config(project_path, name, project_type)
            
            # Git初期化
            self._initialize_git(project_path)
            
            # ナレッジ構造作成
            from .manager import KnowledgeManager
            knowledge_manager = KnowledgeManager(str(project_path))
            knowledge_manager.create_knowledge_structure()
            
            return str(project_path)
            
        except Exception as e:
            raise Exception(f"プロジェクト作成に失敗しました: {e}")
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """
        利用可能なテンプレート一覧を取得
        
        Returns:
            List[Dict]: テンプレート情報リスト
        """
        templates = [
            {
                "type": "basic",
                "name": "基本プロジェクト",
                "description": "基本的なプロジェクト構造"
            },
            {
                "type": "web-development",
                "name": "Webアプリケーション開発",
                "description": "Webアプリケーション開発用の構造"
            },
            {
                "type": "data-science",
                "name": "データサイエンス",
                "description": "データ分析・機械学習プロジェクト用"
            },
            {
                "type": "business",
                "name": "ビジネス・企画",
                "description": "ビジネス企画・提案書作成用"
            },
            {
                "type": "research",
                "name": "学術研究",
                "description": "学術研究・論文作成用"
            },
            {
                "type": "personal",
                "name": "個人学習",
                "description": "個人学習・スキル向上用"
            }
        ]
        
        return templates
    
    def _apply_template(self, project_path: Path, project_type: str, project_name: str) -> None:
        """
        プロジェクトテンプレートを適用
        
        Args:
            project_path: プロジェクトパス
            project_type: プロジェクトタイプ
            project_name: プロジェクト名
        """
        # 基本構造作成
        self._create_basic_structure(project_path, project_name)
        
        # タイプ別の特別な構造追加
        if project_type == "web-development":
            self._create_web_structure(project_path)
        elif project_type == "data-science":
            self._create_data_science_structure(project_path)
        elif project_type == "business":
            self._create_business_structure(project_path)
        elif project_type == "research":
            self._create_research_structure(project_path)
        elif project_type == "personal":
            self._create_personal_structure(project_path)
    
    def _create_basic_structure(self, project_path: Path, project_name: str) -> None:
        """基本的なプロジェクト構造を作成"""
        # 基本ディレクトリ
        dirs = [
            "src",
            "docs",
            "tests",
            "config",
            "scripts"
        ]
        
        for dir_name in dirs:
            (project_path / dir_name).mkdir(exist_ok=True)
        
        # README作成
        readme_content = f"""# {project_name}

## 概要

## セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd {project_name}

# 依存関係インストール
# (プロジェクトタイプに応じて記載)
```

## 使用方法

## 貢献

## ライセンス
"""
        
        with open(project_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        # .gitignore作成
        gitignore_content = """# 一般的な除外ファイル
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# 環境変数
.env
.env.local
.env.development
.env.production

# ログ
*.log
logs/

# OS固有
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# プロジェクト固有
config/secrets.yaml
config/local.json
"""
        
        with open(project_path / ".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
    
    def _create_web_structure(self, project_path: Path) -> None:
        """Webアプリケーション開発用構造"""
        web_dirs = [
            "src/frontend",
            "src/backend", 
            "src/api",
            "public",
            "assets",
            "components"
        ]
        
        for dir_name in web_dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # package.json テンプレート
        package_json = {
            "name": project_path.name,
            "version": "1.0.0",
            "description": "",
            "main": "index.js",
            "scripts": {
                "start": "node src/index.js",
                "dev": "nodemon src/index.js",
                "test": "jest"
            },
            "dependencies": {},
            "devDependencies": {}
        }
        
        with open(project_path / "package.json", "w", encoding="utf-8") as f:
            json.dump(package_json, f, indent=2, ensure_ascii=False)
    
    def _create_data_science_structure(self, project_path: Path) -> None:
        """データサイエンス用構造"""
        ds_dirs = [
            "data/raw",
            "data/processed",
            "notebooks",
            "models",
            "reports/figures"
        ]
        
        for dir_name in ds_dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # requirements.txt
        requirements = """pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
seaborn>=0.11.0
scikit-learn>=1.0.0
jupyter>=1.0.0
"""
        
        with open(project_path / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements)
    
    def _create_business_structure(self, project_path: Path) -> None:
        """ビジネス・企画用構造"""
        business_dirs = [
            "proposals",
            "presentations",
            "research",
            "templates",
            "resources"
        ]
        
        for dir_name in business_dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _create_research_structure(self, project_path: Path) -> None:
        """学術研究用構造"""
        research_dirs = [
            "papers",
            "references",
            "data",
            "analysis",
            "figures"
        ]
        
        for dir_name in research_dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _create_personal_structure(self, project_path: Path) -> None:
        """個人学習用構造"""
        personal_dirs = [
            "learning",
            "projects",
            "notes",
            "practice"
        ]
        
        for dir_name in personal_dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _create_project_config(self, project_path: Path, name: str, project_type: str) -> None:
        """プロジェクト設定ファイルを作成"""
        config_dir = project_path / ".ukf"
        config_dir.mkdir(exist_ok=True)
        
        project_config = {
            "name": name,
            "type": project_type,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "framework_version": "1.0.0"
        }
        
        with open(config_dir / "project.json", "w", encoding="utf-8") as f:
            json.dump(project_config, f, indent=2, ensure_ascii=False)
    
    def _initialize_git(self, project_path: Path) -> None:
        """Gitリポジトリを初期化"""
        try:
            os.chdir(project_path)
            os.system("git init")
            os.system("git add .")
            os.system('git commit -m "初期コミット: プロジェクト作成 🚀"')
        except Exception:
            # Git初期化に失敗しても続行
            pass