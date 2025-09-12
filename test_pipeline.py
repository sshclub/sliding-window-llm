# 테스트용 버전 - vLLM 서버 없이도 실행 가능
import os, json, time
from datetime import datetime
from typing import List, Dict

# 새로운 모듈 import
from prompt_templates import get_prompt_templates, AnalysisType
from sliding_window import create_sliding_window, WindowConfig, WindowProcessor

# 윈도우 설정
WINDOW_CONFIG = WindowConfig(
    max_tokens=5000,
    overlap_ratio=0.15,
    min_tokens=100
)

# 기존 함수들은 새로운 모듈로 대체됨

def mock_llm_call(window_text: str, meta: Dict, analysis_type: AnalysisType = None) -> Dict:
    """vLLM 서버 없이 테스트용 모의 응답 생성 - 새로운 프롬프트 템플릿 사용"""
    # 프롬프트 템플릿 가져오기
    prompt_templates = get_prompt_templates()
    
    # 분석 타입 자동 감지 (지정되지 않은 경우)
    if analysis_type is None:
        analysis_type = prompt_templates.detect_analysis_type(window_text)
    
    # 분석 타입에 따른 모의 응답 생성
    if analysis_type == AnalysisType.DATABASE:
        analysis = """
**데이터베이스 연결 상태 및 오류:**
1. 데이터베이스 연결 타임아웃 (30초)
2. 연결 풀 고갈 (80% 사용)
3. 쿼리 성능 저하 (2.5초 이상)

**쿼리 성능 및 타임아웃 이슈:**
1. [높음] 느린 쿼리로 인한 연결 점유
2. [중간] 인덱스 부족으로 인한 성능 저하
3. [낮음] 네트워크 지연

**데이터베이스 서버 상태 점검 명령:**
```bash
# 연결 상태 확인
mysqladmin -u root -p processlist
netstat -an | grep :3306

# 성능 확인
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads_connected';
```

**성능 최적화 및 모니터링 권장사항:**
1. 연결 풀 크기 증가
2. 쿼리 최적화 및 인덱스 추가
3. 데이터베이스 모니터링 설정

**확신도:** 중간
"""
    elif analysis_type == AnalysisType.MEMORY:
        analysis = """
**메모리 사용량 패턴 및 누수 증상:**
1. 메모리 사용량 급증 (85%)
2. OutOfMemoryError 발생
3. GC 압력 증가

**OutOfMemoryError 및 메모리 부족 원인:**
1. [높음] 메모리 누수로 인한 점진적 증가
2. [중간] 대용량 객체 할당
3. [낮음] 시스템 메모리 부족

**메모리 상태 점검 명령:**
```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head -10

# JVM 힙 덤프 (Java 애플리케이션)
jmap -dump:format=b,file=heap.hprof <pid>
```

**메모리 최적화 및 모니터링 권장사항:**
1. 메모리 누수 코드 수정
2. 힙 크기 조정
3. 메모리 모니터링 알림 설정

**확신도:** 높음
"""
    else:
        analysis = """
**핵심 증상:**
1. 데이터베이스 연결 실패 (timeout after 30s)
2. 메모리 사용량 급증 (85%)
3. OutOfMemoryError 발생
4. 서비스 전체 다운
5. 모든 워커 프로세스 중단

**원인 가설 (우선순위):**
1. [높음] 데이터베이스 연결 풀 고갈 또는 네트워크 이슈
2. [중간] 메모리 누수로 인한 리소스 부족
3. [낮음] 시스템 리소스 부족

**즉시 점검 명령:**
```bash
# 데이터베이스 연결 상태 확인
netstat -an | grep :5432
ss -tuln | grep :5432

# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head -10

# 서비스 로그 확인
journalctl -u ordersvc -f --since "10 minutes ago"
```

**재발방지 액션:**
1. 데이터베이스 연결 풀 크기 조정
2. 메모리 모니터링 알림 설정
3. 자동 재시작 정책 구현
4. 리소스 제한 설정

**확신도:** 중간
"""
    
    return {
        "meta": meta, 
        "analysis": analysis,
        "analysis_type": analysis_type.value
    }

def main(log_path: str, out_path: str, meta: Dict, analysis_type: AnalysisType = None):
    """메인 파이프라인 함수 - 새로운 모듈 사용"""
    # 슬라이딩 윈도우 생성
    sliding_window = create_sliding_window(WINDOW_CONFIG)
    windows = sliding_window.create_windows_from_file(log_path)
    
    if not windows:
        print("❌ 윈도우 생성 실패")
        return
    
    # 윈도우 통계 출력
    stats = sliding_window.get_window_stats(windows)
    print(f"📊 윈도우 통계: {stats['total_windows']}개 윈도우, {stats['total_tokens']}개 토큰")
    
    results = []
    # 시간범위 메타 추출
    now = datetime.utcnow().isoformat() + "Z"
    meta = {**meta, "time_range": meta.get("time_range", f"processed_at={now}")}

    for window in windows:
        window_meta = {
            **meta, 
            "window_index": window.window_index, 
            "total_windows": window.total_windows,
            "window_tokens": window.token_count,
            "window_lines": window.end_line - window.start_line + 1
        }
        
        print(f"🔍 윈도우 {window.window_index + 1}/{window.total_windows} 분석 중... ({window.token_count}토큰)")
        res = mock_llm_call(window.content, window_meta, analysis_type)
        results.append(res)
        
        # 백프레셔 방지
        time.sleep(0.1)

    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 저장 완료: {out_path} (윈도우={len(windows)})")

if __name__ == "__main__":
    # 사용 예
    meta = {"service": "ordersvc", "host": "node-01", "severity": "error>warning>info"}
    main("./test_log.txt", "./test_analysis_results.json", meta)
