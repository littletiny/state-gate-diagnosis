#!/bin/bash
# OPS 角色启动入口
# 切换到 bin 目录加载 AGENTS.md，然后执行 evolve.py

show_help() {
    cat << 'EOF'
Net-Diag 统一入口 (run.sh)

用法: ./run.sh [选项] [参数...]

提示: 所有参数透传至 evolve.py，参考 evolve.py --help 查看完整帮助。
      注意: run.sh 中路径相对于项目根目录，evolve.py 中路径相对于 bin/ 目录。

常用示例:
    ./run.sh -n 5                    # 最多5轮迭代
    ./run.sh --list-skills           # 列出可用Skills
    ./run.sh -c rules/pipeline.yaml  # Pipeline模式

其他:
    ./run.sh --help       # 显示此帮助
    ./run.sh --evolve-help # 显示 evolve.py 详细帮助
EOF
}

# 解析 run.sh 自己的 help
for arg in "$@"; do
    case "$arg" in
        --help|-h)
            show_help
            exit 0
            ;;
        --evolve-help)
            cd "$(dirname "$0")/bin"
            python evolve.py --base-dir .. --help
            exit 0
            ;;
    esac
done

cd "$(dirname "$0")/bin"
# 让 bin/ 目录优先于系统 PATH，使 git wrap 生效
PATH="$(pwd):$PATH"
python evolve.py --base-dir .. "$@"
