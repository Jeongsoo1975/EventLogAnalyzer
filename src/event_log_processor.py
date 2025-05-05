import win32evtlog
import win32evtlogutil
import win32api
import winerror
import datetime
import os
import csv
import logging # logging 모듈 임포트

logger = logging.getLogger(__name__) # 모듈 레벨 로거 생성

def get_critical_errors(log_types=['System'], max_records=1000):
    """지정된 Windows 이벤트 로그에서 심각/오류 이벤트를 읽어옵니다."""
    all_errors = []
    logger.info(f"Attempting to read logs from: {', '.join(log_types)}")

    for log_type in log_types:
        handle = None # 핸들 초기화
        try:
            handle = win32evtlog.OpenEventLog(None, log_type)
            logger.debug(f"Successfully opened '{log_type}' event log.")
        except win32api.error as e:
            if e.winerror == winerror.ERROR_ACCESS_DENIED:
                logger.error(f"Access denied when opening '{log_type}' log. Ensure script is run as Administrator.")
            else:
                logger.error(f"Failed to open '{log_type}' log: {e}")
            continue # 다음 로그 타입으로 진행

        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        try:
            total_records = win32evtlog.GetNumberOfEventLogRecords(handle)
            logger.info(f"Found {total_records} records in '{log_type}'. Reading up to {max_records} recent error events.")
        except Exception as e:
             logger.error(f"Could not get number of records for '{log_type}': {e}")
             win32evtlog.CloseEventLog(handle)
             continue

        events_read_count = 0
        processed_count = 0

        try:
            while True:
                try:
                    events = win32evtlog.ReadEventLog(handle, flags, 0, 8192)
                except Exception as read_err:
                    logger.error(f"Error reading chunk from '{log_type}': {read_err}")
                    break # 읽기 오류 시 해당 로그 중단

                if not events:
                    break

                for event in events:
                    processed_count += 1
                    if event.EventType == win32evtlog.EVENTLOG_ERROR_TYPE:
                        try:
                            message = win32evtlogutil.SafeFormatMessage(event, log_type)
                        except Exception as format_err:
                            # 메시지 포맷 실패 시 경고 로깅 후 계속 진행
                            logger.warning(f"Could not format message for Event ID {event.EventID} in '{log_type}': {format_err}")
                            message = f"Raw Data: {event.Data}" if event.Data else "[Message Formatting Failed]"

                        record = {
                            'Timestamp': event.TimeGenerated.strftime('%Y-%m-%d %H:%M:%S'),
                            'Source': event.SourceName,
                            'EventID': event.EventID,
                            'LevelType': event.EventType,
                            'Message': message.strip() if message else "N/A"
                        }
                        all_errors.append(record)
                        events_read_count += 1
                        # 디버그 레벨에서 개별 오류 로그 기록 (너무 많을 수 있으므로 주의)
                        # logger.debug(f"Found error event: {record['Source']} / {record['EventID']}")

                    if events_read_count >= max_records:
                        break
                if events_read_count >= max_records:
                    logger.info(f"Reached max_records limit ({max_records}) for '{log_type}'.")
                    break
        except Exception as loop_err:
             logger.error(f"An unexpected error occurred while processing events in '{log_type}': {loop_err}")
        finally:
            if handle:
                win32evtlog.CloseEventLog(handle)
                logger.debug(f"Closed '{log_type}' event log handle.")

        logger.info(f"Finished reading '{log_type}'. Found {events_read_count} error events out of {processed_count} processed.")

    logger.info(f"Total critical/error events collected: {len(all_errors)}")
    return all_errors

def save_critical_logs_to_file(logs, filename):
    """추출된 심각/오류 로그 목록을 CSV 파일에 저장합니다."""
    if not logs:
        logger.warning("No critical logs found to save.")
        return

    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logger.info(f"Saving {len(logs)} critical logs to '{filename}'...")
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Timestamp', 'Source', 'EventID', 'LevelType', 'Message']
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(logs)
        logger.info(f"Successfully saved critical logs to '{filename}'.")
    except IOError as e:
        logger.error(f"Failed to save critical logs to file '{filename}': {e}", exc_info=True) # 에러 상세 정보 포함
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving critical logs: {e}", exc_info=True)