# WebAgent/executor_agents/domain_classifier_agent/agent.py

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from WebAgent.confing import constants
from .prompt import (
    DOMAIN_CLASSIFIER_DESCRIPTION,
    DOMAIN_CLASSIFIER_INSTRUCTION
)
from .functions import run_domain_classification
from .state import DomainClassificationResult
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# LLM Client 초기화
LLM_CLIENT = LiteLlm(model=constants.MODEL_GPT_4O_MINI)

# Domain Classifier Agent 생성
Domain_Priority_Classifier_Agent = Agent(
    name="Domain_Priority_Classifier",
    model=LLM_CLIENT,
    description=DOMAIN_CLASSIFIER_DESCRIPTION,
    instruction=DOMAIN_CLASSIFIER_INSTRUCTION,
    output_key="domain_classification_result"
)


# Agent 실행 래퍼 함수
def execute_domain_classification(user_query: str, user_context: dict = None) -> dict:
    """
    Domain Classifier Agent 실행 래퍼
    
    Args:
        user_query: 사용자 질의
        user_context: 추가 컨텍스트 (선택)
    
    Returns:
        dict: 도메인 분류 결과를 딕셔너리로 반환
    """
    try:
        result: DomainClassificationResult = run_domain_classification(
            user_query=user_query,
            user_context=user_context or {}
        )
        
        # 결과를 딕셔너리로 변환
        return {
            "primary_domain": {
                "url": result.primary_domain.url,
                "main_domain": result.primary_domain.main_domain,
                "title": result.primary_domain.title,
                "score": result.primary_domain.total_score,
                "reasoning": result.primary_domain.reasoning
            },
            "alternatives": [
                {
                    "url": alt.url,
                    "main_domain": alt.main_domain,
                    "title": alt.title,
                    "score": alt.total_score
                }
                for alt in result.alternatives
            ],
            "metadata": {
                "original_query": result.original_query,
                "optimized_query": result.optimized_query,
                "total_candidates": result.total_candidates,
                "confidence_score": result.confidence_score,
                "timestamp": result.search_timestamp.isoformat()
            },
            "reasoning": result.reasoning
        }
        
    except Exception as e:
        logger.error(f"Domain classification execution failed: {e}")
        return {
            "error": str(e),
            "primary_domain": None,
            "alternatives": []
        }


# 테스트 실행 함수
def test_domain_classifier():
    """Domain Classifier Agent 테스트"""
    test_query = "숭실대학교 일반대학원 사물함 신청 방법"
    
    print(f"\n{'='*60}")
    print(f"Testing Domain Classifier Agent")
    print(f"{'='*60}")
    print(f"Query: {test_query}\n")
    
    result = execute_domain_classification(test_query)
    
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"✅ Primary Domain:")
    print(f"  - Domain: {result['primary_domain']['main_domain']}")
    print(f"  - Title: {result['primary_domain']['title']}")
    print(f"  - Score: {result['primary_domain']['score']:.3f}")
    print(f"  - URL: {result['primary_domain']['url']}\n")
    
    print(f"📋 Alternative Domains:")
    for idx, alt in enumerate(result['alternatives'], 1):
        print(f"  {idx}. {alt['main_domain']} (Score: {alt['score']:.3f})")
        print(f"     {alt['title']}")
    
    print(f"\n📊 Metadata:")
    print(f"  - Original Query: {result['metadata']['original_query']}")
    print(f"  - Optimized Query: {result['metadata']['optimized_query']}")
    print(f"  - Confidence: {result['metadata']['confidence_score']:.3f}")
    print(f"  - Total Candidates: {result['metadata']['total_candidates']}")
    
    print(f"\n💡 Reasoning:")
    print(f"  {result['reasoning']}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # 테스트 실행
    test_domain_classifier()