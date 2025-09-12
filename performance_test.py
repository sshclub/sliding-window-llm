#!/usr/bin/env python3
"""
성능 테스트 스크립트 - 대용량 로그와 동시 요청 처리 성능 측정
"""

import os
import sys
import json
import time
import threading
import subprocess
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import statistics
import concurrent.futures
from log_generator import LogGenerator

class PerformanceTester:
    def __init__(self):
        self.test_dir = "/home/ssh/work/sliding-window-llm"
        self.vllm_url = "http://127.0.0.1:8000/v1"
        self.model_name = "Qwen/Qwen2.5-7B-Instruct"
        self.results = []
    
    def check_vllm_server(self) -> bool:
        """vLLM 서버 상태 확인"""
        try:
            response = requests.get(f"{self.vllm_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_large_logs(self) -> List[str]:
        """대용량 로그 파일들 생성"""
        print("📝 대용량 로그 파일 생성 중...")
        
        generator = LogGenerator()
        log_files = []
        
        # 다양한 크기의 로그 파일 생성
        sizes = [
            (100, "small"),
            (500, "medium"), 
            (1000, "large"),
            (2000, "xlarge"),
            (5000, "huge")
        ]
        
        for size, name in sizes:
            print(f"  - {name} 로그 생성 ({size}줄)...")
            logs = generator.generate_large_volume_logs(size)
            filename = f"perf_{name}_{size}lines.log"
            filepath = os.path.join(self.test_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write('\n'.join(logs))
            
            log_files.append(filename)
        
        print(f"✅ {len(log_files)}개 대용량 로그 파일 생성 완료")
        return log_files
    
    def measure_single_request_time(self, log_file: str, use_vllm: bool = True) -> Dict:
        """단일 요청 처리 시간 측정"""
        start_time = time.time()
        
        try:
            if use_vllm:
                # vLLM 직접 호출로 측정
                with open(os.path.join(self.test_dir, log_file), 'r') as f:
                    log_content = f.read()
                
                # 간단한 분석 요청
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a log analysis expert. Provide a brief analysis."},
                        {"role": "user", "content": f"Analyze these logs briefly:\n{log_content[:2000]}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                }
                
                response = requests.post(
                    f"{self.vllm_url}/chat/completions",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    end_time = time.time()
                    return {
                        "success": True,
                        "duration": end_time - start_time,
                        "response_length": len(response.json()["choices"][0]["message"]["content"])
                    }
                else:
                    return {
                        "success": False,
                        "duration": time.time() - start_time,
                        "error": f"HTTP {response.status_code}"
                    }
            else:
                # 모의 테스트
                result = subprocess.run([
                    "python3", "test_pipeline.py"
                ], capture_output=True, text=True, cwd=self.test_dir, timeout=30)
                
                end_time = time.time()
                return {
                    "success": result.returncode == 0,
                    "duration": end_time - start_time,
                    "output": result.stdout
                }
                
        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def test_concurrent_requests(self, num_requests: int = 5) -> Dict:
        """동시 요청 처리 테스트"""
        print(f"🔄 동시 요청 테스트 ({num_requests}개 요청)...")
        
        # 간단한 테스트 로그 생성
        test_log = "2024-01-15 10:30:15 ERROR [test] Test error message\n" * 10
        test_file = "concurrent_test.log"
        with open(os.path.join(self.test_dir, test_file), 'w') as f:
            f.write(test_log)
        
        start_time = time.time()
        results = []
        
        def make_request(request_id: int) -> Dict:
            """개별 요청 함수"""
            req_start = time.time()
            try:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a log analysis expert."},
                        {"role": "user", "content": f"Request {request_id}: Analyze this log briefly: {test_log[:500]}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 100
                }
                
                response = requests.post(
                    f"{self.vllm_url}/chat/completions",
                    json=payload,
                    timeout=30
                )
                
                req_end = time.time()
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "duration": req_end - req_start,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "duration": time.time() - req_start,
                    "error": str(e)
                }
        
        # 동시 요청 실행
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r["success"])
        
        # 통계 계산
        durations = [r["duration"] for r in results if r["success"]]
        avg_duration = statistics.mean(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        return {
            "total_requests": num_requests,
            "successful_requests": successful_requests,
            "total_time": total_time,
            "requests_per_second": num_requests / total_time,
            "avg_response_time": avg_duration,
            "min_response_time": min_duration,
            "max_response_time": max_duration,
            "results": results
        }
    
    def test_memory_usage(self, log_file: str) -> Dict:
        """메모리 사용량 테스트"""
        print(f"💾 메모리 사용량 테스트 ({log_file})...")
        
        try:
            # 프로세스 시작 전 메모리 확인
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 파이프라인 실행
            start_time = time.time()
            result = subprocess.run([
                "python3", "log_llm_pipeline.py"
            ], capture_output=True, text=True, cwd=self.test_dir, timeout=120)
            
            end_time = time.time()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "success": result.returncode == 0,
                "duration": end_time - start_time,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_delta_mb": final_memory - initial_memory,
                "output": result.stdout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_token_processing_speed(self) -> Dict:
        """토큰 처리 속도 테스트"""
        print("⚡ 토큰 처리 속도 테스트...")
        
        # 다양한 크기의 텍스트로 토큰 처리 속도 측정
        test_texts = [
            "Short text",
            "Medium length text " * 50,
            "Long text " * 200,
            "Very long text " * 500
        ]
        
        results = []
        
        for i, text in enumerate(test_texts):
            start_time = time.time()
            
            try:
                import tiktoken
                enc = tiktoken.get_encoding("cl100k_base")
                tokens = enc.encode(text)
                token_count = len(tokens)
                
                end_time = time.time()
                duration = end_time - start_time
                
                results.append({
                    "text_size": len(text),
                    "token_count": token_count,
                    "duration": duration,
                    "tokens_per_second": token_count / duration if duration > 0 else 0
                })
            except Exception as e:
                results.append({
                    "text_size": len(text),
                    "error": str(e)
                })
        
        return {"token_processing_results": results}
    
    def run_performance_tests(self) -> None:
        """성능 테스트 실행"""
        print("🚀 성능 테스트 시작")
        print("=" * 60)
        
        # vLLM 서버 상태 확인
        vllm_available = self.check_vllm_server()
        print(f"vLLM 서버 상태: {'✅ 연결됨' if vllm_available else '❌ 연결 안됨'}")
        
        if not vllm_available:
            print("⚠️  vLLM 서버가 없어 일부 테스트를 건너뜁니다.")
        
        # 1. 대용량 로그 생성
        large_logs = self.generate_large_logs()
        print()
        
        # 2. 단일 요청 처리 시간 테스트
        print("⏱️  단일 요청 처리 시간 테스트")
        print("-" * 40)
        
        single_request_results = []
        for log_file in large_logs:
            print(f"  📝 {log_file} 테스트 중...")
            result = self.measure_single_request_time(log_file, use_vllm=vllm_available)
            result["log_file"] = log_file
            single_request_results.append(result)
            
            if result["success"]:
                print(f"    ✅ 성공: {result['duration']:.2f}초")
            else:
                print(f"    ❌ 실패: {result.get('error', 'Unknown error')}")
        
        # 3. 동시 요청 테스트 (vLLM 서버가 있을 때만)
        concurrent_results = None
        if vllm_available:
            print("\n🔄 동시 요청 처리 테스트")
            print("-" * 40)
            concurrent_results = self.test_concurrent_requests(5)
            print(f"  총 요청: {concurrent_results['total_requests']}개")
            print(f"  성공: {concurrent_results['successful_requests']}개")
            print(f"  총 시간: {concurrent_results['total_time']:.2f}초")
            print(f"  RPS: {concurrent_results['requests_per_second']:.2f}")
            print(f"  평균 응답 시간: {concurrent_results['avg_response_time']:.2f}초")
        
        # 4. 메모리 사용량 테스트
        print("\n💾 메모리 사용량 테스트")
        print("-" * 40)
        memory_result = self.test_memory_usage("test_log.txt")
        if memory_result["success"]:
            print(f"  처리 시간: {memory_result['duration']:.2f}초")
            print(f"  메모리 사용량: {memory_result['memory_delta_mb']:.1f}MB")
        else:
            print(f"  ❌ 실패: {memory_result.get('error', 'Unknown error')}")
        
        # 5. 토큰 처리 속도 테스트
        print("\n⚡ 토큰 처리 속도 테스트")
        print("-" * 40)
        token_results = self.test_token_processing_speed()
        for result in token_results["token_processing_results"]:
            if "error" not in result:
                print(f"  텍스트 크기: {result['text_size']}자, 토큰: {result['token_count']}개, 속도: {result['tokens_per_second']:.0f}토큰/초")
        
        # 결과 저장
        self.save_performance_report({
            "timestamp": datetime.now().isoformat(),
            "vllm_available": vllm_available,
            "single_request_results": single_request_results,
            "concurrent_results": concurrent_results,
            "memory_result": memory_result,
            "token_results": token_results
        })
    
    def save_performance_report(self, data: Dict) -> None:
        """성능 테스트 보고서 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"performance_report_{timestamp}.json"
        report_path = os.path.join(self.test_dir, report_file)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 성능 테스트 보고서 저장: {report_file}")
        
        # 요약 출력
        print("\n📊 성능 테스트 요약")
        print("=" * 40)
        
        if data["single_request_results"]:
            successful_results = [r for r in data["single_request_results"] if r["success"]]
            if successful_results:
                avg_duration = statistics.mean([r["duration"] for r in successful_results])
                print(f"평균 처리 시간: {avg_duration:.2f}초")
        
        if data["concurrent_results"]:
            print(f"동시 요청 처리: {data['concurrent_results']['requests_per_second']:.2f} RPS")
        
        if data["memory_result"]["success"]:
            print(f"메모리 사용량: {data['memory_result']['memory_delta_mb']:.1f}MB")

def main():
    tester = PerformanceTester()
    
    print("🎯 성능 테스트 옵션:")
    print("1. 전체 성능 테스트")
    print("2. 동시 요청 테스트만")
    print("3. 메모리 사용량 테스트만")
    print("4. 토큰 처리 속도 테스트만")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        tester.run_performance_tests()
    elif choice == "2":
        if tester.check_vllm_server():
            result = tester.test_concurrent_requests(10)
            print(f"동시 요청 결과: {result}")
        else:
            print("❌ vLLM 서버가 필요합니다.")
    elif choice == "3":
        result = tester.test_memory_usage("test_log.txt")
        print(f"메모리 테스트 결과: {result}")
    elif choice == "4":
        result = tester.test_token_processing_speed()
        print(f"토큰 처리 결과: {result}")
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
