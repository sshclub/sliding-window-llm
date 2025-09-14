# Sliding Window LLM Log Analysis Pipeline - Architecture

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SLIDING WINDOW LLM PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LOG SOURCES   │    │  LOG GENERATOR  │    │ REALTIME LOGGER │    │  LOG MONITOR    │
│                 │    │                 │    │                 │    │                 │
│ • System Logs   │    │ • Scenario 1-6  │    │ • Continuous    │    │ • File Watcher  │
│ • App Logs      │    │ • Realistic     │    │ • Multi-scenario│    │ • Threshold     │
│ • Error Logs    │    │ • Test Data     │    │ • Auto Rotation │    │ • Auto Trigger  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 │                       │
                                 ▼                       ▼
                    ┌─────────────────────────────────────────┐
                    │            LOG FILES                    │
                    │                                         │
                    │ • test_log.txt                         │
                    │ • scenario_*.log                       │
                    │ • realtime.log                         │
                    │ • custom logs                          │
                    └─────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │        SLIDING WINDOW MODULE            │
                    │                                         │
                    │ • Token-based segmentation             │
                    │ • Overlap management                    │
                    │ • Window statistics                     │
                    │ • Preprocessing                         │
                    └─────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │      PROMPT TEMPLATES MODULE            │
                    │                                         │
                    │ • 7 Analysis Types                      │
                    │ • Auto-detection                        │
                    │ • Type-specific prompts                 │
                    │ • LLM configuration                     │
                    └─────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │           vLLM SERVER                   │
                    │                                         │
                    │ • Qwen 7B Model                         │
                    │ • OpenAI Compatible API                 │
                    │ • High Performance                      │
                    │ • GPU Acceleration                      │
                    └─────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │         ANALYSIS RESULTS                │
                    │                                         │
                    │ • JSON format                           │
                    │ • Structured output                     │
                    │ • Metadata included                     │
                    │ • Confidence levels                     │
                    └─────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │         AUTO ANALYSIS                   │
                    │                                         │
                    │ • Continuous monitoring                 │
                    │ • Automatic processing                  │
                    │ • Result aggregation                    │
                    │ • Statistics tracking                   │
                    └─────────────────────────────────────────┘
```

## 🔄 데이터 플로우

```
LOG INPUT → PREPROCESSING → WINDOW SEGMENTATION → ANALYSIS TYPE DETECTION
    ↓              ↓                ↓                      ↓
RAW LOGS → CLEANED LOGS → WINDOWS → PROMPT SELECTION → LLM ANALYSIS
    ↓              ↓                ↓                      ↓
STORAGE ← JSON RESULTS ← STRUCTURED OUTPUT ← AI RESPONSE ← vLLM SERVER
```

## 🧩 모듈 구조

### Core Modules
```
sliding-window-llm/
├── 📁 Core Modules
│   ├── prompt_templates.py     # 프롬프트 템플릿 관리
│   └── sliding_window.py       # 슬라이딩 윈도우 처리
│
├── 📁 Main Pipeline
│   ├── log_llm_pipeline.py     # 메인 분석 파이프라인
│   └── test_pipeline.py        # 테스트용 모의 버전
│
├── 📁 Real-time System
│   ├── realtime_logger.py      # 실시간 로그 생성
│   ├── log_monitor.py          # 로그 모니터링
│   ├── auto_analysis.py        # 자동 분석
│   └── log_dashboard.py        # 실시간 대시보드
│
├── 📁 Test Tools
│   ├── log_generator.py        # 로그 생성기
│   ├── interactive_test.py     # 대화형 테스트
│   ├── batch_test.py           # 배치 테스트
│   ├── performance_test.py     # 성능 테스트
│   ├── quick_test.py           # 빠른 테스트
│   └── test_suite.py           # 종합 테스트
│
└── 📁 Configuration
    ├── requirements.txt        # 의존성
    ├── start_qwen_server.sh    # 서버 시작 스크립트
    └── README.md               # 문서
```

## 🎯 분석 타입별 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANALYSIS TYPES                           │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│    GENERAL      │   DATABASE      │    MEMORY       │  NETWORK    │
│                 │                 │                 │             │
│ • Generic logs  │ • DB errors     │ • Memory leaks  │ • Timeouts  │
│ • Mixed issues  │ • Connections   │ • OOM errors    │ • Latency   │
│ • Unknown type  │ • Queries       │ • GC issues     │ • Failures  │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│   SECURITY      │  PERFORMANCE    │   CRITICAL      │             │
│                 │                 │                 │             │
│ • Attacks       │ • Bottlenecks   │ • System down   │             │
│ • Breaches      │ • Slow queries  │ • Fatal errors  │             │
│ • Unauthorized  │ • Resource use  │ • Emergency     │             │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
```

## 🔧 기술 스택

```
┌─────────────────────────────────────────────────────────────────┐
│                          TECH STACK                             │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│   Language      │   Framework     │   AI/ML         │  Tools      │
│                 │                 │                 │             │
│ • Python 3.8+   │ • vLLM          │ • Qwen 7B       │ • Git       │
│ • Bash          │ • OpenAI API    │ • tiktoken      │ • GitHub    │
│ • JSON          │ • Requests      │ • Tokenization  │ • Shell     │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
```

## 📊 성능 특성

```
┌─────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE                              │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│   Throughput    │   Latency       │   Memory        │  Accuracy   │
│                 │                 │                 │             │
│ • 1000+ logs/min│ • <2s per window│ • 8GB+ RAM      │ • 85%+      │
│ • Parallel proc │ • Real-time     │ • GPU optional  │ • Context   │
│ • Batch support │ • Streaming     │ • Efficient     │ • Aware     │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
```

## 🚀 배포 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT                               │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│   Development   │   Testing       │   Production    │  Monitoring │
│                 │                 │                 │             │
│ • Local dev     │ • Test suite    │ • vLLM server   │ • Dashboard │
│ • Mock pipeline │ • Batch tests   │ • Auto scaling  │ • Alerts    │
│ • Debug mode    │ • Performance   │ • Load balancer │ • Metrics   │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
```

## 🔄 실시간 처리 플로우

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LOG GENERATION │───▶│   MONITORING    │───▶│   ANALYSIS      │
│                 │    │                 │    │                 │
│ • Continuous    │    │ • File watching │    │ • Auto trigger  │
│ • Multi-source  │    │ • Threshold     │    │ • Type detection│
│ • Realistic     │    │ • Event driven  │    │ • LLM processing│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   STORAGE       │    │   DASHBOARD     │    │   RESULTS       │
│                 │    │                 │    │                 │
│ • File system   │    │ • Real-time UI  │    │ • JSON output   │
│ • Rotation      │    │ • Statistics    │    │ • Aggregation   │
│ • Backup        │    │ • Status        │    │ • History       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 사용 시나리오

### 1. 개발/테스트 환경
```
Developer → Test Pipeline → Mock LLM → Results
```

### 2. 실시간 모니터링
```
Production Logs → Monitor → Auto Analysis → Alerts
```

### 3. 배치 분석
```
Log Files → Batch Processing → Comprehensive Analysis → Reports
```

### 4. 대화형 분석
```
User Input → Interactive Mode → Custom Analysis → Immediate Results
```

---

**이 아키텍처는 확장 가능하고 모듈화된 설계로, 다양한 로그 분석 요구사항을 충족할 수 있습니다.**
