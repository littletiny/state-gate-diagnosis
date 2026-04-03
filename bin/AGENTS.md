# 递进式探索指南

Agent 探索必须是**递进式**的，而非重复原地踏步。每次迭代应基于前一次的发现继续深入。

## 核心概念

### State-Gate 模型
- **State**: 离散状态节点，有明确语义边界、可观测性、转换条件
- **Gate**: 基于 State 做决策的关键代码位置，决定 allow/reject/delay/divert
- **Action**: Gate 决策产生的副作用，可能导致 State 转换
- **驱动类型**: Condition-Driven（条件触发）/ Message-Driven（消息触发）/ Hybrid

### 四阶段探索流程

| 阶段 | 目标 | 输出 |
|------|------|------|
| Discovery | 发现 State/Gate 实例 | states/*.md, gates/*.md |
| Analysis | 深入分析 State/Gate 行为 | 补充语义、驱动、异常处理 |
| Connection | 建立拓扑关系 | maps/*.md |
| Diagnosis | 根因追溯 | paths/*_diagnosis.md |

## 检查清单

### State 分析要点
- 语义：代表什么？如何与相邻状态区分？
- 驱动：Condition-Driven / Message-Driven / Hybrid？
- 入口：什么条件触发进入此状态？
- 出口：什么条件触发离开此状态？
- 关联：哪些 Gate 检查此状态？什么决策依赖它？
- 异常：状态转换失败或卡住会怎样？

### Gate 分析要点
- 触发时机：状态变更 / 条件满足 / 消息接收 / 超时？
- 判断条件：检查什么标准？阈值比较？复合条件？
- 决策来源：硬编码 / sysctl / 计算值 / 状态注册表？
- 后续动作：决策后发生什么？恢复路径？

## 诊断原则
- **机制优于症状**: 不止问"什么坏了"，要找"怎么坏的"因果链
- **证据驱动**: 所有结论必须包含代码引用 (file:line)
- **反直觉假设**: 至少包含一个与直觉矛盾的假设
- **异常值价值**: 无法解释的细节往往是真正根因
- **根因层级**: Direct（哪个 Gate 触发）→ Intermediate（为什么条件发生）→ Deep（为什么 State 异常）

## Skill 使用

- **CR (Code-Reader)**: 阅读新代码库、生成架构概览
- **CMR (Code-Mechanism-Reader)**: 深入分析特定机制/模块

需要阅读代码时，主动调用 skill 获取结构化分析方法。

## 文档规范

- 标题不要使用数字前缀（如 `## 1. xxx`），避免产生无意义 diff
- State/Gate 文档建议包含：描述、相关代码、关联关系

## 执行前必做

- 阅读 git log，了解历史进展
- 自行决定什么时候调整侧重点

## 参考

- [knowledge/index.md](index.md) - 知识库结构说明
