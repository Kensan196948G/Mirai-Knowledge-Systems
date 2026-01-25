#!/bin/bash
# ============================================================
# Mirai Knowledge Systems - Linux Node.js モジュールセットアップ
# ============================================================
#
# このスクリプトは、Linux環境でNode.jsモジュールをセットアップします。
# Windows環境との共有フォルダ使用時のバイナリ非互換問題を解決します。
#
# 使用方法:
#   ./scripts/linux/setup-node-modules.sh [--install] [--clean]
#
# オプション:
#   --install    Linux用node_modulesをセットアップ
#   --clean      node_modulesディレクトリを削除
#   --help       ヘルプ表示
#
# ============================================================

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# デフォルト値
INSTALL=false
CLEAN=false

# ヘルプ表示
show_help() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  Mirai Knowledge Systems - Node.js モジュールセットアップ${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --install    Linux用node_modulesをセットアップ"
    echo "  --clean      node_modulesディレクトリを削除"
    echo "  --help       このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 --install"
    echo "  $0 --clean"
    echo ""
    exit 0
}

# node_modulesセットアップ
setup_node_modules() {
    local target_dir="$1"
    local package_json="${target_dir}/package.json"

    if [[ ! -f "$package_json" ]]; then
        echo -e "${YELLOW}[SKIP]${NC} package.json が見つかりません: $target_dir"
        return
    fi

    local node_modules="${target_dir}/node_modules"
    local node_modules_linux="${target_dir}/node_modules.linux"

    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  セットアップ: $(basename "$target_dir")${NC}"
    echo -e "${CYAN}============================================================${NC}"

    # 既存のnode_modulesがシンボリックリンクでない場合
    if [[ -d "$node_modules" && ! -L "$node_modules" ]]; then
        # node_modules.linuxにリネーム
        if [[ ! -d "$node_modules_linux" ]]; then
            echo -e "${BLUE}[INFO]${NC} 既存のnode_modulesを移動: node_modules -> node_modules.linux"
            mv "$node_modules" "$node_modules_linux"
        else
            echo -e "${YELLOW}[WARN]${NC} node_modules.linux が既に存在。node_modulesを削除します。"
            rm -rf "$node_modules"
        fi
    fi

    # シンボリックリンクを削除
    if [[ -L "$node_modules" ]]; then
        echo -e "${BLUE}[INFO]${NC} 既存のシンボリックリンクを削除"
        rm "$node_modules"
    fi

    # node_modules.linuxを作成
    if [[ ! -d "$node_modules_linux" ]]; then
        echo -e "${BLUE}[INFO]${NC} ディレクトリ作成: node_modules.linux"
        mkdir -p "$node_modules_linux"
    fi

    # シンボリックリンク作成
    echo -e "${BLUE}[INFO]${NC} シンボリックリンク作成: node_modules -> node_modules.linux"
    ln -s "node_modules.linux" "$node_modules"

    if [[ -L "$node_modules" ]]; then
        echo -e "${GREEN}[OK]${NC} シンボリックリンク作成成功"
    else
        echo -e "${RED}[ERROR]${NC} シンボリックリンク作成失敗"
        return 1
    fi

    # npm install 実行
    echo -e "${BLUE}[INFO]${NC} npm install を実行中..."
    pushd "$target_dir" > /dev/null

    if command -v npm &> /dev/null; then
        npm install
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}[OK]${NC} npm install 完了"
        else
            echo -e "${YELLOW}[WARN]${NC} npm install に警告があります"
        fi
    else
        echo -e "${YELLOW}[WARN]${NC} npm が見つかりません。手動で npm install を実行してください。"
    fi

    popd > /dev/null
}

# node_modulesクリーンアップ
clean_node_modules() {
    local target_dir="$1"
    local node_modules="${target_dir}/node_modules"
    local node_modules_linux="${target_dir}/node_modules.linux"
    local node_modules_windows="${target_dir}/node_modules.windows"

    # シンボリックリンク削除
    if [[ -L "$node_modules" ]]; then
        echo -e "${BLUE}[INFO]${NC} シンボリックリンク削除: $node_modules"
        rm "$node_modules"
    elif [[ -d "$node_modules" ]]; then
        echo -e "${BLUE}[INFO]${NC} ディレクトリ削除: $node_modules"
        rm -rf "$node_modules"
    fi

    # OS別ディレクトリ削除
    for os_dir in "$node_modules_linux" "$node_modules_windows"; do
        if [[ -d "$os_dir" ]]; then
            echo -e "${BLUE}[INFO]${NC} ディレクトリ削除: $os_dir"
            rm -rf "$os_dir"
        fi
    done
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --install)
            INSTALL=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}不明なオプション: $1${NC}"
            show_help
            ;;
    esac
done

if [[ "$INSTALL" == "false" && "$CLEAN" == "false" ]]; then
    show_help
fi

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Mirai Knowledge Systems - Node.js モジュールセットアップ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo "プロジェクトルート: $PROJECT_ROOT"
echo "OS: Linux"
echo ""

# package.jsonを持つディレクトリを検索
TARGET_DIRS=(
    "${PROJECT_ROOT}/backend"
    "${PROJECT_ROOT}/webui"
    "$PROJECT_ROOT"
)

for target_dir in "${TARGET_DIRS[@]}"; do
    if [[ -f "${target_dir}/package.json" ]]; then
        if [[ "$CLEAN" == "true" ]]; then
            clean_node_modules "$target_dir"
        fi
        if [[ "$INSTALL" == "true" ]]; then
            setup_node_modules "$target_dir"
        fi
    fi
done

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}  完了${NC}"
echo -e "${CYAN}============================================================${NC}"
