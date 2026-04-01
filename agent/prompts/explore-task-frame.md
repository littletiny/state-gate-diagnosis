目标: {task}

当前知识库:
{kb}
{warning}
{iteration_hint}
## 执行要求

1. 阅读源码，获取新的代码洞察
2. 更新或新建 `{knowledge_dir}/` 下的文档（states/, gates/, maps/, paths/）
3. 在 `{knowledge_dir}/research-log.md` 最前面追加本次记录
4. 执行 git add 和 git commit（git 命令已自动指向正确目录）

## 迭代策略提示

- 开始几次迭代：以 Discovery 为主，重点发现新的 State、Gate 和机制
- 最后几次迭代：以 Diagnosis 为主，重点收敛结论、建立诊断路径、填补证据缺口
- 中间阶段：由你根据当前知识库缺口自行决定深度分析或关联映射

{first_round_hint}

**⚠️ 最后一轮（{max_cycles}/{max_cycles}）：必须生成最终报告，汇总完整诊断结论与推荐路径。**

## 系统改进

如果你发现当前的方法论、prompt 设计或文档格式有缺陷，可以直接修改
`{base_dir}/agent/prompts/` 下的对应片段文件。

源码位置: {src_dir}
