"""subagents模块的公共API接口 - 提供便捷函数"""

import logging
from typing import Optional

from ..core.config import Config
from .models import StructuredSymptoms
from .exceptions import ExtractionError
from .extractor import SymptomExtractor  # 保留用于异步版本

logger = logging.getLogger(__name__)


# 便捷函数：同步版本
def extract_symptoms(user_input: str, llm_client=None) -> StructuredSymptoms:
    """
    同步症状提取函数（使用新的提取服务）

    Args:
        user_input: 用户输入的症状描述
        llm_client: 可选的LLM客户端，使用则启用LLM模式

    Returns:
        StructuredSymptoms: 结构化症状信息

    Raises:
        ExtractionError: 提取失败时抛出
    """
    try:
        # 根据配置决定是否使用LLM
        use_llm = Config.ENABLE_LLM_SYMPTOM_EXTRACTION and llm_client is not None
        logger.info(f"症状提取模式: {'LLM' if use_llm else '规则'} (配置开关: {Config.ENABLE_LLM_SYMPTOM_EXTRACTION})")

        # 创建提取器
        extractor = SymptomExtractor(llm_client, use_llm=use_llm)

        # 执行提取
        return extractor.extract(user_input)
    except Exception as e:
        raise ExtractionError(f"症状提取失败: {str(e)}")


# 便捷函数：异步版本
async def extract_symptoms_async(user_input: str, llm_client=None) -> StructuredSymptoms:
    """
    异步症状提取函数

    Args:
        user_input: 用户输入的症状描述
        llm_client: 可选的LLM客户端，使用则启用LLM模式

    Returns:
        StructuredSymptoms: 结构化症状信息
    """
    use_llm = llm_client is not None
    extractor = SymptomExtractor(llm_client, use_llm=use_llm)
    return await extractor.extract_async(user_input)


# 便捷函数：同步版本（使用完整LLM）
def extract_symptoms_sync(user_input: str, llm_client=None) -> StructuredSymptoms:
    """同步症状提取的别名"""
    return extract_symptoms(user_input, llm_client)