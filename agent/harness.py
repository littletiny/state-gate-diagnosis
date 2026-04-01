#!/usr/bin/env python3
"""
Harness 执行框架 - 兼容性导入

所有实现已迁移到 harness/ 子模块：
- harness/constants.py     - GitPrefixes
- harness/prompt_hints.py  - PromptHints
- harness/log_manager.py   - ResearchLogManager
- harness/git_harness.py   - GitCommitHarness
- harness/validator.py     - ExecutionValidator

Session 管理已独立：
- session.py               - SessionRecorder, SimpleLockManager

此文件保留用于向后兼容，新代码请直接从对应模块导入。
"""

from harness import (
    GitPrefixes,
    PromptHints,
    ResearchLogManager,
    GitCommitHarness,
    ExecutionValidator,
)

__all__ = [
    "GitPrefixes",
    "PromptHints",
    "ResearchLogManager",
    "GitCommitHarness",
    "ExecutionValidator",
]
