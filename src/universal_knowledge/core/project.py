"""
プロジェクト管理マネージャー - プロジェクト作成・管理のコアクラス
Project Manager - Core class for project creation and management
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
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
        """Gitリポジトリを初期化（改善版）"""
        from .git_utils import GitManager
        
        git_manager = GitManager()
        success = git_manager.initialize_repository(
            project_path, 
            "初期コミット: プロジェクト作成 🚀"
        )
        
        if not success:
            print("\n💡 Gitリポジトリは後で手動で初期化できます:")
            print(f"   cd {project_path}")
            print("   git init")
            print("   git add .")
            print("   git commit -m \"初期コミット: プロジェクト作成 🚀\"")
    
    def detect_project_context(self, project_path: Path) -> Dict[str, Any]:
        """
        プロジェクトコンテキストを自動検出
        Automatically detect project context
        
        Args:
            project_path: プロジェクトパス
        
        Returns:
            プロジェクトコンテキスト情報
        """
        context = {
            "name": project_path.name,
            "path": str(project_path),
            "type": "basic",
            "phase": "development",
            "tech_stack": [],
            "frameworks": [],
            "programming_languages": [],
            "team_size": 1,
            "team_members": [],
            "custom_fields": {}
        }
        
        # Check if UKF project
        ukf_config = project_path / ".ukf" / "project.json"
        if ukf_config.exists():
            try:
                with open(ukf_config, 'r', encoding='utf-8') as f:
                    ukf_data = json.load(f)
                context.update({
                    "name": ukf_data.get("name", project_path.name),
                    "type": ukf_data.get("type", "basic"),
                    "created_at": ukf_data.get("created_at"),
                    "version": ukf_data.get("version")
                })
            except:
                pass
        
        # Detect technology stack
        context["tech_stack"] = self._detect_tech_stack(project_path)
        context["frameworks"] = self._detect_frameworks(project_path)
        context["programming_languages"] = self._detect_languages(project_path)
        
        # Detect project type if not set
        if context["type"] == "basic":
            context["type"] = self._infer_project_type(project_path, context)
        
        # Detect project phase
        context["phase"] = self._detect_project_phase(project_path)
        
        return context
    
    def _detect_tech_stack(self, project_path: Path) -> List[str]:
        """技術スタックを検出"""
        tech_stack = []
        
        # Node.js
        if (project_path / "package.json").exists():
            tech_stack.extend(["Node.js", "JavaScript"])
        
        # Python
        if any((project_path / file).exists() for file in ["requirements.txt", "pyproject.toml", "setup.py"]):
            tech_stack.append("Python")
        
        # Java
        if any((project_path / file).exists() for file in ["pom.xml", "build.gradle"]):
            tech_stack.append("Java")
        
        # .NET
        if any(project_path.glob("*.csproj")) or any(project_path.glob("*.sln")):
            tech_stack.append(".NET")
        
        # Go
        if (project_path / "go.mod").exists():
            tech_stack.append("Go")
        
        # Rust
        if (project_path / "Cargo.toml").exists():
            tech_stack.append("Rust")
        
        # Docker
        if (project_path / "Dockerfile").exists() or (project_path / "docker-compose.yml").exists():
            tech_stack.append("Docker")
        
        # Kubernetes
        if any(project_path.glob("**/k8s/**/*.yml")) or any(project_path.glob("**/kubernetes/**/*.yaml")):
            tech_stack.append("Kubernetes")
        
        return tech_stack
    
    def _detect_frameworks(self, project_path: Path) -> List[str]:
        """フレームワークを検出"""
        frameworks = []
        
        # Check package.json for JS frameworks
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "react" in dependencies:
                    frameworks.append("React")
                if "vue" in dependencies:
                    frameworks.append("Vue.js")
                if "angular" in dependencies or "@angular/core" in dependencies:
                    frameworks.append("Angular")
                if "express" in dependencies:
                    frameworks.append("Express.js")
                if "next" in dependencies:
                    frameworks.append("Next.js")
                if "nuxt" in dependencies:
                    frameworks.append("Nuxt.js")
            except:
                pass
        
        # Check Python frameworks
        requirements_files = ["requirements.txt", "pyproject.toml"]
        for req_file in requirements_files:
            req_path = project_path / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text(encoding='utf-8').lower()
                    if "django" in content:
                        frameworks.append("Django")
                    if "flask" in content:
                        frameworks.append("Flask")
                    if "fastapi" in content:
                        frameworks.append("FastAPI")
                    if "streamlit" in content:
                        frameworks.append("Streamlit")
                    if "pandas" in content:
                        frameworks.append("Pandas")
                    if "numpy" in content:
                        frameworks.append("NumPy")
                    if "scikit-learn" in content:
                        frameworks.append("Scikit-learn")
                    if "tensorflow" in content:
                        frameworks.append("TensorFlow")
                    if "pytorch" in content:
                        frameworks.append("PyTorch")
                except:
                    pass
        
        return frameworks
    
    def _detect_languages(self, project_path: Path) -> List[str]:
        """プログラミング言語を検出"""
        languages = []
        
        # File extension mapping
        ext_mapping = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JSX",
            ".tsx": "TSX",
            ".java": "Java",
            ".cs": "C#",
            ".cpp": "C++",
            ".c": "C",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".rb": "Ruby",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".sql": "SQL"
        }
        
        # Count files by extension
        lang_counts = {}
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not self._is_ignored_path(file_path):
                ext = file_path.suffix.lower()
                if ext in ext_mapping:
                    lang = ext_mapping[ext]
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
        
        # Return languages sorted by frequency
        return [lang for lang, _ in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)]
    
    def _is_ignored_path(self, file_path: Path) -> bool:
        """無視するパスかどうかを判定"""
        ignored_dirs = {".git", "__pycache__", "node_modules", ".vscode", ".idea", "dist", "build"}
        return any(part in ignored_dirs for part in file_path.parts)
    
    def _infer_project_type(self, project_path: Path, context: Dict[str, Any]) -> str:
        """プロジェクトタイプを推測"""
        tech_stack = context.get("tech_stack", [])
        frameworks = context.get("frameworks", [])
        languages = context.get("programming_languages", [])
        
        # Web development
        web_indicators = ["React", "Vue.js", "Angular", "Express.js", "Django", "Flask", "FastAPI"]
        if any(fw in frameworks for fw in web_indicators) or "JavaScript" in languages:
            return "web-development"
        
        # Data science
        ds_indicators = ["Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Streamlit"]
        if any(fw in frameworks for fw in ds_indicators) or (project_path / "notebooks").exists():
            return "data-science"
        
        # Research
        if (project_path / "papers").exists() or (project_path / "references").exists():
            return "research"
        
        # Business
        if (project_path / "proposals").exists() or (project_path / "presentations").exists():
            return "business"
        
        # Personal
        if (project_path / "learning").exists() or (project_path / "practice").exists():
            return "personal"
        
        return "basic"
    
    def _detect_project_phase(self, project_path: Path) -> str:
        """プロジェクトフェーズを検出"""
        # Check for indicators of different phases
        
        # Planning phase
        if (project_path / "README.md").exists():
            readme_content = (project_path / "README.md").read_text(encoding='utf-8').lower()
            if "todo" in readme_content or "planning" in readme_content:
                return "planning"
        
        # Development phase
        if any(project_path.glob("src/**/*")) or any(project_path.glob("**/*.py")) or any(project_path.glob("**/*.js")):
            return "development"
        
        # Testing phase
        if any(project_path.glob("tests/**/*")) or any(project_path.glob("**/*test*")):
            return "testing"
        
        # Production phase
        if (project_path / "Dockerfile").exists() or (project_path / "docker-compose.yml").exists():
            return "production"
        
        return "development"