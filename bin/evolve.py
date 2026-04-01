#!/usr/bin/env python3
"""
Diag-loop 统一入口

当前支持:
    - 自主模式: Agent 根据知识库状态自主决策
       python evolve.py
       python evolve.py -n 5
       python evolve.py -t "分析TCP"

待重新设计:
    - Pipeline 模式 (原: 按 YAML 配置执行固定流程)
"""

import sys
from pathlib import Path

# agent 目录在 repo root: evolve.py -> bin/ -> repo root -> agent/
agent_dir = Path(__file__).parent.parent / "agent"
sys.path.insert(0, str(agent_dir))

from self_explore import main as explore_main


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Diag-loop 统一入口 - 自主探索',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python evolve.py                    # 标准模式，Agent 自主迭代
  python evolve.py -n 10              # 最多 10 轮迭代
  python evolve.py -t "分析 TCP 拥塞控制"  # 指定任务目标
        """
    )
    
    # 通用参数
    parser.add_argument('--base-dir', default='.', help='基础目录 (默认: 当前目录)')
    parser.add_argument('-n', '--cycles', type=int, default=10, 
                        help='最大迭代轮数 (cycles)')
    parser.add_argument('-s', '--max-steps', type=int, default=100, dest='max_steps',
                        help='单次对话最大工具调用步数 (默认: 100)')
    parser.add_argument('-t', '--task', help='任务目标描述')
    parser.add_argument('--list-skills', action='store_true', help='列出可用 Skills')
    
    args = parser.parse_args()
    
    # 确定基础目录
    base_dir = Path(args.base_dir).resolve()
    
    # 列出 Skills
    if args.list_skills:
        from skill_loader import list_skills
        skills = list_skills(str(base_dir / "skills"))
        print("可用 Skills:")
        for skill in skills:
            skill_path = base_dir / "skills" / skill / "SKILL.md"
            desc = ""
            if skill_path.exists():
                try:
                    content = skill_path.read_text(encoding='utf-8')
                    for line in content.split('\n')[:5]:
                        if line.strip() and not line.startswith('#'):
                            desc = line.strip()[:50]
                            break
                except:
                    pass
            print(f"  {skill:<20} {desc}")
        return
    
    # 自主探索模式
    new_argv = ['evolve', '--base-dir', str(base_dir)]
    new_argv.extend(['-n', str(args.cycles)])
    if args.max_steps != 100:
        new_argv.extend(['--max-steps', str(args.max_steps)])
    if args.task:
        new_argv.extend(['-t', args.task])
    sys.argv = new_argv
    explore_main()


if __name__ == "__main__":
    main()
