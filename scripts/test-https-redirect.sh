#!/bin/bash

# ============================================================================
# HTTPS自動リダイレクトテストスクリプト
# Mirai Knowledge System
# ============================================================================
#
# 用途: HTTP→HTTPSリダイレクトとセキュリティヘッダーの検証
#
# 実行方法:
#   chmod +x scripts/test-https-redirect.sh
#   ./scripts/test-https-redirect.sh
#
# ============================================================================

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# テスト対象
HTTP_URL="http://192.168.0.187"
HTTPS_URL="https://192.168.0.187"
LOCALHOST_HTTP="http://localhost"
LOCALHOST_HTTPS="https://localhost"

# テスト結果カウンター
PASSED=0
FAILED=0

# ============================================================================
# ヘルパー関数
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "\n${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ============================================================================
# テスト1: HTTPからHTTPSへのリダイレクト確認（IPアドレス）
# ============================================================================

test_http_redirect_ip() {
    print_test "HTTP→HTTPSリダイレクト（IPアドレス）"

    RESPONSE=$(curl -s -I -L --max-time 10 "$HTTP_URL/" 2>&1)

    if echo "$RESPONSE" | grep -q "HTTP/1.1 301 Moved Permanently"; then
        print_pass "301リダイレクトレスポンス確認"
    else
        print_fail "301リダイレクトが見つかりません"
        echo "$RESPONSE" | head -5
        return 1
    fi

    if echo "$RESPONSE" | grep -q "Location: https://"; then
        print_pass "LocationヘッダーにHTTPS URL確認"
    else
        print_fail "LocationヘッダーにHTTPSがありません"
        echo "$RESPONSE" | grep "Location" || echo "Locationヘッダーなし"
        return 1
    fi
}

# ============================================================================
# テスト2: HTTPからHTTPSへのリダイレクト確認（localhost）
# ============================================================================

test_http_redirect_localhost() {
    print_test "HTTP→HTTPSリダイレクト（localhost）"

    RESPONSE=$(curl -s -I -L --max-time 10 "$LOCALHOST_HTTP/" 2>&1)

    if echo "$RESPONSE" | grep -q "HTTP/1.1 301 Moved Permanently"; then
        print_pass "301リダイレクトレスポンス確認"
    else
        print_fail "301リダイレクトが見つかりません"
        return 1
    fi
}

# ============================================================================
# テスト3: HTTPSアクセス確認
# ============================================================================

test_https_access() {
    print_test "HTTPSアクセス確認（自己署名証明書）"

    RESPONSE=$(curl -s -I -k --max-time 10 "$HTTPS_URL/" 2>&1)

    if echo "$RESPONSE" | grep -q "HTTP/2 200\|HTTP/1.1 200"; then
        print_pass "HTTPS接続成功（200 OK）"
    else
        print_fail "HTTPS接続失敗"
        echo "$RESPONSE" | head -5
        return 1
    fi

    # HTTP/2対応確認
    if echo "$RESPONSE" | grep -q "HTTP/2"; then
        print_pass "HTTP/2サポート確認"
    else
        print_info "HTTP/2が有効化されていません（HTTP/1.1使用中）"
    fi
}

# ============================================================================
# テスト4: セキュリティヘッダー確認
# ============================================================================

test_security_headers() {
    print_test "セキュリティヘッダー確認"

    RESPONSE=$(curl -s -I -k --max-time 10 "$HTTPS_URL/" 2>&1)

    # HSTS
    if echo "$RESPONSE" | grep -qi "Strict-Transport-Security"; then
        print_pass "HSTS (Strict-Transport-Security) 有効"
        echo "$RESPONSE" | grep -i "Strict-Transport-Security" | sed 's/^/       /'
    else
        print_fail "HSTS (Strict-Transport-Security) が設定されていません"
    fi

    # X-Frame-Options
    if echo "$RESPONSE" | grep -qi "X-Frame-Options"; then
        print_pass "X-Frame-Options 有効"
    else
        print_fail "X-Frame-Options が設定されていません"
    fi

    # X-Content-Type-Options
    if echo "$RESPONSE" | grep -qi "X-Content-Type-Options"; then
        print_pass "X-Content-Type-Options 有効"
    else
        print_fail "X-Content-Type-Options が設定されていません"
    fi

    # Content-Security-Policy
    if echo "$RESPONSE" | grep -qi "Content-Security-Policy"; then
        print_pass "Content-Security-Policy 有効"
    else
        print_fail "Content-Security-Policy が設定されていません"
    fi

    # Referrer-Policy
    if echo "$RESPONSE" | grep -qi "Referrer-Policy"; then
        print_pass "Referrer-Policy 有効"
    else
        print_fail "Referrer-Policy が設定されていません"
    fi
}

# ============================================================================
# テスト5: TLS/SSL設定確認
# ============================================================================

