#!/usr/bin/env python3
"""
Harness 执行框架 - SoftLimit & HardLimit 双层约束机制

设计理念：
- SoftLimit: 通过Prompt hints引导Agent行为（不强制但建议）
- HardLimit: 通过代码检查强制约束Agent输出（不合格时要求重做）

分层结构：
┌─────────────────────────────────────────┐
│  SoftLimit Layer (Prompt Hints)         │
│  - build_*_prompt() 方法构建引导性提示   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Agent 执行层 (Kimi)                    │
│  - 接收Prompt，执行Task                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  HardLimit Layer (Code Enforcement)     │
│  - ExecutionValidator 执行强制性检查     │
└─────────────────────────────────────────┘
"""

from .constants import GitPrefixes
from .prompt_hints import PromptHints
from .log_manager import ResearchLogManager
from .git_harness import GitCommitHarness
from .session import SessionRecorder, SimpleLockManager
from .validator import ExecutionValidator

__all__ = [
    "GitPrefixes",
    "PromptHints",
    "ResearchLogManager",
    "GitCommitHarness",
    "SessionRecorder",
    "SimpleLockManager",
    "ExecutionValidator",
]
