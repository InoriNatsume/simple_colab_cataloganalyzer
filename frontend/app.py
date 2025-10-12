# frida_asset_suite/frontend/app.py (최종 수정: 라디오 버튼 UI 및 모든 오류 해결)
import gradio as gr
import os
import shutil
from pathlib import Path
import sys
from typing import Tuple
import uuid
import tempfile

# --- 프로젝트 경로 설정 및 모듈 임포트 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.logger import setup_logger
from backend.decryption import CatalogDecryptor
from backend.extraction import PathExtractor
from backend.data_models import CharacterManager
from backend.analysis import AssetComparer

# --- Google Drive 경로 설정 ---
DRIVE_CATALOG_DIR = Path("/content/drive/MyDrive/hbr_asset_catalogs")

# --- 전역 객체 초기화 ---
logger = setup_logger(debug=True)

try:
    AES_KEY_HEX = os.environ['AES_KEY_HEX']
    AES_IV_HEX = os.environ['AES_IV_HEX']
except KeyError:
    print("🔴 [치명적 오류] Colab 보안 노트(🔑)에서 AES_KEY_HEX와 AES_IV_HEX를 설정해야 합니다.")
    exit()

try:
    decryptor = CatalogDecryptor(AES_KEY_HEX, AES_IV_HEX)
    extractor = PathExtractor()
    char_manager = CharacterManager(str(PROJECT_ROOT / "data" / "character_info.csv"))
    comparer = AssetComparer(char_manager)
    logger.info("웹 애플리케이션 백엔드 모듈 초기화 완료.")
except Exception as e:
    logger.critical(f"백엔드 모듈 초기화 실패! 오류: {e}")
    exit()

# --- Gradio UI 로직 함수들 ---

def get_drive_catalogs():
    if not DRIVE_CATALOG_DIR.exists(): return []
    return sorted([f.name for f in DRIVE_CATALOG_DIR.glob("*.json")])

def _process_file_to_txt(input_path: str) -> Tuple[Path, str]:
    if not Path(input_path).exists():
        return None, f"입력 파일 '{input_path}'를 찾을 수 없습니다."
    unique_id = uuid.uuid4().hex
    temp_dir = Path(tempfile.gettempdir())
    decrypted_bin_path = temp_dir / f"{unique_id}_decrypted.bin"
    extracted_txt_path = temp_dir / f"{unique_id}_extracted.txt"
    if not decryptor.decrypt_file(input_path, str(decrypted_bin_path)):
        return None, f"'{Path(input_path).name}' 복호화 실패"
    logical_paths = extractor.extract_from_binary(str(decrypted_bin_path))
    decrypted_bin_path.unlink()
    if not logical_paths:
        return None, f"'{Path(input_path).name}' 경로 추출 실패"
    with open(extracted_txt_path, 'w', encoding='utf-8') as f:
        f.writelines(f"{path}\n" for path in sorted(list(logical_paths)))
    return extracted_txt_path, None

def run_analysis(source: str, local_file, drive_file: str, squads, chars, keyword, progress=gr.Progress(track_tqdm=True)):
    input_path = local_file.name if source == "로컬 업로드" and local_file else str(DRIVE_CATALOG_DIR / drive_file) if source == "Google Drive" and drive_file else None
    if not input_path: return "분석할 파일을 선택하거나 업로드해주세요."
    txt_path = None
    try:
        progress(0.2, desc="파일 처리 중...")
        txt_path, error = _process_file_to_txt(input_path)
        if error: return f"[오류] {error}"
        progress(0.7, desc="보고서 생성 중...")
        report = comparer.generate_single_report(txt_path, squads, chars, keyword)
        return report
    finally:
        if txt_path and txt_path.exists(): txt_path.unlink()

def run_comparison(source: str, local_new, local_old, drive_new: str, drive_old: str, squads, chars, keyword, progress=gr.Progress(track_tqdm=True)):
    new_path = local_new.name if source == "로컬 업로드" and local_new else str(DRIVE_CATALOG_DIR / drive_new) if source == "Google Drive" and drive_new else None
    old_path = local_old.name if source == "로컬 업로드" and local_old else str(DRIVE_CATALOG_DIR / drive_old) if source == "Google Drive" and drive_old else None
    if not new_path or not old_path: return "신규 버전과 과거 버전을 모두 선택하거나 업로드해주세요."
    if new_path == old_path: return "서로 다른 파일을 선택해야 합니다."
    new_txt_path, old_txt_path = None, None
    try:
        progress(0.1, desc="신규 버전 처리 중...")
        new_txt_path, error = _process_file_to_txt(new_path)
        if error: return f"[오류] {error}"
        progress(0.5, desc="과거 버전 처리 중...")
        old_txt_path, error = _process_file_to_txt(old_path)
        if error: return f"[오류] {error}"
        progress(0.9, desc="비교 및 보고서 생성 중...")
        report = comparer.generate_comparison_report(new_txt_path, old_txt_path, squads, chars, keyword)
        return report
    finally:
        if new_txt_path and new_txt_path.exists(): new_txt_path.unlink()
        if old_txt_path and old_txt_path.exists(): old_txt_path.unlink()

