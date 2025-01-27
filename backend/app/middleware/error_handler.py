from functools import wraps
from flask import jsonify
from app.utils.logger import get_logger

logger = get_logger()

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"请求处理错误: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return decorated_function 