#!/usr/bin/env python3
"""
종합 테스트 스위트 - vLLM 로그 분석 파이프라인 테스트
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List

# 테스트 설정
TEST_DIR = "/home/ssh/work/sliding-window-llm"
VLLM_SERVER_URL = "http://127.0.0.1:8000/v1"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, status: str = "INFO"):
    """상태 메시지 출력"""
    color = Colors.BLUE
    if status == "SUCCESS":
        color = Colors.GREEN
    elif status == "ERROR":
        color = Colors.RED
    elif status == "WARNING":
        color = Colors.YELLOW
    
    print(f"{color}[{status}]{Colors.ENDC} {message}")

def test_vllm_connection() -> bool:
    """vLLM 서버 연결 테스트"""
    print_status("vLLM 서버 연결 테스트 중...", "INFO")
    
    try:
        # 서버 상태 확인
        response = requests.get(f"{VLLM_SERVER_URL}/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print_status(f"서버 연결 성공! 사용 가능한 모델: {models}", "SUCCESS")
            return True
        else:
            print_status(f"서버 응답 오류: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.ConnectionError:
        print_status("vLLM 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.", "ERROR")
        return False
    except Exception as e:
        print_status(f"연결 테스트 실패: {e}", "ERROR")
        return False

def test_simple_llm_call() -> bool:
    """간단한 LLM 호출 테스트"""
    print_status("간단한 LLM 호출 테스트 중...", "INFO")
    
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please respond with 'Test successful'."}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        response = requests.post(
            f"{VLLM_SERVER_URL}/chat/completions", 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print_status(f"LLM 응답: {content}", "SUCCESS")
            return True
        else:
            print_status(f"LLM 호출 실패: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"LLM 호출 테스트 실패: {e}", "ERROR")
        return False

def create_test_logs():
    """다양한 테스트 로그 파일 생성"""
    print_status("테스트 로그 파일 생성 중...", "INFO")
    
    # 1. 작은 로그 파일
    small_log = """2024-01-15 10:30:15 ERROR [ordersvc] Database connection failed
2024-01-15 10:30:16 WARN [ordersvc] Retrying connection
2024-01-15 10:30:17 INFO [ordersvc] Connection restored"""
    
    with open(f"{TEST_DIR}/small_test.log", "w") as f:
        f.write(small_log)
    
    # 2. 큰 로그 파일 (슬라이딩 윈도우 테스트용)
    large_log_lines = []
    for i in range(100):
        timestamp = f"2024-01-15 10:{30+i//60:02d}:{i%60:02d}"
        level = ["ERROR", "WARN", "INFO"][i % 3]
        message = f"[ordersvc] Test log message {i} - This is a longer message to test token counting and sliding window functionality"
        large_log_lines.append(f"{timestamp} {level} {message}")
    
    with open(f"{TEST_DIR}/large_test.log", "w") as f:
        f.write("\n".join(large_log_lines))
    
    # 3. 복잡한 로그 파일 (다양한 서비스)
    complex_log = """2024-01-15 10:30:15 ERROR [ordersvc] Database connection timeout
