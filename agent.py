# WebAgent/agent.py
from google.adk.agents import Agent 
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from WebAgent.confing import constants
from WebAgent.executor_agents.domain_classifier_agent.agent import Domain_Priority_Classifier_Agent
from WebAgent.prompt import ORCHESTRATOR_DESCRIPTION, ORCHESTRATOR_INSTRUCTION
from dotenv import load_dotenv
logger = logging.getLogger(__name__)

load_dotenv()

# WebPilot Agent Wrapper Tool
class WebPilotAgentTool(AgentTool):
    def __init__(self, agent: Agent):
        super().__init__(agent=agent)

    def _build_payload(self, args: dict | None, tool_context: dict | None) -> dict:
        """툴 인자 및 툴 컨텍스트에서 사용자 입력을 수집하여 하위 에이전트 입력을 구성."""
        args = args or {}
        tool_context = tool_context or {}

        # tool args 우선
        user_query = args.get("user_query")
        user_context = args.get("user_context")

        # ADK Web이 request 키로 전달하는 케이스 대응
        if user_query is None:
            for k in ("request", "input", "query", "prompt", "text", "message"):
                v = args.get(k)
                if isinstance(v, str) and v.strip():
                    user_query = v
                    break

        # 컨텍스트(session_state) 보조
        session_state = tool_context.get("session_state") if isinstance(tool_context, dict) else None
        if user_query is None and isinstance(session_state, dict):
            user_query = session_state.get("user_query")
        if user_context is None and isinstance(session_state, dict):
            user_context = session_state.get("user_context")

        # 추가적인 일반 키 탐색 (ADK Web 입력 호환)
        if user_query is None and isinstance(session_state, dict):
            for k in ("input", "query", "prompt", "text", "message"):
                if k in session_state and isinstance(session_state[k], str) and session_state[k].strip():
                    user_query = session_state[k]
                    break

        # tool_context 최상위에서도 시도 (일부 러너는 session_state 없이 전달)
        if user_query is None and isinstance(tool_context, dict):
            for k in ("user_query", "input", "query", "prompt", "text", "message"):
                v = tool_context.get(k)
                if isinstance(v, str) and v.strip():
                    user_query = v
                    break

        if user_query is None:
            raise KeyError("Context variable not found: `user_query`.")

        return {
            "user_query": user_query,
            "user_context": user_context or {},
        }

    def run(self, args: dict | None = None, tool_context: dict | None = None):
        payload = self._build_payload(args, tool_context)
        return self.agent.run(payload)

    async def run_async(self, args: dict | None = None, tool_context: dict | None = None):
        payload = self._build_payload(args, tool_context)
        return await self.agent.run_async(payload)

# TODO : WebPilot Agent 별 Tool 생성 
# planner_tool = WebPilotAgentTool(Planner_Agent)
domain_classifier_tool = WebPilotAgentTool(Domain_Priority_Classifier_Agent)

LLM_CLIENT = LiteLlm(model=constants.MODEL_O3_MINI)

root_agent = Agent(
    name="WebPilot_Orchestrator",
    model=LLM_CLIENT,
    description=ORCHESTRATOR_DESCRIPTION,
    instruction=ORCHESTRATOR_INSTRUCTION,
    tools=[domain_classifier_tool],
    output_key="orchestrator_result"
)



result = root_agent.run_async(
    args={
        "user_query": "서울대 도서관 예약 방법"
    }
)