# 项目偏好与约束

> 记录 Diag-loop 系统的设计偏好、开发约束和行为规则。
> 
> 这些规则是长期迭代中沉淀下来的约定，Agent 在修改代码或文档时应遵守。

---

## 状态管理

- **无 YAML 状态文件**：状态通过实时解析 `knowledge/` 目录生成，不维护独立的 YAML 状态文件。Agent 直接使用 shell 命令（`ls`/`cat`/`grep`）查询当前状态。
- **迭代计数不持久化**：每次运行迭代从 0 开始，不保存到文件。不同 topic 的运行不应累计计数，知识库内容才是跨运行保持的状态。

## 代码设计

- **极简代码，智能外放**：代码只提供基础设施，所有认知工作交给模型。不信任复杂代码逻辑，保持 Agent 代码在最小规模。
- **Skill 目录只提供路径**：代码只提供 Skill 目录路径，不读取或解析 Skill 文件内容。Agent 自行读取和解析，保持代码极简。
- **AgentRunner 基类抽象**：所有 Runner 继承统一的 `AgentRunner` 基类，执行流程为 `pre → build → call → validate → post`。

## 知识库

- **Knowledge 独立 Git 仓库**：`knowledge/` 作为独立 Git 仓库管理，主仓库通过 `.gitignore` 排除。知识库变更历史独立追踪。
- **Agent 自主 Git Commit**：Agent 自己执行 `git add/commit`，代码只负责提醒和验证。commit 消息必须反映 Agent 的认知。
- **自动执行验证**：系统自动验证 Agent 是否完成承诺的工作（如文档创建、research-log 更新、git 状态检查）。

## 文档

- **禁用数字标题**：所有文档禁止使用数字前缀的标题（如 `## 1. xxx`、`### 1.1 xxx`）。插入或删除章节时会导致编号频繁变动，产生无意义的 diff。请使用纯文本标题，依靠 Markdown 层级本身表达结构。

## Agent 行为约束

Harness 通过代码**强制约束 Agent 执行结果**。

### 约定：使用 Shell 命令直接操作

Agent **应该**通过 shell 命令直接操作，而非使用代码封装的工具函数：

| 操作 | 推荐方式 |
|------|----------|
| 读取文档 | `cat knowledge/states/xxx.md` |
| 查询目录 | `ls knowledge/sessions/current/working/` |
| 检查状态 | `git status`, `git log` |
| 提交更改 | `git add knowledge/ && git commit -m "..."` |

**注意**：这只是约定，Harness 无法验证 Agent 是否遵守。Harness 只检查**结果**。

### Harness 强制检查机制（结果导向）

Agent 执行后，Harness **只检查结果**，**不合格时重新启动 Kimi 让 Agent 重做**：

| 检查项 | 检查方法 | 不合格后果 |
|--------|----------|-----------|
| Research Log 更新 | 检查文件内容长度和章节 | 重试，要求补充日志 |
| Git Commit | `git status --porcelain` | 重试，要求执行提交 |
| Stage 输出完整 | 验证文档数量和状态 | 重试，要求继续完善 |

**无法检查**：Agent 是否读取了文档、是否使用了正确的分析方法（只能通过结果推断）

### Git Commit 强制要求

**每次迭代/Stage 后必须提交**，Harness 会验证：

- **命令**：`git add knowledge/ && git commit -m "[prefix]: 描述"`
- **前缀**：`[research]:`, `[state]:`, `[gate]:`, `[map]:`, `[mechanism]:`, `[path]:`, `[session]:`, `[doc]:`, `[report]:`, `[meta]:`, `[sync]:`, `[init]:`
- **格式**：`[prefix]: ${summary}`（冒号后有空格）
- **内容**：必须反映实际变更，不能敷衍

**示例**：
```bash
git add knowledge/
git commit -m "[research]: 发现 TCP 拥塞控制窗口计算涉及的 State 变量"
```

### 递进式探索要求

Harness 验证 Agent 是否真正推进了研究，而非原地踏步：

- **读取历史**：每次执行前必须 `cat knowledge/research-log.md`
- **差异化策略**：相同 Skill 多次执行时要有递进（第1次广度扫描，第2次深度分析，第3次关联建立）
- **明确目标**：避免模糊说法如"继续分析"，要定义具体可验证的目标
- **更新日志**：执行后必须更新 `knowledge/research-log.md`，新条目前置

### Session 管理

- **当前会话路径**：`knowledge/sessions/current/working/`
- **子目录结构**：`states/`, `gates/`, `maps/`, `mechanisms/`, `paths/`, `logs/`
- **会话记录**：`knowledge/sessions/current/session.md` 记录详细执行过程

## Commit Message Prefix 速查

| Prefix | 用途 |
|--------|------|
| `[research]:` | Research Log 更新 |
| `[report]:` | 报告文档更新 |
| `[doc]:` | 一般文档更新 |
| `[session]:` | 会话管理相关 |
| `[state]:` | State 文档创建/更新 |
| `[gate]:` | Gate 文档创建/更新 |
| `[map]:` | Map/拓扑图创建/更新 |
| `[mechanism]:` | Mechanism 机制文档 |
| `[path]:` | Path 诊断路径 |
| `[meta]:` | 元认知/系统改进 |
| `[sync]:` | 文档同步/索引更新 |
| `[init]:` | 初始化/首次提交

## 深度探索

- **ECTM → CR → CMR 深度流程**：深度探索使用系统级 Skills 的三阶段流程：ECTM (evidence-chain-tracking) 发散 → CR (code-reader) 扫描 → CMR (code-mechanism-reader) 深度分析。

## Skill

- **Skill 即方法**：Skill 是方法论的外部化，Agent 可以创建和修改 Skill。每个 Skill 必须自包含、输入/输出明确、模板完整、指令具体。
