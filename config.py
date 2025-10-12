# frida_asset_suite/config.py (Google Drive 연동 버전)
from pathlib import Path
import os

# --- Google Drive 연동 설정 ---
# Colab 환경에서 '/content/drive'가 마운트되었는지 확인합니다.
DRIVE_MOUNT_PATH = Path("/content/drive")
BASE_DATA_DIR_NAME = "hbr_asset_analyzer_data" # Drive에 생성할 폴더 이름
PROJECT_ROOT = Path(__file__).parent.resolve()

# Google Drive가 연결되어 있고, 데이터 폴더가 존재하면 Drive 경로를 사용합니다.
if (DRIVE_MOUNT_PATH / "MyDrive").exists():
    DRIVE_DATA_DIR = DRIVE_MOUNT_PATH / "MyDrive" / BASE_DATA_DIR_NAME
    DATA_DIR = DRIVE_DATA_DIR
    print(f"✅ Google Drive가 연결되었습니다. 데이터 경로: '{DATA_DIR}'")
else:
    # 그렇지 않으면, Colab의 임시 로컬 저장소를 사용합니다.
    DATA_DIR = PROJECT_ROOT / "data"
    print("ℹ️ Google Drive가 연결되지 않았습니다. 임시 로컬 저장소를 사용합니다.")

# --- 데이터 폴더 경로 ---
UPLOADED_CATALOGS_DIR = DATA_DIR / "uploaded_catalogs"
PROCESSED_CATALOGS_DIR = DATA_DIR / "processed_catalogs"
CHARACTER_INFO_CSV = PROJECT_ROOT / "data" / "character_info.csv" # 캐릭터 정보는 프로젝트 내부에 유지

# --- 폴더 생성 ---
# 프로젝트 실행 시 필요한 폴더들이 없다면 자동으로 생성합니다.
DATA_DIR.mkdir(exist_ok=True)
UPLOADED_CATALOGS_DIR.mkdir(exist_ok=True)
PROCESSED_CATALOGS_DIR.mkdir(exist_ok=True)