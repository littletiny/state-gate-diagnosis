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
