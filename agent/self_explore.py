#!/usr/bin/env python3
"""
Self Explore Agent - 自由探索模式

核心设计：
- 取消 Discovery/Analysis/Connection/Diagnosis 阶段概念
- 取消 status 状态机
- Agent 在 knowledge/ 根目录下扁平工作（states/, gates/, maps/, paths/）
- 代码层自动将变更归档到 sessions/{timestamp}-{task}/working/
- Prompt 拆分为外部片段文件（agent/prompts/），支持动态修改
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_runner import AgentRunner


class ExploreAgent(AgentRunner):
    """探索 Agent - 目标驱动，无阶段约束，扁平工作目录"""

    PROMPT_PARTS = ["identity", "methodology", "constraints"]
    """Prompt 片段列表，按顺序组合成完整 prompt"""

    def _load_prompt_part(self, name: str) -> str:
        """加载 prompt 片段，从 prompts/ 目录读取 .md 文件"""
        # 优先读取 .md 文件
        md_path = self.prompts_dir / f"explore-{name}.md"
        if md_path.exists():
            return md_path.read_text(encoding="utf-8")
        
        # 兼容性：保留 .txt 文件支持
        txt_path = self.prompts_dir / f"{name}.txt"
        if txt_path.exists():
            return txt_path.read_text(encoding="utf-8")
        
        return ""

    def __init__(self, base_dir: str, task: str = None):
        super().__init__(base_dir, task=task or "分析Linux整机网络带宽低的根因")
        self.prompts_dir = self.base_dir / "agent" / "prompts"
        self.progress_file = self.knowledge_dir / "progress.json"
        self.progress = self._load_progress()
        self._stagnant = False
        self._pre_hash = None

    def _get_session_dir(self):
        """获取当前 session 目录，直接使用 SessionRecorder 创建的目录"""
        if self.session_recorder:
            return self.session_recorder.actual_dir
        return None

    def _load_progress(self) -> dict:
        """加载进度文件"""
        if self.progress_file.exists():
            try:
                return json.loads(self.progress_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"task": self.task, "iterations": []}

    def _save_progress(self):
        """保存进度文件"""
        self.progress_file.write_text(
            json.dumps(self.progress, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )



    def _get_head_hash(self) -> str:
        """获取当前 Git HEAD hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.knowledge_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    def _get_docs_changed(self) -> list:
        """获取最近一次 commit 中变更的文件"""
        post_hash = self._get_head_hash()
        if not post_hash or post_hash == self._pre_hash:
            return []
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", post_hash],
                cwd=self.knowledge_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        except Exception:
            pass
        return []

    def _get_kb_snapshot(self) -> str:
        """生成知识库状态快照"""
        lines = []
        for subdir in ["states", "gates", "maps", "paths"]:
            d = self.knowledge_dir / subdir
            if d.exists():
                files = sorted(d.glob("*.md"))
                if files:
                    lines.append(f"- {subdir}/: {len(files)} documents")
                    for f in files[:5]:
                        lines.append(f"  - {f.name}")
                    if len(files) > 5:
                        lines.append(f"  ... and {len(files) - 5} more")
        if not lines:
            lines.append("(empty)")
        return "\n".join(lines)

    def _archive_to_session(self):
        """将 knowledge/ 根目录（除 sessions/、index.md 外）完整归档到 session 目录，并清理原始文件"""
        session_dir = self._get_session_dir()
        if not session_dir:
            return 0

        archived = 0
        exclude_dirs = {"sessions"}  # 排除其他会话目录
        exclude_files = {"index.md"}  # index.md 是 knowledge/ 的元数据，不归档
        
        # 遍历 knowledge/ 下的所有文件和目录
        for item in self.knowledge_dir.iterdir():
            if item.name in exclude_dirs:
                continue
            if item.is_file() and item.name in exclude_files:
                continue
                
            dst = session_dir / item.name
            
            if item.is_dir():
                # 复制整个目录
                if dst.exists():
                    # 合并：复制目录下的文件
                    archived += self._copy_tree(item, dst)
                else:
                    # 完整复制目录
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                    archived += self._count_files(item)
                # 删除源目录
                shutil.rmtree(item)
            else:
                # 复制文件
                shutil.copy2(str(item), str(dst))
                archived += 1
                # 删除源文件
                item.unlink()
                    
        if archived:
            print(f"[Archive] {archived} items archived to {session_dir}")
        return archived
    
    def _copy_tree(self, src: Path, dst: Path) -> int:
        """复制目录内容，返回复制的文件数"""
        count = 0
        for item in src.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src)
                dst_file = dst / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                if not dst_file.exists() or item.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(str(item), str(dst_file))
                count += 1
        return count
    
    def _count_files(self, path: Path) -> int:
        """统计目录下的文件数"""
        return sum(1 for _ in path.rglob("*") if _.is_file())

    def _auto_commit(self) -> bool:
        """自动执行 git add + commit"""
        try:
            # 检查是否有变更
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.knowledge_dir,
                capture_output=True,
                text=True,
            )
            if not result.stdout.strip():
                return True  # 无变更

            # add 所有变更
            subprocess.run(
                ["git", "add", "."],
                cwd=self.knowledge_dir,
                capture_output=True,
                check=True,
            )

            # 检查 staged 是否有内容
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.knowledge_dir,
                capture_output=True,
            )
            if result.returncode == 0:
                return True  # 无 staged 变更

            # 生成 commit message
            msg = self._generate_commit_message()
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=self.knowledge_dir,
                capture_output=True,
                check=True,
            )
            print(f"[Git] Committed: {msg.split(chr(10))[0]}")
            return True
        except Exception as e:
            print(f"[Git] Auto-commit failed: {e}")
            return False

    def _generate_commit_message(self) -> str:
        """从 research-log.md 提取 commit message"""
        log_path = self.knowledge_dir / "research-log.md"
        if not log_path.exists():
            return f"Iteration {self.current_cycle}"

        content = log_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        subject = f"Iteration {self.current_cycle}"
        for line in lines:
            if line.startswith("## "):
                subject = line[3:].strip()
                break

        body_lines = []
        for line in lines[1:]:
            if line.startswith("## "):
                break
            if line.startswith("- ") or line.startswith("### "):
                body_lines.append(line)
            if len(body_lines) > 20:
                break

        body = "\n".join(body_lines) if body_lines else ""
        if body:
            return f"{subject}\n\n{body}"
        return subject

    def get_cycle_name(self) -> str:
        return f"Iteration {self.current_cycle}"

    def pre_execute(self) -> str:
        self._pre_hash = self._get_head_hash()
        return super().pre_execute()

    def build_prompt(self) -> str:
        kb = self._get_kb_snapshot()
        warning = ""
        if self._stagnant:
            warning = (
                "\n[⚠️ 警告] 最近 3 次迭代没有更新文档或研究日志。"
                "请确保本次有实质性进展。\n"
            )

        parts = []
        for name in self.PROMPT_PARTS:
            content = self._load_prompt_part(name)
            if content.strip():
                parts.append(content.strip())

        prompt_body = "\n\n".join(parts)
        kd = self.knowledge_dir

        return f"""{prompt_body}

目标: {self.task}

当前知识库:
{kb}
{warning}
## 执行要求

1. 阅读源码，获取新的代码洞察
2. 更新或新建 `{kd}/` 下的文档（states/, gates/, maps/, paths/）
3. 在 `{kd}/research-log.md` 最前面追加本次记录
4. 执行 git add 和 git commit（git 命令已自动指向正确目录）

## 系统改进

如果你发现当前的方法论、prompt 设计或文档格式有缺陷，可以直接修改
`{self.base_dir}/agent/prompts/` 下的对应片段文件。

源码位置: {self.base_dir / 'linux-src'}
"""

    def finalize_session(self, success: bool = True, stats: dict = None):
        """任务完成后的最终归档：复制文件到 session 目录，然后清理原始文件"""
        if not success:
            print("[Archive] 任务未成功完成，保留 knowledge/ 下的原始文件")
            return
            
        session_dir = self._get_session_dir()
        if not session_dir:
            print("[Archive] 无法获取 session 目录，保留原始文件")
            return
            
        print(f"[Archive] 最终归档到 {session_dir}")
        archived = self._archive_to_session()
        if archived > 0:
            print(f"[Archive] 归档完成，knowledge/ 已清理")
        else:
            print(f"[Archive] 无文件需要归档")

    def post_execute(self, output: str, returncode: int, validation: dict):
        """执行后：自动提交、检查进度"""
        # 1. 自动提交（如果 Agent 没做）
        self._auto_commit()

        # 2. 获取变更文件列表
        docs_changed = self._get_docs_changed()
        log_updated = validation.get("research_log_updated", False)

        # 3. 记录进度
        self.progress["iterations"].append(
            {
                "cycle": self.current_cycle,
                "timestamp": datetime.now().isoformat(),
                "docs_touched": docs_changed,
                "log_updated": log_updated,
            }
        )
        self._save_progress()

        print(f"[Progress] Docs touched: {len(docs_changed)}, Log updated: {log_updated}")

        # 4. 停滞检查
        if len(self.progress["iterations"]) >= 3:
            recent = self.progress["iterations"][-3:]
            total_docs = sum(len(it["docs_touched"]) for it in recent)
            total_logs = sum(1 for it in recent if it["log_updated"])
            if total_docs == 0 and total_logs == 0:
                self._stagnant = True
                print("[HardLimit] 警告：最近 3 次迭代没有实质性进展")
            else:
                self._stagnant = False


def main():
    parser = argparse.ArgumentParser(
        description="Agent 自由探索 - 无阶段约束，目标驱动",
        epilog="""
示例:
  ./evolve.py                    # 启动探索
  ./evolve.py -n 10              # 最多 10 次迭代
  ./evolve.py -t "分析TCP拥塞控制" # 指定任务目标
        """,
    )
    parser.add_argument("--base-dir", default=".", help="基础目录")
    parser.add_argument(
        "-n",
        "--cycles",
        type=int,
        default=20,
        help="最大迭代轮数 (默认: 20)",
    )
    parser.add_argument(
        "-s",
        "--max-steps",
        type=int,
        default=100,
        dest="max_steps",
        help="单次对话最大工具调用步数 (默认: 100)",
    )
    parser.add_argument("-t", "--task", help="任务目标描述")

    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    if not (base_dir / "knowledge").exists():
        script_dir = Path(__file__).parent.parent
        if (script_dir / "knowledge").exists():
            base_dir = script_dir

    agent = ExploreAgent(str(base_dir), task=args.task)
    agent.max_steps = args.max_steps
    agent.run(args.cycles)


if __name__ == "__main__":
    main()
