#!/usr/bin/env python3
"""
자동 분석 시스템 - 실시간 로그를 자동으로 분석하고 결과를 저장
"""

import os
import time
import json
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from collections import defaultdict, deque
import requests

class AutoAnalyzer:
    def __init__(self, log_file: str = "realtime.log"):
        self.log_file = log_file
        self.running = False
        self.last_position = 0
        self.analysis_interval = 60  # 1분마다 분석
        self.min_logs_for_analysis = 20  # 최소 로그 수
        self.max_logs_per_analysis = 100  # 분석당 최대 로그 수
        
        # vLLM 서버 설정
        self.vllm_url = "http://127.0.0.1:8000/v1"
        self.model_name = "Qwen/Qwen2.5-7B-Instruct"
        self.vllm_available = False
        
        # 분석 결과 저장
        self.analysis_history = deque(maxlen=100)  # 최근 100개 분석 결과
        self.analysis_count = 0
        
        # 통계
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "total_logs_analyzed": 0,
            "start_time": datetime.now()
        }
        
        # 분석 임계값
        self.thresholds = {
            "error_rate": 0.15,  # 15% 이상 에러
            "critical_count": 3,  # 3개 이상 크리티컬
            "warning_count": 10,  # 10개 이상 경고
            "service_errors": 5   # 서비스당 5개 이상 에러
        }
    
    def check_vllm_server(self) -> bool:
        """vLLM 서버 상태 확인"""
        try:
            response = requests.get(f"{self.vllm_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """로그 라인 파싱"""
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) \[(\w+)\] (.+)'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp_str, level, service, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            return {
                "timestamp": timestamp,
                "level": level,
                "service": service,
                "message": message,
                "raw": line.strip()
            }
        return None
    
    def read_new_logs(self) -> List[Dict]:
        """새로운 로그 읽기"""
        new_logs = []
        
        try:
            if not os.path.exists(self.log_file):
                return new_logs
            
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()
            
            for line in lines:
                parsed = self.parse_log_line(line)
                if parsed:
                    new_logs.append(parsed)
            
        except Exception as e:
            print(f"❌ 로그 읽기 오류: {e}")
        
        return new_logs
    
    def should_analyze(self, logs: List[Dict]) -> bool:
        """분석 필요 여부 확인"""
        if len(logs) < self.min_logs_for_analysis:
            return False
        
        # 에러율 체크
        error_count = sum(1 for log in logs if log["level"] in ["ERROR", "CRITICAL"])
        error_rate = error_count / len(logs)
        if error_rate >= self.thresholds["error_rate"]:
            return True
        
        # 크리티컬 로그 체크
        critical_count = sum(1 for log in logs if log["level"] == "CRITICAL")
        if critical_count >= self.thresholds["critical_count"]:
            return True
        
        # 경고 로그 체크
        warning_count = sum(1 for log in logs if log["level"] == "WARN")
        if warning_count >= self.thresholds["warning_count"]:
            return True
        
        # 서비스별 에러 체크
        service_errors = defaultdict(int)
        for log in logs:
            if log["level"] in ["ERROR", "CRITICAL"]:
                service_errors[log["service"]] += 1
        
        for service, count in service_errors.items():
            if count >= self.thresholds["service_errors"]:
                return True
        
        return False
    
    def analyze_with_vllm(self, logs: List[Dict]) -> Dict:
        """vLLM을 사용한 분석"""
        try:
            # 로그를 텍스트로 변환
            log_text = "\n".join([log["raw"] for log in logs])
            
            # 분석 요청
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an SRE/DevOps log expert. Analyze the logs and provide: (1) key symptoms, (2) root-cause hypotheses with priority, (3) concrete shell commands to verify, (4) mitigations/preventions, (5) confidence level. Keep answers concise but actionable."
                    },
                    {
                        "role": "user", 
                        "content": f"Analyze these logs:\n\n{log_text}"
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1200
            }
            
            response = requests.post(
                f"{self.vllm_url}/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                return {"success": True, "analysis": analysis}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_with_pipeline(self, logs: List[Dict]) -> Dict:
        """파이프라인을 사용한 분석"""
        try:
            # 임시 로그 파일 생성
            temp_log_file = f"temp_auto_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(temp_log_file, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(log["raw"] + "\n")
            
            # 파이프라인 스크립트 수정
            with open("log_llm_pipeline.py", 'r') as f:
                content = f.read()
            
            modified_content = content.replace(
                'main("./scenario_1_데이터베이스_오류.log", "./analysis_results.json", meta)',
                f'main("./{temp_log_file}", "./temp_auto_analysis_results.json", meta)'
            )
            
            temp_script = f"temp_auto_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            with open(temp_script, 'w') as f:
                f.write(modified_content)
            
            # 분석 실행
            result = subprocess.run([
                "python3", temp_script
            ], capture_output=True, text=True, cwd=".", timeout=120)
            
            # 임시 파일 정리
            os.remove(temp_script)
            os.remove(temp_log_file)
            
            if result.returncode == 0 and os.path.exists("temp_auto_analysis_results.json"):
                with open("temp_auto_analysis_results.json", 'r', encoding='utf-8') as f:
                    analysis_result = json.load(f)
                os.remove("temp_auto_analysis_results.json")
                
                return {
                    "success": True, 
                    "analysis": analysis_result[0]["analysis"] if analysis_result else "분석 결과 없음"
                }
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_analysis(self, logs: List[Dict]) -> Dict:
        """분석 실행"""
        print(f"🔍 자동 분석 실행 중... ({len(logs)}개 로그)")
        
        # vLLM 서버 사용 가능 여부 확인
        if self.vllm_available:
            result = self.analyze_with_vllm(logs)
        else:
            result = self.analyze_with_pipeline(logs)
        
        # 통계 업데이트
        self.stats["total_analyses"] += 1
        if result["success"]:
            self.stats["successful_analyses"] += 1
        else:
            self.stats["failed_analyses"] += 1
        
        self.stats["total_logs_analyzed"] += len(logs)
        
        return result
    
    def save_analysis_result(self, logs: List[Dict], analysis_result: Dict):
        """분석 결과 저장"""
        self.analysis_count += 1
        
        result = {
            "analysis_id": self.analysis_count,
            "timestamp": datetime.now().isoformat(),
            "log_count": len(logs),
            "log_time_range": {
                "start": logs[0]["timestamp"].isoformat() if logs else None,
                "end": logs[-1]["timestamp"].isoformat() if logs else None
            },
            "log_summary": {
                "total": len(logs),
                "by_level": defaultdict(int),
                "by_service": defaultdict(int)
            },
            "analysis": analysis_result.get("analysis", "분석 실패"),
            "success": analysis_result["success"]
        }
        
        # 로그 요약 생성
        for log in logs:
            result["log_summary"]["by_level"][log["level"]] += 1
            result["log_summary"]["by_service"][log["service"]] += 1
        
        # 히스토리에 추가
        self.analysis_history.append(result)
        
        # 파일로 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"auto_analysis_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 자동 분석 결과 저장: {result_file}")
        
        # 분석 결과 요약 출력
        if analysis_result["success"]:
            print("✅ 분석 완료")
            # 분석 결과의 첫 200자만 출력
            analysis_preview = analysis_result["analysis"][:200] + "..." if len(analysis_result["analysis"]) > 200 else analysis_result["analysis"]
            print(f"📋 분석 요약: {analysis_preview}")
        else:
            print(f"❌ 분석 실패: {analysis_result['error']}")
    
    def print_status(self):
        """상태 출력"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        success_rate = (self.stats["successful_analyses"] / max(self.stats["total_analyses"], 1)) * 100
        
        print(f"\n📊 자동 분석 상태")
        print(f"실행 시간: {elapsed:.0f}초")
        print(f"총 분석: {self.stats['total_analyses']}회")
        print(f"성공: {self.stats['successful_analyses']}회 ({success_rate:.1f}%)")
        print(f"실패: {self.stats['failed_analyses']}회")
        print(f"분석된 로그: {self.stats['total_logs_analyzed']}개")
        print(f"vLLM 서버: {'✅ 연결됨' if self.vllm_available else '❌ 연결 안됨'}")
    
    def start_auto_analysis(self):
        """자동 분석 시작"""
        print(f"🤖 자동 분석 시스템 시작")
        print(f"모니터링 파일: {self.log_file}")
        print(f"분석 간격: {self.analysis_interval}초")
        print(f"최소 로그 수: {self.min_logs_for_analysis}개")
        print("중단하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        self.running = True
        last_status_time = time.time()
        accumulated_logs = []
        
        try:
            while self.running:
                # vLLM 서버 상태 확인 (1분마다)
                if time.time() - last_status_time >= 60:
                    self.vllm_available = self.check_vllm_server()
                    last_status_time = time.time()
                
                # 새로운 로그 읽기
                new_logs = self.read_new_logs()
                
                if new_logs:
                    accumulated_logs.extend(new_logs)
                    print(f"📝 새 로그 {len(new_logs)}개 감지 (누적: {len(accumulated_logs)}개)")
                    
                    # 분석 필요 여부 확인
                    if self.should_analyze(accumulated_logs):
                        # 분석할 로그 선택 (최근 로그)
                        analysis_logs = accumulated_logs[-self.max_logs_per_analysis:]
                        
                        # 분석 실행
                        analysis_result = self.run_analysis(analysis_logs)
                        
                        # 결과 저장
                        self.save_analysis_result(analysis_logs, analysis_result)
                        
                        # 누적 로그 초기화
                        accumulated_logs = []
                
                # 상태 출력 (5분마다)
                if time.time() - last_status_time >= 300:
                    self.print_status()
                    last_status_time = time.time()
                
                # 10초 대기
                time.sleep(10)
                
        except KeyboardInterrupt:
            print(f"\n🛑 자동 분석 중단")
        finally:
            self.running = False
            self.print_status()
            
            # 최종 통계 저장
            stats_file = f"auto_analysis_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 자동 분석 통계 저장: {stats_file}")

def main():
    print("🤖 자동 분석 시스템")
    print("=" * 50)
    
    # 설정 입력
    log_file = input("모니터링할 로그 파일 (기본: realtime.log): ").strip() or "realtime.log"
    
    try:
        analysis_interval = int(input("분석 간격(초) (기본: 60): ").strip() or "60")
    except ValueError:
        analysis_interval = 60
    
    try:
        min_logs = int(input("최소 로그 수 (기본: 20): ").strip() or "20")
    except ValueError:
        min_logs = 20
    
    try:
        max_logs = int(input("분석당 최대 로그 수 (기본: 100): ").strip() or "100")
    except ValueError:
        max_logs = 100
    
    # 분석기 생성 및 시작
    analyzer = AutoAnalyzer(log_file)
    analyzer.analysis_interval = analysis_interval
    analyzer.min_logs_for_analysis = min_logs
    analyzer.max_logs_per_analysis = max_logs
    
    analyzer.start_auto_analysis()

if __name__ == "__main__":
    main()
