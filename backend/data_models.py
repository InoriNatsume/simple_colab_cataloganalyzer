# frida_asset_suite/backend/data_models.py
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger('frida_asset_suite')

class CharacterManager:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.char_data: Dict[str, Dict] = {} # { "게임코드": {"name": "캐릭터명", "squad": "부대"} }
        self.squad_data: Dict[str, List[str]] = {} # { "부대": ["캐릭터명1", "캐릭터명2"] }
        self._load_data()

    def _load_data(self):
        if not self.csv_path.exists():
            logger.error(f"캐릭터 정보 파일을 찾을 수 없습니다: {self.csv_path}")
            return
        
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            # 필수 컬럼 확인
            required_cols = ['게임코드', '캐릭터명(K)', '소속 부대']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"CSV 파일에 필수 컬럼({required_cols})이 없습니다.")
                return

            for _, row in df.iterrows():
                code = row['게임코드']
                name = row['캐릭터명(K)']
                squad = row['소속 부대']
                
                self.char_data[code] = {'name': name, 'squad': squad}
                if squad not in self.squad_data:
                    self.squad_data[squad] = []
                self.squad_data[squad].append(name)
            
            logger.info(f"✅ 캐릭터 정보 로드 완료: {len(self.char_data)}명, {len(self.squad_data)}개 부대")
        except Exception as e:
            logger.error(f"캐릭터 CSV 파일 처리 중 오류 발생: {e}", exc_info=True)

    def get_squad_list(self) -> List[str]:
        return sorted(list(self.squad_data.keys()))

    def get_characters_by_squad(self, squads: Optional[List[str]] = None) -> List[str]:
        if not squads: # None 이거나 빈 리스트일 경우
            return sorted([info['name'] for info in self.char_data.values()])
        
        char_list = []
        for squad in squads:
            char_list.extend(self.squad_data.get(squad, []))
        return sorted(char_list)