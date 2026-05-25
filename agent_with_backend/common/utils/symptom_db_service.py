"""
症状/适应症查询服务层（组件1第4周）
封装 symptom_synonyms 和 drug_indications 表的查询逻辑，
供组件3（智能筛选）直接 import，替换硬编码症状库和示例药品数据。

对外接口：
  get_all_synonyms()                → Dict[str, List[str]]   全量同义词表
  find_standard_term(text)          → Optional[str]          任意输入 → 标准症状词
  expand_symptom_list(symptoms)     → List[str]              症状列表扩展为标准词+同义词
  get_drugs_by_symptom(symptom)     → List[dict]             按症状查药（含同义词展开）
  get_drug_indications(drug_id)     → List[str]              查某药品的全部适应症

使用示例（组件3）：
  from common.utils.symptom_db_service import (
      get_all_synonyms, find_standard_term, get_drugs_by_symptom
  )

  # 在 SymptomService._load_symptoms() 中替换硬编码 STANDARD_SYMPTOMS：
  self.STANDARD_SYMPTOMS = get_all_synonyms()

  # 在 ScreeningService.screening_query() 中查药（走缓存优先）：
  from common.utils import get_drug_cache
  cache = get_drug_cache()
  cached = cache.get_drug_list(symptom, None, None, 'drug_id', 'asc')
  if cached is not None:
      drugs = cached
  else:
      drugs = get_drugs_by_symptom(symptom)
      cache.set_drug_list(symptom, None, None, 'drug_id', 'asc', drugs)
"""

from __future__ import annotations

from typing import Dict, List, Optional

from common.utils.database import get_db_connection


def _like_escape(text: str) -> str:
    """对 LIKE 通配符 % 和 _ 进行转义，防止用户输入被当作通配符。"""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_all_synonyms() -> Dict[str, List[str]]:
    """
    读取 symptom_synonyms 表全量数据，返回 {标准词: [同义词...]} 字典。

    组件3 的 SymptomService._load_symptoms() 可直接调用此函数，
    替换硬编码的 STANDARD_SYMPTOMS 字典：
        self.STANDARD_SYMPTOMS = get_all_synonyms()
    """
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT standard_term, synonym FROM symptom_synonyms"
            " ORDER BY standard_term, synonym"
        )
        result: Dict[str, List[str]] = {}
        for row in cur.fetchall():
            result.setdefault(row["standard_term"], []).append(row["synonym"])
        return result
    finally:
        conn.close()


def find_standard_term(input_text: str) -> Optional[str]:
    """
    给定任意症状文本，在 symptom_synonyms 中查找对应标准词。

    查找优先级：
      1. 精确匹配 standard_term（输入本身即标准词）
      2. 精确匹配 synonym（同义词完全命中）
      3. LIKE 模糊匹配 synonym（包含关系）

    返回第一个匹配的 standard_term，无匹配返回 None。
    """
    text = input_text.strip()
    if not text:
        return None

    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT standard_term FROM symptom_synonyms WHERE standard_term = ? LIMIT 1",
            (text,),
        )
        row = cur.fetchone()
        if row:
            return row["standard_term"]

        cur = conn.execute(
            "SELECT standard_term FROM symptom_synonyms WHERE synonym = ? LIMIT 1",
            (text,),
        )
        row = cur.fetchone()
        if row:
            return row["standard_term"]

        # 双向模糊：synonym 包含 text，或 text 包含 synonym
        escaped = _like_escape(text)
        cur = conn.execute(
            "SELECT standard_term FROM symptom_synonyms"
            " WHERE synonym LIKE ? ESCAPE '\\'"
            "    OR ? LIKE '%' || synonym || '%'"
            " LIMIT 1",
            (f"%{escaped}%", text),
        )
        row = cur.fetchone()
        if row:
            return row["standard_term"]

        return None
    finally:
        conn.close()


