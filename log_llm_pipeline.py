# vLLM Qwen 7B 서버 실행 예시
# python -m vllm.entrypoints.openai.api_server \
#   --model Qwen/Qwen2.5-7B-Instruct \
#   --max-model-len 16384 \
#   --tensor-parallel-size 1 \
#   --host 0.0.0.0 --port 8000

# log_llm_pipeline.py
import os, json, time
from datetime import datetime
from typing import List, Dict
import requests

# 새로운 모듈 import
from prompt_templates import get_prompt_templates, AnalysisType
from sliding_window import create_sliding_window, WindowConfig, WindowProcessor
from config import OPENAI_BASE, MODEL, DEFAULT_WINDOW_TOKENS, DEFAULT_OVERLAP_RATIO, DEFAULT_MIN_TOKENS

# 윈도우 설정
WINDOW_CONFIG = WindowConfig(
    max_tokens=DEFAULT_WINDOW_TOKENS,
    overlap_ratio=DEFAULT_OVERLAP_RATIO,
    min_tokens=DEFAULT_MIN_TOKENS
)

# 기존 함수들은 새로운 모듈로 대체됨

def call_llm(window_text: str, meta: Dict, analysis_type: AnalysisType = None) -> Dict:
    """LLM 호출 함수 - 새로운 프롬프트 템플릿 사용"""
    # 프롬프트 템플릿 가져오기
    prompt_templates = get_prompt_templates()
    
    # 분석 타입 자동 감지 (지정되지 않은 경우)
    if analysis_type is None:
        analysis_type = prompt_templates.detect_analysis_type(window_text)
    
    # 시스템 프롬프트와 사용자 프롬프트 생성
    system_prompt = prompt_templates.get_system_prompt(analysis_type)
    user_prompt = prompt_templates.get_user_prompt(
        analysis_type,
        service=meta.get('service', '[unknown]'),
        host=meta.get('host', '[unknown]'),
        time_range=meta.get('time_range', '[unknown]'),
        severity=meta.get('severity', '[unknown]'),
        log_content=window_text
    )
    
    # 분석 설정 가져오기
    config = prompt_templates.get_analysis_config(analysis_type)
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
    }
    
    r = requests.post(f"{OPENAI_BASE}/chat/completions", json=payload, timeout=config["timeout"])
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    
    return {
        "meta": meta, 
        "analysis": content,
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
        res = call_llm(window.content, window_meta, analysis_type)
        results.append(res)
        
        # 백프레셔 방지
        time.sleep(0.1)

    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 저장 완료: {out_path} (윈도우={len(windows)})")

if __name__ == "__main__":
    # 사용 예
    meta = {"service": "ordersvc", "host": "node-01", "severity": "error>warning>info"}
    
    # 분석 타입 지정 (선택사항)
    # analysis_type = AnalysisType.DATABASE  # 데이터베이스 전용 분석
    # analysis_type = AnalysisType.MEMORY    # 메모리 전용 분석
    analysis_type = None  # 자동 감지
    
    main("./scenario_1_데이터베이스_오류.log", "./analysis_results.json", meta, analysis_type)
