#!/usr/bin/env bash
# 手测药品 CRUD：新增「维生素B」→ 查询 → 修改 → 软删除 → 再查应 404
# 前置：在 agent_with_backend 目录已启动服务: python3 main.py
# 用法：./scripts/smoke_drug_api.sh
# 可选：BASE=http://127.0.0.1:8001 ./scripts/smoke_drug_api.sh

set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8001}"

echo ">>> POST 新增维生素B (及适应症)"
RESP=$(curl -sS -X POST "${BASE}/api/drugs" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "维生素B",
    "quantity": 80,
    "expiry_date": 400,
    "shelf_x": 3,
    "shelf_y": 2,
    "shelve_id": 1,
    "category": "维生素矿物质",
    "is_prescription": false,
    "retail_price": 12.5,
    "indications": ["口角炎", "神经炎", "疲劳"]
  }')
echo "$RESP" | python3 -m json.tool || echo "$RESP"
ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drug_id',''))")
if [[ -z "$ID" ]]; then
  echo "POST 失败或未返回 drug_id，请确认服务已启动: python3 main.py （默认端口 8001）" >&2
  exit 1
fi
echo "新药品 drug_id = $ID"

echo ""
echo ">>> GET 详情"
curl -sS "${BASE}/api/drugs/${ID}" | python3 -m json.tool

echo ""
echo ">>> PUT 改价 + 替换适应症"
curl -sS -X PUT "${BASE}/api/drugs/${ID}" \
  -H "Content-Type: application/json" \
  -d '{"retail_price": 15.0, "indications": ["口角炎", "神经炎", "疲劳", "食欲不振"]}' | python3 -m json.tool

echo ""
echo ">>> GET 列表（分页）"
curl -sS "${BASE}/api/drugs?page=1&limit=5&sort_by=name&order=asc" | python3 -m json.tool

echo ""
echo ">>> DELETE 软删除"
curl -sS -X DELETE "${BASE}/api/drugs/${ID}" | python3 -m json.tool

echo ""
echo ">>> GET 详情（应 404）"
curl -sS -w "\nHTTP %{http_code}\n" "${BASE}/api/drugs/${ID}"

echo ""
echo ">>> 请在另一个终端用 sqlite3 复查（把 ID 换成上面打印的）："
echo "    sqlite3 pharmacy.db \"SELECT drug_id,name,quantity,retail_price,is_deleted FROM inventory WHERE drug_id=$ID;\""
echo "    sqlite3 pharmacy.db \"SELECT indication FROM drug_indications WHERE drug_id=$ID;\""
