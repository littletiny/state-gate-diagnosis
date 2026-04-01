# Net-Diag 导航

统一入口: `./run.sh` (OPS) / `kimi` (Developer)

## 两种模式

| 模式 | 命令 | 特点 |
|------|------|------|
| **自主模式** | `./run.sh` | Agent 根据知识库状态自主决定 Phase |
| **Pipeline** | `./run.sh -c rules/pipeline.yaml` | 按 YAML 配置顺序执行 Stage（待重新设计） |

## 核心概念: 递进式探索

```
原始问题 → 迭代1发现 → 迭代2深入 → 迭代3关联 → 迭代4验证
    ↑                                                  ↓
    └────────────── 认知螺旋上升 ──────────────────────────┘
```

Agent 每次执行必须：
1. 读取 `knowledge/sessions/current/session.md` 了解当前会话历史
2. 基于上次发现继续深入（不要原地踏步）
3. 更新会话记录新发现
4. 执行 `git commit` 提交更改

**Harness 双层约束**：
- **SoftLimit**: Prompt hints 引导 Agent 行为（规范提示、模板引导）
- **HardLimit**: 代码强制检查输出（Git状态、日志更新、Stage完成度），不合格时重做

### 会话管理

每个任务独立会话，自动隔离：

```
knowledge/sessions/
├── current -> 20260331-103000-task/  # 🔗 软链接指向当前会话
├── 20260331-103000-task/             # 已完成会话
│   ├── working/                      # 工作目录
│   │   ├── states/                   # State 文档
│   │   ├── gates/                    # Gate 文档
│   │   ├── maps/                     # 拓扑图
│   │   └── logs/                     # 执行日志
│   ├── session.md                    # 详细执行记录
│   └── manifest.json                 # 元数据（文档清单）
└── README.md                         # 会话索引
```

## 命令导航

### 自主模式

```bash
./run.sh                       # 标准模式，Agent 自主迭代
./run.sh -n 5                  # 最多5轮迭代
./run.sh -t "分析TCP"          # 指定任务描述
./run.sh --skill discovery -n 1  # 使用指定 Skill，1轮
```

### Pipeline 模式（待重新设计）

```bash
# 暂不可用，待重新设计
# ./run.sh -c rules/pipeline.yaml
```

### 信息查看

```bash
./run.sh --list-skills              # 列出可用 Skills
cat knowledge/sessions/current/session.md       # 查看当前会话记录
ls -la knowledge/sessions/current/working/      # 查看当前工作目录
ls skills/                          # 查看 Skill 目录
cd knowledge && git log --oneline   # 知识库 Git 历史
git status knowledge/               # 检查未提交更改
```

### 调试与清理

```bash
rm -rf agent/__pycache__                    # 清理缓存
rm -rf knowledge/sessions/current/working/logs/*.log  # 清理当前会话日志

# 强制重置（删除当前会话）
rm -rf knowledge/sessions/current
rm -f knowledge/lock.file knowledge/state.json
```

## 项目结构

```
net-diag/
├── run.sh                 # OPS 统一入口
├── README.md              # 项目概览
├── AGENTS.md              # Developer 指南（架构、扩展）
│
├── bin/                   # OPS 运行时目录
│   ├── evolve.py          # OPS 执行器
│   └── AGENTS.md          # OPS 指南（递进式探索）
│
├── agent/                 # Agent 实现
│   ├── base_runner.py     # 通用执行框架（AgentRunner 基类）
│   ├── self_explore.py    # 自主探索执行器（继承基类）
│   ├── pipeline.py        # Pipeline 执行器（待重新设计）
│   ├── meta_loop.py       # Meta 决策循环（待重新设计）
│   ├── harness.py         # 通用工具（Git/验证/日志管理）
│   └── tools/

│
├── skills/                # Skill 定义（方法论）
│   ├── discovery/SKILL.md
│   ├── analysis/SKILL.md
│   ├── connection/SKILL.md
│   ├── diagnosis/SKILL.md
│   └── report/SKILL.md
│
├── rules/                 # Pipeline 配置（待重新设计）
│   └── pipeline.yaml
│
└── knowledge/             # 知识库（Agent 生成，Git 跟踪）
    ├── sessions/          # 会话目录
    │   ├── current/       # 当前运行会话（软链接或目录）
    │   │   ├── working/   # 工作目录
    │   │   │   ├── states/*.md   # State 变量
    │   │   │   ├── gates/*.md    # Gate 检查点
    │   │   │   ├── maps/*.md     # 拓扑图
    │   │   │   └── logs/*.log    # 执行日志
    │   │   ├── session.md        # 会话记录
    │   │   └── manifest.json     # 元数据
    │   └── README.md      # 会话索引
    ├── research-log.md    # 研究日志主索引
    └── state.json         # 成功标志
```

## 文档索引

| 文档 | 用途 | 目标读者 |
|------|------|----------|
| [README.md](./README.md) | 项目概览、快速开始 | 所有人 |
| [AGENTS.md](./AGENTS.md) | Developer 指南（架构、扩展） | DEVELOPER |
| [bin/AGENTS.md](./bin/AGENTS.md) | OPS 指南（递进式探索） | OPERATOR |
| [knowledge/index.md](./knowledge/index.md) | 知识库索引 | 所有人 |

## 快速任务

### 添加新 Skill

1. 创建 `skills/{name}/SKILL.md`
2. 定义 Purpose/Input/Output/Instructions
3. 测试: `./run.sh --skill {name} -n 1`

### 添加新 Pipeline（待重新设计）

Pipeline 配置和 Stage 定义正在重新设计，暂不可用。

### 检查执行结果

执行后查看 HardLimit 验证报告：
```
[Validation Report - HardLimit Check]
  Success: True
  Research Log Updated: True
  Git Clean: True
  Warnings:
    - (empty if all passed)
```

如果检查失败，Harness 会构建 Retry Prompt 要求 Agent 修复后重做。

---

**Note**: Pipeline 和 MetaLoop 模块正在重新设计，相关命令和说明已标记。
