#!/usr/bin/env python3
"""
Auto Recovery - 恢复中断的任务并归档数据

功能:
1. 找到上次中断的 session（最新的 running/failed 状态）
2. 将 knowledge/ 根目录的数据归档到该 session
3. 更新 manifest.json 状态为 failed
4. 删除 lock.file
5. 更新 sessions 索引

用法:
    python bin/recovery.py              # 执行恢复
    python bin/recovery.py --dry-run    # 只查看，不执行
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


def find_interrupted_session(knowledge_dir: Path) -> tuple[Path, dict] | None:
    """找到上次中断的 session（最新且状态为 running 的）"""
    sessions_dir = knowledge_dir / "sessions"
    if not sessions_dir.exists():
        return None

    candidates = []
    for d in sessions_dir.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        manifest_file = d / "manifest.json"
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                if manifest.get("status") == "running":
                    candidates.append((d, manifest, manifest.get("start_time", "")))
            except Exception:
                pass

    if not candidates:
        return None

    # 按 start_time 排序，取最新的
    candidates.sort(key=lambda x: x[2], reverse=True)
    session_dir, manifest, _ = candidates[0]
    return session_dir, manifest


def archive_to_session(knowledge_dir: Path, session_dir: Path, dry_run: bool = False) -> int:
    """将 knowledge/ 根目录（除 sessions/、index.md 外）完整归档到 session 目录，并清理原始文件"""
    archived = 0
    exclude_dirs = {"sessions"}
    exclude_files = {"index.md"}  # knowledge/ 的元数据，不归档

    for item in knowledge_dir.iterdir():
        if item.name in exclude_dirs:
            continue
        if item.is_file() and item.name in exclude_files:
            continue
            
        dst = session_dir / item.name
        
        if item.is_dir():
            if dst.exists():
                archived += copy_tree(item, dst, dry_run)
            else:
                if not dry_run:
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                archived += count_files(item)
                print(f"  {'[DRY-RUN] ' if dry_run else ''}Archive: {item.name}/")
            if not dry_run:
                shutil.rmtree(item)
        else:
            if not dry_run:
                shutil.copy2(str(item), str(dst))
            archived += 1
            print(f"  {'[DRY-RUN] ' if dry_run else ''}Archive: {item.name}")
            if not dry_run:
                item.unlink()

    return archived


def copy_tree(src: Path, dst: Path, dry_run: bool = False) -> int:
    """复制目录内容，返回复制的文件数"""
    count = 0
    for item in src.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(src)
            dst_file = dst / rel_path
            if not dry_run:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                if not dst_file.exists() or item.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(str(item), str(dst_file))
                    print(f"  Archive: {rel_path}")
            count += 1
    return count


def count_files(path: Path) -> int:
    """统计目录下的文件数"""
    return sum(1 for _ in path.rglob("*") if _.is_file())


def update_manifest(session_dir: Path, manifest: dict, dry_run: bool = False):
    """更新 manifest.json 状态为 failed"""
    manifest_file = session_dir / "manifest.json"
    manifest["status"] = "failed"
    manifest["recovered_at"] = datetime.now().isoformat()

    if not dry_run:
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {'[DRY-RUN] ' if dry_run else ''}Updated manifest.json: status=failed")


def update_session_file(session_dir: Path, dry_run: bool = False):
    """在 session.md 追加恢复记录"""
    session_file = session_dir / "session.md"
    if session_file.exists():
        footer = f"""
## 会话恢复

**恢复时间**: {datetime.now().isoformat()}
**状态**: 已归档并标记为 failed

"""
        if not dry_run:
            with open(session_file, "a", encoding="utf-8") as f:
                f.write(footer)
        print(f"  {'[DRY-RUN] ' if dry_run else ''}Updated session.md")


def update_sessions_index(sessions_dir: Path, dry_run: bool = False):
    """更新 sessions/README.md 索引"""
    readme_path = sessions_dir / "README.md"

    sessions = []
    for item in sorted(sessions_dir.iterdir(), reverse=True):
        if item.is_symlink() or not item.is_dir() or item.name.startswith("."):
            continue
        manifest_file = item / "manifest.json"
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
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

    if not dry_run:
        readme_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"  {'[DRY-RUN] ' if dry_run else ''}Updated sessions/README.md")


def remove_lock(knowledge_dir: Path, dry_run: bool = False):
    """删除 lock.file"""
    lock_file = knowledge_dir / "lock.file"
    if lock_file.exists():
        if not dry_run:
            lock_file.unlink()
        print(f"  {'[DRY-RUN] ' if dry_run else ''}Removed lock.file")


def main():
    parser = argparse.ArgumentParser(
        description="Auto Recovery - 恢复中断的任务并归档数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bin/recovery.py              # 执行恢复
  python bin/recovery.py --dry-run    # 只查看，不执行
        """
    )
    parser.add_argument("--base-dir", default=".", help="基础目录 (默认: 当前目录)")
    parser.add_argument("--dry-run", action="store_true", help="只查看，不执行")

    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    knowledge_dir = base_dir / "knowledge"
    lock_file = knowledge_dir / "lock.file"

    # 检查 lock.file
    if not lock_file.exists():
        print("[Recovery] 没有检测到中断的任务（lock.file 不存在）")
        print("[Recovery] 如需强制归档当前数据，请手动执行 git 操作")
        return 0

    print(f"[Recovery] 检测到中断的任务")
    print(f"[Recovery] Lock file: {lock_file}")

    # 找到中断的 session
    result = find_interrupted_session(knowledge_dir)
    if not result:
        print("[Recovery] 错误: 未找到中断的 session（没有 status=running 的 session）")
        print("[Recovery] 请检查 sessions/ 目录或手动清理 lock.file")
        return 1

    session_dir, manifest = result
    print(f"[Recovery] 找到中断的 session: {session_dir.name}")
    print(f"[Recovery] Task: {manifest.get('task', 'Unknown')}")
    print(f"[Recovery] Started: {manifest.get('start_time', 'Unknown')}")

    if args.dry_run:
        print("\n[Recovery] DRY-RUN 模式 - 只显示操作，不实际执行\n")

    # 执行恢复
    print("\n[Recovery] 开始归档数据...")
    archived = archive_to_session(knowledge_dir, session_dir, dry_run=args.dry_run)
    print(f"[Recovery] 归档完成: {archived} 个 items")
    if not args.dry_run:
        print(f"[Recovery] knowledge/ 已清理")

    print("\n[Recovery] 更新会话状态...")
    update_manifest(session_dir, manifest, dry_run=args.dry_run)
    update_session_file(session_dir, dry_run=args.dry_run)

    print("\n[Recovery] 清理...")
    remove_lock(knowledge_dir, dry_run=args.dry_run)
    update_sessions_index(knowledge_dir / "sessions", dry_run=args.dry_run)

    print("\n[Recovery] 恢复完成")
    print(f"[Recovery] 数据已归档到: {session_dir}")
    if not args.dry_run:
        print(f"[Recovery] knowledge/ 已清理，现在可以重新启动任务了")
    else:
        print(f"[Recovery] DRY-RUN: 实际执行时会清理 knowledge/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
