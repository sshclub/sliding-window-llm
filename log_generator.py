#!/usr/bin/env python3
"""
실제 로그 생성기 - 다양한 시나리오의 로그를 생성하여 테스트
"""

import random
import time
from datetime import datetime, timedelta
from typing import List, Dict
import json

class LogGenerator:
    def __init__(self):
        self.services = [
            "ordersvc", "paymentsvc", "usersvc", "inventorysvc", 
            "notificationsvc", "analyticsvc", "authsvc", "gateway"
        ]
        self.hosts = ["node-01", "node-02", "node-03", "web-01", "web-02", "db-01"]
        self.levels = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
        self.users = ["user123", "admin", "guest", "service_account", "api_user"]
        
    def generate_timestamp(self, base_time: datetime = None, offset_minutes: int = 0) -> str:
        """타임스탬프 생성"""
        if base_time is None:
            base_time = datetime.now()
        timestamp = base_time + timedelta(minutes=offset_minutes)
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_database_error_scenario(self, duration_minutes: int = 30) -> List[str]:
        """데이터베이스 오류 시나리오"""
        logs = []
        base_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # 정상 상태
        for i in range(5):
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [{random.choice(self.services)}] Service running normally")
        
        # 경고 시작
        logs.append(f"{self.generate_timestamp(base_time, 5)} WARN [{random.choice(self.services)}] Database connection pool 80% full")
        logs.append(f"{self.generate_timestamp(base_time, 6)} WARN [{random.choice(self.services)}] Slow query detected: 2.5s")
        
        # 오류 시작
        for i in range(7, 12):
            logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [{random.choice(self.services)}] Database connection timeout after 30s")
            logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] Retrying connection attempt {i-6}/3")
        
        # 심각한 오류
        logs.append(f"{self.generate_timestamp(base_time, 12)} CRITICAL [{random.choice(self.services)}] All database connections failed")
        logs.append(f"{self.generate_timestamp(base_time, 13)} ERROR [{random.choice(self.services)}] Service degraded - read-only mode")
        
        # 복구 시도
        for i in range(14, 18):
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [{random.choice(self.services)}] Attempting database recovery")
            logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] Recovery attempt {i-13} failed")
        
        # 복구 성공
        logs.append(f"{self.generate_timestamp(base_time, 18)} INFO [{random.choice(self.services)}] Database connection restored")
        logs.append(f"{self.generate_timestamp(base_time, 19)} INFO [{random.choice(self.services)}] Service fully operational")
        
        return logs
    
    def generate_memory_leak_scenario(self, duration_minutes: int = 45) -> List[str]:
        """메모리 누수 시나리오"""
        logs = []
        base_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # 정상 시작
        for i in range(10):
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [{random.choice(self.services)}] Memory usage: {random.randint(20, 40)}%")
        
        # 점진적 증가
        for i in range(10, 25):
            memory_usage = 40 + (i - 10) * 2
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [{random.choice(self.services)}] Memory usage: {memory_usage}%")
            if memory_usage > 60:
                logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] High memory usage detected")
        
        # 위험 수준
        for i in range(25, 35):
            memory_usage = 70 + (i - 25) * 3
            logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [{random.choice(self.services)}] Memory usage: {memory_usage}%")
            logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] GC pressure increasing")
        
        # 크리티컬
        logs.append(f"{self.generate_timestamp(base_time, 35)} CRITICAL [{random.choice(self.services)}] Memory usage: 95%")
        logs.append(f"{self.generate_timestamp(base_time, 36)} ERROR [{random.choice(self.services)}] OutOfMemoryError in worker thread")
        logs.append(f"{self.generate_timestamp(base_time, 37)} CRITICAL [{random.choice(self.services)}] Service restarting due to memory pressure")
        
        # 재시작 후
        logs.append(f"{self.generate_timestamp(base_time, 38)} INFO [{random.choice(self.services)}] Service restarted")
        logs.append(f"{self.generate_timestamp(base_time, 39)} INFO [{random.choice(self.services)}] Memory usage: 25%")
        
        return logs
    
    def generate_network_issue_scenario(self, duration_minutes: int = 20) -> List[str]:
        """네트워크 이슈 시나리오"""
        logs = []
        base_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # 정상 상태
        for i in range(5):
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [{random.choice(self.services)}] API response time: {random.randint(50, 150)}ms")
        
        # 지연 시작
        for i in range(5, 10):
            logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] API response time: {random.randint(200, 500)}ms")
            logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] Network latency increasing")
        
        # 타임아웃
        for i in range(10, 15):
            logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [{random.choice(self.services)}] API request timeout after 30s")
            logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [{random.choice(self.services)}] Connection refused to external service")
        
        # 복구
        logs.append(f"{self.generate_timestamp(base_time, 15)} INFO [{random.choice(self.services)}] Network connectivity restored")
        logs.append(f"{self.generate_timestamp(base_time, 16)} INFO [{random.choice(self.services)}] API response time: 120ms")
        
        return logs
    
    def generate_security_incident_scenario(self, duration_minutes: int = 15) -> List[str]:
        """보안 사고 시나리오"""
        logs = []
        base_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # 의심스러운 활동
        logs.append(f"{self.generate_timestamp(base_time, 0)} WARN [{random.choice(self.services)}] Multiple failed login attempts from IP 192.168.1.100")
        logs.append(f"{self.generate_timestamp(base_time, 1)} WARN [{random.choice(self.services)}] Unusual API usage pattern detected")
        
        # 공격 시도
        for i in range(2, 8):
            logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [{random.choice(self.services)}] SQL injection attempt detected")
            logs.append(f"{self.generate_timestamp(base_time, i)} WARN [{random.choice(self.services)}] Rate limit exceeded for IP 192.168.1.100")
        
        # 차단
        logs.append(f"{self.generate_timestamp(base_time, 8)} INFO [{random.choice(self.services)}] IP 192.168.1.100 blocked for 1 hour")
        logs.append(f"{self.generate_timestamp(base_time, 9)} INFO [{random.choice(self.services)}] Security incident resolved")
        
        return logs
    
    def generate_mixed_scenario(self, duration_minutes: int = 60) -> List[str]:
        """복합 시나리오 (여러 문제가 동시에 발생)"""
        logs = []
        base_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # 정상 상태
        for i in range(10):
            service = random.choice(self.services)
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [{service}] Service running normally")
        
        # 문제 시작
        logs.append(f"{self.generate_timestamp(base_time, 10)} WARN [ordersvc] Database connection pool 85% full")
        logs.append(f"{self.generate_timestamp(base_time, 11)} ERROR [paymentsvc] Payment gateway timeout")
        logs.append(f"{self.generate_timestamp(base_time, 12)} WARN [usersvc] High CPU usage: 90%")
        
        # 연쇄 반응
        for i in range(13, 25):
            if i % 3 == 0:
                logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [ordersvc] Database connection failed")
            if i % 4 == 0:
                logs.append(f"{self.generate_timestamp(base_time, i)} WARN [paymentsvc] Payment processing delayed")
            if i % 5 == 0:
                logs.append(f"{self.generate_timestamp(base_time, i)} ERROR [usersvc] Memory usage: {70 + (i-13)*2}%")
        
        # 크리티컬 상황
        logs.append(f"{self.generate_timestamp(base_time, 25)} CRITICAL [ordersvc] Service unavailable")
        logs.append(f"{self.generate_timestamp(base_time, 26)} CRITICAL [paymentsvc] Payment system down")
        logs.append(f"{self.generate_timestamp(base_time, 27)} ERROR [usersvc] OutOfMemoryError")
        
        # 복구 시도
        for i in range(28, 35):
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [ordersvc] Attempting service recovery")
            logs.append(f"{self.generate_timestamp(base_time, i)} INFO [paymentsvc] Restarting payment gateway")
        
        # 복구 완료
        logs.append(f"{self.generate_timestamp(base_time, 35)} INFO [ordersvc] Service restored")
        logs.append(f"{self.generate_timestamp(base_time, 36)} INFO [paymentsvc] Payment system operational")
        logs.append(f"{self.generate_timestamp(base_time, 37)} INFO [usersvc] Memory usage: 30%")
        
        return logs
    
    def generate_large_volume_logs(self, num_lines: int = 1000) -> List[str]:
        """대용량 로그 생성"""
        logs = []
        base_time = datetime.now() - timedelta(hours=2)
        
        for i in range(num_lines):
            service = random.choice(self.services)
            level = random.choices(self.levels, weights=[10, 60, 20, 8, 2])[0]
            timestamp = self.generate_timestamp(base_time, i)
            
            if level == "ERROR":
                messages = [
                    "Database connection failed",
                    "API request timeout",
                    "File not found",
                    "Permission denied",
                    "Network unreachable"
                ]
                message = random.choice(messages)
            elif level == "WARN":
                messages = [
                    "High memory usage detected",
                    "Slow query detected",
                    "Rate limit approaching",
                    "Disk space low",
                    "Connection pool 80% full"
                ]
                message = random.choice(messages)
            else:
                messages = [
                    "Request processed successfully",
                    "User login successful",
                    "Data synchronized",
                    "Cache updated",
                    "Health check passed"
                ]
                message = random.choice(messages)
            
            logs.append(f"{timestamp} {level} [{service}] {message}")
        
        return logs

