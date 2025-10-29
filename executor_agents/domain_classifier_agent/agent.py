# WebAgent/executor_agents/domain_classifier_agent/agent.py

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from WebAgent.confing import constants
from WebAgent.executor_agents.domain_classifier_agent.prompt import (
    DOMAIN_CLASSIFIER_DESCRIPTION,
    DOMAIN_CLASSIFIER_INSTRUCTION
)
from WebAgent.executor_agents.domain_classifier_agent.functions import (
    enhance_query,
    execute_google_search_tool,
)
from dotenv import load_dotenv
load_dotenv()

# LLM Client 초기화
LLM_CLIENT = LiteLlm(model=constants.MODEL_GPT_4O_MINI)

# Domain Classifier Agent 생성
Domain_Priority_Classifier_Agent = Agent(
    name="Domain_Priority_Classifier",
    model=LLM_CLIENT,
    description=DOMAIN_CLASSIFIER_DESCRIPTION,
    instruction=DOMAIN_CLASSIFIER_INSTRUCTION,
    tools=[FunctionTool(enhance_query), FunctionTool(execute_google_search_tool)],
    output_key="domain_classification_result",
    input_data_schema={
        "type": "object",
        "properties": {
            "user_query": {
                "type": "string",
                "description": "사용자의 질의"
            }
        },
        "required": ["user_query"]
    }
)
