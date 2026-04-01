#!/usr/bin/env python3
"""
Harness 执行框架 - SoftLimit & HardLimit 双层约束机制

设计理念：
- SoftLimit: 通过Prompt hints引导Agent行为（不强制但建议）
- HardLimit: 通过代码检查强制约束Agent输出（不合格时要求重做）

分层结构：
┌─────────────────────────────────────────┐
│  SoftLimit Layer (Prompt Hints)         │
│  - build_*_prompt() 方法构建引导性提示   │
│  - 规范提示、模板引导、最佳实践建议      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Agent 执行层 (Kimi)                    │
│  - 接收Prompt，执行Task                 │
│  - 产出Output和行为                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  HardLimit Layer (Code Enforcement)     │
│  - ExecutionValidator 执行强制性检查     │
│  - 检查结果，不合格时触发Retry           │
└─────────────────────────────────────────┘

Agent 直接使用 git/ls/cat/grep 查询信息
代码层只保留必要的 Session 管理和 HardLimit 强制检查
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============ Git 规范常量 ============

class GitPrefixes:
    """Git Commit 前缀规范 - 用于SoftLimit提示和HardLimit验证"""
    RESEARCH = "[research]:"
    REPORT = "[report]:"
    DOC = "[doc]:"
    SESSION = "[session]:"
    STATE = "[state]:"
    GATE = "[gate]:"
    MAP = "[map]:"
    MECHANISM = "[mechanism]:"
    PATH = "[path]:"
    META = "[meta]:"
    SYNC = "[sync]:"
    INIT = "[init]:"
    
    ALL = [RESEARCH, REPORT, DOC, SESSION, STATE, GATE, 
           MAP, MECHANISM, PATH, META, SYNC, INIT]


# ============ SoftLimit: Prompt Hints 生成器 ============

class PromptHints:
    """
    SoftLimit层：生成各种Prompt hints引导Agent行为
    
    这些hints通过Prompt传递给Agent，不强制但建议遵循。
    如果Agent忽略hints，HardLimit层会在后续检查中捕获问题。
    """
    
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


# ============ Research Log 管理（简化） ============

class ResearchLogManager:
    """
    研究日志管理 - 简化版
    
    SoftLimit: Agent 应该直接用 cat knowledge/research-log.md 读取
    HardLimit: 代码层验证日志是否更新（check_research_log_updated）
    """
    
    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)
        self.log_path = self.knowledge_dir / "research-log.md"
    
    def read(self) -> str:
        """读取研究日志主文件"""
        if self.log_path.exists():
            return self.log_path.read_text(encoding='utf-8')
        return ""
    
    def prepend_entry(self, title: str, content: str):
        """在日志最前面添加新条目（prepend）"""
        timestamp = datetime.now().isoformat()
        header = "# Research Log\n\n"
        entry = f"## {title} - {timestamp}\n\n{content}\n\n---\n\n"
        
        current = self.read()
        body = current.replace(header, "") if current.startswith(header) else current
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text(header + entry + body, encoding='utf-8')
    
    def build_trajectory(self, task: str) -> str:
        """
        研究轨迹 - 使用PromptHints生成（SoftLimit）
        """
        log_exists = self.log_path.exists()
        
        trajectory = f"""研究轨迹（Research Trajectory）

原始问题: {task}
研究日志: `{self.log_path}` {'(exists)' if log_exists else '(not exists)'}
结构说明: `knowledge/index.md`

**由你自行分析**:
1. 读取研究日志：`cat {self.log_path}`
2. 如需了解目录结构：`cat knowledge/index.md`
3. 识别探索历史（关注 `## ` 开头的条目）
4. 提取上次遗留的"新产生的问题"
5. 确定本次探索目标

分析要点:
- 迭代条目格式: `## Iteration N - [Phase] - [timestamp]`
- 关注: "新产生的问题"、"下次建议"、"关键发现"
- 结合 Git 历史验证: `git log --oneline --grep="^\\[research\\]:"`

