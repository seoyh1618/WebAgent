# WebAgent/executor_agents/domain_classifier_agent/functions.py
import os, json, requests
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse

from openai import OpenAI
from dotenv import load_dotenv
from WebAgent.executor_agents.domain_classifier_agent.prompt import (
    QUERY_OPTIMIZATION_SYSTEM_PROMPT,
    QUERY_OPTIMIZATION_USER_PROMPT
)
from WebAgent.executor_agents.domain_classifier_agent.state import (
    DomainClassifierState,
    DomainCandidate,
)

# OpenAI Client 초기화
load_dotenv()
openai_client = OpenAI()

# Google Search API 클래스
class GoogleSearchAPI:
    """Google Custom Search API를 사용하여 검색 및 도메인 추출을 수행하는 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        GoogleSearchAPI 초기화
        
        Args:
            api_key: Google Custom Search API 키 (없으면 환경변수에서 로드)
            search_engine_id: Custom Search Engine ID (없으면 환경변수에서 로드)
        """
        # 환경변수 로드
        load_dotenv()
        
        self.api_key = api_key or os.getenv('GOOGLE_SEARCH_JSON_KEY')
        self.search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not self.api_key:
            raise ValueError("Google Search API 키가 설정되지 않았습니다. GOOGLE_SEARCH_JSON_KEY 환경변수를 설정하거나 api_key 매개변수를 제공하세요.")
        
        if not self.search_engine_id:
            raise ValueError("Google Search Engine ID가 설정되지 않았습니다. GOOGLE_SEARCH_ENGINE_ID 환경변수를 설정하거나 search_engine_id 매개변수를 제공하세요.")
        
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, num_results: int = 10) -> Dict:
        """
        Google Custom Search API를 사용하여 검색 수행
        
        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 수 (최대 10)
            
        Returns:
            API 응답 딕셔너리
        """
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': min(num_results, 10) 
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"검색 API 호출 중 오류 발생: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"API 응답 파싱 중 오류 발생: {e}")
    
    def extract_domains(self, search_results: Dict) -> List[str]:
        """
        검색 결과에서 도메인 추출
        
        Args:
            search_results: Google Search API 응답
            
        Returns:
            추출된 도메인 리스트 (중복 제거, 정렬됨)
        """
        domains = set()
        
        if 'items' not in search_results:
            print("검색 결과가 없습니다.")
            return []
        
        for item in search_results['items']:
            if 'link' in item:
                url = item['link']
                try:
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc
                    if domain:  # 빈 도메인 제외
                        domains.add(domain)
                except Exception as e:
                    print(f"URL 파싱 오류 ({url}): {e}")
                    continue
        
        return sorted(list(domains))
    

# 사용자 쿼리를 검색 최적화 쿼리로 변환하는 함수
def enhance_query(user_query: str) -> Dict:
    """
    사용자 쿼리를 검색 엔진 최적화 쿼리로 변환
    
    적용된 프롬프트 기법:
    1. Task Decomposition: 4단계 구조화된 추론 (의도→개체→생성→검증)
    2. Few-Shot Learning: 다양한 도메인 3개 예시 (대학/정부/기업)
    3. Self-Verification: Step 4에서 자체 검증
    4. Chain-of-Thought: 각 단계별 명시적 추론 과정
    5. Structured Output: JSON Schema 강제
    
    Args:
        user_query: 사용자 원본 쿼리
        
    Returns:
        {
            "intent": str,                  # 의도 카테고리
            "optimized_query": str,         # 최적화된 검색 쿼리
            "keywords": List[str],          # 추출된 키워드
            "reasoning": {                  # 추론 과정 (선택적)
                "step1_intent": str,
                "step2_entities": str,
                "step3_generation": str,
                "step4_validation": str
            },
            "original_query": str           # 원본 쿼리
        }
    """
    
    try:
        # Prompt 구성
        system_content = QUERY_OPTIMIZATION_SYSTEM_PROMPT
        user_content = QUERY_OPTIMIZATION_USER_PROMPT.format(user_query=user_query)
        
        # OpenAI API 호출
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # 일관된 출력
            max_tokens=400,   # 추론 과정 포함으로 증가
            top_p=0.9
        )
        
        # JSON 파싱
        result = json.loads(response.choices[0].message.content)
        
        # 원본 쿼리 추가
        result["original_query"] = user_query
        
        # 로깅
        print(f"✓ 최적화 완료: {user_query}")
        print(f"  → {result.get('optimized_query')}")
        print(f"  의도: {result.get('intent')}")
        print(f"  키워드: {result.get('keywords')}")
        
        # reasoning이 있으면 디버그 로깅
        if "reasoning" in result:
            print(f"  추론 과정:")
            for step, content in result["reasoning"].items():
                print(f"    {step}: {content}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
    
    except Exception as e:
        print(f"쿼리 최적화 실패: {e}")

def execute_google_search(state: DomainClassifierState) -> DomainClassifierState:
    """
    Google Search 실행 및 DomainCandidate 생성
    """
    print(f"[Stage 2] Google Search 시작: {state.optimized_query}")
    
    try:
        api = GoogleSearchAPI()
        search_results = api.search(state.optimized_query, num_results=10)
        
        items = search_results.get("items", [])
        if not items:
            print("[Stage 2] 검색 결과 없음")
            state.add_error("No search results found")
            return state
        
        # DomainCandidate 생성
        for idx, item in enumerate(items, 1):
            url = item.get("link", "")
            parsed = urlparse(url)
            main_domain = parsed.netloc.replace("www.", "")
            
            candidate = DomainCandidate(
                url=url,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                search_rank=idx,
                main_domain=main_domain
            )
            
            state.domain_candidates.append(candidate)
            
            # 도메인 빈도 카운팅
            state.domain_frequency_map[main_domain] = \
                state.domain_frequency_map.get(main_domain, 0) + 1
        
        print(f"[Stage 2] {len(state.domain_candidates)}개 도메인 후보 발견")
        
    except Exception as e:
        print(f"[Stage 2] 검색 실패: {e}")
        state.add_error(f"Search error: {str(e)}")
    
    return state

# 외부 툴 인터페이스용 래퍼 함수 (프롬프트 시그니처와 정렬)
def execute_google_search_tool(query: str) -> Dict:
    """
    프롬프트에서 요구하는 형태로 검색을 수행하는 래퍼.

    Args:
        query: 최적화된 검색 쿼리 문자열

    Returns:
        dict: 후보 리스트 직렬화 결과
            {
              "candidates": [
                {
                  "url": str,
                  "title": str,
                  "snippet": str,
                  "search_rank": int,
                  "main_domain": str
                }, ...
              ]
            }
    """
    state = DomainClassifierState(optimized_query=query)
    result_state = execute_google_search(state)

    serialized_candidates = [
        {
            "url": c.url,
            "title": c.title,
            "snippet": c.snippet,
            "search_rank": c.search_rank,
            "main_domain": c.main_domain,
        }
        for c in result_state.domain_candidates
    ]

    return {"candidates": serialized_candidates}
