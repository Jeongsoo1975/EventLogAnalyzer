# PRD: Windows 이벤트 로그 분석 및 자동 해결 제안 시스템

## 1. 개요

본 프로젝트는 Windows 운영체제의 이벤트 로그를 주기적으로 감시하여 심각(Critical) 및 오류(Error) 수준의 로그를 식별하고, 특히 반복적으로 발생하는 오류 패턴을 분석합니다. 분석된 결과는 LLM(Grok-3-Mini-Beta 모델 활용)에 전달되어 해당 오류의 원인 분석 및 해결을 위한 구체적인 제안을 받습니다. 최종적으로 LLM의 답변을 사용자 인터페이스(초기 버전은 콘솔 출력)에 표시하여 사용자가 시스템 문제를 신속하게 진단하고 조치할 수 있도록 지원하는 것을 목표로 합니다.

## 2. 목표

* Windows 이벤트 로그에서 발생하는 심각/오류 로그 자동 감지
* 반복 발생하는 주요 오류 식별 및 요약
* LLM을 활용한 자동 문제 원인 분석 및 해결 방안 제시
* 사용자 친화적인 결과 표시 (초기: 콘솔, 향후: GUI 확장 가능)
* 스크립트 실행 시 모든 프로세스 자동 수행

## 3. 기능 요구사항

| 기능 ID | 기능 설명                                                                 | 세부 내용                                                                                                                               | 우선순위 |
| :------ | :------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------- | :------- |
| FEAT-01 | **자동 실행** | 스크립트가 시작되면 별도 사용자 입력 없이 정의된 모든 분석 및 보고 프로세스가 자동으로 진행되어야 한다.                                          | 필수     |
| FEAT-02 | **심각/오류 로그 필터링 및 저장** | 지정된 Windows 이벤트 로그(예: 시스템, 응용 프로그램)에서 '심각(Critical, Level 1)' 및 '오류(Error, Level 2)' 수준의 이벤트만 추출한다. | 필수     |
| FEAT-03 | **필터링된 로그 파일 저장** | FEAT-02에서 추출된 로그의 주요 정보(시간, 소스, 이벤트 ID, 메시지 등)를 지정된 `output/` 폴더 내 파일로 저장한다. 파일명은 실행 시각 포함 권장.     | 필수     |
| FEAT-04 | **반복 오류 분석** | 저장된 오류 로그 내에서 동일한 '소스(Source)'와 '이벤트 ID(Event ID)' 조합으로 가장 빈번하게 발생한 오류들을 식별하고 빈도수를 계산한다.           | 필수     |
| FEAT-05 | **오류 요약 생성** | FEAT-04에서 식별된 상위 N개(예: 5개) 반복 오류에 대한 요약 정보를 생성한다 (오류 소스, 이벤트 ID, 발생 횟수, 대표 메시지 포함).                    | 필수     |
| FEAT-06 | **LLM 기반 해결 방안 요청** | 생성된 오류 요약 정보를 Grok-3-Mini-Beta API에 전달하여 각 오류에 대한 **구체적인 문제 해결 단계 또는 원인 분석**을 요청하는 프롬프트를 구성한다. | 필수     |
| FEAT-07 | **LLM 프롬프트 최적화** | LLM이 PC 오류 해결이라는 명확한 목적을 이해하고, 제시된 정보(오류 요약)만을 바탕으로 실행 가능한 해결책을 제안하도록 프롬프트를 정교하게 작성한다. | 필수     |
| FEAT-08 | **결과 표시** | LLM으로부터 받은 응답(해결 제안)을 사용자가 쉽게 인지할 수 있도록 콘솔(CLI)에 명확하게 출력한다.                                            | 필수     |

## 4. 비기능 요구사항

* **플랫폼:** Windows 운영체제
* **개발 언어:** Python 3.x
* **주요 라이브러리:** `pywin32` (이벤트 로그 접근), `requests` 또는 `groq` (LLM API 통신), `configparser` (설정 관리)
* **성능:** 대량의 이벤트 로그 처리 시에도 합리적인 시간 내에 분석 완료
* **사용성:** 초기 설정(API 키 등) 외에는 별도 조작 없이 실행 가능
* **보안:** LLM API 키는 소스 코드에 직접 노출되지 않고 `config.ini` 파일을 통해 관리
* **오류 처리:** 이벤트 로그 접근 권한 부재, LLM API 통신 실패 등 예외 상황 처리

## 5. UI/UX (초기 버전: CLI)

* 스크립트 실행 시 진행 상황(로그 읽기, 분석 중, LLM 요청 중 등)을 콘솔에 표시한다.
* 최종 분석 결과(반복 오류 요약) 및 LLM의 해결 제안을 명확히 구분하여 콘솔에 출력한다.

## 6. LLM 상호작용 (Grok-3-Mini-Beta)

* **입력:** 반복 오류 요약 정보 (소스, 이벤트 ID, 빈도, 샘플 메시지)
* **프롬프트 핵심:**
    * 역할 부여: "당신은 숙련된 Windows 시스템 관리자이자 문제 해결 전문가입니다."
    * 상황 설명: "Windows PC의 이벤트 로그에서 반복적으로 발생하는 주요 오류들을 분석했습니다."
    * 데이터 제공: "다음은 분석된 오류 요약 정보입니다: [요약 정보 삽입]"
    * 명확한 요청: "이 정보를 바탕으로, 각 오류의 **가능한 원인**과 사용자가 시도해볼 수 있는 **구체적이고 단계적인 해결 방법**을 제시해 주십시오. 특히, **실행 가능한 조치**에 초점을 맞춰 설명해 주십시오. 추가 정보 요청 없이 주어진 내용만으로 최선의 답변을 부탁드립니다."
    * 출력 형식 제안: "각 오류(소스/이벤트 ID 기준)별로 원인과 해결책을 명확히 구분하여 제시해 주십시오."
* **출력:** LLM이 생성한 텍스트 형식의 문제 해결 제안

## 7. 향후 개선 사항

* GUI(Graphical User Interface) 개발 (Tkinter, PyQt 등)
* 분석할 이벤트 로그 종류(시스템, 응용 프로그램 등) 사용자 선택 기능 추가
* 오류 심각도 레벨(경고 포함 등) 설정 기능 추가
* 지원 LLM 모델 확장
* 분석 결과 리포트 자동 생성 (HTML, PDF 등)