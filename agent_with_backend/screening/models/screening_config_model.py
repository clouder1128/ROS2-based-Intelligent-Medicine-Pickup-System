"""筛选配置数据模型"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

try:
    from common.config import db
    db_base = db.Model
except:
    db_base = declarative_base()


class ScreeningConfig(db_base):
    """筛选系统配置模型
    
    存储筛选系统的全局配置参数，如：
    - 匹配算法参数
    - 置信度阈值
    - 最大结果数
    - 缓存策略等
    """
    __tablename__ = 'screening_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本配置
    config_name = Column(String(100), unique=True, nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")
    
    # 算法参数
    algorithm_type = Column(String(50), default='similarity', comment="匹配算法类型（similarity/ml/hybrid）")
    confidence_threshold = Column(Float, default=0.5, comment="置信度阈值（0-1）")
    max_results = Column(Integer, default=20, comment="最大返回结果数")
    min_symptom_match_rate = Column(Float, default=0.3, comment="最小症状匹配率（0-1）")
    
    # 症状处理参数
    enable_synonym_expansion = Column(Boolean, default=True, comment="是否启用同义词扩展")
    enable_llm_synonym = Column(Boolean, default=False, comment="是否启用LLM同义词重试")
    max_synonym_attempts = Column(Integer, default=3, comment="LLM同义词重试次数")
    
    # 缓存配置
    enable_cache = Column(Boolean, default=True, comment="是否启用缓存")
    cache_ttl = Column(Integer, default=3600, comment="缓存过期时间（秒）")
    cache_strategy = Column(String(50), default='lru', comment="缓存策略（lru/lfu/fifo）")
    
    # 性能配置
    timeout_seconds = Column(Float, default=5.0, comment="筛选查询超时时间（秒）")
    batch_max_size = Column(Integer, default=100, comment="批量查询最大数量")
    
    # 其他参数
    extra_params = Column(JSON, comment="其他扩展参数（JSON格式）")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    version = Column(Integer, default=1, comment="配置版本")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    updated_by = Column(String(100), comment="最后更新人")
    
    def __repr__(self):
        return f\"<ScreeningConfig(id={self.id}, name={self.config_name}, active={self.is_active})>\"
    
    def to_dict(self):
        \"\"\"转换为字典格式\"\"\"
        return {
            'id': self.id,
            'config_name': self.config_name,
            'description': self.description,
            'algorithm_type': self.algorithm_type,
            'confidence_threshold': self.confidence_threshold,
            'max_results': self.max_results,
            'min_symptom_match_rate': self.min_symptom_match_rate,
            'enable_synonym_expansion': self.enable_synonym_expansion,
            'enable_llm_synonym': self.enable_llm_synonym,
            'max_synonym_attempts': self.max_synonym_attempts,
            'enable_cache': self.enable_cache,
            'cache_ttl': self.cache_ttl,
            'cache_strategy': self.cache_strategy,
            'timeout_seconds': self.timeout_seconds,
            'batch_max_size': self.batch_max_size,
            'extra_params': self.extra_params,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
