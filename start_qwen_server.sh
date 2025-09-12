#!/bin/bash

# Qwen 7B vLLM 서버 시작 스크립트
# 사용법: ./start_qwen_server.sh

echo "Starting Qwen 7B vLLM server..."

# vLLM 서버 시작
python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --max-model-len 16384 \
  --tensor-parallel-size 1 \
  --host 0.0.0.0 \
  --port 8000 \
  --trust-remote-code

echo "Qwen 7B server started on http://0.0.0.0:8000"
echo "API endpoint: http://127.0.0.1:8000/v1/chat/completions"
