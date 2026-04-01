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
