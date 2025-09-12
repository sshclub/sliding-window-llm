#!/usr/bin/env python3
"""
슬라이딩 윈도우 모듈 - 로그 파일을 토큰 기반으로 슬라이딩 윈도우로 분할
"""

import tiktoken
from typing import List, Dict, Optional, Generator, Tuple
from dataclasses import dataclass
from enum import Enum

class TokenizerType(Enum):
    """토크나이저 타입"""
    TIKTOKEN = "tiktoken"
    SIMPLE = "simple"

@dataclass
class WindowConfig:
    """윈도우 설정"""
    max_tokens: int = 5000
    overlap_ratio: float = 0.15
    min_tokens: int = 100
    tokenizer_type: TokenizerType = TokenizerType.TIKTOKEN
    encoding_name: str = "cl100k_base"

@dataclass
class WindowResult:
    """윈도우 결과"""
    content: str
    start_line: int
    end_line: int
    token_count: int
    window_index: int
    total_windows: int

class TokenCounter:
    """토큰 카운터 클래스"""
    
    def __init__(self, tokenizer_type: TokenizerType = TokenizerType.TIKTOKEN, encoding_name: str = "cl100k_base"):
        self.tokenizer_type = tokenizer_type
        self.encoding_name = encoding_name
        self._encoder = None
        
        if tokenizer_type == TokenizerType.TIKTOKEN:
            try:
                self._encoder = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                print(f"⚠️ tiktoken 로딩 실패, 간단한 토크나이저 사용: {e}")
                self.tokenizer_type = TokenizerType.SIMPLE
    
    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        if self.tokenizer_type == TokenizerType.TIKTOKEN and self._encoder:
            try:
                return len(self._encoder.encode(text))
            except Exception:
                pass
        
        # 간단한 토크나이저 (대략적인 추정)
        return max(1, len(text) // 4)

class SlidingWindow:
    """슬라이딩 윈도우 클래스"""
    
    def __init__(self, config: WindowConfig = None):
        self.config = config or WindowConfig()
        self.token_counter = TokenCounter(
            self.config.tokenizer_type, 
            self.config.encoding_name
        )
    
    def create_windows(self, lines: List[str]) -> List[WindowResult]:
        """라인 리스트를 슬라이딩 윈도우로 분할"""
        if not lines:
            return []
        
        windows = []
        current_window = []
        current_tokens = 0
        window_index = 0
        line_index = 0
        
        while line_index < len(lines):
            line = lines[line_index]
            line_tokens = self.token_counter.count_tokens(line)
            
            # 현재 라인이 윈도우에 추가될 수 있는지 확인
            if current_tokens + line_tokens <= self.config.max_tokens:
                current_window.append(line)
                current_tokens += line_tokens
                line_index += 1
            else:
                # 윈도우가 가득 찬 경우
                if current_window:
                    # 현재 윈도우 저장
                    window_result = WindowResult(
                        content="\n".join(current_window),
                        start_line=line_index - len(current_window),
                        end_line=line_index - 1,
                        token_count=current_tokens,
                        window_index=window_index,
                        total_windows=0  # 나중에 업데이트
                    )
                    windows.append(window_result)
                    window_index += 1
                    
                    # 오버랩을 위한 윈도우 조정
                    current_window, current_tokens = self._adjust_window_for_overlap(
                        current_window, current_tokens
                    )
                else:
                    # 단일 라인이 윈도우 크기를 초과하는 경우
                    # 라인을 그대로 윈도우로 만듦
                    window_result = WindowResult(
                        content=line,
                        start_line=line_index,
                        end_line=line_index,
                        token_count=line_tokens,
                        window_index=window_index,
                        total_windows=0
                    )
                    windows.append(window_result)
                    window_index += 1
                    line_index += 1
        
        # 마지막 윈도우 처리
        if current_window:
            window_result = WindowResult(
                content="\n".join(current_window),
                start_line=line_index - len(current_window),
                end_line=line_index - 1,
                token_count=current_tokens,
                window_index=window_index,
                total_windows=0
            )
            windows.append(window_result)
        
        # total_windows 업데이트
        for window in windows:
            window.total_windows = len(windows)
        
        return windows
    
    def _adjust_window_for_overlap(self, window: List[str], token_count: int) -> Tuple[List[str], int]:
        """오버랩을 위한 윈도우 조정"""
        if not window or self.config.overlap_ratio <= 0:
            return [], 0
        
        # 유지할 토큰 수 계산
        keep_tokens = int(self.config.max_tokens * self.config.overlap_ratio)
        
        if token_count <= keep_tokens:
            return window, token_count
        
        # 뒤에서부터 토큰 수를 맞춰가며 라인 제거
        kept_lines = []
        kept_tokens = 0
        
        for line in reversed(window):
            line_tokens = self.token_counter.count_tokens(line)
            if kept_tokens + line_tokens > keep_tokens:
                break
            kept_lines.append(line)
            kept_tokens += line_tokens
        
        # 순서 복원
        kept_lines.reverse()
        return kept_lines, kept_tokens
    
    def create_windows_from_file(self, file_path: str) -> List[WindowResult]:
        """파일에서 직접 윈도우 생성"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 줄바꿈 문자 제거
            lines = [line.rstrip('\n\r') for line in lines]
            
            return self.create_windows(lines)
        except Exception as e:
            print(f"❌ 파일 읽기 오류: {e}")
            return []
    
    def get_window_stats(self, windows: List[WindowResult]) -> Dict:
        """윈도우 통계 반환"""
        if not windows:
            return {
                "total_windows": 0,
                "total_tokens": 0,
                "avg_tokens_per_window": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "total_lines": 0
            }
        
        total_tokens = sum(window.token_count for window in windows)
        total_lines = sum(window.end_line - window.start_line + 1 for window in windows)
        token_counts = [window.token_count for window in windows]
        
        return {
            "total_windows": len(windows),
            "total_tokens": total_tokens,
            "avg_tokens_per_window": total_tokens / len(windows),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "total_lines": total_lines
        }
    
    def filter_windows_by_tokens(self, windows: List[WindowResult], min_tokens: int = None) -> List[WindowResult]:
        """토큰 수로 윈도우 필터링"""
        min_tokens = min_tokens or self.config.min_tokens
        return [window for window in windows if window.token_count >= min_tokens]
    
    def get_window_by_index(self, windows: List[WindowResult], index: int) -> Optional[WindowResult]:
        """인덱스로 윈도우 조회"""
        if 0 <= index < len(windows):
            return windows[index]
        return None
    
    def merge_windows(self, windows: List[WindowResult], max_merge_tokens: int = None) -> List[WindowResult]:
        """작은 윈도우들을 병합"""
        if not windows:
            return []
        
        max_merge_tokens = max_merge_tokens or self.config.max_tokens
        merged_windows = []
        current_merge = []
        current_tokens = 0
        window_index = 0
        
        for window in windows:
            if current_tokens + window.token_count <= max_merge_tokens:
                current_merge.append(window)
                current_tokens += window.token_count
            else:
                # 현재 병합 윈도우 저장
                if current_merge:
                    merged_content = "\n".join([w.content for w in current_merge])
                    merged_window = WindowResult(
                        content=merged_content,
                        start_line=current_merge[0].start_line,
                        end_line=current_merge[-1].end_line,
                        token_count=current_tokens,
                        window_index=window_index,
                        total_windows=0
                    )
                    merged_windows.append(merged_window)
                    window_index += 1
                
                # 새 병합 윈도우 시작
                current_merge = [window]
                current_tokens = window.token_count
        
        # 마지막 병합 윈도우 처리
        if current_merge:
            merged_content = "\n".join([w.content for w in current_merge])
            merged_window = WindowResult(
                content=merged_content,
                start_line=current_merge[0].start_line,
                end_line=current_merge[-1].end_line,
                token_count=current_tokens,
                window_index=window_index,
                total_windows=0
            )
            merged_windows.append(merged_window)
        
        # total_windows 업데이트
        for window in merged_windows:
            window.total_windows = len(merged_windows)
        
        return merged_windows

class WindowProcessor:
    """윈도우 처리 유틸리티 클래스"""
    
    @staticmethod
    def preprocess_lines(lines: List[str], filters: List[str] = None) -> List[str]:
        """라인 전처리"""
        if not filters:
            filters = ["healthz", "readinessProbe", "livenessProbe"]
        
        processed_lines = []
        for line in lines:
            # 필터링
            if any(filter_word in line.lower() for filter_word in filters):
                continue
            
            # 줄바꿈 문자 제거
            processed_line = line.rstrip('\n\r')
            if processed_line.strip():  # 빈 줄 제거
                processed_lines.append(processed_line)
        
        return processed_lines
    
    @staticmethod
    def split_large_lines(lines: List[str], max_line_tokens: int = 1000) -> List[str]:
        """큰 라인을 분할"""
        token_counter = TokenCounter()
        split_lines = []
        
        for line in lines:
            if token_counter.count_tokens(line) <= max_line_tokens:
                split_lines.append(line)
            else:
                # 라인을 여러 부분으로 분할
                words = line.split()
                current_chunk = []
                current_tokens = 0
                
                for word in words:
                    word_tokens = token_counter.count_tokens(word + " ")
                    if current_tokens + word_tokens <= max_line_tokens:
                        current_chunk.append(word)
                        current_tokens += word_tokens
                    else:
                        if current_chunk:
                            split_lines.append(" ".join(current_chunk))
                        current_chunk = [word]
                        current_tokens = word_tokens
                
                if current_chunk:
                    split_lines.append(" ".join(current_chunk))
        
        return split_lines

# 편의 함수들
def create_sliding_window(config: WindowConfig = None) -> SlidingWindow:
    """슬라이딩 윈도우 인스턴스 생성"""
    return SlidingWindow(config)

def process_log_file(file_path: str, config: WindowConfig = None) -> List[WindowResult]:
    """로그 파일을 슬라이딩 윈도우로 처리"""
    sliding_window = create_sliding_window(config)
    return sliding_window.create_windows_from_file(file_path)

def process_log_lines(lines: List[str], config: WindowConfig = None) -> List[WindowResult]:
    """로그 라인을 슬라이딩 윈도우로 처리"""
    sliding_window = create_sliding_window(config)
    return sliding_window.create_windows(lines)
