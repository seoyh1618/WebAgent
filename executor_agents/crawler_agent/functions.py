import os
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from openai import OpenAI

def optimize_query(
    original_query: str,
    query_context: Optional[Dict] = None
) -> Dict[str, str]:
    """
    사용자 질의를 Google Search에 최적화된 키워드로 변환
    
    Args:
        original_query: 원본 사용자 질의
        query_context: 사용자 맥락 (학교, 학과 등)
    
    Returns:
        {
            "optimized_query": str,
            "reasoning": str
        }
    """
    from WebAgent.executor_agents.domain_classifier_agent.prompt import QUERY_OPTIMIZATION_PROMPT
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = QUERY_OPTIMIZATION_PROMPT.format(
        original_query=original_query,
        query_context=json.dumps(query_context or {}, ensure_ascii=False)
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 검색 쿼리 최적화 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Query optimized: {original_query} -> {result['optimized_query']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Query optimization failed: {e}")
        return {
            "optimized_query": original_query,
            "reasoning": f"최적화 실패, 원본 쿼리 사용: {str(e)}"
        }