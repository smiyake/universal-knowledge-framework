"""
汎用ナレッジ管理フレームワーク

あらゆるプロジェクトで利用可能な文書管理・知識蓄積システム
Claude-Obsidian連携による効率的なナレッジベース構築を支援
"""

__version__ = "1.0.0"
__author__ = "Universal Knowledge Contributors"

from .core.manager import KnowledgeManager
from .core.project import ProjectManager
from .core.task import TaskManager
from .core.analytics import ProjectAnalytics
from .ai_migration import AIMigrationSystem
from .ai_commands import AICommands

__all__ = [
    "KnowledgeManager",
    "ProjectManager", 
    "TaskManager",
    "ProjectAnalytics",
    "AIMigrationSystem",
    "AICommands",
]