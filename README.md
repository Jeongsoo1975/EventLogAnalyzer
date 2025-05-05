# Windows Event Log Analyzer using LLM

## 개요

이 프로젝트는 Windows 운영체제의 이벤트 로그를 분석하여 반복적으로 발생하는 심각/오류 이벤트를 식별하고, LLM(현재 Groq API 지원)을 활용하여 해당 오류에 대한 잠재적 원인 분석 및 해결 방안을 제시하는 도구입니다. 시스템 관리자나 사용자가 PC 문제를 진단하고 해결하는 데 도움을 주는 것을 목표로 합니다.

## 주요 기능

* **자동 분석:** 스크립트 실행 시 자동으로 이벤트 로그 읽기, 분석, LLM 요청 수행.
* **오류 필터링:** 지정된 이벤트 로그(예: 시스템, 응용 프로그램)에서 '오류(Error)' 수준 이벤트 추출.
* **반복 오류 식별:** 가장 자주 발생하는 오류(Source/EventID 기준) 상위 N개 식별 및 빈도수 계산.
* **LLM 기반 해결 제안:** 식별된 반복 오류 정보를 LLM에 전달하여 원인 및 해결 단계 요청 (현재 Groq 지원).
* **결과 저장:**
    * 추출된 모든 오류 로그는 `logs/critical_errors_{timestamp}.csv` 파일로 저장.
    * 분석된 반복 오류 상세 정보는 `logs/recurring_errors_{timestamp}.json` 파일로 저장.
* **개선된 콘솔 출력:** `rich` 라이브러리를 사용한 가독성 높은 진행 상황 및 결과 표시.
* **로깅:** 상세한 실행 과정을 `logs/analyzer.log` 파일에 기록 (로그 레벨, 파일 크기 등 설정 가능).

## 프로젝트 구조

EventLogAnalyzer/
├── src/                     # 소스 코드
│   ├── main.py              # 메인 실행 로직
│   ├── event_log_processor.py # 이벤트 로그 처리
│   ├── error_analyzer.py      # 오류 분석
│   ├── llm_interface.py       # LLM 연동
│   └── ui_display.py          # 콘솔 UI 및 로깅 설정
├── docs/                    # 문서
│   └── PRD.md
├── logs/                    # 실행 로그 및 결과 파일 저장
├── tests/                   # 단위 테스트 (향후)
├── .gitignore
├── requirements.txt         # 의존성 패키지
├── config.ini               # 설정 파일
├── setup.py                 # 패키징 설정
└── README.md                # 본 파일


## 요구 사항

* **운영체제:** Windows (이벤트 로그 접근 및 `pywin32` 사용)
* **Python:** 3.8 이상 권장

## 설치 방법

1.  **저장소 복제:**
    ```bash
    git clone [https://github.com/](https://github.com/)[Your GitHub Username]/EventLogAnalyzer.git
    cd EventLogAnalyzer
    ```

2.  **가상 환경 생성 및 활성화 (권장):**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **필수 패키지 설치:**
    ```bash
    pip install -r requirements.txt
    ```
    *참고: `pywin32`는 Windows 환경에서만 설치됩니다.*

4.  **(선택사항) 개발 모드로 설치:** 프로젝트를 수정하며 사용하려면 개발 모드로 설치할 수 있습니다.
    ```bash
    pip install -e .
    ```
    이렇게 하면 `analyze-logs` 명령어를 사용할 수 있습니다.

## 설정 (`config.ini`)

프로젝트 루트의 `config.ini` 파일을 열어 다음 설정을 환경에 맞게 수정합니다.

* **`[LLM]` 섹션:**
    * `provider`: 사용할 LLM 제공자 (현재 `groq` 지원).
    * `groq_api_key`: **(필수)** GroqCloud에서 발급받은 API 키를 입력합니다 (`YOUR_GROK_API_KEY_HERE` 부분을 수정).
    * `model`: 사용할 Groq 모델 이름 (예: `llama3-8b-8192`). Groq 문서를 참고하세요.
    * `request_timeout`: LLM API 요청 시 타임아웃 시간(초).
* **`[ANALYSIS]` 섹션:**
    * `log_names`: 분석할 Windows 이벤트 로그 이름 (쉼표로 구분).
    * `max_events_to_read`: 각 로그에서 읽어올 최대 이벤트 수.
    * `top_recurring_errors`: 분석할 반복 오류 상위 개수.
    * `log_output_dir`: 결과 파일(`*.csv`, `*.json`) 및 로그 파일(`analyzer.log`)이 저장될 디렉토리 이름.
* **`[DEFAULT]` 섹션:**
    * 애플리케이션 로그 파일(`analyzer.log`) 관련 설정 (레벨, 파일명, 크기, 백업 개수).

## 사용 방법

1.  **관리자 권한:** 모든 이벤트 로그에 접근하려면 관리자 권한으로 명령 프롬프트나 PowerShell을 실행해야 할 수 있습니다.
2.  **스크립트 직접 실행:**
    ```bash
    python src/main.py
    ```
3.  **개발 모드로 설치 후 명령어 사용:** (`pip install -e .` 실행 후)
    ```bash
    analyze-logs
    ```

스크립트가 실행되면 콘솔에 진행 상황이 표시되고, 분석이 완료되면 반복 오류 요약과 LLM의 해결 제안이 출력됩니다. 상세 로그와 결과 파일은 `config.ini`에 지정된 `log_output_dir` (기본값 `logs/`) 디렉토리에 저장됩니다.

## 출력 설명

* **콘솔:** `rich`를 사용하여 진행 상황, 경고, 오류, 최종 분석 결과(반복 오류 요약, LLM 제안)를 시각적으로 표시합니다.
* **`logs/analyzer.log`:** 스크립트 실행에 대한 상세 로그 (설정된 로그 레벨 기준).
* **`logs/critical_errors_{timestamp}.csv`:** 분석 과정에서 추출된 모든 'Error' 수준 이벤트 로그 목록.
* **`logs/recurring_errors_{timestamp}.json`:** 분석된 상위 반복 오류에 대한 상세 정보 (Source, EventID, Count, SampleMessage).

## 라이선스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다. (프로젝트 루트에 LICENSE 파일을 추가하세요)

## 향후 개선 사항

* 더 많은 LLM 제공자(OpenAI, Anthropic 등) 지원 추가.
* 이벤트 로그 분석 로직 심화 (메시지 내용 기반 분석, 상관관계 분석 등).
* GUI 인터페이스 개발.
* 테스트 커버리지 확보.
* 설치 및 실행 환경 검사 로직 추가.