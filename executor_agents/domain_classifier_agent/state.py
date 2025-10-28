# WebAgent/executor_agents/domain_classifier_agent/state.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class DomainCandidate:
    """검색 결과로부터 추출된 도메인 후보"""
    url: str
    title: str
    snippet: str
    search_rank: int  
    main_domain: str  
    
@dataclass
class ScoredDomain:
    """점수가 부여된 도메인"""
    url: str
    main_domain: str
    title: str
    snippet: str
    
    # 점수 구성 요소
    title_similarity: float  # 0.0 ~ 0.2
    snippet_relevance: float  # 0.0 ~ 0.3
    domain_frequency_bonus: float  # 0.0 ~ 0.1 (누적)
    rank_bonus: float  # 0.0 ~ 0.2
    
    total_score: float
    reasoning: str  # 점수 부여 근거
    
@dataclass
class DomainClassificationResult:
    """Domain Classifier의 최종 결과"""
    primary_domain: ScoredDomain
    alternatives: List[ScoredDomain]  # 최소 2개 보장
    
    # 메타데이터
    original_query: str
    optimized_query: str
    search_timestamp: datetime
    total_candidates: int
    
    confidence_score: float  # Primary domain 신뢰도
    reasoning: str  # 전체 분류 근거

@dataclass
class DomainClassifierState:
    """Domain Classifier Agent의 전역 상태"""
    
    # 입력
    user_query: str = ""
    user_context: Dict = field(default_factory=dict)
    
    # Stage 1: Query Optimization
    optimized_query: str = ""
    query_intent: str = ""  # 정보탐색/신청절차 등
    
    # Stage 2: Google Search
    search_results: List[Dict] = field(default_factory=list)
    domain_candidates: List[DomainCandidate] = field(default_factory=list)
    
    # Stage 3: Scoring & Ranking
    scored_domains: List[ScoredDomain] = field(default_factory=list)
    domain_frequency_map: Dict[str, int] = field(default_factory=dict)  # main_domain → count
    
    # 최종 결과
    result: Optional[DomainClassificationResult] = None
    
    # 실행 메타데이터
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error_msg: str):
        """에러 추가"""
        self.errors.append(f"[{datetime.now().isoformat()}] {error_msg}")
    
    def get_execution_time(self) -> float:
        """실행 시간 계산 (초)"""
        if self.execution_start and self.execution_end:
            return (self.execution_end - self.execution_start).total_seconds()
        return 0.0