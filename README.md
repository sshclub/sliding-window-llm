# Sliding Window LLM Log Analysis Pipeline

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/sshclub/sliding-window-llm)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://python.org)
[![vLLM](https://img.shields.io/badge/vLLM-Compatible-green)](https://github.com/vllm-project/vllm)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

이 프로젝트는 로그 파일을 슬라이딩 윈도우로 분할하여 vLLM을 통해 분석하는 파이프라인입니다. 실제 운영 환경의 다양한 로그 시나리오를 테스트할 수 있는 종합적인 테스트 도구를 포함하며, 모듈화된 구조로 확장성과 유지보수성을 제공합니다.

## 🚀 빠른 시작

```bash
# 저장소 클론
git clone https://github.com/sshclub/sliding-window-llm.git
cd sliding-window-llm

# 의존성 설치
pip install -r requirements.txt

# vLLM 서버 시작 (별도 터미널)
./start_qwen_server.sh

# 테스트 실행
python3 test_pipeline.py
```

## 주요 특징

- **모듈화된 구조**: 프롬프트 템플릿과 슬라이딩 윈도우를 별도 모듈로 분리
- **7가지 분석 타입**: 일반, 데이터베이스, 메모리, 네트워크, 보안, 성능, 크리티컬
- **자동 분석 타입 감지**: 로그 내용을 기반으로 적절한 분석 타입 자동 선택
- **실시간 로그 시스템**: 지속적인 로그 생성 및 자동 분석
- **종합 테스트 도구**: 다양한 시나리오 테스트 및 성능 측정

## 모델 설정

현재 **Qwen 7B** 모델을 사용하도록 설정되어 있습니다.

### 지원하는 모델들

1. **Qwen 7B (현재 설정)**
   - 모델명: `Qwen/Qwen2.5-7B-Instruct`
   - 추천: 한국어 지원이 우수하고 성능이 좋음

2. **다른 모델로 변경하려면**
   - `log_llm_pipeline.py`의 `MODEL` 변수 수정
   - `start_qwen_server.sh`의 `--model` 파라미터 수정

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/sshclub/sliding-window-llm.git
cd sliding-window-llm
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 설정 (선택사항)
```bash
# 환경변수 설정 파일 복사
cp env.example .env

# 필요에 따라 .env 파일 수정
nano .env
```

### 4. vLLM 서버 시작 (Qwen 7B)
```bash
# 방법 1: 스크립트 사용
./start_qwen_server.sh

# 방법 2: 직접 실행
python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --max-model-len 16384 \
  --tensor-parallel-size 1 \
  --host 0.0.0.0 --port 8000 \
  --trust-remote-code
```

### 5. 로그 분석 실행
```bash
python3 log_llm_pipeline.py
```

## 파일 구조

### 핵심 모듈
- `prompt_templates.py` - 프롬프트 템플릿 관리 모듈
- `sliding_window.py` - 슬라이딩 윈도우 처리 모듈

### 메인 파이프라인
- `log_llm_pipeline.py` - 메인 분석 스크립트 (vLLM 연동)
- `test_pipeline.py` - 테스트용 모의 버전 (vLLM 서버 없이 실행 가능)
- `start_qwen_server.sh` - Qwen 7B 서버 시작 스크립트

### 실시간 로그 시스템
- `realtime_logger.py` - 실시간 로그 생성기
- `log_monitor.py` - 로그 모니터링 시스템
- `auto_analysis.py` - 자동 분석 시스템
- `log_dashboard.py` - 실시간 대시보드

### 테스트 도구
- `log_generator.py` - 실제 시나리오 로그 생성기
- `interactive_test.py` - 대화형 테스트 스크립트
- `batch_test.py` - 배치 테스트 스크립트
- `performance_test.py` - 성능 테스트 스크립트
- `quick_test.py` - 빠른 테스트 스크립트
- `test_suite.py` - 종합 테스트 스위트

### 설정 및 데이터
- `requirements.txt` - Python 의존성
- `README.md` - 사용법 문서
- `test_log.txt` - 기본 테스트 로그 파일
- `scenario_*.log` - 생성된 시나리오 로그 파일들
- `realtime.log` - 실시간 생성되는 로그 파일

## 핵심 모듈 상세

### 프롬프트 템플릿 모듈 (`prompt_templates.py`)

**지원하는 분석 타입:**
- `GENERAL` - 일반적인 로그 분석
- `DATABASE` - 데이터베이스 관련 이슈 분석
- `MEMORY` - 메모리 누수 및 관리 이슈 분석
- `NETWORK` - 네트워크 연결 및 성능 이슈 분석
- `SECURITY` - 보안 위협 및 인시던트 분석
- `PERFORMANCE` - 시스템 성능 및 병목 분석
- `CRITICAL` - 크리티컬 상황 및 긴급 대응 분석

**주요 기능:**
- 자동 분석 타입 감지 (키워드 기반)
- 타입별 전용 시스템/사용자 프롬프트
- 분석 설정 관리 (temperature, max_tokens, timeout)

### 슬라이딩 윈도우 모듈 (`sliding_window.py`)

**주요 기능:**
- 토큰 기반 윈도우 분할 (tiktoken 또는 간단한 토크나이저)
- 오버랩 관리로 컨텍스트 유지
- 윈도우 통계 및 메타데이터 제공
- 윈도우 병합 및 전처리 기능

**설정 옵션:**
```python
WindowConfig(
    max_tokens=5000,      # 윈도우당 최대 토큰 수
    overlap_ratio=0.15,   # 윈도우 간 오버랩 비율 (15%)
    min_tokens=100,       # 최소 토큰 수
    tokenizer_type=TokenizerType.TIKTOKEN,  # 토크나이저 타입
    encoding_name="cl100k_base"  # 인코딩 이름
)
```

## 설정 옵션

### vLLM 서버 설정
- `VLLM_HOST` - vLLM 서버 호스트 (기본값: 127.0.0.1)
- `VLLM_PORT` - vLLM 서버 포트 (기본값: 8000)
- `MODEL_NAME` - 사용할 모델명 (기본값: Qwen/Qwen2.5-7B-Instruct)

### 환경변수 설정
```bash
# .env 파일에서 설정 가능
VLLM_HOST=your-server-ip
VLLM_PORT=8000
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
WINDOW_TOKENS=5000
OVERLAP_RATIO=0.15
ENVIRONMENT=production
```

## 출력

분석 결과는 JSON 형태로 저장됩니다:
- `analysis_results.json` - 실제 vLLM 분석 결과
- `test_analysis_results.json` - 모의 테스트 결과
- `interactive_analysis_*.json` - 대화형 테스트 결과
- `batch_test_report_*.json` - 배치 테스트 보고서
- `performance_report_*.json` - 성능 테스트 보고서

### 결과 파일 구조
```json
[
  {
    "meta": {
      "service": "ordersvc",
      "host": "node-01", 
      "severity": "error>warning>info",
      "time_range": "processed_at=2025-09-12T05:06:08.107811Z",
      "window_index": 0,
      "total_windows": 1,
      "window_tokens": 648,
      "window_lines": 29
    },
    "analysis": "### 1. 핵심 증상\n1. **Database Connection Timeout**...",
    "analysis_type": "database"
  }
]
```

**새로운 필드:**
- `window_tokens`: 윈도우의 토큰 수
- `window_lines`: 윈도우의 라인 수
- `analysis_type`: 사용된 분석 타입 (general, database, memory, network, security, performance, critical)

## 모델 변경 방법

다른 모델을 사용하려면:

1. `log_llm_pipeline.py`에서 `MODEL` 변수 수정
2. `start_qwen_server.sh`에서 `--model` 파라미터 수정
3. 필요시 `--trust-remote-code` 플래그 추가/제거

### 예시: Llama 모델로 변경
```python
MODEL = "meta-llama/Llama-2-7b-chat-hf"
```

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-chat-hf \
  --max-model-len 16384 \
  --tensor-parallel-size 1 \
  --host 0.0.0.0 --port 8000
```

## 실시간 로그 시스템

### 1. 실시간 로그 생성기
실제 운영 환경처럼 지속적으로 로그를 생성합니다:

```bash
python3 realtime_logger.py
```

**기능:**
- 다양한 시나리오 (정상, 성능 저하, 크리티컬)
- 로그 로테이션 지원
- 실시간 통계 출력
- 설정 가능한 생성 간격 및 최대 로그 수

### 2. 로그 모니터링 시스템
실시간으로 새 로그를 감지하고 분석합니다:

```bash
python3 log_monitor.py
```

**기능:**
- 새 로그 자동 감지
- 임계값 기반 분석 트리거
- 알림 시스템
- 분석 결과 자동 저장

### 3. 자동 분석 시스템
로그가 쌓이면 자동으로 분석을 실행합니다:

```bash
python3 auto_analysis.py
```

**기능:**
- vLLM 서버 상태에 따른 분석 방법 선택
- 분석 결과 자동 저장
- 통계 및 히스토리 관리
- 설정 가능한 분석 임계값

### 4. 실시간 대시보드
로그 생성과 분석 상태를 모니터링합니다:

```bash
python3 log_dashboard.py
```

**기능:**
- 로그 파일 상태 실시간 모니터링
- 분석 결과 파일 관리
- 시스템 상태 표시
- 최근 로그 실시간 표시

## 테스트 도구 사용법

### 1. 로그 생성기
다양한 시나리오의 실제 로그를 생성합니다:

```bash
python3 log_generator.py
```

**생성 가능한 시나리오:**
- 데이터베이스 오류 (29줄)
- 메모리 누수 (54줄) 
- 네트워크 이슈 (27줄)
- 보안 사고 (16줄)
- 복합 시나리오 (42줄)
- 대용량 로그 (500줄)

### 2. 대화형 테스트
직접 로그를 입력하거나 파일을 선택하여 테스트:

```bash
python3 interactive_test.py
```

**기능:**
- 기존 로그 파일로 테스트
- 직접 로그 입력하여 테스트
- 로그 파일 미리보기
- 분석 결과 보기

### 3. 배치 테스트
여러 로그 파일을 자동으로 테스트:

```bash
python3 batch_test.py
```

**옵션:**
- vLLM 테스트만
- 모의 테스트만
- 둘 다 테스트
- 자동 (vLLM 서버 상태에 따라)

### 4. 성능 테스트
대용량 로그와 동시 요청 처리 성능 측정:

```bash
python3 performance_test.py
```

**테스트 항목:**
- 대용량 로그 처리 성능
- 동시 요청 처리 (RPS 측정)
- 메모리 사용량 측정
- 토큰 처리 속도 측정

### 5. 빠른 테스트
기본 기능을 빠르게 확인:

```bash
python3 quick_test.py
```

### 6. 종합 테스트 스위트
모든 테스트를 한 번에 실행:

```bash
python3 test_suite.py
```

## 분석 타입 사용법

### 자동 감지 (기본값)
```python
# 분석 타입을 지정하지 않으면 로그 내용을 기반으로 자동 감지
from log_llm_pipeline import main
main(log_path, out_path, meta, analysis_type=None)
```

### 특정 분석 타입 지정
```python
from prompt_templates import AnalysisType
from log_llm_pipeline import main

# 데이터베이스 전용 분석
main(log_path, out_path, meta, AnalysisType.DATABASE)

# 메모리 전용 분석
main(log_path, out_path, meta, AnalysisType.MEMORY)

# 보안 전용 분석
main(log_path, out_path, meta, AnalysisType.SECURITY)
```

### 분석 타입별 특징

| 분석 타입 | 키워드 | 전용 프롬프트 | 최적화 설정 |
|-----------|--------|---------------|-------------|
| DATABASE | database, db, mysql, connection, query | 데이터베이스 전문가 역할 | temperature: 0.1, max_tokens: 1500 |
| MEMORY | memory, oom, outofmemory, gc, heap | 메모리 관리 전문가 역할 | temperature: 0.1, max_tokens: 1400 |
| NETWORK | network, timeout, connection refused | 네트워크 전문가 역할 | temperature: 0.2, max_tokens: 1300 |
| SECURITY | security, attack, breach, unauthorized | 보안 전문가 역할 | temperature: 0.1, max_tokens: 1600 |
| PERFORMANCE | performance, slow, bottleneck, cpu | 성능 전문가 역할 | temperature: 0.2, max_tokens: 1400 |
| CRITICAL | critical, fatal, emergency, down | 긴급 대응 전문가 역할 | temperature: 0.1, max_tokens: 1800 |

## 실제 사용 예시

### 시나리오 1: 데이터베이스 오류 분석
```bash
# 1. 로그 생성
python3 log_generator.py  # 선택: 1 (데이터베이스 오류)

# 2. 분석 실행 (자동 감지)
python3 log_llm_pipeline.py

# 3. 결과 확인
cat analysis_results.json
```

### 시나리오 2: 특정 분석 타입으로 분석
```python
# Python 스크립트에서 직접 호출
from prompt_templates import AnalysisType
from log_llm_pipeline import main

meta = {"service": "ordersvc", "host": "node-01", "severity": "error>warning>info"}
main("./scenario_2_메모리_누수.log", "./memory_analysis.json", meta, AnalysisType.MEMORY)
```

### 시나리오 3: 실시간 로그 시스템 실행
```bash
# 터미널 1: 실시간 로그 생성
python3 realtime_logger.py

# 터미널 2: 로그 모니터링
python3 log_monitor.py

# 터미널 3: 자동 분석
python3 auto_analysis.py

# 터미널 4: 대시보드
python3 log_dashboard.py
```

### 시나리오 4: 대화형 테스트
```bash
# 대화형 테스트 시작
python3 interactive_test.py

# 메뉴에서 선택:
# 1. 기존 로그 파일로 테스트
# 2. 직접 로그 입력하여 테스트
```

### 시나리오 5: 성능 벤치마크
```bash
# 성능 테스트 실행
python3 performance_test.py

# 결과 확인
ls -la performance_report_*.json
```

## 분석 결과 예시

실제 데이터베이스 오류 시나리오 분석 결과:

```json
{
  "analysis": "### 1. 핵심 증상\n1. **Database Connection Timeout**: ordersvc, paymentsvc에서 발생\n2. **Database Recovery Failures**: analyticsvc, usersvc에서 실패\n3. **Service Degradation**: usersvc가 읽기 모드로 전환\n\n### 2. 원인 가설(우선순위)\n1. **Database Server Overload**: 데이터베이스 서버의 부하가 너무 높음\n2. **Network Issues**: 네트워크 문제로 인한 통신 지연\n3. **Database Configuration Issues**: 데이터베이스 설정 문제\n\n### 3. 즉시 점검 명령(쉘)\n```sh\n# 1. Check database server load\nssh node-01 \"top -b -n 1 | grep mysql\"\n\n# 2. Check network latency\nssh node-01 \"ping -c 10 <database_server_ip>\"\n```\n\n### 4. 재발방지 액션\n1. **Increase Database Connection Pool Size**\n2. **Optimize Queries**\n3. **Improve Network Infrastructure**\n\n### 5. 확신도\n**중간**: 증상은 명확하지만 추가 조사 필요"
}
```

## 고급 사용법

### 커스텀 프롬프트 템플릿 추가
```python
from prompt_templates import PromptTemplates, AnalysisType

# 새로운 분석 타입 추가
class CustomAnalysisType(Enum):
    CUSTOM = "custom"

# 커스텀 프롬프트 템플릿 생성
templates = PromptTemplates()
templates.system_prompts[CustomAnalysisType.CUSTOM] = "You are a custom log analyst..."
templates.user_prompt_templates[CustomAnalysisType.CUSTOM] = "Custom analysis template..."
```

### 슬라이딩 윈도우 커스터마이징
```python
from sliding_window import WindowConfig, create_sliding_window

# 커스텀 윈도우 설정
custom_config = WindowConfig(
    max_tokens=3000,      # 더 작은 윈도우
    overlap_ratio=0.3,    # 더 큰 오버랩
    min_tokens=50,        # 더 작은 최소 토큰
    tokenizer_type=TokenizerType.SIMPLE  # 간단한 토크나이저 사용
)

sliding_window = create_sliding_window(custom_config)
windows = sliding_window.create_windows_from_file("log.txt")
```

### 배치 처리 및 병렬 분석
```python
import concurrent.futures
from log_llm_pipeline import call_llm

def analyze_window_parallel(window, meta, analysis_type):
    return call_llm(window.content, meta, analysis_type)

# 병렬 분석 실행
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(analyze_window_parallel, window, meta, analysis_type) 
               for window in windows]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]
