# System Architecture

> 多阶段知识探索框架（待重新设计）

## Overview

此系统提供自主探索和知识构建的基础框架：
- **文档驱动**: 通过文档状态跟踪进度
- **Skill-based 执行**: 模块化方法论文档
- **Git-tracked**: 所有变更版本控制

## Architecture Layers

```
┌─────────────────────────────────────────┐
│  Layer 2: Runner                        │
│  (agent/base_runner.py)                 │
│  - 执行框架                             │
│  - SoftLimit/HardLimit 双层约束         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Layer 1: Skills                        │
│  (skills/*/SKILL.md)                    │
│  - 自包含的方法论                       │
│  - 定义输入/输出/模板                   │
└─────────────────────────────────────────┘
```

## Components

### Agent Runner

通用执行框架，提供基础执行能力。

**File**: `agent/base_runner.py`

**核心机制**:
- **SoftLimit**: PromptHints 提供规范提示
- **HardLimit**: ExecutionValidator 强制检查
- **模板方法模式**: 子类只需实现 `build_prompt()` 和 `get_cycle_name()`

### Skills

自包含的方法论定义。

**Location**: `skills/{name}/SKILL.md`

**Structure**:
```markdown
# Skill Name

## Purpose
What this skill does

## Input
- Expected input format/location

## Output
- Expected output format/location

## Instructions
Step-by-step for the agent
```

### Knowledge Base

文档存储。

**Location**: `knowledge/`

**Structure**:
```
knowledge/
├── research-log.md       # 探索日志
├── logs/*.log            # 执行日志
└── ...                   # 其他文档（由 Skill 定义）
```

## State-Gate Protocol

领域特定方法论，用于资源流控制分析。

**Reference**: [docs/state-gate-protocol.md](./state-gate-protocol.md)

**Core Model**:
- **State**: 资源级别计数器
- **Gate**: 基于 State 阈值的决策点
- **Action**: 系统响应

## Extension Points

### Custom Domain

替换 State-Gate 为你自己的领域模型：
1. 定义核心概念
2. 创建领域特定 Skills
3. 运行探索

---

**Note**: Pipeline 和 MetaLoop 模块正在重新设计，相关内容已移除。
