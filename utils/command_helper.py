"""
Helper utilities for command naming based on environment stage
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_stage():
    """Lấy stage hiện tại từ environment variables"""
    return (os.environ.get('STAGE') or os.getenv('STAGE', 'production')).lower()

def is_dev():
    """Kiểm tra xem có đang ở môi trường dev không"""
    return get_stage() == 'dev'

def get_command_name(base_name: str) -> str:
    """
    Trả về tên command với prefix 'dev' nếu đang ở môi trường dev
    
    Args:
        base_name: Tên command gốc (vd: 'ping', 'addrepo')
    
    Returns:
        Tên command đầy đủ (vd: 'devping' nếu dev, 'ping' nếu production)
    
    Examples:
        >>> get_command_name('ping')  # Trong dev
        'devping'
        >>> get_command_name('addrepo')  # Trong production
        'addrepo'
    """
    return f"dev_{base_name}" if is_dev() else base_name
