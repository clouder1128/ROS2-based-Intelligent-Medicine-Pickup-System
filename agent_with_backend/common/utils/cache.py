"""
第三周（组件1）：内存缓存层
────────────────────────────────────────────────────────────
提供线程安全的 TTL 内存缓存，主要用于热门药品查询加速。

对外公开：
  get_drug_cache() → DrugCache   全局单例，其他组件直接调用
  DrugCache                       领域封装：列表 / 统计 / 详情 / 分类
  SimpleCache                     底层通用 KV 缓存（可独立复用）

TTL 默认值：
  药品列表  120 s   — 写操作后整批失效
  药品统计   60 s   — 任何库存变更后失效
  药品详情  300 s   — 更新/删除后按 ID 精确失效
  分类列表  300 s   — 分类写操作后整批失效

失效规则：
  create_drug / update_drug / delete_drug / adjust_inventory
      → invalidate_drug_writes(drug_id=...)
  create_category / update_category / delete_category
      → invalidate_categories()

使用示例（drug_controller.py）：
  from common.utils.cache import get_drug_cache
  cache = get_drug_cache()

  # 读取
  cached = cache.get_drug_list(symptom, name, category, sort_by, sort_order)
  if cached is not None:
      drugs = cached
  else:
      drugs = query_drugs(...)
      cache.set_drug_list(symptom, name, category, sort_by, sort_order, drugs)

  # 写后失效
  cache.invalidate_drug_writes(drug_id=drug_id)
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Optional


# ──────────────────────────────────────────────────────────────────
# 底层通用缓存
# ──────────────────────────────────────────────────────────────────

class SimpleCache:
    """
    线程安全的内存 TTL 键值缓存。

    存储结构：key → (value, expires_at_monotonic)
    过期检查在 get() 时懒惰触发；调用 evict_expired() 主动清理。
    """

    def __init__(self, default_ttl: int = 300) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl

    # ── 核心操作 ──────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """返回缓存值；过期或不存在返回 None。"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """写入缓存；ttl 为 None 时使用实例默认值（秒）。"""
        with self._lock:
            effective_ttl = self._default_ttl if ttl is None else ttl
            self._store[key] = (value, time.monotonic() + effective_ttl)

    def delete(self, key: str) -> bool:
        """精确删除单个 key；返回是否存在。"""
        with self._lock:
            return self._store.pop(key, None) is not None

    def delete_prefix(self, prefix: str) -> int:
        """删除所有以 prefix 开头的 key；返回删除数量。"""
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            return len(keys)

    def clear(self) -> None:
        """清空全部缓存。"""
        with self._lock:
            self._store.clear()

    # ── 运维 ──────────────────────────────────────────────────────

    def evict_expired(self) -> int:
        """主动清理已过期条目；返回清理数量。"""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
            return len(expired)

    def info(self) -> dict:
        """返回缓存统计信息（用于调试 / 监控）。"""
        now = time.monotonic()
        with self._lock:
            total = len(self._store)
            active = sum(1 for _, exp in self._store.values() if now <= exp)
            return {
                "total_keys": total,
                "active_keys": active,
                "expired_keys": total - active,
            }


# ──────────────────────────────────────────────────────────────────
# 药品域缓存封装
# ──────────────────────────────────────────────────────────────────

class DrugCache:
    """
    药品查询缓存（组件1第三周交付物）。

    封装了键名规则与 TTL 策略，调用方无需关心底层 SimpleCache 的 key 格式。
    供组件2（drug_controller / category_controller）和组件3（screening）复用。
    """

    LIST_TTL   = 120   # 药品列表：120 s
    STATS_TTL  =  60   # 统计汇总：60 s
    DETAIL_TTL = 300   # 单药详情：300 s
    CAT_TTL    = 300   # 分类列表：300 s

    _PREFIX_LIST   = "drug_list:"
    _PREFIX_DETAIL = "drug:"
    _KEY_STATS     = "drug_stats"
    _PREFIX_CAT    = "cat_list:"

    def __init__(self) -> None:
        self._cache = SimpleCache(default_ttl=120)

    # ── 药品列表 ──────────────────────────────────────────────────

    @staticmethod
    def _list_key(
        symptom: Optional[str],
        name: Optional[str],
        category: Optional[str],
        sort_by: str,
        sort_order: str,
    ) -> str:
        # json.dumps 保证各字段值含冒号、空字符串、None 时也不产生碰撞
        suffix = json.dumps(
            [symptom, name, category, sort_by, sort_order],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return f"drug_list:{suffix}"

    def get_drug_list(
        self,
        symptom: Optional[str],
        name: Optional[str],
        category: Optional[str],
        sort_by: str,
        sort_order: str,
    ) -> Optional[list]:
        """返回缓存的药品列表（未分页完整列表）；未命中返回 None。"""
        return self._cache.get(
            self._list_key(symptom, name, category, sort_by, sort_order)
        )

    def set_drug_list(
        self,
        symptom: Optional[str],
        name: Optional[str],
        category: Optional[str],
        sort_by: str,
        sort_order: str,
        data: list,
    ) -> None:
        """缓存药品列表（query_drugs 返回的完整列表，分页在外部切片）。"""
        self._cache.set(
            self._list_key(symptom, name, category, sort_by, sort_order),
            data,
            ttl=self.LIST_TTL,
        )

    # ── 药品统计 ──────────────────────────────────────────────────

    def get_stats(self) -> Optional[dict]:
        """返回缓存的统计字典；未命中返回 None。"""
        return self._cache.get(self._KEY_STATS)

    def set_stats(self, data: dict) -> None:
        """缓存 drug_stats 结果（含 total_drugs / total_quantity 等）。"""
        self._cache.set(self._KEY_STATS, data, ttl=self.STATS_TTL)

    # ── 药品详情 ──────────────────────────────────────────────────

    def get_drug(self, drug_id: int) -> Optional[dict]:
        """返回缓存的单药详情；未命中返回 None。"""
        return self._cache.get(f"{self._PREFIX_DETAIL}{drug_id}")

    def set_drug(self, drug_id: int, data: dict) -> None:
        """缓存单药详情（含 indications 列表）。"""
        self._cache.set(f"{self._PREFIX_DETAIL}{drug_id}", data, ttl=self.DETAIL_TTL)

    # ── 分类列表 ──────────────────────────────────────────────────

    @staticmethod
    def _cat_key(want_tree: bool) -> str:
        return f"cat_list:{'tree' if want_tree else 'flat'}"

    def get_categories(self, want_tree: bool) -> Optional[list]:
        """返回缓存的分类列表（平铺或树形）；未命中返回 None。"""
        return self._cache.get(self._cat_key(want_tree))

    def set_categories(self, want_tree: bool, data: list) -> None:
        """缓存分类列表。"""
        self._cache.set(self._cat_key(want_tree), data, ttl=self.CAT_TTL)

    # ── 失效 ──────────────────────────────────────────────────────

    def invalidate_drug_writes(self, drug_id: Optional[int] = None) -> None:
        """
        任何药品写操作（create / update / delete / adjust）后调用。
        - 失效全部 drug_list:* 和 drug_stats（统计/列表立即刷新）
        - 若提供 drug_id，同时精确失效该药品详情缓存
        """
        self._cache.delete_prefix(self._PREFIX_LIST)
        self._cache.delete(self._KEY_STATS)
        if drug_id is not None:
            self._cache.delete(f"{self._PREFIX_DETAIL}{drug_id}")

    def invalidate_categories(self) -> None:
        """分类写操作（create / update / delete）后调用，失效全部分类缓存。"""
        self._cache.delete_prefix(self._PREFIX_CAT)

    # ── 运维 ──────────────────────────────────────────────────────

    def evict_expired(self) -> int:
        """主动清理过期缓存条目；返回清理数量（可由后台定时任务调用）。"""
        return self._cache.evict_expired()

    def clear(self) -> None:
        """清空全部缓存（测试 / 重启时使用）。"""
        self._cache.clear()

    def info(self) -> dict:
        """返回缓存统计，包含 TTL 配置和当前条目数（供 /api/health 扩展）。"""
        base = self._cache.info()
        base["ttl_config"] = {
            "list_ttl_sec": self.LIST_TTL,
            "stats_ttl_sec": self.STATS_TTL,
            "detail_ttl_sec": self.DETAIL_TTL,
            "category_ttl_sec": self.CAT_TTL,
        }
        return base


# ──────────────────────────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────────────────────────

_drug_cache = DrugCache()


def get_drug_cache() -> DrugCache:
    """
    获取全局共享 DrugCache 实例（进程级单例）。

    用法：
        from common.utils.cache import get_drug_cache
        cache = get_drug_cache()
    """
    return _drug_cache