```

### 실시간 모니터링 설정
```python
# 자동 분석 임계값 조정
from auto_analysis import AutoAnalyzer

analyzer = AutoAnalyzer("realtime.log")
analyzer.thresholds = {
    "error_rate": 0.05,      # 5% 이상 에러
    "critical_count": 2,     # 2개 이상 크리티컬
    "warning_count": 5,      # 5개 이상 경고
    "service_errors": 3      # 서비스당 3개 이상 에러
}
```

## 문제 해결

### vLLM 서버 연결 실패
```bash
# 서버 상태 확인
curl http://127.0.0.1:8000/v1/models

# 서버 재시작
./start_qwen_server.sh

# 포트 충돌 확인
netstat -tlnp | grep 8000
```

### 메모리 부족 오류
```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head -10

# vLLM 서버 설정 조정
python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --max-model-len 8192 \  # 토큰 수 줄이기
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.8  # GPU 메모리 사용률 제한
```

### 토큰 카운팅 오류
```bash
# tiktoken 재설치
pip uninstall tiktoken
pip install tiktoken

# 간단한 토크나이저로 대체
# sliding_window.py에서 TokenizerType.SIMPLE 사용
```

### 권한 오류
```bash
# 실행 권한 부여
chmod +x *.py *.sh

# 파일 소유권 확인
ls -la *.py
```

### 분석 타입 감지 오류
```python
# 수동으로 분석 타입 지정
from prompt_templates import AnalysisType
main(log_path, out_path, meta, AnalysisType.GENERAL)  # 강제로 일반 분석 사용
```

### 실시간 로그 시스템 문제
```bash
# 로그 파일 권한 확인
ls -la realtime.log

