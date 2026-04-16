"""症状提取子代理 - 从用户输入提取结构化症状信息"""

import logging

logger = logging.getLogger(__name__)


# 重新导出公共API
from .models import Gender, PatientInfo, StructuredSymptoms
from .exceptions import ExtractionError
from .extractor import SymptomExtractor
from .api import extract_symptoms, extract_symptoms_async, extract_symptoms_sync


