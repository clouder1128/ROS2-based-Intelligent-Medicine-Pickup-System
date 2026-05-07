\"\"\"筛选系统API路由

定义所有智能筛选的REST API端点
\"\"\"

from flask import Blueprint, request, jsonify, make_response
import logging
from typing import Tuple
from datetime import datetime

from screening.services import (
    SymptomService,
    ScreeningService,
    ConfigService,
    HistoryService,
)

logger = logging.getLogger(__name__)


def create_screening_blueprint(db_session=None) -> Blueprint:
    \"\"\"创建筛选系统蓝图
    
    Args:
        db_session: 数据库会话
        
    Returns:
        Flask蓝图
    \"\"\"
    bp = Blueprint('screening', __name__, url_prefix='/api/screening')
    
    # 初始化服务
    symptom_service = SymptomService(db_session)
    screening_service = ScreeningService(symptom_service, db_session)
    config_service = ConfigService(db_session)
    history_service = HistoryService(db_session)
    
    # ==================== 症状处理接口 ====================
    
    @bp.route('/symptoms/standardize', methods=['POST'])
    def standardize_symptoms():
        \"\"\"POST /api/screening/symptoms/standardize
        
        症状文本标准化处理
        
        请求体:
        {
            \"symptoms\": [\"头疼\", \"发烧\"],  // 症状文本列表
            \"language\": \"zh\"  // 语言（可选）
        }
        
        响应:
        {
            \"success\": true,
            \"standardized_symptoms\": [\"头痛\", \"发热\"],
            \"unmatched\": [],
            \"confidence\": 1.0
        }
        \"\"\"
        try:
            data = request.get_json()
            symptoms = data.get('symptoms', [])
            
            if not symptoms:
                return jsonify({
                    'success': False,
                    'error': '症状列表不能为空'
                }), 400
            
            result = symptom_service.standardize_symptoms(symptoms)
            
            return jsonify({
                'success': True,
                'data': result
            }), 200
            
        except Exception as e:
            logger.error(f\"Error in standardize_symptoms: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/symptoms/synonyms', methods=['GET'])
    def get_symptom_synonyms():
        \"\"\"GET /api/screening/symptoms/synonyms
        
        获取症状同义词
        
        查询参数:
            symptom_name: 症状名称
            
        响应:
        {
            \"success\": true,
            \"symptom_name\": \"头痛\",
            \"synonyms\": [\"头疼\", \"头痛\"]
        }
        \"\"\"
        try:
            symptom_name = request.args.get('symptom_name')
            
            if not symptom_name:
                return jsonify({
                    'success': False,
                    'error': '症状名称不能为空'
                }), 400
            
            synonyms = symptom_service.get_synonyms(symptom_name)
            
            return jsonify({
                'success': True,
                'data': {
                    'symptom_name': symptom_name,
                    'synonyms': synonyms
                }
            }), 200
            
        except Exception as e:
            logger.error(f\"Error in get_symptom_synonyms: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ==================== 筛选查询接口 ====================
    
    @bp.route('/query', methods=['POST'])
    def screening_query():
        \"\"\"POST /api/screening/query
        
        根据症状筛选药品
        
        请求体:
        {
            \"symptoms\": [\"头痛\", \"发热\"],  // 标准化的症状列表
            \"patient_info\": {
                \"age\": 35,
                \"gender\": \"M\",
                \"allergies\": []
            },
            \"filters\": {
                \"max_results\": 20,
                \"price_range\": [0, 50]
            }
        }
        
        响应:
        {
            \"success\": true,
            \"results\": [...],
            \"confidence_scores\": {...},
            \"total_count\": 5,
            \"execution_time\": 0.123
        }
        \"\"\"
        try:
            data = request.get_json()
            
            symptoms = data.get('symptoms', [])
            patient_info = data.get('patient_info')
            filters = data.get('filters')
            user_id = data.get('user_id')
            request_id = data.get('request_id')
            
            # 执行筛选查询
            result = screening_service.screening_query(
                symptoms=symptoms,
                patient_info=patient_info,
                filters=filters,
                user_id=user_id,
                request_id=request_id
            )
            
            # 保存历史记录
            if result['success'] and user_id:
                history_service.save_history({
                    'user_id': user_id,
                    'input_symptoms': symptoms,
                    'patient_info': patient_info,
                    'filters': filters,
                    'result_drugs': result.get('results', []),
                    'result_count': result.get('total_count', 0),
                    'confidence_scores': result.get('confidence_scores', {}),
                    'execution_time': result.get('execution_time'),
                    'status': 'success' if result['success'] else 'error',
                    'error_message': result.get('error'),
                    'request_id': result.get('request_id')
                })
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f\"Error in screening_query: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/batch', methods=['POST'])
    def batch_screening():
        \"\"\"POST /api/screening/batch
        
        批量症状筛选
        
        请求体:
        {
            \"queries\": [
                {\"symptoms\": [...], \"patient_info\": {...}},
                ...
            ],
            \"batch_id\": \"batch123\"  // 可选
        }
        
        响应:
        {
            \"batch_id\": \"batch123\",
            \"total_queries\": 2,
            \"successful_queries\": 2,
            \"failed_queries\": 0,
            \"results\": [...]
        }
        \"\"\"
        try:
            data = request.get_json()
            queries = data.get('queries', [])
            batch_id = data.get('batch_id')
            
            if not queries:
                return jsonify({
                    'success': False,
                    'error': '查询列表不能为空'
                }), 400
            
            result = screening_service.batch_screening(queries, batch_id)
            
            return jsonify({
                'success': True,
                'data': result
            }), 200
            
        except Exception as e:
            logger.error(f\"Error in batch_screening: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ==================== 配置管理接口 ====================
    
    @bp.route('/config', methods=['GET'])
    def get_config():
        \"\"\"GET /api/screening/config
        
        获取筛选配置
        
        查询参数:
            config_name: 配置名称（可选，默认为'default'）
            
        响应:
        {
            \"success\": true,
            \"config\": {...}
        }
        \"\"\"
        try:
            config_name = request.args.get('config_name', 'default')
            config = config_service.get_config(config_name)
            
            if not config:
                return jsonify({
                    'success': False,
                    'error': f'配置 {config_name} 不存在'
                }), 404
            
            return jsonify({
                'success': True,
                'data': config
            }), 200
            
        except Exception as e:
            logger.error(f\"Error in get_config: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/config', methods=['PUT'])
    def update_config():
        \"\"\"PUT /api/screening/config
        
        更新筛选配置
        
        请求体:
        {
            \"config_name\": \"default\",
            \"confidence_threshold\": 0.6,
            \"max_results\": 25
        }
        
        响应:
        {
            \"success\": true,
            \"config\": {...},
            \"message\": \"配置更新成功\"
        }
        \"\"\"
        try:
            data = request.get_json()
            config_name = data.get('config_name', 'default')
            
            # 移除config_name，剩余的作为更新字段
            updates = {k: v for k, v in data.items() if k != 'config_name'}
            
            result = config_service.update_config(config_name, updates)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f\"Error in update_config: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ==================== 历史管理接口 ====================
    
    @bp.route('/history', methods=['GET'])
    def get_history():
        \"\"\"GET /api/screening/history
        
        获取筛选历史
        
        查询参数:
            user_id: 用户ID（必填）
            limit: 结果数量限制（默认20）
            offset: 分页偏移（默认0）
            start_date: 开始日期（ISO格式，可选）
            end_date: 结束日期（ISO格式，可选）
            
        响应:
        {
            \"success\": true,
            \"total\": 100,
            \"count\": 20,
            \"history\": [...]
        }
        \"\"\"
        try:
            user_id = request.args.get('user_id', type=int)
            
            if not user_id:
                return jsonify({
                    'success': False,
                    'error': '用户ID不能为空'
                }), 400
            
            limit = request.args.get('limit', default=20, type=int)
            offset = request.args.get('offset', default=0, type=int)
            
            # 处理日期范围
            date_range = None
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
            if start_date_str and end_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                    end_date = datetime.fromisoformat(end_date_str)
                    date_range = (start_date, end_date)
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '日期格式错误，请使用ISO格式'
                    }), 400
            
            result = history_service.get_history(
                user_id=user_id,
                limit=limit,
                offset=offset,
                date_range=date_range
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f\"Error in get_history: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/history/<int:history_id>', methods=['GET'])
    def get_history_detail(history_id: int):
        \"\"\"GET /api/screening/history/{id}
        
        获取历史详情
        
        路径参数:
            id: 历史记录ID
            
        响应:
        {
            \"success\": true,
            \"detail\": {...}
        }
        \"\"\"
        try:
            result = history_service.get_history_detail(history_id)
            status_code = 200 if result['success'] else 404
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f\"Error in get_history_detail: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ==================== 状态监控接口 ====================
    
    @bp.route('/status', methods=['GET'])
    def get_status():
        \"\"\"GET /api/screening/status
        
        获取筛选服务状态
        
        响应:
        {
            \"success\": true,
            \"status\": \"healthy\",
            \"service_name\": \"ScreeningService\",
            \"version\": \"1.0.0\",
            \"metrics\": {...}
        }
        \"\"\"
        try:
            status = screening_service.get_service_status()
            
            return jsonify({
                'success': True,
                'data': status
            }), 200
            
        except Exception as e:
            logger.error(f\"Error in get_status: {str(e)}\")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ==================== 错误处理 ====================
    
    @bp.errorhandler(400)
    def bad_request(e):
        return jsonify({
            'success': False,
            'error': '请求格式错误',
            'message': str(e)
        }), 400
    
    @bp.errorhandler(404)
    def not_found(e):
        return jsonify({
            'success': False,
            'error': '资源不存在',
            'message': str(e)
        }), 404
    
    @bp.errorhandler(500)
    def internal_error(e):
        logger.error(f\"Internal server error: {str(e)}\")
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'message': str(e)
        }), 500
    
    return bp