# 디스크 공간 확인
df -h

# 로그 로테이션 설정 확인
# realtime_logger.py에서 로테이션 비활성화
```

## 🔒 보안 고려사항

### 환경변수 사용
- **민감한 정보**: IP 주소, 포트, API 키 등은 환경변수로 관리
- **설정 파일**: `.env` 파일을 사용하여 로컬 설정 관리
- **Git 제외**: `.env` 파일은 `.gitignore`에 포함되어 버전 관리에서 제외

### 네트워크 보안
```bash
# 프로덕션 환경에서 권장 설정
VLLM_HOST=your-secure-server-ip
VLLM_PORT=8000
ENVIRONMENT=production
ALLOWED_HOSTS=your-domain.com,your-ip
```

### API 보안
- **인증**: API_KEY 환경변수로 인증 설정 가능
- **방화벽**: vLLM 서버 포트에 대한 접근 제한
- **HTTPS**: 프로덕션에서는 HTTPS 사용 권장

### 로그 보안
- **민감한 데이터**: 로그에서 개인정보, 패스워드 등 제거
- **접근 권한**: 로그 파일에 대한 적절한 파일 권한 설정
- **암호화**: 필요시 로그 파일 암호화

## 성능 최적화

### 윈도우 크기 최적화
- **작은 윈도우 (1000-3000 토큰)**: 빠른 분석, 컨텍스트 손실 가능
- **중간 윈도우 (3000-5000 토큰)**: 균형잡힌 성능과 정확도
- **큰 윈도우 (5000+ 토큰)**: 높은 정확도, 느린 분석

### 오버랩 비율 조정
- **낮은 오버랩 (0.1-0.15)**: 빠른 처리, 컨텍스트 손실 가능
- **중간 오버랩 (0.15-0.25)**: 균형잡힌 성능
- **높은 오버랩 (0.25+)**: 높은 정확도, 중복 처리

### 분석 타입별 최적화
- **DATABASE/SECURITY**: 낮은 temperature (0.1)로 일관성 확보
- **PERFORMANCE/NETWORK**: 중간 temperature (0.2)로 창의적 해결책
- **CRITICAL**: 높은 max_tokens (1800)로 상세한 분석

## 시스템 요구사항

### 최소 요구사항
- **Python**: 3.8 이상
- **메모리**: 8GB RAM (vLLM 서버용)
- **GPU**: NVIDIA GPU (권장, vLLM 가속용)
- **디스크**: 10GB 여유 공간

### 권장 요구사항
- **Python**: 3.10 이상
- **메모리**: 16GB RAM 이상
- **GPU**: NVIDIA RTX 3080 이상 (8GB VRAM)
- **디스크**: 50GB 여유 공간 (모델 및 로그 저장용)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 🤝 기여하기

이 프로젝트에 기여해주셔서 감사합니다! 기여 방법은 다음과 같습니다:

1. **Fork the Project** - 저장소를 포크하세요
2. **Create your Feature Branch** - `git checkout -b feature/AmazingFeature`
3. **Commit your Changes** - `git commit -m 'Add some AmazingFeature'`
4. **Push to the Branch** - `git push origin feature/AmazingFeature`
5. **Open a Pull Request** - Pull Request를 생성하세요

### 기여 가이드라인
- **새로운 분석 타입**: `prompt_templates.py`에 템플릿 추가
- **새로운 테스트 시나리오**: `log_generator.py`에 추가
- **성능 개선**: `sliding_window.py`에서 진행
- **문서화**: README.md와 코드 주석에 반영
- **버그 리포트**: [Issues](https://github.com/sshclub/sliding-window-llm/issues)에 등록

### 개발 환경 설정
```bash
# 개발용 의존성 설치
pip install -r requirements.txt

