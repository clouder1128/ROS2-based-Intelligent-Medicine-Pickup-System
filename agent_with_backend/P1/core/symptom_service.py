# agent_with_backend/P1/core/symptom_service.py
"""统一症状提取服务，根据配置选择模式"""

import logging
from typing import Optional

from subagents.models import StructuredSymptoms
from .config import Config

logger = logging.getLogger(__name__)


class SymptomExtractionService:
    """统一症状提取服务，根据配置选择模式"""

    @staticmethod
    def extract(user_input: str, llm_client=None) -> StructuredSymptoms:
        """
        根据配置提取症状

        Args:
            user_input: 用户输入的症状描述
            llm_client: 可选的LLM客户端，使用则启用LLM模式

        Returns:
            StructuredSymptoms: 结构化症状信息
        """
        if not user_input or not user_input.strip():
            raise ValueError("用户输入不能为空")

        # 延迟导入以避免循环依赖
        from subagents.extractor import SymptomExtractor

        # 根据配置决定是否使用LLM
        use_llm = Config.ENABLE_LLM_SYMPTOM_EXTRACTION and llm_client is not None

        logger.info(f"症状提取模式: {'LLM' if use_llm else '规则'} (配置开关: {Config.ENABLE_LLM_SYMPTOM_EXTRACTION})")

        # 创建提取器
        extractor = SymptomExtractor(llm_client, use_llm=use_llm)

        # 执行提取
        try:
            return extractor.extract(user_input)
        except Exception as e:
            logger.error(f"症状提取失败: {e}")
            raise

    @staticmethod
    def extract_with_correction(original_input: str, correction_text: str, llm_client=None) -> StructuredSymptoms:
        """
        基于纠正重新提取症状

        Args:
            original_input: 原始用户输入
            correction_text: 用户纠正文本
            llm_client: 可选的LLM客户端

        Returns:
            StructuredSymptoms: 重新提取的结构化症状信息
        """
        # 组合原始输入和纠正信息
        combined_input = f"{original_input} [用户纠正: {correction_text}]"
        logger.info(f"重新提取症状: 原始='{original_input[:50]}...', 纠正='{correction_text}'")

        return SymptomExtractionService.extract(combined_input, llm_client)