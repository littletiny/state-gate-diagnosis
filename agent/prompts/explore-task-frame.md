目标: {task}

当前知识库:
{kb}
{warning}
{iteration_hint}
## 执行要求

1. 阅读源码，获取新的代码洞察
2. 更新或新建文档到 `{knowledge_dir}/` 下的对应目录
3. 更新 `{knowledge_dir}/research-log.md` 记录本次进展
4. 提交你的变更

## 迭代策略提示

- 开始阶段：以 Discovery 为主，发现新的 State、Gate 和机制
- 后期阶段：以 Diagnosis 为主，收敛结论、建立诊断路径
- 中间阶段：根据知识库缺口自主决定深入方向

{first_round_hint}

{last_round_hint}

## 文档目录说明

- State/Gate/Map/Path 文档: `{knowledge_dir}/states/`, `gates/`, `maps/`, `paths/`
- CR/CMR 生成的架构文档: `{knowledge_dir}/doc/`

## 系统改进

如果你发现当前的方法论、prompt 设计或文档格式有缺陷，可以直接修改
`{base_dir}/agent/prompts/` 下的对应片段文件。

源码位置: {src_dir}
