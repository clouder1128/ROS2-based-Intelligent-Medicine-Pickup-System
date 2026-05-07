"""筛选配置服务"""

import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigService:
    \"\"\"筛选系统配置服务
    
    负责：
    - 读取和更新筛选配置
    - 配置版本管理
    - 配置验证
    \"\"\"
    
    # 默认配置模板
    DEFAULT_CONFIG = {
        'config_name': 'default',
        'description': '默认筛选配置',
        'algorithm_type': 'similarity',
        'confidence_threshold': 0.5,
        'max_results': 20,
        'min_symptom_match_rate': 0.3,
        'enable_synonym_expansion': True,
        'enable_llm_synonym': False,
        'max_synonym_attempts': 3,
        'enable_cache': True,
        'cache_ttl': 3600,
        'cache_strategy': 'lru',
        'timeout_seconds': 5.0,
        'batch_max_size': 100,
        'is_active': True,
        'version': 1,
    }
    
    def __init__(self, db_session=None):
        \"\"\"初始化配置服务
        
        Args:
            db_session: 数据库会话
        \"\"\"
        self.db_session = db_session
        self._config_cache = {}
        self._load_configs()
    
    def _load_configs(self):
        \"\"\"从数据库加载配置\"\"\"
        # TODO: 从数据库加载所有活跃配置
        # 暂时使用默认配置
        self._config_cache['default'] = self.DEFAULT_CONFIG.copy()
    
    def get_config(self, config_name: str = 'default') -> Optional[Dict]:
        \"\"\"获取筛选配置
        
        Args:
            config_name: 配置名称，默认为'default'
            
        Returns:
            配置字典，如果不存在返回None
        \"\"\"
        if config_name in self._config_cache:
            return self._config_cache[config_name].copy()
        
        # TODO: 从数据库查询
        return None
    
    def get_active_config(self) -> Dict:
        \"\"\"获取当前活跃配置
        
        Returns:
            活跃的筛选配置
        \"\"\"
        # TODO: 从数据库查询is_active=True的配置
        return self.get_config('default') or self.DEFAULT_CONFIG
    
    def list_configs(self) -> list:
        \"\"\"获取所有配置列表
        
        Returns:
            配置列表
        \"\"\"
        return list(self._config_cache.values())
    
    def create_config(self, config_data: Dict, created_by: str = 'system') -> Dict:
        \"\"\"创建新配置
        
        Args:
            config_data: 配置数据
            created_by: 创建者
            
        Returns:
            创建的配置或错误信息
        \"\"\"
        # 验证必填字段
        if 'config_name' not in config_data:
            return {'success': False, 'error': '配置名称不能为空'}
        
        config_name = config_data['config_name']
        
        # 检查是否已存在
        if config_name in self._config_cache:
            return {'success': False, 'error': f'配置 {config_name} 已存在'}
        
        # 合并默认配置
        new_config = self.DEFAULT_CONFIG.copy()
        new_config.update(config_data)
        new_config['version'] = 1
        new_config['created_at'] = datetime.utcnow().isoformat()
        
        # 保存到缓存和数据库
        self._config_cache[config_name] = new_config
        
        # TODO: 保存到数据库
        # if self.db_session:
        #     db_config = ScreeningConfig(**new_config)
        #     self.db_session.add(db_config)
        #     self.db_session.commit()
        
        return {
            'success': True,
            'config': new_config,
            'message': f'配置 {config_name} 创建成功'
        }
    
    def update_config(
        self,
        config_name: str,
        updates: Dict,
        updated_by: str = 'system'
    ) -> Dict:
        \"\"\"更新配置
        
        Args:
            config_name: 配置名称
            updates: 更新的字段
            updated_by: 更新者
            
        Returns:
            更新结果
        \"\"\"
        if config_name not in self._config_cache:
            return {'success': False, 'error': f'配置 {config_name} 不存在'}
        
        config = self._config_cache[config_name]
        
        # 验证配置字段
        validation_result = self._validate_config_fields(updates)
        if not validation_result['valid']:
            return {'success': False, 'error': validation_result['errors']}
        
        # 更新配置
        config.update(updates)
        config['version'] = config.get('version', 1) + 1
        config['updated_at'] = datetime.utcnow().isoformat()
        config['updated_by'] = updated_by
        
        # TODO: 保存到数据库
        
        return {
            'success': True,
            'config': config,
            'message': f'配置 {config_name} 更新成功'
        }
    
    def delete_config(self, config_name: str) -> Dict:
        \"\"\"删除配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            删除结果
        \"\"\"
        if config_name == 'default':
            return {'success': False, 'error': '默认配置不能删除'}
        
        if config_name not in self._config_cache:
            return {'success': False, 'error': f'配置 {config_name} 不存在'}
        
        del self._config_cache[config_name]
        
        # TODO: 从数据库删除
        
        return {
            'success': True,
            'message': f'配置 {config_name} 删除成功'
        }
    
    def _validate_config_fields(self, config_data: Dict) -> Dict:
        \"\"\"验证配置字段
        
        Args:
            config_data: 配置数据
            
        Returns:
            验证结果
        \"\"\"
        errors = []
        
        # 验证数值范围
        if 'confidence_threshold' in config_data:
            threshold = config_data['confidence_threshold']
            if not (0 <= threshold <= 1):
                errors.append('置信度阈值必须在0-1之间')
        
        if 'min_symptom_match_rate' in config_data:
            rate = config_data['min_symptom_match_rate']
            if not (0 <= rate <= 1):
                errors.append('最小症状匹配率必须在0-1之间')
        
        if 'max_results' in config_data:
            max_results = config_data['max_results']
            if not (1 <= max_results <= 1000):
                errors.append('最大结果数必须在1-1000之间')
        
        if 'timeout_seconds' in config_data:
            timeout = config_data['timeout_seconds']
            if timeout <= 0 or timeout > 60:
                errors.append('超时时间必须在0-60秒之间')
        
        if 'cache_ttl' in config_data:
            ttl = config_data['cache_ttl']
            if ttl <= 0 or ttl > 86400:
                errors.append('缓存TTL必须在0-86400秒之间')
        
        # 验证枚举值
        if 'algorithm_type' in config_data:
            valid_algos = {'similarity', 'ml', 'hybrid'}
            if config_data['algorithm_type'] not in valid_algos:
                errors.append(f'算法类型必须是: {valid_algos}')
        
        if 'cache_strategy' in config_data:
            valid_strategies = {'lru', 'lfu', 'fifo'}
            if config_data['cache_strategy'] not in valid_strategies:
                errors.append(f'缓存策略必须是: {valid_strategies}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