def main():
    generator = LogGenerator()
    
    print("🔧 실제 로그 생성기")
    print("=" * 50)
    
    scenarios = {
        "1": ("데이터베이스 오류", generator.generate_database_error_scenario),
        "2": ("메모리 누수", generator.generate_memory_leak_scenario),
        "3": ("네트워크 이슈", generator.generate_network_issue_scenario),
        "4": ("보안 사고", generator.generate_security_incident_scenario),
        "5": ("복합 시나리오", generator.generate_mixed_scenario),
        "6": ("대용량 로그", lambda: generator.generate_large_volume_logs(500)),
        "7": ("모든 시나리오", None)
    }
    
    print("생성할 로그 시나리오를 선택하세요:")
    for key, (name, _) in scenarios.items():
        print(f"  {key}. {name}")
    
    choice = input("\n선택 (1-7): ").strip()
    
    if choice == "7":
        # 모든 시나리오 생성
        for key, (name, func) in scenarios.items():
            if key != "7" and func:
                print(f"\n📝 {name} 로그 생성 중...")
                logs = func()
                filename = f"scenario_{key}_{name.replace(' ', '_').lower()}.log"
                with open(filename, "w") as f:
                    f.write("\n".join(logs))
                print(f"✅ {filename} 생성 완료 ({len(logs)}줄)")
    elif choice in scenarios and scenarios[choice][1]:
        name, func = scenarios[choice]
        print(f"\n📝 {name} 로그 생성 중...")
        logs = func()
        filename = f"scenario_{choice}_{name.replace(' ', '_').lower()}.log"
        with open(filename, "w") as f:
            f.write("\n".join(logs))
        print(f"✅ {filename} 생성 완료 ({len(logs)}줄)")
    else:
        print("❌ 잘못된 선택입니다.")
        return
    
    print(f"\n🎯 생성된 로그 파일들을 테스트하려면:")
    print("python3 interactive_test.py")

if __name__ == "__main__":
    main()
