# Harness 执行框架

> **双层约束机制**：SoftLimit（Prompt引导层）+ HardLimit（代码强制层）

Harness是一套**工程约束机制**，通过分层的方式确保Agent输出符合规范：

- **SoftLimit（软性约束）**: 通过Prompt提供hints、指导和建议，引导Agent行为
- **HardLimit（硬性约束）**: 通过代码检查Output/行为，**不合格时强制要求重做**

---

## 设计原则

```
┌─────────────────────────────────────────┐
│  SoftLimit Layer (Prompt Hints)         │
│  - 编码规范提示、文档模板引导            │
│  - 执行流程建议、最佳实践提示            │
│  - 不强制，但强烈建议遵循                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Agent 执行层 (Kimi)                    │
│  - 接收Prompt，执行Task                 │
│  - 产出Output和行为                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  HardLimit Layer (Code Enforcement)     │
│  - 检查结果是否符合硬性要求              │
│  - 不合格 → 自动重启Agent要求重做        │
│  - 合格 → 继续执行                       │
└─────────────────────────────────────────┘
```

### 核心原则

1. **SoftLimit在前**: 通过Prompt充分引导，降低HardLimit触发概率
2. **HardLimit兜底**: 代码层最终检查，确保底线不被突破
3. **透明可预测**: Agent清楚知道哪些会被检查，失败后会明确告知原因
4. **结果导向**: HardLimit只检查Output，不追踪执行过程

---

## SoftLimit（软性约束层）

SoftLimit通过各种Prompt hints引导Agent行为，**不强制但强烈建议**。

### Prompt Hint 类型

| 类型 | 作用 | 示例 |
|------|------|------|
| **规范提示** | 代码/文档风格规范 | "使用纯文本标题，禁止数字前缀" |
| **模板引导** | 输出格式模板 | "文档必须包含 frontmatter" |
| **流程建议** | 执行顺序建议 | "执行前先读取 research-log.md" |
| **最佳实践** | 推荐做法 | "优先使用 shell 命令" |

### SoftLimit 实现位置

```
1. Skill 文档 (skills/*/SKILL.md)
   └── Instructions 部分提供执行指导

2. Runner Prompt (agent/base_runner.py)
   └── build_prompt() 构建的系统级提示
```

### SoftLimit 示例

```markdown
## Instructions (SoftLimit)

执行前请：
1. 读取 `knowledge/research-log.md` 了解历史

输出要求：
- 文档使用 YAML frontmatter 格式
- 标题禁止使用数字前缀
- 关键发现必须记录在日志中

建议：
- 相同 Skill 多次执行时采用差异化策略
- 优先使用 shell 命令直接操作文件
```

---

## HardLimit（硬性约束层）

HardLimit通过代码**强制检查**Agent的输出和行为，**不合格时必须重做**。

### 强制检查项

| 检查项 | 检查方法 | 失败处理 |
|--------|----------|----------|
| **Git Commit** | `check_git_clean()` | 要求重新执行 commit |
| **Research Log 更新** | `check_research_log_updated()` | 要求补充日志记录 |
| **文档创建** | 检查 working/ 目录 | 要求创建缺失文档 |

### HardLimit 实现位置

```python
# agent/harness.py - 核心检查器
class ExecutionValidator:
    def validate_execution(...) -> dict     # 执行结果验证
    def check_git_clean(...) -> bool        # Git 状态检查
    def check_research_log_updated(...) -> bool  # 日志更新检查

# agent/base_runner.py - 验证触发点
class AgentRunner:
    def validate(...) -> dict               # 触发 HardLimit 检查
    def run_cycle() -> bool                 # 检查失败时终止循环
```

### HardLimit 检查流程

```
Agent 执行完成
      ↓
[HardLimit Check]
  ├─ Git Clean? ──No──→ Retry Prompt: "请执行 git commit"
  ├─ Log Updated? ─No─→ Retry Prompt: "请更新 research-log.md"  
  └─ Output Valid? ─No─→ Retry Prompt: "输出不符合要求，请修复"
      ↓
   Yes → 继续执行
```

### Retry Prompt 模板

当HardLimit检查失败时，系统构建Retry Prompt要求Agent重做：

```python
def build_retry_prompt(reason: str, instruction: str, original_task: str) -> str:
    return f'''上次执行未通过结果验证。

检查失败: {reason}

你需要: {instruction}

修复后，请继续完成原任务:
{original_task}

注意：
1. 先修复上述问题
2. 然后继续完成原任务的所有要求
3. 最后再次执行 git add 和 git commit
'''
```

---

## 双层协作示例

以 **Git Commit 规范** 为例：

### SoftLimit（Prompt Hint）

```markdown
### Git Commit 规范提示

每次迭代后必须提交更改：
- 执行 `git add knowledge/` 和 `git commit`
- 使用规范前缀：`[research]:`, `[state]:`, `[gate]:` 等
- 提交消息必须反映实际变更内容

可用前缀：
- `[research]:` Research Log 更新
- `[state]:` State 文档创建/更新
- `[gate]:` Gate 文档创建/更新
```

### HardLimit（Code Enforcement）

```python
def check_git_clean(self, base_dir: str) -> bool:
    """检查是否有未提交的更改"""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "knowledge/"],
        cwd=base_dir, capture_output=True, text=True
    )
    if result.stdout.strip():
        # HardLimit 触发：未提交更改
        return False  # → 将触发 Retry
    return True
```

### 协作效果

1. Agent 首先看到 SoftLimit 提示，**应该**按规范执行 commit
2. 如果 Agent 忽略提示，HardLimit 在代码层**强制捕获**
3. 触发 Retry，Agent 必须修复后才能继续