# 테스트 실행
python3 test_suite.py

# 코드 스타일 확인
python3 -m flake8 *.py
```

## 변경 로그

### v2.0.0 (2025-09-12)
- **모듈화**: 프롬프트 템플릿과 슬라이딩 윈도우를 별도 모듈로 분리
- **7가지 분석 타입**: 일반, 데이터베이스, 메모리, 네트워크, 보안, 성능, 크리티컬
- **자동 분석 타입 감지**: 로그 내용 기반 자동 감지
- **실시간 로그 시스템**: 지속적인 로그 생성 및 자동 분석
- **향상된 윈도우 관리**: 토큰 기반 정확한 윈도우 분할
- **종합 테스트 도구**: 다양한 시나리오 테스트 및 성능 측정

### v1.0.0 (2025-09-12)
- **기본 파이프라인**: 슬라이딩 윈도우 기반 로그 분석
- **vLLM 연동**: Qwen 7B 모델 지원
- **테스트 도구**: 기본적인 테스트 스크립트

## 🆘 지원

문제가 발생하거나 질문이 있으시면:

- **🐛 버그 리포트**: [GitHub Issues](https://github.com/sshclub/sliding-window-llm/issues)에 문제를 보고해주세요
- **💬 질문 및 토론**: [GitHub Discussions](https://github.com/sshclub/sliding-window-llm/discussions)에서 질문을 남겨주세요
- **📧 직접 연락**: 프로젝트 메인테이너에게 직접 연락

### 자주 묻는 질문 (FAQ)

**Q: vLLM 서버가 시작되지 않아요**
A: GPU 메모리와 모델 경로를 확인해주세요. `start_qwen_server.sh` 스크립트를 사용하거나 직접 실행해보세요.

**Q: 분석 결과가 부정확해요**
A: 분석 타입을 수동으로 지정하거나 프롬프트 템플릿을 커스터마이징해보세요.

**Q: 메모리 부족 오류가 발생해요**
A: 윈도우 크기를 줄이거나 vLLM 서버의 `--max-model-len` 파라미터를 조정해보세요.

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 도움을 받아 만들어졌습니다:

- **[vLLM](https://github.com/vllm-project/vllm)** - 고성능 LLM 서빙 프레임워크
- **[Qwen](https://github.com/QwenLM/Qwen)** - 우수한 한국어 지원 LLM
- **[tiktoken](https://github.com/openai/tiktoken)** - 정확한 토큰 카운팅
- **[OpenAI](https://openai.com)** - API 호환성 표준

### 스타를 눌러주세요! ⭐

이 프로젝트가 도움이 되었다면 GitHub에서 스타를 눌러주세요. 더 많은 사람들이 이 프로젝트를 발견할 수 있도록 도와주세요!

---

**Made with ❤️ by [sshclub](https://github.com/sshclub)**
