from collections import Counter
import json
import os
import logging

logger = logging.getLogger(__name__)

def find_recurring_errors(logs, top_n=5):
    """
    로그 목록에서 가장 빈번하게 발생하는 오류를 찾아 요약 텍스트와 상세 데이터를 반환합니다.
    향후 개선: 단순 Source/EventID 외에 메시지 패턴 분석, 시간대별 군집화 등 심화 분석 가능.
    """
    if not logs:
        logger.warning("No error logs provided for analysis.")
        return "No errors found to analyze.", []

    logger.info(f"Analyzing {len(logs)} error logs to find top {top_n} recurring errors...")
    # 오류 식별자: (Source, EventID) 사용
    error_identifiers = [(log.get('Source', 'Unknown'), log.get('EventID', 0)) for log in logs]

    if not error_identifiers:
         logger.warning("Could not extract error identifiers from logs.")
         return "Could not identify errors.", []

    try:
        error_counts = Counter(error_identifiers)
        most_common_errors = error_counts.most_common(top_n)
    except Exception as e:
        logger.error(f"Failed to count recurring errors: {e}", exc_info=True)
        return "Error during error counting.", []

    if not most_common_errors:
        logger.info("No recurring errors found matching the criteria.")
        return "No recurring errors found.", []

    logger.info(f"Found {len(most_common_errors)} distinct recurring errors.")
    summary_lines = [f"--- Top {len(most_common_errors)} Recurring Errors ---"]
    detailed_errors = []

    for (source, event_id), count in most_common_errors:
        # 샘플 메시지 찾기 (가장 최근)
        sample_message = "N/A"
        for log in reversed(logs):
            if log.get('Source') == source and log.get('EventID') == event_id:
                msg = log.get('Message', '')
                sample_message = msg[:200] + ('...' if len(msg) > 200 else '')
                break

        summary_line = f"Source: {source}, Event ID: {event_id}, Count: {count}"
        summary_lines.append(summary_line)
        detailed_errors.append({
            'Source': source,
            'EventID': event_id,
            'Count': count,
            'SampleMessage': sample_message
        })
        logger.debug(f"Recurring Error: {summary_line} | Sample: {sample_message}")

    summary_text = "\n".join(summary_lines)
    return summary_text, detailed_errors

def save_recurring_errors_to_json(error_details, filename):
    """분석된 반복 오류 상세 데이터를 JSON 파일에 저장합니다."""
    if not error_details:
        logger.warning("No recurring error details provided to save.")
        return

    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logger.info(f"Saving recurring error details to '{filename}'...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(error_details, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved recurring errors to '{filename}'.")
    except IOError as e:
        logger.error(f"Failed to save recurring errors to JSON file '{filename}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving recurring errors: {e}", exc_info=True)