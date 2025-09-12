#!/usr/bin/env python3
"""
프롬프트 템플릿 모듈 - 다양한 분석 시나리오에 대한 프롬프트 템플릿 관리
"""

from typing import Dict, List, Optional
from enum import Enum

class AnalysisType(Enum):
    """분석 타입 열거형"""
    GENERAL = "general"
    DATABASE = "database"
    MEMORY = "memory"
    NETWORK = "network"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CRITICAL = "critical"

class PromptTemplates:
    """프롬프트 템플릿 관리 클래스"""
    
    def __init__(self):
        self.system_prompts = {
            AnalysisType.GENERAL: self._get_general_system_prompt(),
            AnalysisType.DATABASE: self._get_database_system_prompt(),
            AnalysisType.MEMORY: self._get_memory_system_prompt(),
            AnalysisType.NETWORK: self._get_network_system_prompt(),
            AnalysisType.SECURITY: self._get_security_system_prompt(),
            AnalysisType.PERFORMANCE: self._get_performance_system_prompt(),
            AnalysisType.CRITICAL: self._get_critical_system_prompt()
        }
        
        self.user_prompt_templates = {
            AnalysisType.GENERAL: self._get_general_user_template(),
            AnalysisType.DATABASE: self._get_database_user_template(),
            AnalysisType.MEMORY: self._get_memory_user_template(),
            AnalysisType.NETWORK: self._get_network_user_template(),
            AnalysisType.SECURITY: self._get_security_user_template(),
            AnalysisType.PERFORMANCE: self._get_performance_user_template(),
            AnalysisType.CRITICAL: self._get_critical_user_template()
        }
    
    def _get_general_system_prompt(self) -> str:
        """일반적인 로그 분석 시스템 프롬프트"""
        return (
            "You are an SRE/DevOps log expert. Be factual and concise. "
            "Analyze the provided logs and provide actionable insights. "
            "Focus on identifying root causes and providing concrete solutions. "
            "Keep answers structured and easy to follow."
        )
    
    def _get_database_system_prompt(self) -> str:
        """데이터베이스 관련 로그 분석 시스템 프롬프트"""
        return (
            "You are a database and infrastructure expert specializing in database performance and reliability. "
            "Analyze database-related logs to identify connection issues, performance problems, and data integrity concerns. "
            "Provide specific database tuning recommendations and monitoring commands. "
            "Consider both immediate fixes and long-term optimizations."
        )
    
    def _get_memory_system_prompt(self) -> str:
        """메모리 관련 로그 분석 시스템 프롬프트"""
        return (
            "You are a system performance expert specializing in memory management and resource optimization. "
            "Analyze memory-related logs to identify leaks, allocation issues, and resource constraints. "
            "Provide specific memory tuning recommendations and monitoring strategies. "
            "Consider both application-level and system-level memory management."
        )
    
    def _get_network_system_prompt(self) -> str:
        """네트워크 관련 로그 분석 시스템 프롬프트"""
        return (
            "You are a network infrastructure expert specializing in connectivity and performance issues. "
            "Analyze network-related logs to identify connectivity problems, latency issues, and protocol errors. "
            "Provide specific network troubleshooting steps and optimization recommendations. "
            "Consider both local network and external service connectivity."
        )
    
    def _get_security_system_prompt(self) -> str:
        """보안 관련 로그 분석 시스템 프롬프트"""
        return (
            "You are a cybersecurity expert specializing in threat detection and incident response. "
            "Analyze security-related logs to identify potential threats, attacks, and vulnerabilities. "
            "Provide specific security recommendations and incident response procedures. "
            "Prioritize immediate security actions and long-term security improvements."
        )
    
    def _get_performance_system_prompt(self) -> str:
        """성능 관련 로그 분석 시스템 프롬프트"""
        return (
            "You are a performance engineering expert specializing in system optimization and scalability. "
            "Analyze performance-related logs to identify bottlenecks, resource constraints, and optimization opportunities. "
            "Provide specific performance tuning recommendations and monitoring strategies. "
            "Consider both immediate performance fixes and architectural improvements."
        )
    
    def _get_critical_system_prompt(self) -> str:
        """크리티컬 상황 로그 분석 시스템 프롬프트"""
        return (
            "You are an emergency response expert specializing in critical system failures and incident management. "
            "Analyze critical logs to identify immediate threats to system availability and data integrity. "
            "Provide urgent response procedures and immediate mitigation steps. "
            "Prioritize system recovery and data protection above all else."
        )
    
    def _get_general_user_template(self) -> str:
        """일반적인 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[TASK]
1) 핵심 증상 3~5개
2) 원인 가설(우선순위)
3) 즉시 점검 명령(쉘)
4) 재발방지 액션
5) 확신도[낮음/중간/높음]"""
    
    def _get_database_user_template(self) -> str:
        """데이터베이스 관련 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[DATABASE ANALYSIS TASK]
1) 데이터베이스 연결 상태 및 오류
2) 쿼리 성능 및 타임아웃 이슈
3) 연결 풀 및 리소스 사용량
4) 데이터베이스 서버 상태 점검 명령
5) 성능 최적화 및 모니터링 권장사항
6) 확신도[낮음/중간/높음]"""
    
    def _get_memory_user_template(self) -> str:
        """메모리 관련 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[MEMORY ANALYSIS TASK]
1) 메모리 사용량 패턴 및 누수 증상
2) OutOfMemoryError 및 메모리 부족 원인
3) GC 압력 및 메모리 할당 이슈
4) 메모리 상태 점검 명령
5) 메모리 최적화 및 모니터링 권장사항
6) 확신도[낮음/중간/높음]"""
    
    def _get_network_user_template(self) -> str:
        """네트워크 관련 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[NETWORK ANALYSIS TASK]
1) 네트워크 연결 상태 및 타임아웃
2) 지연시간 및 패킷 손실 이슈
3) 외부 서비스 연결 문제
4) 네트워크 상태 점검 명령
5) 네트워크 최적화 및 모니터링 권장사항
6) 확신도[낮음/중간/높음]"""
    
    def _get_security_user_template(self) -> str:
        """보안 관련 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[SECURITY ANALYSIS TASK]
1) 보안 위협 및 공격 시도
2) 인증/인가 실패 및 권한 문제
3) 의심스러운 활동 패턴
4) 보안 상태 점검 명령
5) 보안 강화 및 모니터링 권장사항
6) 확신도[낮음/중간/높음]"""
    
    def _get_performance_user_template(self) -> str:
        """성능 관련 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[PERFORMANCE ANALYSIS TASK]
1) 성능 병목 및 응답 시간 이슈
2) 리소스 사용량 및 제약사항
3) 처리량 및 동시성 문제
4) 성능 상태 점검 명령
5) 성능 최적화 및 모니터링 권장사항
6) 확신도[낮음/중간/높음]"""
    
    def _get_critical_user_template(self) -> str:
        """크리티컬 상황 사용자 프롬프트 템플릿"""
        return """[META]
service={service}
host={host}
time_range={time_range}
severity_top={severity}

[LOG WINDOW]
{log_content}

[CRITICAL INCIDENT ANALYSIS TASK]
1) 즉시 위험 요소 및 시스템 다운 증상
2) 데이터 손실 위험 및 무결성 문제
3) 서비스 중단 원인 및 영향 범위
4) 긴급 복구 및 점검 명령
5) 즉시 조치사항 및 장기 개선방안
6) 확신도[낮음/중간/높음]"""
    
    def get_system_prompt(self, analysis_type: AnalysisType) -> str:
        """분석 타입에 따른 시스템 프롬프트 반환"""
        return self.system_prompts.get(analysis_type, self.system_prompts[AnalysisType.GENERAL])
    
    def get_user_prompt(self, analysis_type: AnalysisType, **kwargs) -> str:
        """분석 타입에 따른 사용자 프롬프트 반환"""
        template = self.user_prompt_templates.get(analysis_type, self.user_prompt_templates[AnalysisType.GENERAL])
        return template.format(**kwargs)
    
    def detect_analysis_type(self, log_content: str) -> AnalysisType:
        """로그 내용을 기반으로 분석 타입 자동 감지"""
        log_lower = log_content.lower()
        
        # 키워드 기반 분석 타입 감지
        if any(keyword in log_lower for keyword in ['database', 'db', 'mysql', 'postgresql', 'connection', 'query', 'sql']):
            return AnalysisType.DATABASE
        elif any(keyword in log_lower for keyword in ['memory', 'oom', 'outofmemory', 'gc', 'heap', 'ram']):
            return AnalysisType.MEMORY
        elif any(keyword in log_lower for keyword in ['network', 'timeout', 'connection refused', 'unreachable', 'latency']):
            return AnalysisType.NETWORK
        elif any(keyword in log_lower for keyword in ['security', 'attack', 'breach', 'unauthorized', 'injection', 'hack']):
            return AnalysisType.SECURITY
        elif any(keyword in log_lower for keyword in ['performance', 'slow', 'bottleneck', 'cpu', 'response time']):
            return AnalysisType.PERFORMANCE
        elif any(keyword in log_lower for keyword in ['critical', 'fatal', 'emergency', 'down', 'unavailable']):
            return AnalysisType.CRITICAL
        else:
            return AnalysisType.GENERAL
    
    def get_analysis_config(self, analysis_type: AnalysisType) -> Dict:
        """분석 타입에 따른 설정 반환"""
        configs = {
            AnalysisType.GENERAL: {
                "temperature": 0.2,
                "max_tokens": 1200,
                "timeout": 60
            },
            AnalysisType.DATABASE: {
                "temperature": 0.1,
                "max_tokens": 1500,
                "timeout": 90
            },
            AnalysisType.MEMORY: {
                "temperature": 0.1,
                "max_tokens": 1400,
                "timeout": 90
            },
            AnalysisType.NETWORK: {
                "temperature": 0.2,
                "max_tokens": 1300,
                "timeout": 75
            },
            AnalysisType.SECURITY: {
                "temperature": 0.1,
                "max_tokens": 1600,
                "timeout": 120
            },
            AnalysisType.PERFORMANCE: {
                "temperature": 0.2,
                "max_tokens": 1400,
                "timeout": 90
            },
            AnalysisType.CRITICAL: {
                "temperature": 0.1,
                "max_tokens": 1800,
                "timeout": 150
            }
        }
        return configs.get(analysis_type, configs[AnalysisType.GENERAL])

# 전역 인스턴스
prompt_templates = PromptTemplates()

def get_prompt_templates() -> PromptTemplates:
    """프롬프트 템플릿 인스턴스 반환"""
    return prompt_templates
