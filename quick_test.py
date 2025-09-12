#!/usr/bin/env python3
"""
빠른 테스트 스크립트 - 기본 기능만 테스트
"""

import requests
import subprocess
import sys
import os

def test_vllm_server():
    """vLLM 서버 연결 테스트"""
    print("🔍 vLLM 서버 연결 테스트...")
    try:
        response = requests.get("http://127.0.0.1:8000/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ vLLM 서버 연결 성공!")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return False

def test_mock_pipeline():
    """모의 파이프라인 테스트"""
    print("🧪 모의 파이프라인 테스트...")
    try:
        result = subprocess.run(["python3", "test_pipeline.py"], 
                              capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            print("✅ 모의 파이프라인 테스트 성공!")
            return True
        else:
            print(f"❌ 모의 파이프라인 테스트 실패: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 모의 파이프라인 테스트 실패: {e}")
        return False

def test_real_pipeline():
    """실제 vLLM 파이프라인 테스트"""
    print("🚀 실제 vLLM 파이프라인 테스트...")
    try:
        result = subprocess.run(["python3", "log_llm_pipeline.py"], 
                              capture_output=True, text=True, cwd=".", timeout=60)
        if result.returncode == 0:
            print("✅ 실제 vLLM 파이프라인 테스트 성공!")
            return True
        else:
            print(f"❌ 실제 vLLM 파이프라인 테스트 실패: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ 테스트 시간 초과 (60초)")
        return False
    except Exception as e:
        print(f"❌ 실제 vLLM 파이프라인 테스트 실패: {e}")
        return False

def main():
    print("=== 빠른 테스트 시작 ===\n")
    
    # 1. 모의 파이프라인 테스트 (항상 실행)
    mock_success = test_mock_pipeline()
    print()
    
    # 2. vLLM 서버 연결 테스트
    server_success = test_vllm_server()
    print()
    
    # 3. 실제 파이프라인 테스트 (서버가 실행 중일 때만)
    real_success = False
    if server_success:
        real_success = test_real_pipeline()
    else:
        print("⚠️  vLLM 서버가 실행되지 않아 실제 파이프라인 테스트를 건너뜁니다.")
        print("   서버를 시작하려면: ./start_qwen_server.sh")
    print()
    
    # 결과 요약
    print("=== 테스트 결과 ===")
    print(f"모의 파이프라인: {'✅ 성공' if mock_success else '❌ 실패'}")
    print(f"vLLM 서버 연결: {'✅ 성공' if server_success else '❌ 실패'}")
    print(f"실제 파이프라인: {'✅ 성공' if real_success else '❌ 실패' if server_success else '⏭️  건너뜀'}")
    
    if mock_success and (server_success and real_success or not server_success):
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print("\n⚠️  일부 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
