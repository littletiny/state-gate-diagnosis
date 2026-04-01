#!/usr/bin/env python3
"""
SoftLimit: Prompt Hints 生成器

这些hints通过Prompt传递给Agent，不强制但建议遵循。
如果Agent忽略hints，HardLimit层会在后续检查中捕获问题。
"""


class PromptHints:
    """SoftLimit层：生成各种Prompt hints引导Agent行为"""
    
    @staticmethod
    def git_commit_hint() -> str:
        """Git commit 规范提示"""
        return """
### Git Commit 规范（必须执行）

每次迭代完成后，必须提交更改：
```bash
git add knowledge/
git commit -m "[prefix]: 描述变更内容"
```

可用前缀：
- `[research]:` Research Log 更新
- `[state]:` State 文档创建/更新  
- `[gate]:` Gate 文档创建/更新
- `[map]:` Map/拓扑图创建/更新
- `[mechanism]:` 机制分析文档
- `[path]:` 诊断路径文档
- `[session]:` 会话管理相关
- `[meta]:` 元认知/系统改进
- `[sync]:` 文档同步/索引更新

**重要**：Harness会强制检查Git状态，未提交将导致重试。
"""
    
    @staticmethod
    def research_trajectory_hint(task: str) -> str:
        """研究轨迹构建提示"""
        return f"""
### 研究轨迹（Research Trajectory）

原始问题: {task}

执行前请自行分析：
1. 读取 `knowledge/research-log.md` 了解历史探索
2. 读取 `knowledge/sessions/current/session.md` 了解当前会话
3. 提取上次遗留的"新产生的问题"
4. 确定本次探索目标

分析要点：
- 迭代条目格式: `## Iteration N - [Phase] - [timestamp]`
- 关注: "新产生的问题"、"下次建议"、"关键发现"
- 结合Git历史验证: `git log --oneline --grep="^\\[research\\]:"`

当前认知边界（由你根据日志分析填写）:
- Known: 
- Exploring: 
- Unknown: 
"""
    
    @staticmethod
    def document_format_hint() -> str:
        """文档格式规范提示"""
        return """
### 文档格式规范

所有Markdown文档必须遵循：

1. **禁止使用数字前缀标题**：如 `## 1. xxx`、`### 1.1 xxx`
   - 原因：插入/删除章节会导致编号变动，产生无意义diff
   - 使用纯文本标题，依靠Markdown层级表达结构

2. **State/Gate文档模板**：
   ```yaml
   ---
   name: xxx
   type: state|gate
   status: discovered|analyzed|connected|done
   created: 2026-03-31T10:00:00
   ---
   
   # State/Gate 名称
   
   ## 描述
   ## 相关代码
   ## 关联
   ```

3. **执行摘要输出格式**：
   ```markdown
   ### 执行摘要
   ### 关键发现
   ### 已回答的问题
   ### 新产生的问题
   ### 下次建议
   ### 文档更新
   ```
"""
    
    @staticmethod
    def execution_flow_hint() -> str:
        """执行流程提示"""
        return """
### 执行流程建议

1. **执行前必做**：
   - 读取研究日志了解历史
   - 构建研究轨迹
   - 明确Known/Exploring/Unknown

2. **执行中**：
   - 基于研究轨迹继续深入
   - 相同Skill多次执行时差异化：
     - 第1次：广度优先，扫描发现
     - 第2次：深度优先，深入分析
     - 第3次：关联分析，建立关系
     - 第4次+: 缺口填补

3. **执行后必做**：
   - 更新 `knowledge/research-log.md`（新条目前置）
   - 执行 `git add knowledge/` 和 `git commit`
   - 输出结构化结果（执行摘要、关键发现等）

**提示**：Harness会验证以上输出要求是否完成。
"""
    
    @staticmethod
    def build_retry_prompt(reason: str, instruction: str, original_task: str) -> str:
        """
        构建HardLimit触发后的Retry Prompt
        
        当HardLimit检查失败时，使用此prompt要求Agent重做。
        """
        return f"""[Harness] 上次执行未通过强制检查（HardLimit）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 检查失败: {reason}

✅ 你需要: {instruction}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

修复后，请继续完成原任务:
{original_task}

⚠️ 重要提示：
1. 先修复上述HardLimit检查失败的问题
2. 然后继续完成原任务的所有要求
3. 最后再次执行 git add 和 git commit

HardLimit会持续检查直到通过。
"""
