"""subagents模块的公共API接口 - 提供便捷函数"""

import logging
from typing import Optional

from common.config import Config
from .models import StructuredSymptoms
from .exceptions import ExtractionError
from .extractor import SymptomExtractor

logger = logging.getLogger(__name__)


def extract_symptoms(user_input: str, llm_client=None) -> StructuredSymptoms:
    """同步症状提取函数"""
    try:
        use_llm = Config.ENABLE_LLM_SYMPTOM_EXTRACTION and llm_client is not None
        logger.info(f"症状提取模式: {'LLM' if use_llm else '规则'} (配置开关: {Config.ENABLE_LLM_SYMPTOM_EXTRACTION})")
        extractor = SymptomExtractor(llm_client, use_llm=use_llm)
        return extractor.extract(user_input)
    except Exception as e:
        raise ExtractionError(f"症状提取失败: {str(e)}")


async def extract_symptoms_async(user_input: str, llm_client=None) -> StructuredSymptoms:
    """异步症状提取函数"""
    use_llm = llm_client is not None
    extractor = SymptomExtractor(llm_client, use_llm=use_llm)
    return await extractor.extract_async(user_input)


def extract_symptoms_sync(user_input: str, llm_client=None) -> StructuredSymptoms:
    """同步症状提取的别名"""
    return extract_symptoms(user_input, llm_client)
