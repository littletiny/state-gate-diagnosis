目标: {task}

当前知识库:
{kb}
{warning}
## 执行要求

1. 阅读源码，获取新的代码洞察
2. 更新或新建 `{knowledge_dir}/` 下的文档（states/, gates/, maps/, paths/）
3. 在 `{knowledge_dir}/research-log.md` 最前面追加本次记录
4. 执行 git add 和 git commit（git 命令已自动指向正确目录）

## 系统改进

如果你发现当前的方法论、prompt 设计或文档格式有缺陷，可以直接修改
`{base_dir}/agent/prompts/` 下的对应片段文件。

源码位置: {src_dir}
