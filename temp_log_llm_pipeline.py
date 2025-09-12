# vLLM Qwen 7B 서버 실행 예시
# python -m vllm.entrypoints.openai.api_server \
#   --model Qwen/Qwen2.5-7B-Instruct \
#   --max-model-len 16384 \
#   --tensor-parallel-size 1 \
#   --host 0.0.0.0 --port 8000

# log_llm_pipeline.py
import os, json, math, time
from datetime import datetime
from typing import List, Dict
import tiktoken  # 설치시 사용, 없으면 문자수/4 근사치로 대체 [애매: 없으면 간이토크나이저로]
import requests

OPENAI_BASE = "http://127.0.0.1:8000/v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"  # Qwen 7B 모델명
WINDOW_TOKENS = 5000
OVERLAP_RATIO = 0.15  # 15% 오버랩
SYSTEM_PROMPT = (
    "You are an SRE/DevOps log expert. Be factual. "
    "Provide: (1) key symptoms, (2) root-cause hypotheses with priority, "
    "(3) concrete shell commands to verify, (4) mitigations/preventions, "
    "(5) confidence level. Keep answers concise but actionable."
)

def rough_token_count(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)

def sliding_windows(lines: List[str], win_tokens=WINDOW_TOKENS, overlap_ratio=OVERLAP_RATIO):
    out = []
    buf = []
    tok = 0
    stride = int(win_tokens * (1 - overlap_ratio))

    i = 0
    while i < len(lines):
        line = lines[i]
        t = rough_token_count(line)
        if tok + t <= win_tokens:
            buf.append(line)
            tok += t
            i += 1
        else:
            out.append("\n".join(buf))
            # 오버랩 유지: 뒤에서 overlap_ratio 만큼 남기고 재시작
            keep_tokens = int(win_tokens * overlap_ratio)
            kept = []
            ktok = 0
            for l in reversed(buf):
                lt = rough_token_count(l)
                if ktok + lt > keep_tokens: break
                kept.append(l)
                ktok += lt
            buf = list(reversed(kept))
            tok = sum(rough_token_count(l) for l in buf)

    if buf:
        out.append("\n".join(buf))
    return out

def preprocess(lines: List[str]) -> List[str]:
    out = []
    for ln in lines:
        # 노이즈/헬스체크/중복축약 예시
        if "healthz" in ln or "readinessProbe" in ln:
            continue
        out.append(ln.rstrip("\n"))
    return out

def call_llm(window_text: str, meta: Dict) -> Dict:
    user_prompt = f"""[META]
service={meta.get('service','[unknown]')}
host={meta.get('host','[unknown]')}
time_range={meta.get('time_range','[unknown]')}
severity_top={meta.get('severity','[unknown]')}

[LOG WINDOW]
{window_text}

[TASK]
1) 핵심 증상 3~5개
2) 원인 가설(우선순위)
3) 즉시 점검 명령(쉘)
4) 재발방지 액션
5) 확신도[낮음/중간/높음]
"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }
    r = requests.post(f"{OPENAI_BASE}/chat/completions", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    return {"meta": meta, "analysis": content}

def main(log_path: str, out_path: str, meta: Dict):
    with open(log_path, "r", errors="ignore") as f:
        raw = f.readlines()
    lines = preprocess(raw)
    wins = sliding_windows(lines)
    results = []
    # 시간범위 메타 추출(간단 예시)
    now = datetime.utcnow().isoformat() + "Z"
    meta = {**meta, "time_range": meta.get("time_range", f"processed_at={now}")}

    for idx, w in enumerate(wins):
        m = {**meta, "window_index": idx, "total_windows": len(wins)}
        res = call_llm(w, m)
        results.append(res)
        # 백프레셔 방지
        time.sleep(0.1)

    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"saved: {out_path} (windows={len(wins)})")

if __name__ == "__main__":
    # 사용 예
    meta = {"service": "ordersvc", "host": "node-01", "severity": "error>warning>info"}
    main("./large_test.log", "./analysis_results.json", meta)
