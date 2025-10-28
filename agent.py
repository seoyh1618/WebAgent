# WebAgent/agent.py
from google.adk.agents import Agent 
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from WebAgent.confing import constants
from WebAgent.prompt import ORCHESTRATOR_DESCRIPTION, ORCHESTRATOR_INSTRUCTION
from dotenv import load_dotenv
import json
import logging


logger = logging.getLogger(__name__)
load_dotenv()

# WebPilot Agent Wrapper Tool
class WebPilotAgentTool(AgentTool):
    def __init__(self, agent: Agent):
        super().__init__(agent=agent)

# TODO : WebPilot Agent 별 Tool 생성 
# planner_tool = WebPilotAgentTool(Planner_Agent)
# domain_classifier_tool = WebPilotAgentTool(Domain_Priority_Classifier_Agent)

LLM_CLIENT = LiteLlm(model=constants.MODEL_O3_MINI)

root_agent = Agent(
    name="WebPilot_Orchestrator",
    model=LLM_CLIENT,
    description=ORCHESTRATOR_DESCRIPTION,
    instruction=ORCHESTRATOR_INSTRUCTION,
    output_key="orchestrator_result"
)

