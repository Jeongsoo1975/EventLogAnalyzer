import os
import logging
import requests # requests 라이브러리 사용
import json

logger = logging.getLogger(__name__)

# X.AI Grok API 엔드포인트
XAI_API_ENDPOINT = "https://api.x.ai/v1/chat/completions"

def get_llm_suggestions_from_env(error_details):
    """환경 변수에서 설정을 읽어 LLM(X.AI Grok)에게 해결 방안을 요청합니다."""

    # 환경 변수에서 설정 읽기
    provider = os.getenv('LLM_PROVIDER', 'grok').lower()
    api_key = os.getenv('GROK_API_KEY') # X.AI Grok API 키
    model = os.getenv('GROK_MODEL', 'grok-3-mini-beta')
    try:
        timeout = int(os.getenv('LLM_REQUEST_TIMEOUT', '60'))
    except ValueError:
        logger.warning("Invalid LLM_REQUEST_TIMEOUT value, using default 60 seconds.")
        timeout = 60

    # 설정 유효성 검사
    if provider not in ['grok', 'xai', 'x.ai']:
        # 현재는 grok/xai (X.AI) 만 지원
        error_msg = f"지원되지 않는 LLM 제공자 '{provider}'가 환경 변수에 설정되었습니다. 현재는 'grok', 'xai', 'x.ai'만 지원됩니다."
        logger.error(error_msg)
        return f"오류: {error_msg}"

    if not api_key or api_key.startswith('YOUR_') or api_key == 'YOUR_GROK_API_KEY_HERE':
        error_msg = "GROK_API_KEY 환경 변수가 설정되지 않았거나 기본값 그대로입니다."
        logger.error(error_msg)
        return f"오류: Grok API 키가 환경 변수에 설정되지 않았습니다. (.env 파일을 확인하세요)"

    # 오류 요약 텍스트 생성 (이전과 동일, 한국어 환경 고려)
    error_summary_text = ""
    for i, error in enumerate(error_details, 1):
        source = error.get('Source', '알 수 없음')
        event_id = error.get('EventID', '알 수 없음')
        count = error.get('Count', '알 수 없음')
        sample_message = error.get('SampleMessage', '메시지 없음')
        error_summary_text += (
            f"\n--- 오류 #{i} ---\n"
            f"소스: {source}\n"
            f"이벤트 ID: {event_id}\n"
            f"발생 횟수: {count}\n"
            f"샘플 메시지 일부: {sample_message}\n"
        )

    # 프롬프트 생성 (한국어 버전 유지)
    prompt = f"""
당신은 숙련된 Windows 시스템 관리자이자 문제 해결 전문가입니다.
Windows PC의 이벤트 로그를 분석하여 반복적으로 발생하는 주요 심각/오류 이벤트를 확인했습니다.

다음은 가장 빈번하게 발생한 오류들의 요약 정보입니다:
{error_summary_text}

위에 제공된 정보(소스, 이벤트 ID, 발생 횟수, 샘플 메시지 일부)만을 바탕으로, 각 오류에 대해 다음을 **한국어**로 수행해 주십시오:

1.  **잠재적 원인 식별:** 이 오류가 발생할 수 있는 가장 가능성 높은 이유를 간략하게 설명합니다.
2.  **구체적인 문제 해결 단계 제공:** 사용자가 문제를 진단하고 잠재적으로 해결하기 위해 취할 수 있는 구체적이고 단계적인 조치를 제안합니다. 실용적이고 실행 가능한 조언에 초점을 맞추고, 가장 일반적이거나 효과적인 해결책을 우선적으로 제시합니다.
3.  **구조:** 위에서 식별된 각 오류에 대한 분석(원인 및 단계)을 명확하게 구분합니다 (예: "오류 #1 분석", "오류 #2 분석" 과 같은 제목 사용).

**중요:**
* 추가 정보를 요청하지 마십시오. 입력된 요약 정보만을 바탕으로 최선의 지침을 제공하십시오.
* 당신의 목표는 이 로그를 바탕으로 사용자가 PC 문제를 해결하도록 돕는 것입니다.
* **반드시 한국어로 답변해야 합니다.** 명확하고 이해하기 쉬운 한국어를 사용해 주십시오.
"""

    # API 요청 헤더 및 페이로드 구성 (curl 예시 참조)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            # 시스템 메시지로 한국어 응답 요청 추가
            {"role": "system", "content": "You are a helpful Windows troubleshooting assistant. Always respond in Korean language."},
            {"role": "user", "content": prompt}
        ],
        "model": model,
        "stream": False, # 스트리밍 응답 사용 안 함
        "temperature": 0.7 # 약간의 창의성 허용 (필요에 따라 0으로 설정)
    }

    logger.info(f"X.AI Grok API ({XAI_API_ENDPOINT}) 요청 시작 (모델: {model}, 타임아웃: {timeout}s)")

    try:
        response = requests.post(
            XAI_API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생 (4xx, 5xx)

        # 응답 처리
        response_data = response.json()
        # 응답 구조가 OpenAI 호환이므로 동일하게 처리 시도
        if 'choices' in response_data and len(response_data['choices']) > 0:
            message_content = response_data['choices'][0].get('message', {}).get('content')
            if message_content:
                logger.info("X.AI Grok API로부터 성공적으로 응답 수신.")
                return message_content.strip()
            else:
                logger.error("API 응답 구조에서 메시지 내용을 찾을 수 없습니다.", extra={"response": response_data})
                return "오류: LLM 응답에서 내용을 추출하지 못했습니다."
        else:
            logger.error("API 응답이 예상한 'choices' 구조를 포함하지 않습니다.", extra={"response": response_data})
            return "오류: LLM으로부터 유효하지 않은 응답 형식을 받았습니다."

    except requests.exceptions.Timeout:
        logger.error(f"LLM API 요청 시간 초과 ({timeout}초)")
        return f"오류: LLM API 요청 시간이 초과되었습니다 ({timeout}초)."
    except requests.exceptions.HTTPError as e:
        # HTTP 오류 상태 코드와 응답 내용을 로깅
        error_details = f"HTTP 오류 코드: {e.response.status_code}"
        try:
            error_content = e.response.json()
            error_details += f", 응답: {error_content}"
        except json.JSONDecodeError:
            error_details += f", 응답 내용(텍스트): {e.response.text}"
        logger.error(f"LLM API HTTP 오류 발생: {error_details}", exc_info=False) 
        return f"오류: LLM API 요청 실패 ({error_details})"
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API 요청 중 네트워크 오류 발생: {e}", exc_info=True)
        return f"오류: LLM API 요청 중 네트워크 오류 발생: {e}"
    except json.JSONDecodeError as e:
         logger.error(f"LLM API 응답 JSON 디코딩 실패: {e}", extra={"response_text": response.text if 'response' in locals() else 'N/A'})
         return f"오류: LLM API 응답 처리 중 오류 발생 (JSON 형식 오류)"
    except Exception as e:
        logger.error(f"LLM 상호작용 중 예기치 않은 오류 발생: {e}", exc_info=True)
        return f"오류: LLM 요청 중 예기치 않은 오류 발생: {e}"