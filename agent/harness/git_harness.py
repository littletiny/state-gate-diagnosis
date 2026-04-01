#!/usr/bin/env python3
"""
Git 提交辅助 - 简化版

SoftLimit: Agent 应该自己执行 git add knowledge/ && git commit
HardLimit: ExecutionValidator.check_git_clean() 强制检查提交状态
"""

import subprocess
from pathlib import Path


class GitCommitHarness:
    """Git 提交辅助"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
    
    def has_changes(self, path: str = "knowledge/") -> bool:
        """检查是否有未提交的更改 - HardLimit使用"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", path],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def commit(self, message: str, path: str = "knowledge/") -> bool:
        """
        执行 git add + commit
        注意：Agent 应该自己执行 git 命令，此方法仅在必要时使用
        """
        try:
            # 检查是否是 git 仓库
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False
            
            # 添加变更
            subprocess.run(
                ["git", "add", "--", path],
                cwd=self.base_dir,
                capture_output=True,
                check=True
            )
            
            # 检查是否有变更需要提交
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.base_dir,
                capture_output=True
            )
            if result.returncode == 0:
                return True  # 无变更，视为成功
            
            # 提交
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.base_dir,
                capture_output=True,
                check=True
            )
            return True
            
        except:
            return False