当前认知边界（由你根据日志分析填写）:
- Known: 
- Exploring: 
- Unknown: 
"""
        return trajectory


# ============ Git 提交辅助 ============

class GitCommitHarness:
    """
    Git 提交辅助 - 简化版
    
    SoftLimit: Agent 应该自己执行 git add knowledge/ && git commit
    HardLimit: ExecutionValidator.check_git_clean() 强制检查提交状态
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
    
    def has_changes(self, path: str = "knowledge/") -> bool:
        """检查是否有未提交的更改 - HardLimit使用"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", path],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def commit(self, message: str, path: str = "knowledge/") -> bool:
        """
        执行 git add + commit
        注意：Agent 应该自己执行 git 命令，此方法仅在必要时使用
        """
        try:
            # 检查是否是 git 仓库
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False
            
            # 添加变更
            subprocess.run(
                ["git", "add", "--", path],
                cwd=self.base_dir,
                capture_output=True,
                check=True
            )
            
            # 检查是否有变更需要提交
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.base_dir,
                capture_output=True
            )
            if result.returncode == 0:
                return True  # 无变更，视为成功
            
            # 提交
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.base_dir,
                capture_output=True,
                check=True
            )
            return True
            
        except:
            return False


# ============ Session 记录器 ============

class SessionRecorder:
    """
    会话记录器 - 创建带 task name 的目录
    
    SoftLimit: Agent应读取session.md了解会话历史
    HardLimit: 代码层自动创建和管理目录结构
    """
    
    def __init__(self, knowledge_dir: str, task: str):
        self.kb = Path(knowledge_dir).resolve()
        self.sessions_dir = self.kb / "sessions"
        self.task = task
        self.start_time = datetime.now()
        self.timestamp = self.start_time.strftime("%Y%m%d-%H%M%S")
        
        # 生成 slug
        self.task_slug = self._slugify(task)
        self.session_name = f"{self.timestamp}-{self.task_slug}"
        
        # 创建目录结构
        self.actual_dir = self.sessions_dir / self.session_name
        self.actual_dir.mkdir(parents=True, exist_ok=True)
        
        for subdir in ["states", "gates", "maps", "mechanisms", "paths", "logs"]:
            (self.actual_dir / subdir).mkdir(exist_ok=True)
        
        # 初始化会话文件
        self._init_session_file()
    
    def _slugify(self, text: str) -> str:
        """将文本转换为目录名"""
        return text.replace(" ", "-").replace("/", "-").replace("\\", "-")[:50]
    
    def _init_session_file(self):
        """初始化 session.md 和 manifest.json"""
        session_file = self.actual_dir / "session.md"
        session_file.write_text(f"""# Session: {self.session_name}

**任务**: {self.task}
**开始时间**: {self.start_time.isoformat()}
**状态**: running

## 会话记录

""", encoding='utf-8')
        
        manifest = {
            "name": self.session_name,
            "task": self.task,
            "start_time": self.start_time.isoformat(),
            "status": "running",
            "stages": [],
            "documents": {"created": [], "modified": []},
            "key_findings": [],
            "references": {}
        }
        manifest_file = self.actual_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def get_working_dir(self, subdir: str = None) -> Path:
        """获取工作目录路径"""
        if subdir:
            return self.actual_dir / subdir
        return self.actual_dir
    
    def record_stage(self, stage_name: str, summary: str, findings: list = None, 
                     documents: list = None, questions: list = None):
        """记录一个阶段的执行结果"""
        session_file = self.actual_dir / "session.md"
        timestamp = datetime.now().isoformat()
        
        entry = f"""### {stage_name} - {timestamp}

**摘要**: {summary}

