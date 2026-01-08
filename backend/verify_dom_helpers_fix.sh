#!/bin/bash

# setSecureChildren エラー修正の検証スクリプト
# 2026-01-08

echo "========================================"
echo "DOM Helpers 修正検証スクリプト"
echo "========================================"
echo ""

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 修正が必要なHTMLファイルのリスト
HTML_FILES=(
    "/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/search-detail.html"
    "/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/sop-detail.html"
    "/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/expert-consult.html"
    "/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/incident-detail.html"
)

echo "1. dom-helpers.js ファイルの存在確認"
if [ -f "/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/dom-helpers.js" ]; then
    echo -e "   ${GREEN}✓${NC} dom-helpers.js が存在します"
    FUNC_COUNT=$(grep -c "^function " /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/dom-helpers.js)
    echo "   定義されている関数数: ${FUNC_COUNT}"
else
    echo -e "   ${RED}✗${NC} dom-helpers.js が見つかりません"
    exit 1
fi

echo ""
echo "2. HTMLファイルでのdom-helpers.js読み込み確認"
ALL_OK=true
for html_file in "${HTML_FILES[@]}"; do
    filename=$(basename "$html_file")
    if grep -q "dom-helpers.js" "$html_file"; then
        echo -e "   ${GREEN}✓${NC} $filename - dom-helpers.js を読み込んでいます"

        # 読み込み順序の確認（dom-helpers.js が detail-pages.js より前か）
        line_dom=$(grep -n "dom-helpers.js" "$html_file" | cut -d: -f1)
        line_detail=$(grep -n "detail-pages.js" "$html_file" | cut -d: -f1)

        if [ "$line_dom" -lt "$line_detail" ]; then
            echo -e "     ${GREEN}✓${NC} 読み込み順序が正しい (dom-helpers.js → detail-pages.js)"
        else
            echo -e "     ${RED}✗${NC} 読み込み順序が間違っています"
            ALL_OK=false
        fi
    else
        echo -e "   ${RED}✗${NC} $filename - dom-helpers.js を読み込んでいません"
        ALL_OK=false
    fi
done

echo ""
echo "3. detail-pages.js での関数使用状況"
if [ -f "/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/detail-pages.js" ]; then
    USAGE_COUNT=$(grep -c "setSecureChildren\|createSecureElement\|createMetaInfoElement" /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/detail-pages.js)
    echo "   detail-pages.js での DOM helper 関数使用箇所: ${USAGE_COUNT} 箇所"

    if [ "$USAGE_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} detail-pages.js は DOM helper 関数を使用しています"
    else
        echo -e "   ${YELLOW}⚠${NC} detail-pages.js で DOM helper 関数が見つかりません"
    fi
else
    echo -e "   ${RED}✗${NC} detail-pages.js が見つかりません"
    ALL_OK=false
fi

echo ""
echo "4. setSecureChildren 関数の定義確認"
if grep -q "^function setSecureChildren" /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/dom-helpers.js; then
    echo -e "   ${GREEN}✓${NC} setSecureChildren が定義されています"

    # 関数のシグネチャを表示
    FUNC_SIG=$(grep "^function setSecureChildren" /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/dom-helpers.js)
    echo "   シグネチャ: $FUNC_SIG"
else
    echo -e "   ${RED}✗${NC} setSecureChildren が定義されていません"
    ALL_OK=false
fi

echo ""
echo "========================================"
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ すべての検証項目が正常です${NC}"
    echo "修正が正しく適用されています。"
    exit 0
else
    echo -e "${RED}✗ 一部の検証項目でエラーがあります${NC}"
    echo "修正内容を確認してください。"
    exit 1
fi
