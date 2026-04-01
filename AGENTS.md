# Diag-loop Developer Guide

你是这个项目的开发者，负责开发、维护 diag-loop 系统本身。

## 项目结构

```
run.sh              # OPS 入口（切到 bin/ 执行 evolve.py）
bin/
  evolve.py         # OPS 执行器
  AGENTS.md         # OPS 角色上下文（模型读取）
agent/
  base_runner.py    # AgentRunner 基类
  self_explore.py   # 自主探索模式（继承基类，Agent 自主决策）
  pipeline.py       # Pipeline 模式（待重新设计）
  meta_loop.py      # Meta 决策循环（待重新设计）
  harness.py        # PromptHints + ExecutionValidator（Soft/Hard Limit）
skills/             # Skill 定义（自包含的方法论文档）
rules/              # Pipeline YAML 配置（待重新设计）
knowledge/          # 知识库（Agent 生成，Git 跟踪）
docs/preferences.md # 代码规范、设计偏好
```

## 核心设计原则

- **代码极简**：只提供基础设施（状态查询、文件管理），不做认知决策
- **模型自治**：所有认知工作（决策、分析、改进）由模型承担
- **Skill 驱动**：可配置的方法论，模型自主选择和执行

## Harness 双层约束

SoftLimit（Prompt hints 引导）→ Agent 执行 → HardLimit（代码强制检查）→ 失败则 Retry

关键类：
- `PromptHints`（harness.py）：生成规范提示、模板引导、最佳实践建议
- `ExecutionValidator`（harness.py）：强制检查 Git 状态、日志更新、Stage 完成度

## 扩展 Runner

继承 AgentRunner，实现 build_prompt() 和 get_cycle_name()：

```python
from agent.base_runner import AgentRunner

class MyRunner(AgentRunner):
    def build_prompt(self) -> str:
        return "..."
    
    def get_cycle_name(self) -> str:
        return f"Cycle-{self.current_cycle}"
```

## 开发约束

- 禁止数字前缀标题（如 `## 1. xxx`），避免产生无意义 diff
- 修改前查阅 docs/preferences.md
- Git commit 必须带规范前缀：`[research]:`, `[state]:`, `[gate]:` 等
- 本文档是写给 Agent 看的，不要写为了人类阅读的额外格式（分割线、装饰性 ASCII 图表、冗余空行）
- **不要直接修改代码**：任何涉及架构调整、方案变更、接口改动的操作，必须先提出方案并等待用户确认，获批后方可执行

## 参考

- `docs/mechanism-map.md` - 机制到代码的映射（快速定位代码位置）
- `docs/preferences.md` - 代码规范、设计偏好

---

**Note**: Pipeline 和 MetaLoop 模块正在重新设计，接口细节待确定。
