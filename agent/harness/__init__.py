#!/usr/bin/env python3
"""
Harness 执行框架 - SoftLimit & HardLimit 双层约束机制

设计理念：
- SoftLimit: 通过Prompt hints引导Agent行为（不强制但建议）
- HardLimit: 通过代码检查强制约束Agent输出（不合格时要求重做）
"""

from .constants import GitPrefixes
from .prompt_hints import PromptHints
from .log_manager import ResearchLogManager
from .git_harness import GitCommitHarness
from .validator import ExecutionValidator

__all__ = [
    "GitPrefixes",
    "PromptHints",
    "ResearchLogManager",
    "GitCommitHarness",
    "ExecutionValidator",
]
