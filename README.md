# Net-Diag

递进式知识探索系统，用于网络诊断领域。

## 核心理念

**递进式探索 (Research Trajectory)**
```
原始问题 → 迭代1发现 → 迭代2深入 → 迭代3关联 → 迭代4验证
    ↑                                                  ↓
    └────────────── 认知螺旋上升 ─────────────────────────┘
```

每次迭代基于前一次的发现继续深入，避免原地踏步。

## 快速开始

```bash
# 启动探索
./run.sh -t "分析 TCP 带宽问题" --src-dir=/path/to/linux -n 10

# 观察执行
# - 读取 research-log.md 了解历史
# - 自动验证执行结果
# - 自动 git commit
```

## 系统架构

```
┌─────────────────────────────────────────┐
│         AgentRunner (基类)               │
│  ├─ pre_execute()    - 执行前准备        │
│  ├─ build_prompt()   - 构建 Prompt      │
│  ├─ call_agent()     - 调用 Kimi        │
│  ├─ validate()       - 验证结果         │
│  └─ post_execute()   - 执行后处理        │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Skills + Knowledge Base                │
│  - Skill: 方法论文档                    │
│  - Knowledge: 探索产出                  │
└─────────────────────────────────────────┘
```

## 项目结构

```
agent/
├── base_runner.py      # 通用执行框架基类
├── harness.py          # Git/验证/日志管理
└── ...

skills/
└── */SKILL.md          # 方法论文档

knowledge/              # Agent 生成内容（Git 跟踪）
├── sessions/           # 会话目录（按任务隔离）
│   ├── current -> ...  # 🔗 软链接指向当前/最新会话
│   └── 202603.../      # 历史会话
│       ├── working/    # 工作目录
│       ├── session.md  # 会话记录（详细）
│       └── manifest.json
├── research-log.md     # 研究日志主索引
└── index.md            # 知识库索引
```

## 递进式探索流程

### 执行前 Agent 必做

- 读取 `knowledge/sessions/current/session.md` 了解当前会话历史
- 构建研究轨迹（原始问题 → 探索历史 → 认知边界 → 本次目标）
- 明确 Known / Exploring / Unknown

### 会话生命周期

```
启动 → 创建 sessions/20260331-103000-running/
          ↓
        创建软链接 current -> 20260331-103000-running/
          ↓
运行 → 在 working/ 下创建文档、日志
          ↓
完成 → 删除软链接，重命名目录
          ↓
        生成 state.json 作为成功标志
```

### 执行中

- 基于研究轨迹继续深入
- 差异化策略：
  - 第1次：广度优先，扫描发现
  - 第2次：深度优先，深入分析
  - 第3次：关联分析，建立关系
  - 第4次+: 缺口填补

### 执行后 Agent 必做

- 更新 `knowledge/research-log.md`（新条目前置）
- Git commit 所有更改
- 输出结构化结果

### Harness 双层约束验证

系统通过 **SoftLimit（Prompt引导）** + **HardLimit（代码强制）** 双层机制确保输出质量：

```
SoftLimit (Prompt Hints)     HardLimit (Code Enforcement)
    ↓                                   ↓
 规范提示                          Git提交检查
 模板引导                          日志更新检查  
 流程建议                          文档创建检查
    ↓                                   ↓
  建议遵循                    不合格 → 强制重做
```

详见 [docs/harness.md](./docs/harness.md)。

## 核心概念

### State-Gate 模型

- **State**: 资源计数器
- **Gate**: 决策点
- **Action**: 系统响应

详见 [docs/state-gate-protocol.md](./docs/state-gate-protocol.md)。

### 设计原则

1. **递进式**: 每次迭代基于前一次发现继续深入
2. **双层约束**: SoftLimit（Prompt引导）+ HardLimit（代码强制）
3. **Git 跟踪**: 所有 knowledge/ 更改自动 commit
4. **自主验证**: Harness 自动验证 Agent 输出
5. **独立迭代**: 每次运行迭代从 0 开始

## 示例：网络带宽分析

```bash
# 启动分析
./run.sh -t "分析特定主机网络吞吐性能下降"

# 查看当前会话记录
cat knowledge/sessions/current/session.md

# 查看会话工作目录
ls -la knowledge/sessions/current/working/
```

## 故障排除

**检查 Kimi CLI**:
```bash
which kimi
kimi --version
```

**重置知识库**:
```bash
# 备份后重置
mv knowledge knowledge.backup.$(date +%s)
mkdir knowledge

# 或使用 git
git checkout -- knowledge/
```

**检查未提交更改**:
```bash
git status knowledge/
git diff knowledge/
```

## 文档索引

| 文档 | 内容 |
|------|------|
| [AGENTS.md](AGENTS.md) | Developer 指南（架构、扩展） |
| [bin/AGENTS.md](bin/AGENTS.md) | OPS 指南 |
| [NAVIGATION.md](NAVIGATION.md) | 项目结构、快速命令 |
| [docs/state-gate-protocol.md](docs/state-gate-protocol.md) | State-Gate 方法论 |

## 环境要求

- Python 3.8+
- Kimi CLI (`kimi` 命令可用)
- Git (用于更改跟踪)
- Linux 内核源码（可选，用于网络分析）

---

**Note**: Pipeline 和 MetaLoop 模块正在重新设计，相关使用说明已移除。
