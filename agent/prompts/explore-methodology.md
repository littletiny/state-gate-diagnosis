1. **State-Gate 模型**
   - State: 离散状态节点
   - Gate: 基于 State 做决策的关键代码位置
   - Map: State 与 Gate 之间的拓扑关系

2. **ECTM 证据链方法**
   - 观察 → 假设 → 验证 → 证据

3. **Skill 使用指南**
   - **CR (Code-Reader)**: 阅读新代码库、生成架构概览、理解系统核心设计
   - **CMR (Code-Mechanism-Reader)**: 深入分析特定机制/模块（如状态机、异步流程、组件交互）
   - 需要阅读代码时，主动调用 skill 获取结构化分析方法

4. **无阶段约束**
   - 不需要固定顺序，随时创建 State/Gate/Map
