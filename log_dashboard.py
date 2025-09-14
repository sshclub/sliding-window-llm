#!/usr/bin/env python3
"""
로그 대시보드 - 실시간 로그 생성과 분석 상태를 모니터링하는 간단한 대시보드
"""

import os
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from collections import defaultdict, deque

class LogDashboard:
    def __init__(self):
        self.running = False
        self.log_files = ["realtime.log", "scenario_1_데이터베이스_오류.log", "scenario_2_메모리_누수.log"]
        self.analysis_files = []
        self.stats = {
            "log_files": {},
            "analysis_files": {},
            "system_status": {
                "vllm_server": False,
                "last_check": None
            },
            "start_time": datetime.now()
        }
        
        # 화면 클리어를 위한 ANSI 코드
        self.CLEAR_SCREEN = '\033[2J'
        self.CURSOR_HOME = '\033[H'
        self.COLORS = {
            'RED': '\033[91m',
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'MAGENTA': '\033[95m',
            'CYAN': '\033[96m',
            'WHITE': '\033[97m',
            'BOLD': '\033[1m',
            'END': '\033[0m'
        }
    
    def clear_screen(self):
        """화면 클리어"""
        print(self.CLEAR_SCREEN + self.CURSOR_HOME, end='')
    
    def colorize(self, text: str, color: str) -> str:
        """텍스트 색상 적용"""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['END']}"
    
    def get_file_size(self, filepath: str) -> int:
        """파일 크기 반환 (바이트)"""
        try:
            return os.path.getsize(filepath) if os.path.exists(filepath) else 0
        except:
            return 0
    
    def get_file_lines(self, filepath: str) -> int:
        """파일 라인 수 반환"""
        try:
            if not os.path.exists(filepath):
                return 0
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def get_file_last_modified(self, filepath: str) -> Optional[datetime]:
        """파일 마지막 수정 시간 반환"""
        try:
            if not os.path.exists(filepath):
                return None
            timestamp = os.path.getmtime(filepath)
            return datetime.fromtimestamp(timestamp)
        except:
            return None
    
    def parse_log_file(self, filepath: str, max_lines: int = 100) -> Dict:
        """로그 파일 파싱"""
        stats = {
            "total_lines": 0,
            "by_level": defaultdict(int),
            "by_service": defaultdict(int),
            "recent_logs": [],
            "error_count": 0,
            "critical_count": 0
        }
        
        try:
            if not os.path.exists(filepath):
                return stats
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                stats["total_lines"] = len(lines)
                
                # 최근 로그만 파싱
                recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
                
                for line in recent_lines:
                    parsed = self.parse_log_line(line.strip())
                    if parsed:
                        stats["by_level"][parsed["level"]] += 1
                        stats["by_service"][parsed["service"]] += 1
                        
                        if parsed["level"] == "ERROR":
                            stats["error_count"] += 1
                        elif parsed["level"] == "CRITICAL":
                            stats["critical_count"] += 1
                        
                        stats["recent_logs"].append(parsed)
        
        except Exception as e:
            print(f"❌ 로그 파일 파싱 오류 ({filepath}): {e}")
        
        return stats
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """로그 라인 파싱"""
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) \[(\w+)\] (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp_str, level, service, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            return {
                "timestamp": timestamp,
                "level": level,
                "service": service,
                "message": message,
                "raw": line
            }
        return None
    
    def get_analysis_files(self) -> List[str]:
        """분석 결과 파일 목록 반환"""
        analysis_files = []
        for file in os.listdir("."):
            if file.startswith(("analysis_results", "auto_analysis", "monitor_analysis")) and file.endswith(".json"):
                analysis_files.append(file)
        return sorted(analysis_files, key=lambda x: os.path.getmtime(x), reverse=True)
    
    def parse_analysis_file(self, filepath: str) -> Dict:
        """분석 결과 파일 파싱"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                # 파이프라인 결과 형식
                analysis = data[0].get("analysis", "")
                meta = data[0].get("meta", {})
                return {
                    "type": "pipeline",
                    "analysis": analysis,
                    "meta": meta,
                    "success": True
                }
            elif isinstance(data, dict):
                # 자동 분석 결과 형식
                return {
                    "type": "auto",
                    "analysis": data.get("analysis", ""),
                    "meta": data.get("log_summary", {}),
                    "success": data.get("success", False),
                    "timestamp": data.get("timestamp", ""),
                    "log_count": data.get("log_count", 0)
                }
        except Exception as e:
            return {
                "type": "unknown",
                "error": str(e),
                "success": False
            }
        
        return {"type": "unknown", "success": False}
    
    def check_vllm_server(self) -> bool:
        """vLLM 서버 상태 확인"""
        try:
            import requests
            from config import get_vllm_url
            response = requests.get(f"{get_vllm_url()}/models", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def update_stats(self):
        """통계 업데이트"""
        # 로그 파일 통계
        for log_file in self.log_files:
            if os.path.exists(log_file):
                self.stats["log_files"][log_file] = {
                    "size": self.get_file_size(log_file),
                    "lines": self.get_file_lines(log_file),
                    "last_modified": self.get_file_last_modified(log_file),
                    "parsed_stats": self.parse_log_file(log_file, 50)
                }
        
        # 분석 파일 통계
        analysis_files = self.get_analysis_files()
        for analysis_file in analysis_files[:10]:  # 최근 10개만
            self.stats["analysis_files"][analysis_file] = {
                "size": self.get_file_size(analysis_file),
                "last_modified": self.get_file_last_modified(analysis_file),
                "parsed_data": self.parse_analysis_file(analysis_file)
            }
        
        # 시스템 상태
        self.stats["system_status"]["vllm_server"] = self.check_vllm_server()
        self.stats["system_status"]["last_check"] = datetime.now()
    
    def format_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
    
    def format_time_ago(self, timestamp: Optional[datetime]) -> str:
        """시간 경과 포맷팅"""
        if not timestamp:
            return "N/A"
        
        elapsed = datetime.now() - timestamp
        if elapsed.total_seconds() < 60:
            return f"{elapsed.total_seconds():.0f}초 전"
        elif elapsed.total_seconds() < 3600:
            return f"{elapsed.total_seconds() / 60:.0f}분 전"
        else:
            return f"{elapsed.total_seconds() / 3600:.1f}시간 전"
    
    def display_header(self):
        """헤더 표시"""
        elapsed = datetime.now() - self.stats["start_time"]
        print(self.colorize("=" * 80, 'CYAN'))
        print(self.colorize("🔍 로그 분석 대시보드", 'BOLD'))
        print(self.colorize(f"실행 시간: {elapsed.total_seconds():.0f}초 | 업데이트: {datetime.now().strftime('%H:%M:%S')}", 'BLUE'))
        print(self.colorize("=" * 80, 'CYAN'))
    
    def display_system_status(self):
        """시스템 상태 표시"""
        print(self.colorize("\n📊 시스템 상태", 'BOLD'))
        print("-" * 40)
        
        vllm_status = "✅ 연결됨" if self.stats["system_status"]["vllm_server"] else "❌ 연결 안됨"
        vllm_color = 'GREEN' if self.stats["system_status"]["vllm_server"] else 'RED'
        print(f"vLLM 서버: {self.colorize(vllm_status, vllm_color)}")
        
        last_check = self.format_time_ago(self.stats["system_status"]["last_check"])
        print(f"마지막 체크: {last_check}")
    
    def display_log_files(self):
        """로그 파일 상태 표시"""
        print(self.colorize("\n📁 로그 파일 상태", 'BOLD'))
        print("-" * 40)
        
        for log_file, stats in self.stats["log_files"].items():
            if not stats:
                continue
            
            print(f"\n{self.colorize(log_file, 'YELLOW')}")
            print(f"  크기: {self.format_size(stats['size'])}")
            print(f"  라인: {stats['lines']:,}개")
            print(f"  수정: {self.format_time_ago(stats['last_modified'])}")
            
            if stats.get('parsed_stats'):
                parsed = stats['parsed_stats']
                print(f"  최근 로그 분석:")
                
                # 레벨별 통계
                for level, count in parsed['by_level'].items():
                    if count > 0:
                        color = 'RED' if level in ['ERROR', 'CRITICAL'] else 'YELLOW' if level == 'WARN' else 'GREEN'
                        print(f"    {self.colorize(level, color)}: {count}개")
                
                # 에러/크리티컬 강조
                if parsed['error_count'] > 0:
                    print(f"    {self.colorize(f'ERROR: {parsed[\"error_count\"]}개', 'RED')}")
                if parsed['critical_count'] > 0:
                    print(f"    {self.colorize(f'CRITICAL: {parsed[\"critical_count\"]}개', 'RED')}")
    
    def display_analysis_files(self):
        """분석 결과 파일 표시"""
        print(self.colorize("\n📄 분석 결과 파일", 'BOLD'))
        print("-" * 40)
        
        analysis_files = list(self.stats["analysis_files"].items())[:5]  # 최근 5개만
        
        for analysis_file, stats in analysis_files:
            if not stats:
                continue
            
            print(f"\n{self.colorize(analysis_file, 'MAGENTA')}")
            print(f"  크기: {self.format_size(stats['size'])}")
            print(f"  수정: {self.format_time_ago(stats['last_modified'])}")
            
            if stats.get('parsed_data'):
                data = stats['parsed_data']
                success_color = 'GREEN' if data.get('success') else 'RED'
                success_text = "✅ 성공" if data.get('success') else "❌ 실패"
                print(f"  상태: {self.colorize(success_text, success_color)}")
                
                if data.get('type') == 'auto':
                    print(f"  로그 수: {data.get('log_count', 0)}개")
                    print(f"  시간: {data.get('timestamp', 'N/A')}")
                
                # 분석 결과 미리보기
                analysis = data.get('analysis', '')
                if analysis:
                    preview = analysis[:100] + "..." if len(analysis) > 100 else analysis
                    print(f"  분석: {preview}")
    
    def display_recent_logs(self):
        """최근 로그 표시"""
        print(self.colorize("\n📝 최근 로그 (실시간)", 'BOLD'))
        print("-" * 40)
        
        realtime_log = self.stats["log_files"].get("realtime.log")
        if realtime_log and realtime_log.get('parsed_stats'):
            recent_logs = realtime_log['parsed_stats']['recent_logs'][-5:]  # 최근 5개
            
            for log in recent_logs:
                level_color = 'RED' if log['level'] in ['ERROR', 'CRITICAL'] else 'YELLOW' if log['level'] == 'WARN' else 'GREEN'
                time_str = log['timestamp'].strftime('%H:%M:%S')
                print(f"{time_str} {self.colorize(log['level'], level_color)} [{log['service']}] {log['message'][:50]}...")
    
    def display_help(self):
        """도움말 표시"""
        print(self.colorize("\n❓ 도움말", 'BOLD'))
        print("-" * 40)
        print("q: 종료")
        print("r: 새로고침")
        print("s: 통계 저장")
        print("h: 도움말")
    
    def save_stats(self):
        """통계 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = f"dashboard_stats_{timestamp}.json"
        
        # JSON 직렬화를 위해 datetime 객체를 문자열로 변환
        serializable_stats = {}
        for key, value in self.stats.items():
            if isinstance(value, dict):
                serializable_stats[key] = {}
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict) and 'last_modified' in sub_value:
                        serializable_stats[key][sub_key] = {
                            **sub_value,
                            'last_modified': sub_value['last_modified'].isoformat() if sub_value['last_modified'] else None
                        }
                    else:
                        serializable_stats[key][sub_key] = sub_value
            else:
                serializable_stats[key] = value
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_stats, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n📄 통계 저장: {stats_file}")
        except Exception as e:
            print(f"\n❌ 통계 저장 실패: {e}")
    
    def run_dashboard(self):
        """대시보드 실행"""
        print("🚀 로그 분석 대시보드 시작")
        print("중단하려면 'q'를 입력하세요")
        time.sleep(2)
        
        self.running = True
        
        try:
            while self.running:
                # 화면 클리어
                self.clear_screen()
                
                # 통계 업데이트
                self.update_stats()
                
                # 대시보드 표시
                self.display_header()
                self.display_system_status()
                self.display_log_files()
                self.display_analysis_files()
                self.display_recent_logs()
                self.display_help()
                
                # 사용자 입력 대기 (논블로킹)
                import select
                import sys
                
                if select.select([sys.stdin], [], [], 1)[0]:  # 1초 타임아웃
                    user_input = input().strip().lower()
                    
                    if user_input == 'q':
                        break
                    elif user_input == 'r':
                        continue  # 새로고침
                    elif user_input == 's':
                        self.save_stats()
                        time.sleep(1)
                    elif user_input == 'h':
                        continue  # 도움말은 이미 표시됨
                
                # 5초 대기
                time.sleep(5)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            print("\n👋 대시보드를 종료합니다.")

def main():
    dashboard = LogDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
