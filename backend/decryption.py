# frida_asset_suite/backend/decryption.py
import gzip
import logging
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# 전역 로거 대신, 이 모듈의 이름을 사용하는 로거를 가져옵니다.
logger = logging.getLogger('frida_asset_suite')

class CatalogDecryptor:
    def __init__(self, key_hex: str, iv_hex: str):
        try:
            self.key = bytes.fromhex(key_hex)
            self.iv = bytes.fromhex(iv_hex)
            logger.debug(f"복호화기 초기화 완료")
        except ValueError as e:
            logger.critical(f"AES Key/IV 초기화 실패! 16진수 문자열이 올바른지 확인하세요: {e}")
            raise

    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """암호화된 카탈로그 파일을 복호화하여 GZip 압축 해제된 바이너리 파일로 저장합니다."""
        input_p = Path(input_path)
        output_p = Path(output_path)
        
        try:
            logger.info(f"'{input_p.name}' 파일 복호화를 시작합니다 -> '{output_p.name}'")
            
            logger.debug("1/4: 암호화된 파일 읽기...")
            with open(input_p, 'rb') as f:
                encrypted_data = f.read()

            logger.debug("2/4: AES 복호화 수행...")
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            decrypted_padded_data = cipher.decrypt(encrypted_data)
            gzipped_data = unpad(decrypted_padded_data, AES.block_size)

            logger.debug("3/4: GZip 압축 해제 수행...")
            final_data_bytes = gzip.decompress(gzipped_data)

            logger.debug("4/4: 복호화된 바이너리 파일 저장...")
            with open(output_p, 'wb') as f:
                f.write(final_data_bytes)
                
            logger.info(f"✅ 복호화 성공: '{output_p.name}'")
            return True

        except FileNotFoundError:
            logger.error(f"[복호화 실패] 입력 파일을 찾을 수 없습니다: '{input_path}'")
        except (ValueError, KeyError) as e:
            logger.error(f"[복호화 실패] 패딩 또는 키 오류. Key/IV 또는 파일이 올바른지 확인하세요. 오류: {e}")
        except gzip.BadGzipFile:
            logger.error("[복호화 실패] GZip 압축 해제 실패. 데이터가 손상되었거나 형식이 다를 수 있습니다.")
        except Exception as e:
            logger.error(f"[복호화 실패] 알 수 없는 오류가 발생했습니다: {e}", exc_info=True)
            
        return False