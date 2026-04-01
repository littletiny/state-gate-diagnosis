#!/usr/bin/env python3
"""
SoftLimit: Prompt Hints 生成器

这些hints通过Prompt传递给Agent，不强制但建议遵循。
如果Agent忽略hints，HardLimit层会在后续检查中捕获问题。

模板文件位于 agent/prompts/ 目录：
- git-commit-hint.md
- research-trajectory-hint.md
- document-format-hint.md
- execution-flow-hint.md
- retry-prompt.md
"""

from pathlib import Path
from string import Template


class PromptHints:
    """SoftLimit层：生成各种Prompt hints引导Agent行为"""
    
    _default_instance = None
    
    def __init__(self, prompts_dir: str = None):
        """
        初始化，可选指定 prompts 目录
        
        Args:
            prompts_dir: prompt 模板目录，默认使用 agent/prompts/
        """
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            # 默认路径：从 harness/ 上溯到 agent/ 下的 prompts/
            self.prompts_dir = Path(__file__).parent.parent / "prompts"
    
    @classmethod
    def _get_default(cls):
        """获取默认实例（单例模式）"""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance
    
    def _load_template(self, name: str) -> str:
        """加载模板文件，如果不存在返回空字符串"""
        template_file = self.prompts_dir / f"{name}.md"
        if template_file.exists():
            return template_file.read_text(encoding='utf-8')
        return ""
    
    @classmethod
    def git_commit_hint(cls) -> str:
        """Git commit 规范提示"""
        return cls._get_default()._load_template("git-commit-hint")
    
    @classmethod
    def research_trajectory_hint(cls, task: str) -> str:
        """研究轨迹构建提示"""
        template = cls._get_default()._load_template("research-trajectory-hint")
        if template:
            return template.format(task=task)
        return f"原始问题: {task}"
    
    @classmethod
    def document_format_hint(cls) -> str:
        """文档格式规范提示"""
        return cls._get_default()._load_template("document-format-hint")
    
    @classmethod
    def execution_flow_hint(cls) -> str:
        """执行流程提示"""
        return cls._get_default()._load_template("execution-flow-hint")
    
    @classmethod
    def build_retry_prompt(cls, reason: str, instruction: str, original_task: str) -> str:
        """
        构建HardLimit触发后的Retry Prompt
        
        当HardLimit检查失败时，使用此prompt要求Agent重做。
        """
        template = cls._get_default()._load_template("retry-prompt")
        if template:
            return template.format(
                reason=reason,
                instruction=instruction,
                original_task=original_task
            )
        # Fallback: 如果模板不存在，返回简单的提示
        return f"[Harness] 检查失败: {reason}。需要: {instruction}"
