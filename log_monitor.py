#!/usr/bin/env python3
"""
로그 모니터링 시스템 - 실시간으로 생성되는 로그를 모니터링하고 분석
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

class LogMonitor:
    def __init__(self, log_file: str = "realtime.log"):
        self.log_file = log_file
        self.running = False
        self.last_position = 0
        self.analysis_interval = 30  # 30초마다 분석
        self.window_size = 50  # 분석할 로그 라인 수
        
        # 통계
        self.stats = {
            "total_logs": 0,
            "by_level": defaultdict(int),
            "by_service": defaultdict(int),
            "error_count": 0,
            "critical_count": 0,
            "last_analysis": None,
            "analysis_count": 0
        }
        
        # 최근 로그 저장 (슬라이딩 윈도우)
        self.recent_logs = deque(maxlen=1000)
        
        # 분석 결과 저장
        self.analysis_results = []
        
        # 알림 임계값
        self.thresholds = {
            "error_rate": 0.1,  # 10% 이상 에러
            "critical_count": 5,  # 5개 이상 크리티컬
            "analysis_trigger": 20  # 20개 이상 새 로그
        }
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """로그 라인 파싱"""
        # 형식: YYYY-MM-DD HH:MM:SS LEVEL [SERVICE] MESSAGE
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
                    self.recent_logs.append(parsed)
            
        except Exception as e:
            print(f"❌ 로그 읽기 오류: {e}")
        
        return new_logs
    
    def update_stats(self, logs: List[Dict]):
        """통계 업데이트"""
        for log in logs:
            self.stats["total_logs"] += 1
            self.stats["by_level"][log["level"]] += 1
            self.stats["by_service"][log["service"]] += 1
            
            if log["level"] == "ERROR":
                self.stats["error_count"] += 1
            elif log["level"] == "CRITICAL":
                self.stats["critical_count"] += 1
    
    def should_analyze(self, new_logs: List[Dict]) -> bool:
        """분석 필요 여부 확인"""
        # 새 로그가 충분히 쌓였거나
        if len(new_logs) >= self.thresholds["analysis_trigger"]:
            return True
        
        # 에러율이 임계값을 넘었거나
        if len(new_logs) > 0:
            error_count = sum(1 for log in new_logs if log["level"] in ["ERROR", "CRITICAL"])
            error_rate = error_count / len(new_logs)
            if error_rate >= self.thresholds["error_rate"]:
                return True
        
        # 크리티컬 로그가 임계값을 넘었거나
        critical_count = sum(1 for log in new_logs if log["level"] == "CRITICAL")
        if critical_count >= self.thresholds["critical_count"]:
            return True
        
        # 주기적 분석 (30초마다)
        if self.stats["last_analysis"] is None:
            return True
        
        elapsed = (datetime.now() - self.stats["last_analysis"]).total_seconds()
        if elapsed >= self.analysis_interval:
            return True
        
        return False
    
    def run_analysis(self, logs: List[Dict]) -> Dict:
        """로그 분석 실행"""
        print(f"🔍 로그 분석 실행 중... ({len(logs)}개 로그)")
        
        # 분석할 로그를 임시 파일로 저장
        temp_log_file = f"temp_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(temp_log_file, 'w', encoding='utf-8') as f:
            for log in logs:
                f.write(log["raw"] + "\n")
        
        try:
            # 파이프라인 스크립트 수정
            with open("log_llm_pipeline.py", 'r') as f:
                content = f.read()
            
            # 로그 파일 경로 변경
            modified_content = content.replace(
                'main("./scenario_1_데이터베이스_오류.log", "./analysis_results.json", meta)',
                f'main("./{temp_log_file}", "./temp_analysis_results.json", meta)'
            )
            
            temp_script = f"temp_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            with open(temp_script, 'w') as f:
                f.write(modified_content)
            
            # 분석 실행
            result = subprocess.run([
                "python3", temp_script
            ], capture_output=True, text=True, cwd=".", timeout=60)
            
            # 임시 파일 정리
            os.remove(temp_script)
            os.remove(temp_log_file)
            
            if result.returncode == 0:
                # 결과 읽기
                if os.path.exists("temp_analysis_results.json"):
                    with open("temp_analysis_results.json", 'r', encoding='utf-8') as f:
                        analysis_result = json.load(f)
                    os.remove("temp_analysis_results.json")
                    
                    return {
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "log_count": len(logs),
                        "analysis": analysis_result[0]["analysis"] if analysis_result else "분석 결과 없음"
                    }
                else:
                    return {"success": False, "error": "결과 파일 없음"}
            else:
                return {"success": False, "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "분석 시간 초과"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_alerts(self, new_logs: List[Dict]):
        """알림 체크"""
        alerts = []
        
        # 에러율 체크
        if len(new_logs) > 0:
            error_count = sum(1 for log in new_logs if log["level"] in ["ERROR", "CRITICAL"])
            error_rate = error_count / len(new_logs)
            if error_rate >= self.thresholds["error_rate"]:
                alerts.append(f"🚨 높은 에러율: {error_rate:.1%}")
        
        # 크리티컬 로그 체크
        critical_count = sum(1 for log in new_logs if log["level"] == "CRITICAL")
        if critical_count >= self.thresholds["critical_count"]:
            alerts.append(f"🚨 크리티컬 로그 다수: {critical_count}개")
        
        # 특정 서비스 에러 체크
        service_errors = defaultdict(int)
        for log in new_logs:
            if log["level"] in ["ERROR", "CRITICAL"]:
                service_errors[log["service"]] += 1
        
        for service, count in service_errors.items():
            if count >= 5:
                alerts.append(f"🚨 {service} 서비스 에러 다수: {count}개")
        
        return alerts
    
    def print_status(self):
        """상태 출력"""
        print(f"\n📊 로그 모니터링 상태")
        print(f"총 로그: {self.stats['total_logs']}개")
        print(f"분석 횟수: {self.stats['analysis_count']}회")
        
        if self.stats['last_analysis']:
            elapsed = (datetime.now() - self.stats['last_analysis']).total_seconds()
            print(f"마지막 분석: {elapsed:.0f}초 전")
        
        print("레벨별 분포:")
        for level, count in self.stats['by_level'].items():
            if count > 0:
                percentage = (count / self.stats['total_logs']) * 100
                print(f"  {level}: {count}개 ({percentage:.1f}%)")
        
        # 상위 3개 서비스
        top_services = sorted(self.stats['by_service'].items(), key=lambda x: x[1], reverse=True)[:3]
        print("상위 서비스:")
        for service, count in top_services:
            if count > 0:
                print(f"  {service}: {count}개")
    
    def save_analysis_result(self, result: Dict):
        """분석 결과 저장"""
        self.analysis_results.append(result)
        
        # 결과를 파일로 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"monitor_analysis_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 분석 결과 저장: {result_file}")
    
    def start_monitoring(self):
        """모니터링 시작"""
        print(f"🔍 로그 모니터링 시작")
        print(f"모니터링 파일: {self.log_file}")
        print(f"분석 간격: {self.analysis_interval}초")
        print("중단하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        self.running = True
        last_status_time = time.time()
        
        try:
            while self.running:
                # 새로운 로그 읽기
                new_logs = self.read_new_logs()
                
                if new_logs:
                    print(f"📝 새 로그 {len(new_logs)}개 감지")
                    
                    # 통계 업데이트
                    self.update_stats(new_logs)
                    
                    # 알림 체크
                    alerts = self.check_alerts(new_logs)
                    for alert in alerts:
                        print(alert)
                    
                    # 분석 필요 여부 확인
                    if self.should_analyze(new_logs):
                        # 최근 로그로 분석 실행
                        analysis_logs = list(self.recent_logs)[-self.window_size:]
                        result = self.run_analysis(analysis_logs)
                        
                        if result["success"]:
                            print("✅ 분석 완료")
                            self.save_analysis_result(result)
                        else:
                            print(f"❌ 분석 실패: {result['error']}")
                        
                        self.stats["analysis_count"] += 1
                        self.stats["last_analysis"] = datetime.now()
                
                # 상태 출력 (30초마다)
                if time.time() - last_status_time >= 30:
                    self.print_status()
                    last_status_time = time.time()
                
                # 1초 대기
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 모니터링 중단")
        finally:
            self.running = False
            self.print_status()
            
            # 최종 통계 저장
            stats_file = f"monitor_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.stats), f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 모니터링 통계 저장: {stats_file}")

def main():
    print("🔍 로그 모니터링 시스템")
    print("=" * 50)
    
    # 설정 입력
    log_file = input("모니터링할 로그 파일 (기본: realtime.log): ").strip() or "realtime.log"
    
    try:
        analysis_interval = int(input("분석 간격(초) (기본: 30): ").strip() or "30")
    except ValueError:
        analysis_interval = 30
    
    try:
        window_size = int(input("분석 윈도우 크기 (기본: 50): ").strip() or "50")
    except ValueError:
        window_size = 50
    
    # 모니터 생성 및 시작
    monitor = LogMonitor(log_file)
    monitor.analysis_interval = analysis_interval
    monitor.window_size = window_size
    
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
