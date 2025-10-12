# frida_asset_suite/backend/logger.py
import logging
import sys

def setup_logger(debug=False):
    """프로젝트 전역에서 사용할 로거를 설정하고 반환합니다."""
    # 로거 이름으로 'frida_asset_suite'를 사용
    logger = logging.getLogger('frida_asset_suite')
    
    # 핸들러가 이미 설정되어 있다면 중복 추가 방지
    if logger.hasHandlers():
        logger.handlers.clear()
        
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    logger.setLevel(level)
    logger.addHandler(handler)
    
    # 다른 라이브러리의 로그가 최상위 레벨에 영향을 주지 않도록 전파(propagate) 방지
    logger.propagate = False 
    
    return logger