2024-01-15 10:30:16 WARN [paymentsvc] Payment gateway slow response
2024-01-15 10:30:17 INFO [usersvc] User login successful
2024-01-15 10:30:18 ERROR [ordersvc] Order processing failed
2024-01-15 10:30:19 CRITICAL [ordersvc] Service unavailable
2024-01-15 10:30:20 INFO [ordersvc] Service restarting
2024-01-15 10:30:21 WARN [inventorysvc] Low stock alert
2024-01-15 10:30:22 ERROR [ordersvc] Memory usage critical: 95%
2024-01-15 10:30:23 INFO [ordersvc] Service recovered"""
    
    with open(f"{TEST_DIR}/complex_test.log", "w") as f:
        f.write(complex_log)
    
    print_status("테스트 로그 파일 생성 완료", "SUCCESS")

def test_pipeline_with_mock():
    """모의 버전으로 파이프라인 테스트"""
    print_status("모의 버전 파이프라인 테스트 중...", "INFO")
    
    try:
        # test_pipeline.py 실행
        result = subprocess.run([
            "python3", f"{TEST_DIR}/test_pipeline.py"
        ], capture_output=True, text=True, cwd=TEST_DIR)
        
        if result.returncode == 0:
            print_status("모의 파이프라인 테스트 성공", "SUCCESS")
            print(f"출력: {result.stdout}")
            return True
        else:
            print_status(f"모의 파이프라인 테스트 실패: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"모의 파이프라인 테스트 실패: {e}", "ERROR")
        return False

def test_pipeline_with_vllm():
    """실제 vLLM으로 파이프라인 테스트"""
    print_status("실제 vLLM 파이프라인 테스트 중...", "INFO")
    
    try:
        # log_llm_pipeline.py 실행
        result = subprocess.run([
            "python3", f"{TEST_DIR}/log_llm_pipeline.py"
        ], capture_output=True, text=True, cwd=TEST_DIR, timeout=120)
        
        if result.returncode == 0:
            print_status("실제 vLLM 파이프라인 테스트 성공", "SUCCESS")
            print(f"출력: {result.stdout}")
            return True
        else:
            print_status(f"실제 vLLM 파이프라인 테스트 실패: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("vLLM 파이프라인 테스트 시간 초과 (120초)", "WARNING")
        return False
    except Exception as e:
        print_status(f"실제 vLLM 파이프라인 테스트 실패: {e}", "ERROR")
        return False

def test_different_log_files():
    """다양한 로그 파일로 테스트"""
    print_status("다양한 로그 파일 테스트 중...", "INFO")
    
    test_files = ["small_test.log", "large_test.log", "complex_test.log"]
    results = []
    
    for log_file in test_files:
        print_status(f"테스트 파일: {log_file}", "INFO")
        
        # 파이프라인 스크립트 수정하여 다른 로그 파일 사용
        try:
            # 임시로 다른 로그 파일을 사용하도록 스크립트 수정
            with open(f"{TEST_DIR}/log_llm_pipeline.py", "r") as f:
                content = f.read()
            
            # test_log.txt를 다른 파일로 변경
            modified_content = content.replace("./test_log.txt", f"./{log_file}")
            
            with open(f"{TEST_DIR}/temp_pipeline.py", "w") as f:
                f.write(modified_content)
            
            # 임시 스크립트 실행
            result = subprocess.run([
                "python3", f"{TEST_DIR}/temp_pipeline.py"
            ], capture_output=True, text=True, cwd=TEST_DIR, timeout=60)
            
            if result.returncode == 0:
                print_status(f"{log_file} 테스트 성공", "SUCCESS")
                results.append(True)
            else:
                print_status(f"{log_file} 테스트 실패: {result.stderr}", "ERROR")
                results.append(False)
                
        except Exception as e:
            print_status(f"{log_file} 테스트 실패: {e}", "ERROR")
            results.append(False)
    
    # 임시 파일 정리
    if os.path.exists(f"{TEST_DIR}/temp_pipeline.py"):
        os.remove(f"{TEST_DIR}/temp_pipeline.py")
    
    success_count = sum(results)
    print_status(f"로그 파일 테스트 결과: {success_count}/{len(test_files)} 성공", 
                "SUCCESS" if success_count == len(test_files) else "WARNING")
    
    return success_count == len(test_files)

def run_all_tests():
    """모든 테스트 실행"""
    print(f"{Colors.BOLD}{Colors.BLUE}=== vLLM 로그 분석 파이프라인 테스트 시작 ==={Colors.ENDC}")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("테스트 로그 파일 생성", create_test_logs),
        ("모의 파이프라인 테스트", test_pipeline_with_mock),
        ("vLLM 서버 연결 테스트", test_vllm_connection),
        ("간단한 LLM 호출 테스트", test_simple_llm_call),
        ("실제 vLLM 파이프라인 테스트", test_pipeline_with_vllm),
        ("다양한 로그 파일 테스트", test_different_log_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"{Colors.BOLD}--- {test_name} ---{Colors.ENDC}")
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print_status(f"테스트 실행 중 오류: {e}", "ERROR")
            results.append((test_name, False))
            print()
    
    # 결과 요약
    print(f"{Colors.BOLD}{Colors.BLUE}=== 테스트 결과 요약 ==={Colors.ENDC}")
    success_count = 0
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.ENDC} {test_name}")
        if result:
            success_count += 1
    
    print()
    print(f"전체 결과: {success_count}/{len(results)} 테스트 통과")
    
    if success_count == len(results):
        print_status("모든 테스트 통과! 🎉", "SUCCESS")
    else:
        print_status(f"{len(results) - success_count}개 테스트 실패", "WARNING")

if __name__ == "__main__":
    run_all_tests()