def expand_symptom_list(symptoms: List[str]) -> List[str]:
    """
    将症状列表中每个词扩展为"标准词 + 该标准词全部同义词"，去重后返回。

    供 ScreeningService 在查询 drug_indications 前预处理，提高召回率。
    """
    if not symptoms:
        return []

    conn = get_db_connection()
    try:
        expanded: set = set(symptoms)
        for symptom in symptoms:
            cur = conn.execute(
                "SELECT standard_term FROM symptom_synonyms"
                " WHERE standard_term = ? OR synonym = ? LIMIT 1",
                (symptom, symptom),
            )
            row = cur.fetchone()
            if row:
                standard = row["standard_term"]
                expanded.add(standard)
                cur2 = conn.execute(
                    "SELECT synonym FROM symptom_synonyms WHERE standard_term = ?",
                    (standard,),
                )
                expanded.update(r["synonym"] for r in cur2.fetchall())
        return list(expanded)
    finally:
        conn.close()


def get_drugs_by_symptom(
    symptom: str,
    include_deleted: bool = False,
    include_zero_stock: bool = False,
) -> List[Dict]:
    """
    按症状查询可用药品，自动展开同义词后查 drug_indications + inventory。

    参数：
      symptom            — 症状文本（标准词或同义词均可）
      include_deleted    — 是否包含软删除药品（默认 False）
      include_zero_stock — 是否包含库存为 0 的药品（默认 False）

    返回含 indications 字段的药品字典列表，按 drug_id 升序，已去重。
    """
    symptom = symptom.strip()
    if not symptom:
        return []

    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT standard_term FROM symptom_synonyms"
            " WHERE standard_term = ? OR synonym = ? LIMIT 1",
            (symptom, symptom),
        )
        row = cur.fetchone()
        if row:
            standard = row["standard_term"]
            cur2 = conn.execute(
                "SELECT synonym FROM symptom_synonyms WHERE standard_term = ?",
                (standard,),
            )
            search_terms = {standard} | {r["synonym"] for r in cur2.fetchall()}
        else:
            search_terms = {symptom}

        # 对 LIKE 通配符转义，防止 % / _ 被当作通配符
        like_clauses = " OR ".join(
            "indication LIKE ? ESCAPE '\\'" for _ in search_terms
        )
        like_params = tuple(f"%{_like_escape(t)}%" for t in search_terms)
        cur = conn.execute(
            f"SELECT DISTINCT drug_id FROM drug_indications WHERE {like_clauses}",
            like_params,
        )
        drug_ids = [r["drug_id"] for r in cur.fetchall()]

        if not drug_ids:
            return []

        placeholders = ",".join("?" for _ in drug_ids)
        conditions = [f"drug_id IN ({placeholders})"]
        if not include_deleted:
            conditions.append("COALESCE(is_deleted, 0) = 0")
        if not include_zero_stock:
            conditions.append("quantity > 0")

        where_sql = "WHERE " + " AND ".join(conditions)
        cur = conn.execute(
            f"SELECT * FROM inventory {where_sql} ORDER BY drug_id",
            tuple(drug_ids),
        )
        drugs = [dict(row) for row in cur.fetchall()]

        if drugs:
            ids = [d["drug_id"] for d in drugs]
            ph2 = ",".join("?" for _ in ids)
            cur = conn.execute(
                f"SELECT drug_id, indication FROM drug_indications"
                f" WHERE drug_id IN ({ph2})",
                ids,
            )
            imap: Dict[int, List[str]] = {}
            for r in cur.fetchall():
                imap.setdefault(r["drug_id"], []).append(r["indication"])
            for d in drugs:
                d["indications"] = imap.get(d["drug_id"], [])

        return drugs
    finally:
        conn.close()


def get_drug_indications(drug_id: int) -> List[str]:
    """查询单个药品的全部适应症列表，按 id 排序。"""
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT indication FROM drug_indications WHERE drug_id = ? ORDER BY id",
            (drug_id,),
        )
        return [row["indication"] for row in cur.fetchall()]
    finally:
        conn.close()
