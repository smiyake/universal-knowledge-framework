"""AI integration module for Universal Knowledge Framework."""

from .session_tracker import SessionTracker
from .claude_manager import ClaudeManager
from .auto_updater import AutoUpdateManager
from .pattern_learner import PatternLearner

__all__ = ['SessionTracker', 'ClaudeManager', 'AutoUpdateManager', 'PatternLearner']