def update_character_dropdown(squads: list):
    return gr.Dropdown(choices=char_manager.get_characters_by_squad(squads), value=[])

def switch_source_ui(choice: str):
    """라디오 버튼 선택에 따라 UI의 가시성을 변경합니다."""
    if choice == "로컬 업로드":
        return gr.Group(visible=True), gr.Group(visible=False)
    else: # Google Drive
        return gr.Group(visible=False), gr.Group(visible=True)

# --- Gradio 웹 UI 구성 ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as demo:
    gr.Markdown("# 🎮 Unity Addressable 에셋 분석기")
    
    with gr.Tabs():
        with gr.TabItem("분석 (파일 1개)"):
            gr.Markdown("하나의 카탈로그 파일 내용을 필터링하며 봅니다.")
            source_radio_a = gr.Radio(["로컬 업로드", "Google Drive"], label="파일 소스 선택", value="로컬 업로드")
            
            with gr.Group(visible=True) as local_group_a:
                analyze_local_file = gr.File(label="분석할 catalog.json 파일", type="filepath")
            with gr.Group(visible=False) as drive_group_a:
                analyze_drive_dd = gr.Dropdown(label="Google Drive에서 파일 선택", choices=get_drive_catalogs())

            with gr.Row():
                squad_dd_a = gr.Dropdown(label="소속 부대", choices=char_manager.get_squad_list(), multiselect=True)
                char_dd_a = gr.Dropdown(label="캐릭터", multiselect=True, max_choices=5)
            keyword_a = gr.Textbox(label="키워드로 경로 필터링")
            analyze_btn = gr.Button("분석 실행", variant="primary")
            report_output_a = gr.Markdown()

        with gr.TabItem("비교 (파일 2개)"):
            gr.Markdown("두 개의 카탈로그 파일을 비교하여 추가된 에셋만 확인합니다.")
            source_radio_c = gr.Radio(["로컬 업로드", "Google Drive"], label="파일 소스 선택", value="로컬 업로드")

            with gr.Group(visible=True) as local_group_c:
                with gr.Row():
                    compare_local_new = gr.File(label="신규 버전 (기준)", type="filepath")
                    compare_local_old = gr.File(label="과거 버전 (비교 대상)", type="filepath")
            with gr.Group(visible=False) as drive_group_c:
                with gr.Row():
                    compare_drive_new = gr.Dropdown(label="신규 버전 (기준)", choices=get_drive_catalogs())
                    compare_drive_old = gr.Dropdown(label="과거 버전 (비교 대상)", choices=get_drive_catalogs())
            
            with gr.Row():
                squad_dd_c = gr.Dropdown(label="소속 부대", choices=char_manager.get_squad_list(), multiselect=True)
                char_dd_c = gr.Dropdown(label="캐릭터", multiselect=True, max_choices=5)
            keyword_c = gr.Textbox(label="키워드로 경로 필터링")
            compare_btn = gr.Button("비교 실행", variant="primary")
            report_output_c = gr.Markdown()

    # --- UI 이벤트 리스너 연결 ---
    source_radio_a.change(fn=switch_source_ui, inputs=source_radio_a, outputs=[local_group_a, drive_group_a])
    source_radio_c.change(fn=switch_source_ui, inputs=source_radio_c, outputs=[local_group_c, drive_group_c])
    
    squad_dd_a.change(fn=update_character_dropdown, inputs=[squad_dd_a], outputs=[char_dd_a])
    squad_dd_c.change(fn=update_character_dropdown, inputs=[squad_dd_c], outputs=[char_dd_c])
    
    analyze_btn.click(fn=run_analysis, inputs=[source_radio_a, analyze_local_file, analyze_drive_dd, squad_dd_a, char_dd_a, keyword_a], outputs=[report_output_a], show_progress="full")
    compare_btn.click(fn=run_comparison, inputs=[source_radio_c, compare_local_new, compare_local_old, compare_drive_new, compare_drive_old, squad_dd_c, char_dd_c, keyword_c], outputs=[report_output_c], show_progress="full")

if __name__ == "__main__":
    demo.launch()