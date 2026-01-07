#!/bin/bash
# PostgreSQL セットアップスクリプト（ネイティブインストール用）
# Mirai Knowledge Systems - Phase B-10
#
# 使用方法:
#   ./setup_postgres.sh [init|migrate|status|reset]
#
# 環境変数:
#   DATABASE_URL: PostgreSQL接続URL（省略可）
#   PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE: 個別設定

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# デフォルト設定
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGDATABASE="${PGDATABASE:-mirai_knowledge_db}"
DATABASE_URL="${DATABASE_URL:-postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# PostgreSQL接続確認
check_postgres() {
    log_info "PostgreSQL接続を確認中..."

    if ! command -v psql &> /dev/null; then
        log_error "psqlコマンドが見つかりません"
        log_info "PostgreSQLをインストールしてください:"
        log_info "  Ubuntu: sudo apt install postgresql postgresql-contrib"
        log_info "  CentOS: sudo yum install postgresql-server postgresql-contrib"
        return 1
    fi

    if pg_isready -h "$PGHOST" -p "$PGPORT" > /dev/null 2>&1; then
        log_success "PostgreSQLサーバー: 起動中"
        return 0
    else
        log_error "PostgreSQLサーバーに接続できません"
        log_info "PostgreSQLサービスを起動してください:"
        log_info "  sudo systemctl start postgresql"
        return 1
    fi
}

# データベース初期化
init_database() {
    log_info "データベースを初期化中..."

    check_postgres || return 1

    # データベース存在確認
    if psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$PGDATABASE"; then
        log_warn "データベース '$PGDATABASE' は既に存在します"
        read -p "既存のデータベースを使用しますか？ (y/N): " use_existing
        if [ "$use_existing" != "y" ] && [ "$use_existing" != "Y" ]; then
            return 1
        fi
    else
        log_info "データベース '$PGDATABASE' を作成中..."
        createdb -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" 2>/dev/null || {
            log_error "データベース作成に失敗しました"
            log_info "手動で作成してください: createdb -U $PGUSER $PGDATABASE"
            return 1
        }
        log_success "データベースを作成しました"
    fi

    # init-db.sql実行
    log_info "スキーマを作成中..."
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$PROJECT_ROOT/init-db.sql"

    log_success "データベース初期化が完了しました"
}

# データベースステータス確認
check_status() {
    log_info "PostgreSQLステータスを確認中..."

    if ! check_postgres; then
        return 1
    fi

    # データベース存在確認
    if psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$PGDATABASE"; then
        log_success "データベース '$PGDATABASE': 存在"

        # 接続テスト
        if psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT 1" > /dev/null 2>&1; then
            log_success "データベース接続: OK"

            # テーブル数確認
            TABLE_COUNT=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('public', 'auth', 'audit');" 2>/dev/null | tr -d ' ')
            log_info "テーブル数: $TABLE_COUNT"

            # データ件数確認
            if [ "$TABLE_COUNT" -gt 0 ]; then
                KNOWLEDGE_COUNT=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT count(*) FROM public.knowledge;" 2>/dev/null | tr -d ' ' || echo "0")
                USER_COUNT=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT count(*) FROM auth.users;" 2>/dev/null | tr -d ' ' || echo "0")
                log_info "ナレッジ件数: $KNOWLEDGE_COUNT"
                log_info "ユーザー数: $USER_COUNT"
            fi
        else
            log_warn "データベース接続: 失敗"
        fi
    else
        log_warn "データベース '$PGDATABASE': 存在しない"
        log_info "初期化を実行してください: $0 init"
    fi
}

# データ移行実行
run_migration() {
    log_info "JSONからPostgreSQLへのデータ移行を開始..."

    check_postgres || return 1

    cd "$BACKEND_DIR"

    # 仮想環境の有効化
    if [ -d "venv_linux" ]; then
        source venv_linux/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # 移行スクリプト実行
    DATABASE_URL="$DATABASE_URL" python scripts/migrate_json_to_postgres.py --verbose

    log_success "データ移行が完了しました"
}

# Alembicマイグレーション実行
run_alembic() {
    log_info "Alembicマイグレーションを実行中..."

    cd "$BACKEND_DIR"

    # 仮想環境の有効化
    if [ -d "venv_linux" ]; then
        source venv_linux/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # マイグレーション実行
    DATABASE_URL="$DATABASE_URL" alembic upgrade head

    log_success "Alembicマイグレーションが完了しました"
}

# データベースリセット
reset_database() {
    log_warn "データベースをリセットします。全データが削除されます。"
    read -p "続行しますか？ (y/N): " confirm

    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "キャンセルしました"
        return 0
    fi

    check_postgres || return 1

    log_info "データベースを削除中..."
    dropdb -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" 2>/dev/null || true

    log_info "データベースを再作成中..."
    init_database

    log_success "データベースをリセットしました"
}

# フルセットアップ
full_setup() {
    log_info "PostgreSQLフルセットアップを開始..."

    init_database || return 1

    log_info "データ移行を実行しますか？"
    read -p "JSONデータをPostgreSQLに移行する (y/N): " migrate_confirm

    if [ "$migrate_confirm" = "y" ] || [ "$migrate_confirm" = "Y" ]; then
        run_migration
    fi

    log_success "セットアップが完了しました"
    echo ""
    echo "次のステップ:"
    echo "  1. 環境変数を設定: export DATABASE_URL='$DATABASE_URL'"
    echo "  2. アプリケーションを起動: cd backend && python app_v2.py"
    echo "  3. ヘルスチェック: curl http://localhost:5100/api/v1/health"
}

# ヘルプ表示
show_help() {
    echo "PostgreSQL セットアップスクリプト（ネイティブインストール用）"
    echo ""
    echo "使用方法:"
    echo "  $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  init      データベースとスキーマを初期化"
    echo "  status    データベースステータスを確認"
    echo "  migrate   JSONデータをPostgreSQLに移行"
    echo "  alembic   Alembicマイグレーションを実行"
    echo "  reset     データベースをリセット（全データ削除）"
    echo "  setup     フルセットアップ（初期化 + 移行）"
    echo "  help      このヘルプを表示"
    echo ""
    echo "環境変数:"
    echo "  DATABASE_URL  PostgreSQL接続URL"
    echo "  PGHOST        ホスト（デフォルト: localhost）"
    echo "  PGPORT        ポート（デフォルト: 5432）"
    echo "  PGUSER        ユーザー（デフォルト: postgres）"
    echo "  PGPASSWORD    パスワード"
    echo "  PGDATABASE    データベース名（デフォルト: mirai_knowledge_db）"
    echo ""
    echo "例:"
    echo "  PGPASSWORD=mypassword $0 init"
    echo "  $0 status"
    echo "  $0 migrate"
}

# メイン処理
case "${1:-help}" in
    init)
        init_database
        ;;
    status)
        check_status
        ;;
    migrate)
        run_migration
        ;;
    alembic)
        run_alembic
        ;;
    reset)
        reset_database
        ;;
    setup)
        full_setup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "不明なコマンド: $1"
        show_help
        exit 1
        ;;
esac
