"""症状数据模型"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

# 假设从common配置中导入数据库基类
try:
    from common.config import db
except:
    # 如果导入失败，定义一个简单的基类用于开发
    from sqlalchemy.ext.declarative import declarative_base
    db_base = declarative_base()
    class DbModel:
        pass
else:
    db_base = db.Model
    class DbModel:
        pass


class Symptom(db_base):
    """症状标准化模型
    
    存储标准的医学症状名称和相关信息
    """
    __tablename__ = 'symptoms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    standard_name = Column(String(100), unique=True, nullable=False, comment="标准症状名称")
    category = Column(String(50), nullable=False, comment="症状分类（如：消化道、呼吸道等）")
    description = Column(Text, comment="症状描述")
    severity_levels = Column(String(200), comment="严重程度（轻、中、重）")
    related_drugs_count = Column(Integer, default=0, comment="关联药品数量")
    
    # 关系
    synonyms = relationship('SymptomSynonym', back_populates='symptom', cascade='all, delete-orphan')
    screening_histories = relationship('ScreeningHistory', back_populates='symptom')
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<Symptom(id={self.id}, name={self.standard_name}, category={self.category})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'standard_name': self.standard_name,
            'category': self.category,
            'description': self.description,
            'severity_levels': self.severity_levels,
            'related_drugs_count': self.related_drugs_count,
            'synonyms': [s.synonym_name for s in self.synonyms] if self.synonyms else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SymptomSynonym(db_base):
    """症状同义词模型
    
    存储症状的各种表述方式（同义词）以支持模糊匹配
    例如："头疼" -> 标准名称"头痛"
    """
    __tablename__ = 'symptom_synonyms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symptom_id = Column(Integer, ForeignKey('symptoms.id'), nullable=False, comment="关联的标准症状ID")
    synonym_name = Column(String(100), nullable=False, comment="同义词名称")
    priority = Column(Integer, default=1, comment="优先级（1-10，数字越大优先级越高）")
    
    # 关系
    symptom = relationship('Symptom', back_populates='synonyms')
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    def __repr__(self):
        return f"<SymptomSynonym(id={self.id}, synonym={self.synonym_name})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'symptom_id': self.symptom_id,
            'synonym_name': self.synonym_name,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
