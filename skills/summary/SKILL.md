---
name: summary
description: SUM - Summary Report Generator. Generate structured final reports by consolidating analysis documents from previous stages (CR, CMR, Explore, etc).
---

# Summary Report Generator

**定位：** 报告生成专家，负责整合多阶段分析结果，输出结构化最终报告。

---

## 核心目标

将分散的分析文档（架构理解、机制分析、探索发现）整合为一份**结构清晰、结论明确、可执行**的最终报告。

---

## 输入规范

读取以下目录中的分析文档：
- `doc/*.md` - CR/CMR 生成的架构和机制文档
- `knowledge/states/*.md` - Explore 阶段发现的状态
- `knowledge/gates/*.md` - Explore 阶段发现的决策点
- `knowledge/maps/*.md` - Explore 阶段构建的拓扑图
- `knowledge/research-log.md` - 研究日志

---

## 输出规范

**单一输出文件：** `knowledge/final-report.md`

### 报告结构

```markdown
# 分析报告：{任务名称}

生成时间: {timestamp}
基于文档: {来源文档列表}

---

## 一、执行摘要 (Executive Summary)

3-5 句话概括：
- 分析目标
- 核心发现（最关键的结论）
- 建议行动

---

## 二、背景与范围

### 2.1 分析目标
{任务描述}

### 2.2 分析范围
- 代码库：{路径}
- 关键模块：{列表}

### 2.3 方法论
- Code-Reader：架构全景扫描
- Code-Mechanism-Reader：关键机制深入
- Explore：自由探索与验证

---

## 三、架构概览 (Architecture Overview)

基于 CR 输出的 `doc/01-architecture-overview.md`：

### 3.1 技术栈
{技术栈总结}

### 3.2 分层结构
{分层描述}

### 3.3 核心组件
| 组件 | 职责 | 关键文件 |
|------|------|----------|
| {name} | {desc} | {file} |

---

## 四、关键机制分析 (Key Mechanisms)

基于 CMR 输出的 `doc/mechanism-*.md`：

### 4.1 {机制名}
**一句话定义：** {definition}

**核心流程：**
```
{流程简述}
```

**关键代码位置：**
- `{file:line}` - {作用}

### 4.2 {机制名}
...

---

## 五、深入发现 (Deep Dive Findings)

基于 Explore 阶段的知识库：

### 5.1 关键 State
| State | 语义 | 相关 Gate |
|-------|------|-----------|
| {name} | {desc} | {gates} |

### 5.2 关键 Gate
| Gate | 决策逻辑 | 触发条件 |
|------|----------|----------|
| {name} | {logic} | {trigger} |

### 5.3 重要发现
1. **{发现标题}**
   - 证据：{引用文档或代码}
   - 影响：{对系统的影响}

---

## 六、问题与风险 (Issues & Risks)

### 6.1 已识别问题
| 问题 | 严重程度 | 位置 | 建议 |
|------|----------|------|------|
| {desc} | {H/M/L} | {loc} | {action} |

### 6.2 潜在风险
- {风险描述}：{理由}

---

## 七、结论与建议 (Conclusions & Recommendations)

### 7.1 核心结论
1. {结论 1}
2. {结论 2}
3. {结论 3}

### 7.2 行动建议
| 优先级 | 建议 | 负责人 | 预期收益 |
|--------|------|--------|----------|
| P0 | {action} | {owner} | {benefit} |
| P1 | {action} | {owner} | {benefit} |

### 7.3 后续工作
- [ ] {待办事项 1}
- [ ] {待办事项 2}

---

## 八、参考资料 (References)

### 8.1 生成的文档
- `doc/01-architecture-overview.md` - 架构全景
- `doc/mechanism-{name}.md` - 机制分析
- `knowledge/states/*.md` - 状态定义
- `knowledge/gates/*.md` - 决策点定义
- `knowledge/maps/*.md` - 拓扑关系

### 8.2 关键代码引用
- `{file:line}` - {description}

---

*报告由 Summary Skill 自动生成*
```

---

## 执行步骤

### Step 1: 收集输入
读取所有相关文档：
```bash
ls doc/*.md knowledge/*/*.md knowledge/*.md 2>/dev/null
```

### Step 2: 提取关键信息
对每份输入文档：
- 识别文档类型（架构/机制/状态/门/地图）
- 提取核心结论
- 记录关键引用（文件路径、行号）

### Step 3: 整合与去重
- 合并相似结论
- 消除矛盾信息
- 建立引用关联

### Step 4: 生成报告
按上述模板填充内容，确保：
- 每个章节都有内容（如无内容则标注"N/A"）
- 所有关键结论都有文档或代码引用
- 报告可独立阅读（不依赖原文档）

### Step 5: 输出与确认
- 写入 `knowledge/final-report.md`
- 更新 `knowledge/research-log.md` 记录报告生成
- Git commit：`[summary]: 生成最终分析报告`

---

## 质量标准

- [ ] 报告结构完整，8 个章节齐全
- [ ] 执行摘要能在 30 秒内传达核心信息
- [ ] 每个结论都有可追溯的引用
- [ ] 建议具体、可执行、有优先级
- [ ] 无明显的信息遗漏或矛盾

---

## 注意事项

1. **不要新增分析**：Summary 只整合已有内容，不做新的代码探索
2. **保持客观**：如实反映分析结果，不夸大或缩小发现
3. **重视引用**：每个关键结论都要标注来源文档
4. **行动导向**：结论必须转化为可执行的建议
