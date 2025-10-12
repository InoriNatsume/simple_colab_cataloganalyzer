# frida_asset_suite/backend/analysis.py
import logging
from pathlib import Path
from typing import Set, List, Optional, Dict
from collections import defaultdict
from .data_models import CharacterManager

logger = logging.getLogger('frida_asset_suite')

class AssetComparer:
    def __init__(self, char_manager: CharacterManager):
        self.char_manager = char_manager

    def read_path_file(self, file_path: Path) -> Set[str]:
        """경로가 저장된 텍스트 파일을 읽어 Set으로 반환합니다."""
        if not file_path.exists():
            logger.warning(f"분석 대상 파일을 찾을 수 없습니다: {file_path}")
            return set()
        with open(file_path, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip()}

    def compare_versions(self, new_path_file: Path, old_path_file: Path) -> Set[str]:
        """두 버전의 경로 파일을 비교하여 추가된 경로만 반환합니다."""
        logger.info(f"버전 비교 시작: '{new_path_file.name}' vs '{old_path_file.name}'")
        new_paths = self.read_path_file(new_path_file)
        old_paths = self.read_path_file(old_path_file)
        
        added_paths = new_paths - old_paths
        logger.info(f"비교 완료: {len(added_paths)}개의 신규 에셋 경로 발견.")
        return added_paths

    def _filter_and_structure_paths(self, paths: Set[str], squads: Optional[List[str]],
                                    characters: Optional[List[str]], keyword: Optional[str]) -> Dict:
        """주어진 경로 목록을 필터링하고 부대/캐릭터별로 구조화합니다."""
        
        # 1. 키워드 필터링
        filtered_paths = paths
        if keyword:
            keyword_lower = keyword.lower()
            filtered_paths = {p for p in paths if keyword_lower in p.lower()}
            logger.debug(f"키워드 '{keyword}' 필터링 후 {len(filtered_paths)}개 경로 남음.")

        # 2. 캐릭터/부대 필터링 및 데이터 구조화
        report_data: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        target_chars = set(characters) if characters else set()
        target_squads = set(squads) if squads else set()

        # 캐릭터 코드와 이름을 매핑하는 딕셔너리를 미리 생성하여 검색 효율 향상
        name_to_code_map = {info['name']: code for code, info in self.char_manager.char_data.items()}
        target_codes = {name_to_code_map.get(name) for name in target_chars}

        for path in sorted(list(filtered_paths)):
            found_char = False
            for code, info in self.char_manager.char_data.items():
                if f"_{code.lower()}_" in path.lower() or f"/{code.lower()}/" in path.lower():
                    squad, name = info['squad'], info['name']
                    
                    squad_match = not target_squads or squad in target_squads
                    char_match = not target_chars or name in target_chars
                    
                    if squad_match and char_match:
                        report_data[squad][name].append(path)
                        found_char = True
                        break

            if not found_char:
                # 필터가 없을 때만 '기타' 항목 추가
                if not target_squads and not target_chars:
                    report_data["기타"]["공용/미분류 에셋"].append(path)
        
        return report_data

    def format_report_to_markdown(self, report_data: Dict, title: str) -> str:
        """구조화된 데이터를 사람이 읽기 좋은 마크다운 텍스트로 변환합니다."""
        if not report_data:
            return "### 지정한 조건에 해당하는 에셋을 찾지 못했습니다."

        report_lines = [f"# 📝 {title}", "="*30]
        total_assets = 0
        
        for squad in sorted(report_data.keys()):
            report_lines.append(f"\n## 🏢 부대: {squad}")
            report_lines.append("-" * (len(squad) + 8))
            
            squad_chars = report_data[squad]
            for char_name in sorted(squad_chars.keys()):
                assets = squad_chars[char_name]
                asset_count = len(assets)
                total_assets += asset_count
                report_lines.append(f"\n### 👤 {char_name} ({asset_count}개)")
                for asset in assets:
                    report_lines.append(f"  - {asset}")
        
        # 보고서 맨 위에 총계 추가
        report_lines.insert(1, f"총 {total_assets}개의 에셋이 발견되었습니다.")
        return "\n".join(report_lines)

    def generate_single_report(self, path_file: Path, squads: List, chars: List, keyword: str):
        """단일 카탈로그 분석 보고서를 생성합니다."""
        all_paths = self.read_path_file(path_file)
        structured_data = self._filter_and_structure_paths(all_paths, squads, chars, keyword)
        return self.format_report_to_markdown(structured_data, f"'{path_file.name}' 분석 결과")

    def generate_comparison_report(self, new_file: Path, old_file: Path, squads: List, chars: List, keyword: str):
        """두 카탈로그 비교 분석 보고서를 생성합니다."""
        added_paths = self.compare_versions(new_file, old_file)
        structured_data = self._filter_and_structure_paths(added_paths, squads, chars, keyword)
        title = f"'{new_file.name}' vs '{old_file.name}' 비교 결과"
        return self.format_report_to_markdown(structured_data, title)