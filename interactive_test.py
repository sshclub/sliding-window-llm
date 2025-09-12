#!/usr/bin/env python3
"""
대화형 테스트 스크립트 - 사용자가 직접 로그를 입력하거나 파일을 선택하여 테스트
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from typing import List, Dict

class InteractiveTester:
    def __init__(self):
        self.test_dir = "/home/ssh/work/sliding-window-llm"
        self.vllm_url = "http://127.0.0.1:8000/v1"
        self.model_name = "Qwen/Qwen2.5-7B-Instruct"
    
    def check_vllm_server(self) -> bool:
        """vLLM 서버 상태 확인"""
        try:
            response = requests.get(f"{self.vllm_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_log_files(self) -> List[str]:
        """사용 가능한 로그 파일 목록"""
        log_files = []
        for file in os.listdir(self.test_dir):
            if file.endswith('.log') or file.endswith('.txt'):
                log_files.append(file)
        return sorted(log_files)
    
    def display_log_preview(self, filename: str, lines: int = 10) -> None:
        """로그 파일 미리보기"""
        filepath = os.path.join(self.test_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines_content = f.readlines()
            
            print(f"\n📄 {filename} 미리보기 (처음 {min(lines, len(lines_content))}줄):")
            print("-" * 60)
            for i, line in enumerate(lines_content[:lines]):
                print(f"{i+1:3d}| {line.rstrip()}")
            if len(lines_content) > lines:
                print(f"... (총 {len(lines_content)}줄)")
            print("-" * 60)
        except Exception as e:
            print(f"❌ 파일 읽기 오류: {e}")
    
    def run_pipeline_test(self, log_file: str, use_vllm: bool = True) -> Dict:
        """파이프라인 테스트 실행"""
        print(f"\n🚀 {'vLLM' if use_vllm else '모의'} 파이프라인 테스트 시작...")
        
        # 파이프라인 스크립트 선택
        script_name = "log_llm_pipeline.py" if use_vllm else "test_pipeline.py"
        output_file = f"interactive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 스크립트 수정 (로그 파일 경로 변경)
        script_path = os.path.join(self.test_dir, script_name)
        temp_script_path = os.path.join(self.test_dir, f"temp_{script_name}")
        
        try:
            # 원본 스크립트 읽기
            with open(script_path, 'r') as f:
                content = f.read()
            
            # 로그 파일 경로 변경
            if "test_log.txt" in content:
                modified_content = content.replace("./test_log.txt", f"./{log_file}")
            else:
                # 다른 로그 파일이 이미 설정된 경우
                import re
                modified_content = re.sub(r'main\("\./[^"]+",', f'main("./{log_file}",', content)
            
            # 임시 스크립트 생성
            with open(temp_script_path, 'w') as f:
                f.write(modified_content)
            
            # 스크립트 실행
            result = subprocess.run([
                "python3", temp_script_path
            ], capture_output=True, text=True, cwd=self.test_dir, timeout=120)
            
            # 임시 파일 삭제
            os.remove(temp_script_path)
            
            if result.returncode == 0:
                print("✅ 파이프라인 테스트 성공!")
                print(f"출력: {result.stdout}")
                
                # 결과 파일 확인
                result_files = [f for f in os.listdir(self.test_dir) if f.startswith('analysis_results') or f.startswith('test_analysis_results')]
                if result_files:
                    latest_result = max(result_files, key=lambda x: os.path.getmtime(os.path.join(self.test_dir, x)))
                    return {"success": True, "result_file": latest_result, "output": result.stdout}
                else:
                    return {"success": True, "result_file": None, "output": result.stdout}
            else:
                print(f"❌ 파이프라인 테스트 실패: {result.stderr}")
                return {"success": False, "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            print("⏰ 테스트 시간 초과 (120초)")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"❌ 테스트 실행 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def display_analysis_result(self, result_file: str) -> None:
        """분석 결과 표시"""
        if not result_file:
            print("❌ 결과 파일을 찾을 수 없습니다.")
            return
        
        filepath = os.path.join(self.test_dir, result_file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            print(f"\n📊 분석 결과 ({result_file}):")
            print("=" * 80)
            
            for i, result in enumerate(results):
                meta = result.get('meta', {})
                analysis = result.get('analysis', '')
                
                print(f"\n🔍 윈도우 {i+1}/{len(results)}")
                print(f"서비스: {meta.get('service', 'N/A')}")
                print(f"호스트: {meta.get('host', 'N/A')}")
                print(f"시간: {meta.get('time_range', 'N/A')}")
                print("-" * 40)
                print(analysis)
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ 결과 파일 읽기 오류: {e}")
    
    def custom_log_input(self) -> str:
        """사용자 정의 로그 입력"""
        print("\n📝 직접 로그를 입력하세요 (완료하려면 빈 줄에서 Enter):")
        print("형식: YYYY-MM-DD HH:MM:SS LEVEL [SERVICE] MESSAGE")
        print("예시: 2024-01-15 10:30:15 ERROR [ordersvc] Database connection failed")
        print("-" * 60)
        
        logs = []
        line_num = 1
        
        while True:
            try:
                line = input(f"{line_num:3d}| ")
                if not line.strip():
                    break
                logs.append(line)
                line_num += 1
            except KeyboardInterrupt:
                print("\n입력이 취소되었습니다.")
                return None
        
        if not logs:
            print("❌ 입력된 로그가 없습니다.")
            return None
        
        # 임시 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"custom_log_{timestamp}.log"
        temp_filepath = os.path.join(self.test_dir, temp_filename)
        
        with open(temp_filepath, 'w') as f:
            f.write('\n'.join(logs))
        
        print(f"✅ 임시 로그 파일 생성: {temp_filename} ({len(logs)}줄)")
        return temp_filename
    
    def run_interactive_test(self):
        """대화형 테스트 실행"""
        print("🎯 대화형 로그 분석 테스트")
        print("=" * 50)
        
        # vLLM 서버 상태 확인
        vllm_available = self.check_vllm_server()
        print(f"vLLM 서버 상태: {'✅ 연결됨' if vllm_available else '❌ 연결 안됨'}")
        
        if not vllm_available:
            print("⚠️  vLLM 서버가 실행되지 않았습니다.")
            print("   서버를 시작하려면: ./start_qwen_server.sh")
            print("   모의 테스트만 가능합니다.")
        
        while True:
            print(f"\n{'='*50}")
            print("테스트 옵션을 선택하세요:")
            print("1. 기존 로그 파일로 테스트")
            print("2. 직접 로그 입력하여 테스트")
            print("3. 로그 파일 미리보기")
            print("4. 분석 결과 보기")
            print("5. 종료")
            
            choice = input("\n선택 (1-5): ").strip()
            
            if choice == "1":
                # 기존 로그 파일 테스트
                log_files = self.list_log_files()
                if not log_files:
                    print("❌ 사용 가능한 로그 파일이 없습니다.")
                    continue
                
                print(f"\n📁 사용 가능한 로그 파일:")
                for i, file in enumerate(log_files, 1):
                    print(f"  {i}. {file}")
                
                try:
                    file_choice = int(input(f"\n파일 선택 (1-{len(log_files)}): ")) - 1
                    if 0 <= file_choice < len(log_files):
                        selected_file = log_files[file_choice]
                        
                        # 테스트 타입 선택
                        if vllm_available:
                            test_type = input("테스트 타입 (1: vLLM, 2: 모의): ").strip()
                            use_vllm = test_type == "1"
                        else:
                            use_vllm = False
                            print("vLLM 서버가 없어 모의 테스트만 실행합니다.")
                        
                        result = self.run_pipeline_test(selected_file, use_vllm)
                        if result["success"] and result["result_file"]:
                            self.display_analysis_result(result["result_file"])
                    else:
                        print("❌ 잘못된 선택입니다.")
                except ValueError:
                    print("❌ 숫자를 입력해주세요.")
            
            elif choice == "2":
                # 직접 로그 입력
                custom_file = self.custom_log_input()
                if custom_file:
                    if vllm_available:
                        test_type = input("테스트 타입 (1: vLLM, 2: 모의): ").strip()
                        use_vllm = test_type == "1"
                    else:
                        use_vllm = False
                        print("vLLM 서버가 없어 모의 테스트만 실행합니다.")
                    
                    result = self.run_pipeline_test(custom_file, use_vllm)
                    if result["success"] and result["result_file"]:
                        self.display_analysis_result(result["result_file"])
            
            elif choice == "3":
                # 로그 파일 미리보기
                log_files = self.list_log_files()
                if not log_files:
                    print("❌ 사용 가능한 로그 파일이 없습니다.")
                    continue
                
                print(f"\n📁 로그 파일 목록:")
                for i, file in enumerate(log_files, 1):
                    print(f"  {i}. {file}")
                
                try:
                    file_choice = int(input(f"\n미리보기할 파일 선택 (1-{len(log_files)}): ")) - 1
                    if 0 <= file_choice < len(log_files):
                        selected_file = log_files[file_choice]
                        self.display_log_preview(selected_file)
                    else:
                        print("❌ 잘못된 선택입니다.")
                except ValueError:
                    print("❌ 숫자를 입력해주세요.")
            
            elif choice == "4":
                # 분석 결과 보기
                result_files = [f for f in os.listdir(self.test_dir) 
                              if f.startswith('analysis_results') or f.startswith('test_analysis_results') or f.startswith('interactive_analysis_')]
                
                if not result_files:
                    print("❌ 분석 결과 파일이 없습니다.")
                    continue
                
                print(f"\n📊 분석 결과 파일:")
                for i, file in enumerate(result_files, 1):
                    print(f"  {i}. {file}")
                
                try:
                    file_choice = int(input(f"\n보기할 파일 선택 (1-{len(result_files)}): ")) - 1
                    if 0 <= file_choice < len(result_files):
                        selected_file = result_files[file_choice]
                        self.display_analysis_result(selected_file)
                    else:
                        print("❌ 잘못된 선택입니다.")
                except ValueError:
                    print("❌ 숫자를 입력해주세요.")
            
            elif choice == "5":
                print("👋 테스트를 종료합니다.")
                break
            
            else:
                print("❌ 잘못된 선택입니다.")

def main():
    tester = InteractiveTester()
    tester.run_interactive_test()

if __name__ == "__main__":
    main()
