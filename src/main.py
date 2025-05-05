import os
import sys
import datetime
import logging
from dotenv import load_dotenv # dotenv 임포트

# --- 경로 설정 및 sys.path 수정 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- .env 파일 로드 ---
# 스크립트 시작 시 .env 파일 로드 시도
# .env 파일이 없어도 오류 없이 진행됨 (환경 변수가 직접 설정되었을 수 있음)
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
loaded_dotenv = load_dotenv(dotenv_path=dotenv_path)
if loaded_dotenv:
    print(f"Loaded environment variables from: {dotenv_path}") # 로거 설정 전이므로 print 사용
else:
    print("No .env file found or failed to load. Relying on system environment variables.")

# --- 기본 설정값 (환경 변수에서 읽어오되, 실패 시 사용할 값) ---
DEFAULT_LOG_DIR_NAME = 'logs'

# --- 로그 디렉토리 경로 설정 ---
log_output_dir_env = os.getenv('ANALYSIS_LOG_OUTPUT_DIR', DEFAULT_LOG_DIR_NAME)
log_dir = os.path.join(PROJECT_ROOT, log_output_dir_env)

# --- 중요: 로그 디렉토리 생성 ---
try:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"Created log directory: {log_dir}")
    else:
        print(f"Log directory already exists: {log_dir}")
except OSError as e:
    print(f"Warning: Failed to create log directory '{log_dir}': {e}")
    # 심각한 오류지만 일단 진행, 디렉토리 생성 실패는 나중에 로깅에서 다시 시도됨

# --- 절대 경로 임포트 ---
from src.event_log_processor import get_critical_errors, save_critical_logs_to_file
from src.error_analyzer import find_recurring_errors, save_recurring_errors_to_json
from src.llm_interface import get_llm_suggestions_from_env # LLM 함수 이름 변경 반영
from src.ui_display import (
    setup_logging, display_start_message, display_progress, display_error_summary,
    display_llm_results, display_end_message, display_warning, display_error
)

# --- 로거 설정 ---
# 환경 변수 또는 기본값으로 로깅 설정
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
log_filename = os.getenv('LOG_FILENAME', 'analyzer.log')
log_file = os.path.join(log_dir, log_filename)

try:
    max_bytes = int(os.getenv('LOG_FILE_MAX_BYTES', '5242880'))
    backup_count = int(os.getenv('LOG_FILE_BACKUP_COUNT', '3'))
except ValueError:
    print("Warning: Invalid logging size/count settings in environment variables. Using defaults.")
    max_bytes = 5 * 1024 * 1024
    backup_count = 3

try:
    # 로깅 설정 (파일 및 콘솔)
    setup_logging(log_level=log_level, log_file=log_file, max_bytes=max_bytes, backup_count=backup_count)
    logger = logging.getLogger(__name__) # main 모듈 로거
    logger.info(f"Logging configured. Level: {log_level_str}, File: '{log_file}'")
except Exception as e:
    print(f"FATAL: Failed to setup logging: {e}")
    sys.exit(1)

def run_analyzer():
    """메인 분석 프로세스를 실행합니다."""
    start_time = datetime.datetime.now()
    display_start_message()

    # 분석 설정 읽기 (환경 변수 또는 기본값)
    log_names_str = os.getenv('ANALYSIS_LOG_NAMES', 'System,Application')
    log_names = [name.strip() for name in log_names_str.split(',')]
    try:
        max_events = int(os.getenv('ANALYSIS_MAX_EVENTS_TO_READ', '2000'))
        top_n = int(os.getenv('ANALYSIS_TOP_RECURRING_ERRORS', '5'))
    except ValueError:
        logger.warning("Invalid analysis settings (max_events, top_n) in environment variables. Using defaults.")
        max_events = 2000
        top_n = 5

    logger.info(f"Analysis Settings - Log Names: {log_names}, Max Events: {max_events}, Top N: {top_n}")

    # 1. 이벤트 로그 읽기
    critical_errors = []
    try:
        display_progress(f"Reading event logs ({', '.join(log_names)})...")
        critical_errors = get_critical_errors(log_types=log_names, max_records=max_events)
    except Exception as e:
        logger.error(f"An error occurred during event log processing: {e}", exc_info=True)
        display_error("Failed during event log processing.")

    if not critical_errors:
        display_warning("No critical/error events found or processing failed.")
        display_end_message(start_time)
        return

    # 2. 필터링된 로그 파일 저장 (CSV)
    timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
    # 로그 디렉토리는 로거 설정 시 결정된 log_dir 사용
    critical_log_filename = os.path.join(log_dir, f"critical_errors_{timestamp_str}.csv")
    display_progress(f"Saving {len(critical_errors)} critical logs...")
    save_critical_logs_to_file(critical_errors, critical_log_filename)

    # 3. 반복 오류 분석
    display_progress("Analyzing recurring errors...")
    summary_text, recurring_error_details = find_recurring_errors(critical_errors, top_n=top_n)

    if not recurring_error_details:
        display_warning(summary_text)
    else:
        display_error_summary(summary_text)
        # 3.1 반복 오류 상세 결과 저장 (JSON)
        recurring_errors_filename = os.path.join(log_dir, f"recurring_errors_{timestamp_str}.json")
        save_recurring_errors_to_json(recurring_error_details, recurring_errors_filename)

        # 4. LLM에게 해결 방안 요청
        display_progress("Requesting analysis from LLM...")
        # LLM 함수는 내부적으로 환경 변수 사용하므로 config 객체 전달 불필요
        llm_suggestions = get_llm_suggestions_from_env(recurring_error_details)

        # 5. LLM 결과 출력
        display_llm_results(llm_suggestions)

    display_end_message(start_time)

if __name__ == "__main__":
    # 관리자 권한 확인 (이전과 동일)
    is_admin = False
    if os.name == 'nt':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.warning(f"Could not check for administrator privileges: {e}")

        if not is_admin:
            logger.warning("This script might require administrator privileges to read all event logs.")

    run_analyzer()