"""
        if findings:
            entry += "**关键发现**:\n"
            for f in findings[:5]:
                entry += f"- {f}\n"
            entry += "\n"
        
        if documents:
            entry += "**相关文档**:\n"
            for doc in documents:
                entry += f"- `{doc}`\n"
            entry += "\n"
        
        if questions:
            entry += "**待解决问题**:\n"
            for q in questions[:3]:
                entry += f"- {q}\n"
            entry += "\n"
        
        entry += "---\n\n"
        
        with open(session_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        self._update_manifest(stage_name, findings, documents)
    
    def _update_manifest(self, stage_name: str, findings: list, documents: list):
        """更新 manifest.json"""
        manifest_file = self.actual_dir / "manifest.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest["stages"].append(stage_name)
            if findings:
                manifest["key_findings"].extend(findings[:3])
            if documents:
                manifest["documents"]["created"].extend(documents)
            manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def finalize(self, success: bool = True, stats: dict = None):
        """结束会话"""
        session_file = self.actual_dir / "session.md"
        manifest_file = self.actual_dir / "manifest.json"
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if session_file.exists():
            footer = f"""
## 会话结束

**结束时间**: {end_time.isoformat()}
**持续时间**: {duration:.0f}秒
**状态**: {'completed' if success else 'failed'}

