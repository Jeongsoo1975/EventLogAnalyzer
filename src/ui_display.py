# src/ui_display.py

import datetime
import logging
import os # os 모듈 임포트
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.logging import RichHandler

console = Console()
logger = logging.getLogger(__name__) # 로거 사용 확인

def setup_logging(log_level=logging.INFO, log_file=None, max_bytes=5*1024*1024, backup_count=3):
    """rich와 파일 로깅을 함께 사용하도록 로깅 설정"""
    # 기본 로거 설정 (RichHandler 사용)
    # basicConfig는 루트 로거를 설정하므로, 핸들러를 직접 추가/제거하는 것이 더 유연할 수 있음
    # 기존 핸들러 제거 후 재설정 (중복 방지)
    root_logger = logging.getLogger()
    # 기존 핸들러 모두 제거 (특히 파일 핸들러 중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close() # 핸들러 닫기

    # 루트 로거 레벨 설정
    root_logger.setLevel(log_level)

    # 콘솔 핸들러 추가
    console_handler = RichHandler(console=console, rich_tracebacks=True, show_path=False, markup=True)
    console_handler.setLevel(log_level) # 콘솔 핸들러 레벨 설정
    root_logger.addHandler(console_handler)

    # 파일 핸들러 추가 (옵션)
    if log_file:
        from logging.handlers import RotatingFileHandler
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                print(f"Log directory created: '{log_dir}'") # 로거 사용 전
            except OSError as e:
                print(f"Warning: Could not create log directory '{log_dir}': {e}")
                log_file = None # 생성 실패 시 파일 로깅 비활성화

        if log_file:
            try:
                file_handler = RotatingFileHandler(
                    log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
                )
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                file_handler.setLevel(log_level) # 파일 핸들러 레벨 설정
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Failed to setup file logging handler for '{log_file}': {e}")

# --- 나머지 display 함수들은 이전과 동일 ---
def display_start_message():
    """프로그램 시작 메시지를 패널로 출력"""
    console.print(Panel("[bold cyan]Starting Windows Event Log Analyzer[/]", title="Status", border_style="cyan"))

# ... (display_progress, display_error_summary 등 나머지 함수 동일) ...
def display_progress(message):
    logger.info(message)

def display_error_summary(summary_text):
    console.print(Panel(summary_text, title="[bold yellow]Recurring Error Summary[/]", border_style="yellow", expand=False))

def display_llm_results(suggestions):
    title = "[bold green]LLM Troubleshooting Suggestions[/]"
    border_style = "green"
    # suggestions 문자열에 마크업이 포함될 수 있으므로 Text 객체 사용 시 주의
    # Text(suggestions) 대신 그냥 suggestions 문자열 사용 시도
    content = suggestions

    if suggestions.strip().startswith("오류:"): # 한국어 오류 메시지 확인
        title = "[bold red]LLM Request Error[/]"
        border_style = "red"
        content = f"[red]{suggestions}[/red]" # 오류 스타일 직접 적용

    console.print(Panel(content, title=title, border_style=border_style, expand=True)) # expand=True 추가

def display_end_message(start_time):
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    console.print(Panel(f"Analysis complete in [bold blue]{duration:.2f}[/] seconds", title="Status", border_style="blue"))

def display_warning(message):
     logger.warning(message)

def display_error(message):
     logger.error(message)