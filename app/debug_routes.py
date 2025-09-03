# app/debug_routes.py
"""
Debug routes for troubleshooting payment system issues
"""

from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
import os
import logging

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/payment-config')
@login_required
def debug_payment_config():
    """
    Debug endpoint to show payment service configuration and selection
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    logger = logging.getLogger(__name__)
    
    # Collect environment variables
    env_vars = {
        'MOCK_PAYMENTS_ENABLED': os.environ.get('MOCK_PAYMENTS_ENABLED', 'NOT_SET'),
        'POSTFINANCE_SPACE_ID': 'SET' if os.environ.get('POSTFINANCE_SPACE_ID') else 'NOT_SET',
        'POSTFINANCE_USER_ID': 'SET' if os.environ.get('POSTFINANCE_USER_ID') else 'NOT_SET',
        'POSTFINANCE_API_SECRET': 'SET' if os.environ.get('POSTFINANCE_API_SECRET') else 'NOT_SET',
        'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT_SET',
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'NOT_SET')
    }
    
    # Collect Flask config
    flask_config = {}
    try:
        flask_config = {
            'MOCK_PAYMENTS_ENABLED': current_app.config.get('MOCK_PAYMENTS_ENABLED', 'NOT_IN_CONFIG'),
            'POSTFINANCE_SPACE_ID': 'SET' if current_app.config.get('POSTFINANCE_SPACE_ID') else 'NOT_SET',
            'POSTFINANCE_USER_ID': 'SET' if current_app.config.get('POSTFINANCE_USER_ID') else 'NOT_SET', 
            'POSTFINANCE_API_SECRET': 'SET' if current_app.config.get('POSTFINANCE_API_SECRET') else 'NOT_SET',
            'DATABASE_URI': 'SET' if current_app.config.get('SQLALCHEMY_DATABASE_URI') else 'NOT_SET'
        }
    except Exception as e:
        flask_config = {'error': str(e)}
    
    # Test payment service selection
    payment_service_info = {}
    try:
        from app.services.payment_factory import get_payment_service
        service = get_payment_service()
        payment_service_info = {
            'service_type': service.__class__.__name__,
            'service_module': service.__class__.__module__,
            'initialization_success': True
        }
    except Exception as e:
        payment_service_info = {
            'error': str(e),
            'initialization_success': False
        }
    
    # Test database connectivity
    db_info = {}
    try:
        from app import db
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1 as test'))
        db_info = {
            'connection_success': True,
            'test_query_result': 'OK'
        }
    except Exception as e:
        db_info = {
            'connection_success': False,
            'error': str(e)
        }
    
    return jsonify({
        'timestamp': current_app.config.get('TIMESTAMP', 'unknown'),
        'environment_variables': env_vars,
        'flask_config': flask_config,
        'payment_service': payment_service_info,
        'database': db_info,
        'user_id': current_user.id,
        'user_is_admin': current_user.is_admin
    })

@debug_bp.route('/test-mock-purchase/<int:lesson_id>')
@login_required  
def test_mock_purchase(lesson_id):
    """
    Test mock payment service directly
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from app.models import Lesson
        from app.services.mock_payment_service import MockPaymentService
        
        lesson = Lesson.query.get_or_404(lesson_id)
        mock_service = MockPaymentService()
        
        # Type cast to ensure proper User type
        from app.models import User
        user = current_user._get_current_object()
        if not isinstance(user, User):
            return jsonify({'error': 'Invalid user object', 'success': False})
        result = mock_service.create_lesson_transaction(user, lesson)
        
        return jsonify({
            'test_type': 'direct_mock_service',
            'lesson_id': lesson_id,
            'lesson_title': lesson.title,
            'user_id': current_user.id,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'test_type': 'direct_mock_service',
            'error': str(e),
            'success': False
        })

@debug_bp.route('/test-factory-purchase/<int:lesson_id>')
@login_required
def test_factory_purchase(lesson_id):
    """
    Test payment service via factory
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
        
    try:
        from app.models import Lesson
        from app.services.payment_factory import get_payment_service
        
        lesson = Lesson.query.get_or_404(lesson_id)
        payment_service = get_payment_service()
        
        # Type cast to ensure proper User type  
        from app.models import User
        user = current_user._get_current_object()
        if not isinstance(user, User):
            return jsonify({'error': 'Invalid user object', 'success': False})
        result = payment_service.create_lesson_transaction(user, lesson)
        
        return jsonify({
            'test_type': 'factory_service',
            'service_type': payment_service.__class__.__name__,
            'lesson_id': lesson_id,
            'lesson_title': lesson.title,
            'user_id': current_user.id,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'test_type': 'factory_service', 
            'error': str(e),
            'success': False
        })

@debug_bp.route('/environment-info')
@login_required
def environment_info():
    """
    Show comprehensive environment information
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    import sys
    import platform
    
    return jsonify({
        'python_version': sys.version,
        'platform': platform.platform(),
        'working_directory': os.getcwd(),
        'environment_variables_count': len(os.environ),
        'flask_app_name': current_app.name,
        'flask_config_keys': list(current_app.config.keys()),
        'instance_path': current_app.instance_path,
        'root_path': current_app.root_path
    })
