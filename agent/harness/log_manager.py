#!/usr/bin/env python3
"""
Research Log 管理 - 简化版

SoftLimit: Agent 应该直接用 cat knowledge/research-log.md 读取
HardLimit: 代码层验证日志是否更新（check_research_log_updated）
"""

from datetime import datetime
from pathlib import Path


class ResearchLogManager:
    """研究日志管理"""
    
    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)
        self.log_path = self.knowledge_dir / "research-log.md"
    
    def read(self) -> str:
        """读取研究日志主文件"""
        if self.log_path.exists():
            return self.log_path.read_text(encoding='utf-8')
        return ""
    
    def prepend_entry(self, title: str, content: str):
        """在日志最前面添加新条目（prepend）"""
        timestamp = datetime.now().isoformat()
        header = "# Research Log\n\n"
        entry = f"## {title} - {timestamp}\n\n{content}\n\n---\n\n"
        
        current = self.read()
        body = current.replace(header, "") if current.startswith(header) else current
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text(header + entry + body, encoding='utf-8')
    
    def build_trajectory(self, task: str) -> str:
        """研究轨迹 - 使用PromptHints生成（SoftLimit）"""
        log_exists = self.log_path.exists()
        
        trajectory = f"""研究轨迹（Research Trajectory）

原始问题: {task}
研究日志: `{self.log_path}` {'(exists)' if log_exists else '(not exists)'}
结构说明: `knowledge/index.md`

**由你自行分析**:
1. 读取研究日志：`cat {self.log_path}`
2. 如需了解目录结构：`cat knowledge/index.md`
3. 识别探索历史（关注 `## ` 开头的条目）
4. 提取上次遗留的"新产生的问题"
5. 确定本次探索目标

分析要点:
- 迭代条目格式: `## Iteration N - [Phase] - [timestamp]`
- 关注: "新产生的问题"、"下次建议"、"关键发现"
- 结合 Git 历史验证: `git log --oneline --grep="^\\[research\\]:"`

当前认知边界（由你根据日志分析填写）:
- Known: 
- Exploring: 
- Unknown: 
"""
        return trajectory