test_tls_settings() {
    print_test "TLS/SSL設定確認"

    # OpenSSL s_clientでTLS接続テスト
    OPENSSL_OUTPUT=$(echo "Q" | timeout 10 openssl s_client -connect 192.168.0.187:443 -servername 192.168.0.187 2>&1)

    # TLS 1.2以降のみ許可確認
    if echo "$OPENSSL_OUTPUT" | grep -q "Protocol.*TLSv1\.[23]"; then
        TLS_VERSION=$(echo "$OPENSSL_OUTPUT" | grep "Protocol" | awk '{print $3}')
        print_pass "TLS 1.2以降使用中: $TLS_VERSION"
    else
        print_fail "TLS 1.2以降が使用されていません"
    fi

    # 暗号スイート確認
    if echo "$OPENSSL_OUTPUT" | grep -q "Cipher.*AES\|Cipher.*CHACHA"; then
        CIPHER=$(echo "$OPENSSL_OUTPUT" | grep "Cipher" | head -1)
        print_pass "強固な暗号スイート使用中"
        echo "       $CIPHER"
    else
        print_fail "暗号スイート情報取得失敗"
    fi
}

# ============================================================================
# テスト6: 証明書確認
# ============================================================================

test_certificate() {
    print_test "SSL証明書確認"

    # 証明書ファイル存在確認
    if [ -f "/mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt" ]; then
        print_pass "証明書ファイル存在確認"
    else
        print_fail "証明書ファイルが見つかりません"
        return 1
    fi

    # 証明書有効期限確認
    CERT_INFO=$(openssl x509 -in /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt -noout -dates 2>&1)

    if [ $? -eq 0 ]; then
        print_pass "証明書読み取り成功"
        echo "$CERT_INFO" | sed 's/^/       /'

        # 有効期限チェック
        NOT_AFTER=$(echo "$CERT_INFO" | grep "notAfter" | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$NOT_AFTER" +%s)
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

        if [ $DAYS_LEFT -gt 30 ]; then
            print_pass "証明書有効期限: $DAYS_LEFT日後"
        elif [ $DAYS_LEFT -gt 0 ]; then
            print_info "証明書有効期限: $DAYS_LEFT日後（更新推奨）"
        else
            print_fail "証明書が期限切れです"
        fi
    else
        print_fail "証明書読み取りエラー"
    fi

    # SubjectAltName確認
    SAN_INFO=$(openssl x509 -in /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt -noout -ext subjectAltName 2>&1)
    if echo "$SAN_INFO" | grep -q "IP Address"; then
        print_pass "SubjectAltName (SAN) 設定確認"
        echo "$SAN_INFO" | grep "IP Address" | sed 's/^/       /'
    else
        print_info "SubjectAltName (SAN) 未設定（IPアドレス証明書では任意）"
    fi
}

# ============================================================================
# テスト7: APIエンドポイントHTTPSアクセス
# ============================================================================

test_api_https() {
    print_test "APIエンドポイントHTTPS確認"

    # ヘルスチェック
    RESPONSE=$(curl -s -k --max-time 10 "$HTTPS_URL/health" 2>&1)

    if echo "$RESPONSE" | grep -q "status\|healthy"; then
        print_pass "APIヘルスチェック成功"
    else
        print_fail "APIヘルスチェック失敗"
        echo "$RESPONSE" | head -3
    fi
}

# ============================================================================
# テスト実行
# ============================================================================

main() {
    print_header "HTTPS自動リダイレクトテスト - Mirai Knowledge System"

    echo ""
    echo "テスト対象:"
    echo "  HTTP: $HTTP_URL"
    echo "  HTTPS: $HTTPS_URL"
    echo ""

    # テスト実行
    test_http_redirect_ip || true
    test_http_redirect_localhost || true
    test_https_access || true
    test_security_headers || true
    test_tls_settings || true
    test_certificate || true
    test_api_https || true

    # 結果サマリー
    print_header "テスト結果サマリー"
    echo ""
    echo -e "  ${GREEN}成功: $PASSED${NC}"
    echo -e "  ${RED}失敗: $FAILED${NC}"
    echo -e "  合計: $((PASSED + FAILED))"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ すべてのテストに合格しました！${NC}"
        echo ""
        echo "推奨事項:"
        echo "  - 本番環境ではLet's Encrypt証明書の使用を検討"
        echo "  - 定期的なセキュリティヘッダーテスト実施"
        echo "  - SSL Labsでの外部評価: https://www.ssllabs.com/ssltest/"
        return 0
    else
        echo -e "${RED}✗ 一部のテストが失敗しました${NC}"
        echo ""
        echo "トラブルシューティング:"
        echo "  1. Nginxが起動しているか確認: sudo systemctl status nginx"
        echo "  2. 設定ファイルの構文確認: sudo nginx -t"
        echo "  3. ログ確認: sudo tail -f /var/log/nginx/error.log"
        return 1
    fi
}

# スクリプト実行
main
EXIT_CODE=$?

exit $EXIT_CODE
