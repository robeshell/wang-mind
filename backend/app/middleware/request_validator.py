from functools import wraps
from flask import request, jsonify
from app.utils.logger import get_logger

logger = get_logger()

def validate_json_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': '请求必须是JSON格式'
            }), 400
            
        return f(*args, **kwargs)
    return decorated_function 