"""
            if stats:
                footer += "**统计**:\n"
                for k, v in stats.items():
                    footer += f"- {k}: {v}\n"
            
            with open(session_file, 'a', encoding='utf-8') as f:
                f.write(footer)
        
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest["status"] = "completed" if success else "failed"
            manifest["end_time"] = end_time.isoformat()
            manifest["duration_seconds"] = duration
            if stats:
                manifest["stats"] = stats
            manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')


# ============ 锁管理器 ============

class SimpleLockManager:
    """
    极简文件锁管理 - 单实例运行
    
    HardLimit: 确保同时只有一个Agent实例运行
    """
    
    LOCK_FILE = "lock.file"
    STATE_FILE = "state.json"
    
    def __init__(self, knowledge_dir: str, base_dir: str = None):
        self.kb = Path(knowledge_dir).resolve()
        self.base_dir = Path(base_dir).resolve() if base_dir else self.kb.parent
        self.lock_path = self.kb / self.LOCK_FILE
        self.state_path = self.kb / self.STATE_FILE
        self.sessions_dir = self.kb / "sessions"
    
    def acquire(self, task: str) -> dict:
        """获取运行锁 - HardLimit"""
        if self.lock_path.exists():
            lock_content = self.lock_path.read_text(encoding='utf-8')
            raise RuntimeError(
                f"Agent 正在运行中 (lock.file 存在)\n"
                f"内容: {lock_content}\n"
                f"请等待完成或手动删除: {self.lock_path}"
            )
        
        # 检查上次是否失败
        if not self.state_path.exists():
            self._handle_previous_failure()
        
        # 创建锁文件
        start_time = datetime.now()
        lock_content = f"pid={os.getpid()}\ntask={task}\nstart={start_time.isoformat()}"
        self.lock_path.write_text(lock_content, encoding='utf-8')
        
        return {"task": task, "start_time": start_time, "pid": os.getpid()}
    
    def release(self, success: bool = True, stats: dict = None):
        """释放锁"""
        if success:
            state = {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "stats": stats or {}
            }
            self.state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
            self._finalize_session(stats)
    
    def _handle_previous_failure(self):
        """处理上次失败的会话"""
        # 找到最新的 session 目录（按修改时间排序）
        actual_dir = None
        if self.sessions_dir.exists():
            dirs = [d for d in self.sessions_dir.iterdir() if d.is_dir()]
            if dirs:
                actual_dir = sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        
        if not actual_dir or not actual_dir.exists():
            return
        
        # 更新 manifest
        manifest_file = actual_dir / "manifest.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest["status"] = "failed"
            manifest["failed_at"] = datetime.now().isoformat()
            manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 归档锁文件
        if self.lock_path.exists():
            shutil.move(str(self.lock_path), str(actual_dir / "lock.file"))
        
        self._update_sessions_index()
        print(f"[LockManager] 已标记失败会话: {actual_dir.name}")
    
    def _finalize_session(self, stats: dict = None):
        """完成会话"""
        # 找到最新的 session 目录（按修改时间排序）
        actual_dir = None
        if self.sessions_dir.exists():
            dirs = [d for d in self.sessions_dir.iterdir() if d.is_dir()]
            if dirs:
                actual_dir = sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        
        if actual_dir and actual_dir.exists():
            # 更新 manifest
            manifest_file = actual_dir / "manifest.json"
            if manifest_file.exists():
                manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
                manifest["status"] = "completed"
                manifest["completed_at"] = datetime.now().isoformat()
                manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"[LockManager] 会话完成: {actual_dir.name}")
        
        self.lock_path.unlink(missing_ok=True)
        self._update_sessions_index()
    
    def _update_sessions_index(self):
        """更新 sessions/README.md 索引"""
        readme_path = self.sessions_dir / "README.md"
        
        sessions = []
        if self.sessions_dir.exists():
            for item in sorted(self.sessions_dir.iterdir(), reverse=True):
                if item.is_symlink():
                    continue
                if item.is_dir():
                    manifest_file = item / "manifest.json"
                    if manifest_file.exists():
                        try:
                            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
                            sessions.append({
                                "name": item.name,
                                "task": manifest.get("task", "Unknown")[:40],
                                "status": manifest.get("status", "unknown"),
                                "stages": ", ".join(manifest.get("stages", [])[:2])
                            })
                        except:
                            pass
        
        lines = ["# Sessions Index", "", "会话历史（按时间倒序）", ""]
        lines.extend(["| 会话 | 任务 | 状态 | 阶段 |", "|------|------|------|------|"])
        
        for s in sessions[:20]:
            lines.append(f"| `{s['name']}` | {s['task']} | {s['status']} | {s['stages']} |")
        
        lines.append('')
        readme_path.write_text('\n'.join(lines), encoding='utf-8')


# ============ HardLimit: 执行验证器 ============

class ExecutionValidator:
    """
    执行结果验证器 - HardLimit核心实现
    
    通过代码强制检查Agent输出，不合格时要求重做。
    与SoftLimit（PromptHints）形成双层约束机制。
    """
    
    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)
        self.log_manager = ResearchLogManager(knowledge_dir)
    
    def check_research_log_updated(self, before_content: str = None) -> bool:
        """
        HardLimit检查: research-log.md 是否有更新
        
        检查项：
        - 文件是否存在
        - 内容是否有效（不只是header）
        - 相比before_content是否有新增内容
        """
        current = self.log_manager.read()
        if not current or current.strip() == "# Research Log":
            return False
        if before_content is None:
            return "##" in current
        return len(current) > len(before_content)
    
    def check_git_clean(self, base_dir: str) -> bool:
        """
        HardLimit检查: Git是否有未提交更改
        
        如果存在未提交更改，Agent需要重做（执行git commit）。
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", "knowledge/"],
                cwd=base_dir,
                capture_output=True,
                text=True
            )
            return not result.stdout.strip()
        except:
            return True
    
    def validate_execution(self, output: str, returncode: int, 
                          research_log_before: str = None) -> dict:
        """
        HardLimit入口: 验证执行结果
        
        Returns:
            dict: 包含以下字段的验证结果
                - success: 是否成功（returncode == 0）
                - research_log_updated: 日志是否更新（HardLimit）
                - git_clean: Git是否干净（HardLimit）
                - need_continue: 是否需要继续执行
                - continue_reason: 继续原因
                - warnings: 警告列表
        """
        result = {
            "success": returncode == 0,
            "research_log_updated": False,
            "git_clean": True,
            "need_continue": False,
            "continue_reason": None,
            "warnings": []
        }
        
        # 检查是否达到step限制
        if "Max number of steps reached" in output:
            result["need_continue"] = True
            result["continue_reason"] = "steps_exhausted"
            result["warnings"].append("Agent reached step limit")
        
        # HardLimit检查: Research Log更新
        result["research_log_updated"] = self.check_research_log_updated(research_log_before)
        if not result["research_log_updated"]:
            result["warnings"].append("HardLimit: research-log.md was not updated")
        
        return result
    
    def format_validation_report(self, result: dict) -> str:
        """格式化HardLimit验证报告"""
        lines = ["\n[Validation Report - HardLimit Check]"]
        lines.append(f"  Success: {result['success']}")
        lines.append(f"  Research Log Updated: {result['research_log_updated']}")
        lines.append(f"  Git Clean: {result['git_clean']}")
        if result['need_continue']:
            lines.append(f"  Need Continue: Yes ({result['continue_reason']})")
        if result['warnings']:
            lines.append("  Warnings:")
            for w in result['warnings']:
                lines.append(f"    - {w}")
        return '\n'.join(lines)
    
    def validate_stage_output(self, stage_name: str, working_dir: Path) -> dict:
        """
        HardLimit检查: 验证特定 stage 的输出是否满足进入下一阶段的要求
        
        Returns:
            {
                "sufficient": bool,  # 是否满足条件
                "details": dict,     # 详细信息
                "message": str       # 人类可读的消息
            }
        """
        if stage_name == "connection":
            return self._validate_connection_output(working_dir)
        elif stage_name == "diagnosis":
            return self._validate_diagnosis_output(working_dir)
        # 其他 stage 可以在这里扩展
        return {"sufficient": True, "details": {}, "message": "No validation for this stage"}
    
    def _validate_connection_output(self, working_dir: Path) -> dict:
        """
        HardLimit检查: connection stage 的输出
        
        要求：
        - 至少创建了一个 map
        - 没有剩余的 analyzed states/gates（即都被处理了）
        """
        maps_dir = working_dir / "maps"
        states_dir = working_dir / "states"
        gates_dir = working_dir / "gates"
        
        # 统计 maps 数量
        maps_count = len(list(maps_dir.glob("*.md"))) if maps_dir.exists() else 0
        
        # 统计还有多少 analyzed 的 states/gates
        analyzed_states = self._count_docs_with_status(states_dir, "analyzed")
        analyzed_gates = self._count_docs_with_status(gates_dir, "analyzed")
        remaining_analyzed = analyzed_states + analyzed_gates
        
        # 判定标准
        sufficient = maps_count > 0 and remaining_analyzed == 0
        
        details = {
            "maps_created": maps_count,
            "analyzed_states": analyzed_states,
            "analyzed_gates": analyzed_gates,
            "remaining_analyzed": remaining_analyzed
        }
        
        if sufficient:
            message = f"Connection complete: {maps_count} maps created, all states/gates processed"
        else:
            if maps_count == 0:
                message = "HardLimit: Connection incomplete - no maps created"
            elif remaining_analyzed > 0:
                message = f"HardLimit: Connection incomplete - {remaining_analyzed} analyzed docs remain (need status update to connected)"
            else:
                message = "HardLimit: Connection incomplete - unknown reason"
        
        return {
            "sufficient": sufficient,
            "details": details,
            "message": message
        }
    
    def _count_docs_with_status(self, dir_path: Path, status: str) -> int:
        """统计目录中有多少 markdown 文件包含指定的 status"""
        if not dir_path.exists():
            return 0
        
        count = 0
        for f in dir_path.glob("*.md"):
            try:
                content = f.read_text(encoding='utf-8')
                if f"status: {status}" in content:
                    count += 1
            except:
                pass
        return count
    
    def _validate_diagnosis_output(self, working_dir: Path) -> dict:
        """
        HardLimit检查: diagnosis stage 的输出
        
        要求：
        - 至少创建了一个 diagnosis 路径文档
        """
        paths_dir = working_dir / "paths"
        
        # 统计 paths 数量
        paths_count = len(list(paths_dir.glob("*.md"))) if paths_dir.exists() else 0
        
        # 判定标准：至少有一个 diagnosis 文档
        sufficient = paths_count > 0
        
        details = {
            "paths_created": paths_count
        }
        
        if sufficient:
            message = f"Diagnosis complete: {paths_count} diagnosis path(s) created"
        else:
            message = "HardLimit: Diagnosis incomplete - no diagnosis paths created"
        
        return {
            "sufficient": sufficient,
            "details": details,
            "message": message
        }
