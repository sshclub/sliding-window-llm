#!/usr/bin/env python3
"""
배치 테스트 스크립트 - 여러 로그 시나리오를 자동으로 테스트
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import glob

class BatchTester:
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
    
    def find_log_files(self, pattern: str = "*.log") -> List[str]:
        """로그 파일 찾기"""
        log_files = []
        for file in glob.glob(os.path.join(self.test_dir, pattern)):
            if os.path.isfile(file):
                log_files.append(os.path.basename(file))
        return sorted(log_files)
    
    def run_single_test(self, log_file: str, use_vllm: bool = True) -> Dict:
        """단일 테스트 실행"""
        print(f"  📝 {log_file} 테스트 중...")
        
        start_time = time.time()
        script_name = "log_llm_pipeline.py" if use_vllm else "test_pipeline.py"
        script_path = os.path.join(self.test_dir, script_name)
        temp_script_path = os.path.join(self.test_dir, f"temp_{script_name}")
        
        try:
            # 스크립트 수정
            with open(script_path, 'r') as f:
                content = f.read()
            
            # 로그 파일 경로 변경
            if "test_log.txt" in content:
                modified_content = content.replace("./test_log.txt", f"./{log_file}")
            else:
                import re
                modified_content = re.sub(r'main\("\./[^"]+",', f'main("./{log_file}",', content)
            
            with open(temp_script_path, 'w') as f:
                f.write(modified_content)
            
            # 테스트 실행
            result = subprocess.run([
                "python3", temp_script_path
            ], capture_output=True, text=True, cwd=self.test_dir, timeout=120)
            
            # 임시 파일 삭제
            os.remove(temp_script_path)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                # 결과 파일 찾기
                result_files = [f for f in os.listdir(self.test_dir) 
                              if f.startswith('analysis_results') or f.startswith('test_analysis_results')]
                latest_result = max(result_files, key=lambda x: os.path.getmtime(os.path.join(self.test_dir, x))) if result_files else None
                
                return {
                    "success": True,
                    "log_file": log_file,
                    "duration": duration,
                    "result_file": latest_result,
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "log_file": log_file,
                    "duration": duration,
                    "error": result.stderr.strip()
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "log_file": log_file,
                "duration": 120,
                "error": "Timeout (120초)"
            }
        except Exception as e:
            return {
                "success": False,
                "log_file": log_file,
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def analyze_result_file(self, result_file: str) -> Dict:
        """결과 파일 분석"""
        if not result_file:
            return {"windows": 0, "analysis_length": 0}
        
        filepath = os.path.join(self.test_dir, result_file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            total_analysis_length = sum(len(result.get('analysis', '')) for result in results)
            
            return {
                "windows": len(results),
                "analysis_length": total_analysis_length,
                "has_analysis": total_analysis_length > 0
            }
        except Exception as e:
            return {"windows": 0, "analysis_length": 0, "error": str(e)}
    
    def run_batch_test(self, test_vllm: bool = True, test_mock: bool = True) -> None:
        """배치 테스트 실행"""
        print("🚀 배치 테스트 시작")
        print("=" * 60)
        
        # 로그 파일 찾기
        log_files = self.find_log_files()
        if not log_files:
            print("❌ 테스트할 로그 파일이 없습니다.")
            print("   로그를 생성하려면: python3 log_generator.py")
            return
        
        print(f"📁 발견된 로그 파일: {len(log_files)}개")
        for file in log_files:
            print(f"  - {file}")
        print()
        
        # vLLM 서버 상태 확인
        vllm_available = self.check_vllm_server()
        print(f"vLLM 서버 상태: {'✅ 연결됨' if vllm_available else '❌ 연결 안됨'}")
        
        if test_vllm and not vllm_available:
            print("⚠️  vLLM 서버가 없어 vLLM 테스트를 건너뜁니다.")
            test_vllm = False
        
        total_tests = 0
        if test_vllm:
            total_tests += len(log_files)
        if test_mock:
            total_tests += len(log_files)
        
        print(f"📊 총 {total_tests}개 테스트 실행 예정")
        print()
        
        # 테스트 실행
        test_count = 0
        
        # vLLM 테스트
        if test_vllm:
            print("🔮 vLLM 테스트 시작")
            print("-" * 40)
            for log_file in log_files:
                test_count += 1
                print(f"[{test_count}/{total_tests}] vLLM - {log_file}")
                result = self.run_single_test(log_file, use_vllm=True)
                result["test_type"] = "vLLM"
                self.results.append(result)
                
                if result["success"]:
                    analysis_info = self.analyze_result_file(result["result_file"])
                    print(f"  ✅ 성공 ({result['duration']:.1f}초, {analysis_info['windows']}윈도우)")
                else:
                    print(f"  ❌ 실패: {result['error']}")
                print()
        
        # 모의 테스트
        if test_mock:
            print("🧪 모의 테스트 시작")
            print("-" * 40)
            for log_file in log_files:
                test_count += 1
                print(f"[{test_count}/{total_tests}] 모의 - {log_file}")
                result = self.run_single_test(log_file, use_vllm=False)
                result["test_type"] = "모의"
                self.results.append(result)
                
                if result["success"]:
                    analysis_info = self.analyze_result_file(result["result_file"])
                    print(f"  ✅ 성공 ({result['duration']:.1f}초, {analysis_info['windows']}윈도우)")
                else:
                    print(f"  ❌ 실패: {result['error']}")
                print()
    
    def generate_report(self) -> None:
        """테스트 결과 보고서 생성"""
        if not self.results:
            print("❌ 테스트 결과가 없습니다.")
            return
        
        print("📊 테스트 결과 보고서")
        print("=" * 60)
        
        # 전체 통계
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"전체 테스트: {total_tests}개")
        print(f"성공: {successful_tests}개 ({successful_tests/total_tests*100:.1f}%)")
        print(f"실패: {failed_tests}개 ({failed_tests/total_tests*100:.1f}%)")
        print()
        
        # 테스트 타입별 통계
        vllm_results = [r for r in self.results if r.get("test_type") == "vLLM"]
        mock_results = [r for r in self.results if r.get("test_type") == "모의"]
        
        if vllm_results:
            vllm_success = sum(1 for r in vllm_results if r["success"])
            vllm_avg_time = sum(r["duration"] for r in vllm_results if r["success"]) / max(vllm_success, 1)
            print(f"vLLM 테스트: {vllm_success}/{len(vllm_results)} 성공 (평균 {vllm_avg_time:.1f}초)")
        
        if mock_results:
            mock_success = sum(1 for r in mock_results if r["success"])
            mock_avg_time = sum(r["duration"] for r in mock_results if r["success"]) / max(mock_success, 1)
            print(f"모의 테스트: {mock_success}/{len(mock_results)} 성공 (평균 {mock_avg_time:.1f}초)")
        print()
        
        # 실패한 테스트 상세
        failed_results = [r for r in self.results if not r["success"]]
        if failed_results:
            print("❌ 실패한 테스트:")
            for result in failed_results:
                print(f"  - {result['test_type']} - {result['log_file']}: {result['error']}")
            print()
        
        # 성공한 테스트 상세
        successful_results = [r for r in self.results if r["success"]]
        if successful_results:
            print("✅ 성공한 테스트:")
            for result in successful_results:
                analysis_info = self.analyze_result_file(result["result_file"])
                print(f"  - {result['test_type']} - {result['log_file']}: {result['duration']:.1f}초, {analysis_info['windows']}윈도우")
        
        # 결과를 JSON 파일로 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"batch_test_report_{timestamp}.json"
        report_path = os.path.join(self.test_dir, report_file)
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests/total_tests*100
            },
            "results": self.results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 상세 보고서 저장: {report_file}")

def main():
    tester = BatchTester()
    
    print("🎯 배치 테스트 옵션:")
    print("1. vLLM 테스트만")
    print("2. 모의 테스트만")
    print("3. 둘 다 테스트")
    print("4. 자동 (vLLM 서버 상태에 따라)")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        tester.run_batch_test(test_vllm=True, test_mock=False)
    elif choice == "2":
        tester.run_batch_test(test_vllm=False, test_mock=True)
    elif choice == "3":
        tester.run_batch_test(test_vllm=True, test_mock=True)
    elif choice == "4":
        vllm_available = tester.check_vllm_server()
        tester.run_batch_test(test_vllm=vllm_available, test_mock=True)
    else:
        print("❌ 잘못된 선택입니다.")
        return
    
    tester.generate_report()

if __name__ == "__main__":
    main()
