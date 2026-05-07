#!/usr/bin/env bash
# 整齐查看 inventory 表结构（比 .schema 单行更易读）
# 用法：在 agent_with_backend 目录下
#   ./scripts/peek_inventory.sh
#   ./scripts/peek_inventory.sh /path/to/other.db

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${1:-$ROOT/pharmacy.db}"

if [[ ! -f "$DB" ]]; then
  echo "找不到数据库文件: $DB" >&2
  exit 1
fi

echo "=== inventory 列清单 (PRAGMA table_info) ==="
echo "数据库: $DB"
echo ""

sqlite3 "$DB" <<'SQL'
.headers on
.mode column
.width 3 22 9 2 30
SELECT cid AS i,
       name AS column_name,
       type,
       [notnull] AS rq,
       ifnull(dflt_value, '') AS default_val
FROM pragma_table_info('inventory')
ORDER BY cid;
SQL

echo ""
echo "=== 行数统计 ==="
sqlite3 "$DB" "SELECT COUNT(*) AS inventory_rows FROM inventory; SELECT COUNT(*) AS indication_rows FROM drug_indications;"
