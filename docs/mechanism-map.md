# 机制到代码映射

模糊正确即可，帮助快速定位代码。

## Harness 双层约束

**机制**: Prompt 引导 + 代码强制检查

**代码**:
- `agent/harness.py`
  - `PromptHints` - 生成规范提示（SoftLimit）
  - `ExecutionValidator` - 强制检查（HardLimit）
  - `SimpleLockManager` - 单实例运行锁
  - `SessionRecorder` - 会话目录管理

**调用链**:
```
AgentRunner.run_cycle()
  -> build_prompt()  # 可插入 PromptHints
  -> call_agent()     # 调用 Kimi
  -> validate()       # ExecutionValidator 检查
  -> 失败则触发 Retry Prompt
```

## Prompt 构建机制

**核心**: Prompt 是驱动 Agent 的"主程序"，代码只负责组装，认知逻辑全在 Prompt 里

**Prompt 组成部分**:

1. 系统角色定义 - build_prompt() 开头写死
   "你是 Linux 内核网络专家..."

2. 研究轨迹 (Research Trajectory) - ResearchLogManager 生成
   - 历史迭代摘要
   - 上次遗留问题
   - 本次目标建议

3. Skill 方法论 - 直接读取 skills/{name}/SKILL.md
   - Purpose/Input/Output/Instructions

4. 具体任务指令 - Runner 构建时传入
   - 当前要做什么

5. SoftLimit Hints - PromptHints 生成
   - Git commit 规范
   - 文档格式要求
   - 输出模板

6. 输出格式要求 - Skill Template + Runner 要求
   - 执行摘要结构
   - 必须更新的文件清单

**代码组装位置**:
- `agent/base_runner.py` - 基础 Prompt 构建

**动态内容来源**:
- 研究轨迹：`ResearchLogManager.build_trajectory(task)`
- Skill 内容：`get_skill_path(skill)` 读取 `skills/{name}/SKILL.md`
- 规范提示：`PromptHints.git_commit_hint()`, `document_format_hint()`

**修改行为只需改 Prompt**:
- 改 Skill -> 改 `skills/*/SKILL.md`
- 改规范提示 -> 改 `PromptHints` 类
- 改任务逻辑 -> 改 Runner 的 `build_prompt()`

## Skill 系统

**机制**: 自包含的方法论文档

**代码**:

  - `get_skill_path()` - 查找 Skill
  - `list_skills()` - 列出可用 Skill
- `skills/{name}/SKILL.md` - 方法论文档本身

**约定**:
- Skill 文件包含: Purpose, Input, Output, Instructions
- Prompt 中插入 Skill 内容作为方法论指导

## 会话管理

**机制**: 每次任务独立目录 + current/running/failed 软链接

**代码**:
- `agent/harness.py:SessionRecorder`
  - `__init__()` - 创建目录结构、初始化 session.md、更新软链接
  - `_slugify()` - 任务名转目录名
  - `_update_symlinks()` - 原子更新 current/running 软链接
  - `_init_session_file()` - 写入 session.md 模板、manifest.json
  - `get_working_dir(subdir)` - 获取工作子目录路径
  - `finalize()` - 结束会话、更新状态、归档软链接

**目录命名规则**:
```
knowledge/sessions/{timestamp}-{task-slug}/
# 例如: 20260331-162300-analyze-tcp-bandwidth/
```

**软链接管理**:
- running -> 当前运行中的会话
- current -> 最后一次成功完成的会话
- failed -> 最后一次失败的会话

## Research Log

**机制**: 前置追加（prepend）方式记录迭代历史

**代码**:
- `agent/harness.py:ResearchLogManager`
  - `read()` - 读取 `knowledge/research-log.md`
  - `prepend_entry()` - 新条目插在最前面

**设计意图**:
- 最新内容在前，方便 Agent 读最近历史
- 避免重复读取整个文件

## Git 强制提交

**机制**: HardLimit 检查未提交更改，失败则 Retry

**代码**:
- `agent/harness.py:GitCommitHarness`
  - `has_changes()` - 检查是否有未提交更改
  - `commit()` - 执行 add + commit
- `agent/harness.py:ExecutionValidator.check_git_clean()`

**Retry 流程**:
```
Agent 执行结束
  -> validate() 发现 git dirty
  -> 构建 Retry Prompt（包含 git commit 指令）
  -> Agent 重新执行，这次必须 commit
```

## Runner 执行框架

**机制**: 模板方法模式，子类只实现 prompt 构建

**代码**:
- `agent/base_runner.py:AgentRunner`
  - `run(max_cycles)` - 主循环
  - `run_cycle()` - 单次迭代（pre -> prompt -> call -> validate -> post）
  - `call_agent()` - 调用 Kimi CLI

**子类只需实现**:
- `build_prompt()` - 构建本轮 Prompt
- `get_cycle_name()` - 返回本轮名称（用于日志）

## 参数传递链

**机制**: 命令行参数层层传递

**代码路径**:
```
run.sh
  -> cd bin/ && python evolve.py --base-dir ..
     -> argparse: -n/--cycles, -s/--max-steps
        -> base_runner.AgentRunner.run(cycles)
           -> self.max_steps 控制 kimi --max-steps-per-turn
```

## 关键配置

| 文件 | 用途 |
|------|------|
| `docs/preferences.md` | 代码规范、设计偏好 |
| `skills/*/SKILL.md` | 方法论定义 |

---

**Note**: Pipeline 和 MetaLoop 模块正在重新设计，相关映射已移除。
