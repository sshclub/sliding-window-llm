#!/usr/bin/env python3
"""
실시간 로그 생성기 - 실제 운영 환경처럼 로그가 지속적으로 생성되는 시스템
"""

import time
import random
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict
import json
import os

class RealTimeLogger:
    def __init__(self, log_file: str = "realtime.log"):
        self.log_file = log_file
        self.running = False
        self.services = [
            "ordersvc", "paymentsvc", "usersvc", "inventorysvc", 
            "notificationsvc", "analyticsvc", "authsvc", "gateway",
            "apigateway", "websocket", "scheduler", "worker"
        ]
        self.hosts = ["node-01", "node-02", "node-03", "web-01", "web-02", "db-01", "cache-01"]
        self.levels = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
        self.users = ["user123", "admin", "guest", "service_account", "api_user", "bot"]
        
        # 로그 패턴 정의
        self.log_patterns = {
            "normal": {
                "weight": 70,
                "messages": [
                    "Request processed successfully",
                    "User login successful", 
                    "Data synchronized",
                    "Cache updated",
                    "Health check passed",
                    "API response time: {time}ms",
                    "Database query executed: {time}ms",
                    "File uploaded successfully",
                    "Email sent to {user}",
                    "Background job completed"
                ]
            },
            "warning": {
                "weight": 20,
                "messages": [
                    "High memory usage detected: {usage}%",
                    "Slow query detected: {time}s",
                    "Rate limit approaching",
                    "Disk space low: {usage}%",
                    "Connection pool 80% full",
                    "API response time high: {time}ms",
                    "Cache miss rate high: {rate}%",
                    "Network latency increasing",
                    "Queue size growing: {size}",
                    "Resource usage high: {usage}%"
                ]
            },
            "error": {
                "weight": 8,
                "messages": [
                    "Database connection failed",
                    "API request timeout",
                    "File not found: {file}",
                    "Permission denied",
                    "Network unreachable",
                    "Service unavailable",
                    "Authentication failed for user {user}",
                    "OutOfMemoryError in worker thread",
                    "Disk I/O error",
                    "External service timeout"
                ]
            },
            "critical": {
                "weight": 2,
                "messages": [
                    "Service down - all workers failed",
                    "Database cluster failure",
                    "Critical security breach detected",
                    "System overload - shutting down",
                    "Data corruption detected",
                    "Network partition occurred",
                    "All backup systems failed",
                    "Emergency shutdown initiated"
                ]
            }
        }
        
        # 시나리오 상태 관리
        self.scenario_states = {
            "normal": 0.8,      # 80% 정상 상태
            "degraded": 0.15,   # 15% 성능 저하
            "critical": 0.05    # 5% 크리티컬 상태
        }
        self.current_scenario = "normal"
        self.scenario_start_time = datetime.now()
        
        # 통계
        self.stats = {
            "total_logs": 0,
            "by_level": {"DEBUG": 0, "INFO": 0, "WARN": 0, "ERROR": 0, "CRITICAL": 0},
            "by_service": {service: 0 for service in self.services},
            "start_time": datetime.now()
        }
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러 - 정상 종료"""
        print(f"\n🛑 시그널 {signum} 수신, 로그 생성 중단 중...")
        self.running = False
        self.print_final_stats()
        sys.exit(0)
    
    def get_current_scenario(self) -> str:
        """현재 시나리오 결정"""
        elapsed = (datetime.now() - self.scenario_start_time).total_seconds()
        
        # 시나리오 변경 조건
        if elapsed > 300:  # 5분마다 시나리오 변경
            self.scenario_start_time = datetime.now()
            rand = random.random()
            if rand < 0.7:
                self.current_scenario = "normal"
            elif rand < 0.9:
                self.current_scenario = "degraded"
            else:
                self.current_scenario = "critical"
        
        return self.current_scenario
    
    def generate_log_entry(self) -> str:
        """단일 로그 엔트리 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        service = random.choice(self.services)
        host = random.choice(self.hosts)
        
        # 시나리오에 따른 로그 패턴 선택
        scenario = self.get_current_scenario()
        
        if scenario == "normal":
            pattern_type = random.choices(
                ["normal", "warning", "error", "critical"],
                weights=[70, 20, 8, 2]
            )[0]
        elif scenario == "degraded":
            pattern_type = random.choices(
                ["normal", "warning", "error", "critical"],
                weights=[40, 40, 18, 2]
            )[0]
        else:  # critical
            pattern_type = random.choices(
                ["normal", "warning", "error", "critical"],
                weights=[10, 30, 40, 20]
            )[0]
        
        # 로그 레벨 결정
        if pattern_type == "normal":
            level = random.choices(["DEBUG", "INFO"], weights=[20, 80])[0]
        elif pattern_type == "warning":
            level = "WARN"
        elif pattern_type == "error":
            level = "ERROR"
        else:
            level = "CRITICAL"
        
        # 메시지 생성
        message_template = random.choice(self.log_patterns[pattern_type]["messages"])
        
        # 템플릿 변수 치환
        message = message_template.format(
            time=random.randint(50, 2000),
            usage=random.randint(70, 95),
            rate=random.randint(60, 90),
            size=random.randint(100, 1000),
            user=random.choice(self.users),
            file=f"/var/log/{random.choice(['app', 'system', 'error'])}.log"
        )
        
        log_entry = f"{timestamp} {level} [{service}] {message}"
        
        # 통계 업데이트
        self.stats["total_logs"] += 1
        self.stats["by_level"][level] += 1
        self.stats["by_service"][service] += 1
        
        return log_entry
    
    def write_log(self, log_entry: str):
        """로그 파일에 쓰기"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"❌ 로그 쓰기 오류: {e}")
    
    def print_stats(self):
        """통계 출력"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        logs_per_second = self.stats["total_logs"] / elapsed if elapsed > 0 else 0
        
        print(f"\n📊 실시간 로그 통계 (경과: {elapsed:.0f}초)")
        print(f"총 로그: {self.stats['total_logs']}개 ({logs_per_second:.1f} 로그/초)")
        print(f"현재 시나리오: {self.current_scenario}")
        print("레벨별 분포:")
        for level, count in self.stats["by_level"].items():
            if count > 0:
                percentage = (count / self.stats["total_logs"]) * 100
                print(f"  {level}: {count}개 ({percentage:.1f}%)")
        
        # 상위 3개 서비스
        top_services = sorted(self.stats["by_service"].items(), key=lambda x: x[1], reverse=True)[:3]
        print("상위 서비스:")
        for service, count in top_services:
            if count > 0:
                print(f"  {service}: {count}개")
    
    def print_final_stats(self):
        """최종 통계 출력"""
        print(f"\n🏁 로그 생성 완료!")
        print(f"총 생성된 로그: {self.stats['total_logs']}개")
        print(f"로그 파일: {self.log_file}")
        
        # 통계를 JSON 파일로 저장
        stats_file = f"log_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2, default=str)
        print(f"통계 저장: {stats_file}")
    
    def start_logging(self, interval: float = 1.0, max_logs: int = None):
        """로그 생성 시작"""
        print(f"🚀 실시간 로그 생성 시작")
        print(f"로그 파일: {self.log_file}")
        print(f"생성 간격: {interval}초")
        if max_logs:
            print(f"최대 로그 수: {max_logs}개")
        print("중단하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        self.running = True
        log_count = 0
        
        try:
            while self.running:
                # 로그 생성 및 쓰기
                log_entry = self.generate_log_entry()
                self.write_log(log_entry)
                log_count += 1
                
                # 통계 출력 (10초마다)
                if log_count % 10 == 0:
                    self.print_stats()
                
                # 최대 로그 수 체크
                if max_logs and log_count >= max_logs:
                    print(f"\n✅ 최대 로그 수({max_logs})에 도달했습니다.")
                    break
                
                # 대기
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 사용자에 의해 중단되었습니다.")
        finally:
            self.running = False
            self.print_final_stats()

class LogRotator:
    """로그 로테이션 관리"""
    
    def __init__(self, base_file: str = "realtime.log", max_size_mb: int = 10):
        self.base_file = base_file
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.rotation_count = 0
    
    def should_rotate(self) -> bool:
        """로테이션 필요 여부 확인"""
        if not os.path.exists(self.base_file):
            return False
        
        file_size = os.path.getsize(self.base_file)
        return file_size >= self.max_size_bytes
    
    def rotate(self):
        """로그 파일 로테이션"""
        if not self.should_rotate():
            return
        
        self.rotation_count += 1
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated_file = f"{self.base_file}.{timestamp}.{self.rotation_count}"
        
        try:
            os.rename(self.base_file, rotated_file)
            print(f"🔄 로그 로테이션: {self.base_file} -> {rotated_file}")
        except Exception as e:
            print(f"❌ 로그 로테이션 실패: {e}")

def main():
    print("🔧 실시간 로그 생성기")
    print("=" * 50)
    
    # 설정 입력
    log_file = input("로그 파일명 (기본: realtime.log): ").strip() or "realtime.log"
    
    try:
        interval = float(input("생성 간격(초) (기본: 1.0): ").strip() or "1.0")
    except ValueError:
        interval = 1.0
    
    max_logs_input = input("최대 로그 수 (무제한: Enter): ").strip()
    max_logs = int(max_logs_input) if max_logs_input else None
    
    # 로그 로테이션 설정
    enable_rotation = input("로그 로테이션 활성화? (y/N): ").strip().lower() == 'y'
    max_size_mb = 10
    if enable_rotation:
        try:
            max_size_mb = int(input("최대 파일 크기(MB) (기본: 10): ").strip() or "10")
        except ValueError:
            max_size_mb = 10
    
    # 로거 생성 및 시작
    logger = RealTimeLogger(log_file)
    rotator = LogRotator(log_file, max_size_mb) if enable_rotation else None
    
    # 로테이션 체크 스레드
    if rotator:
        def rotation_check():
            while logger.running:
                rotator.rotate()
                time.sleep(30)  # 30초마다 체크
        
        rotation_thread = threading.Thread(target=rotation_check, daemon=True)
        rotation_thread.start()
    
    # 로그 생성 시작
    logger.start_logging(interval, max_logs)

if __name__ == "__main__":
    main()
