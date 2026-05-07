"""筛选历史数据模型"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship

try:
    from common.config import db
    db_base = db.Model
except:
    from sqlalchemy.ext.declarative import declarative_base
    db_base = declarative_base()


class ScreeningHistory(db_base):
    """筛选历史模型
    
    记录每次的药品筛选查询，包括输入症状、返回结果、执行时间等
    """
    __tablename__ = 'screening_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="用户ID")
    
    # 输入信息
    input_symptoms = Column(JSON, nullable=False, comment="输入的症状列表（JSON格式）")
    input_text = Column(Text, comment="原始输入文本")
    patient_info = Column(JSON, comment="患者信息（年龄、性别等）")
    filters = Column(JSON, comment="应用的筛选条件（JSON格式）")
    
    # 输出信息
    result_drugs = Column(JSON, nullable=False, comment="筛选出的药品列表（JSON格式）")
    result_count = Column(Integer, default=0, comment="返回的药品数量")
    confidence_scores = Column(JSON, comment="各结果的置信度分数（JSON格式）")
    
    # 执行信息
    execution_time = Column(Float, comment="执行耗时（秒）")
    status = Column(String(20), default='success', comment="执行状态（success/error/partial）")
    error_message = Column(Text, comment="错误信息（如有）")
    
    # 追踪信息
    request_id = Column(String(100), unique=True, comment="请求唯一ID，用于追踪")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f\"<ScreeningHistory(id={self.id}, user_id={self.user_id}, result_count={self.result_count})>\"
    
    def to_dict(self):
        \"\"\"转换为字典格式\"\"\"
        return {
            'id': self.id,
            'user_id': self.user_id,
            'input_symptoms': self.input_symptoms,
            'input_text': self.input_text,
            'patient_info': self.patient_info,
            'filters': self.filters,
            'result_drugs': self.result_drugs,
            'result_count': self.result_count,
            'confidence_scores': self.confidence_scores,
            'execution_time': self.execution_time,
            'status': self.status,
            'error_message': self.error_message,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