---

## 核心组件

### GitPrefixes

Git Commit 前缀常量定义。

```python
from agent.harness import GitPrefixes

GitPrefixes.RESEARCH    # "[research]:"
GitPrefixes.REPORT      # "[report]:"
GitPrefixes.DOC         # "[doc]:"
GitPrefixes.SESSION     # "[session]:"
GitPrefixes.STATE       # "[state]:"
GitPrefixes.GATE        # "[gate]:"
GitPrefixes.META        # "[meta]:"
```

### ResearchLogManager

研究日志管理（简化版）。**Agent 应该直接使用 shell 命令读取**，代码层仅在需要程序化写入时使用。

```python
from agent.harness import ResearchLogManager

log_mgr = ResearchLogManager("knowledge")

# 读取日志（Agent 应直接用: cat knowledge/research-log.md）
content = log_mgr.read()

# 前置添加新条目
log_mgr.prepend_entry("Iteration 1", "发现 State A 和 Gate B")

# 构建研究轨迹 prompt 片段
trajectory = log_mgr.build_trajectory("分析 TCP 拥塞控制")
```

### GitCommitHarness

Git 提交辅助。**Agent 应该自己执行 git 命令**，此类仅在必要时供代码调用。

```python
from agent.harness import GitCommitHarness

harness = GitCommitHarness(".")

# 检查是否有未提交更改
has_changes = harness.has_changes("knowledge/")

# 执行提交（优先让 Agent 自己做）
harness.commit("[research]: 描述", "knowledge/")
```

### SessionRecorder

会话记录器，创建带 task name 的目录结构 + 软链接管理。

```python
from agent.harness import SessionRecorder

session = SessionRecorder("knowledge", "分析 TCP 带宽问题")

# 获取工作目录
working_dir = session.get_working_dir()
states_dir = session.get_working_dir("states")

# 记录阶段结果
session.record_stage(
    stage_name="discovery",
    summary="发现 5 个 State 变量",
    findings=["State: tcp_memory_allocated", "State: sk_buff_count"],
    documents=["states/tcp_memory_allocated.md"],
    questions=["生产者/消费者关系待确认"]
)

# 结束会话
session.finalize(success=True, stats={"states": 5, "gates": 3})
```

**创建的目录结构**：
```
knowledge/sessions/
├── current -> 20260331-103000-task/  # 软链接
├── running -> 20260331-103000-task/  # 运行时软链接
└── 20260331-103000-task/
    ├── working/
    │   ├── states/     # State 文档
    │   ├── gates/      # Gate 文档
    │   ├── maps/       # 拓扑图
    │   ├── mechanisms/ # 机制分析
    │   ├── paths/      # 诊断路径
    │   └── logs/       # 执行日志
    ├── session.md      # 会话记录
    └── manifest.json   # 元数据
```

### SimpleLockManager

极简文件锁管理，确保单实例运行。

```python
from agent.harness import SimpleLockManager
lock = SimpleLockManager("knowledge", ".")

# 获取锁
try:
    lock_info = lock.acquire("分析任务")
    # ... 执行任务 ...
    lock.release(success=True)
except RuntimeError as e:
    # Agent 正在运行中
    print(e)
```

### ExecutionValidator

执行结果验证器，**HardLimit 的核心实现**。

```python
from agent.harness import ExecutionValidator

validator = ExecutionValidator("knowledge")

# 检查 research-log 是否更新
updated = validator.check_research_log_updated()

# 检查 Git 是否干净
clean = validator.check_git_clean(".")

# 验证执行结果（HardLimit 入口）
result = validator.validate_execution(
    output=output_text,
    returncode=0,
    research_log_before=before_content
)

# 格式化报告
report = validator.format_validation_report(result)
```

---

## HardLimit 检查详情

### 能检查的项目

| 检查项 | 方法 | 检查内容 |
|--------|------|----------|
| Research Log 更新 | `check_research_log_updated()` | 文件是否存在、内容长度、是否有新条目 |
| Git Commit | `check_git_clean()` | `git status` 是否有未提交更改 |
| 文档创建 | 检查 working/ 目录 | 特定类型文档是否存在 |

### 无法检查的项目

Harness **无法**验证（这些依赖 SoftLimit）：
- Agent 是否读取了文档
- Agent 是否使用了 shell 命令
- Agent 分析过程是否正确
- Agent 是否遵循了最佳实践

---

## 扩展 HardLimit

如需添加新的强制检查项：

```python
class ExecutionValidator:
    
    def validate_execution(self, output, returncode, research_log_before):
        result = {
            # ... 现有检查 ...
            "new_check_passed": True,  # 新增检查项
            "warnings": []
        }
        
        # 新增 HardLimit 检查
        if not self._check_new_requirement(output):
            result["new_check_passed"] = False
            result["warnings"].append("New requirement not met")
        
        return result
```

---

## 使用建议

### Agent 层（Prompt Builder）

1. **充分使用 SoftLimit**: 在 Prompt 中提供清晰的 hints 和模板
2. **说明 HardLimit**: 告诉 Agent 哪些检查会被强制执行
3. **提供修复指导**: 告诉 Agent 如果检查失败如何修复

### Runner 层

1. **保持 HardLimit 精简**: 只检查真正关键的约束
2. **明确的失败信息**: 检查失败时清楚说明原因和修复方法
3. **自动 Retry**: 利用 Retry 机制让 Agent 自我修复

### 避免过度约束

- **SoftLimit 可以丰富**: 提供充分的引导和建议
- **HardLimit 必须克制**: 只保留底线检查，避免频繁触发 Retry
