# frida_asset_suite/backend/extraction.py
import re
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger('frida_asset_suite')

class PathExtractor:
    # 정규표현식: 'Assets/'로 시작하며, 일반적인 경로에 사용되는 문자들(알파벳,숫자,_,/,.,-)로 구성.
    # NULL 문자(\x00)나 다른 제어 문자가 나오기 전까지의 경로를 탐색합니다.
    _ASSET_PATH_PATTERN = re.compile(rb'Assets/[-_a-zA-Z0-9./]+')

    def extract_from_binary(self, binary_path: str) -> Set[str]:
        """복호화된 바이너리 파일에서 'Assets/...' 형태의 논리 경로를 모두 추출합니다."""
        binary_p = Path(binary_path)
        logical_paths: Set[str] = set()
        
        if not binary_p.exists():
            logger.error(f"경로 추출 실패: 바이너리 파일을 찾을 수 없습니다: '{binary_path}'")
            return logical_paths
        
        logger.info(f"'{binary_p.name}' 파일에서 논리 경로 추출을 시작합니다.")
        try:
            with open(binary_p, 'rb') as f:
                content = f.read()

            matches = self._ASSET_PATH_PATTERN.findall(content)

            for match in matches:
                try:
                    # 바이너리 문자열을 UTF-8로 디코딩하여 Set에 추가
                    path_str = match.decode('utf-8')
                    logical_paths.add(path_str)
                except UnicodeDecodeError:
                    logger.warning(f"UTF-8 디코딩 실패. 바이너리 경로: {match}")
            
            if not logical_paths:
                logger.warning("논리 경로를 하나도 찾지 못했습니다. 파일 내용이나 정규표현식을 확인하세요.")
            else:
                logger.info(f"✅ 경로 추출 성공: {len(logical_paths):,}개의 고유 경로 발견.")
            
            return logical_paths
            
        except Exception as e:
            logger.error(f"바이너리 파일 처리 중 예외 발생: {e}", exc_info=True)
            return set()