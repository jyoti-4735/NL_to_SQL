import os
from dotenv import load_dotenv

from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

load_dotenv()

DB_PATH = "clinic.db"

class DefaultUserResolver(UserResolver):
    def resolve_user(self, request=None):
        return User(id="default-user", name="Default User")

def build_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    llm = GeminiLlmService(
        model="gemini-2.5-flash",
        api_key=api_key
    )

    sqlite_runner = SqliteRunner(database=DB_PATH)
    memory = DemoAgentMemory()
    tool_registry = ToolRegistry()

    run_sql_tool = RunSqlTool(sql_runner=sqlite_runner)
    visualize_tool = VisualizeDataTool()
    save_question_tool = SaveQuestionToolArgsTool(agent_memory=memory)
    search_saved_tool = SearchSavedCorrectToolUsesTool(agent_memory=memory)

    tool_registry.register(run_sql_tool)
    tool_registry.register(visualize_tool)
    tool_registry.register(save_question_tool)
    tool_registry.register(search_saved_tool)

    user_resolver = DefaultUserResolver()

    agent = Agent(
        config=AgentConfig(name="clinic-nl2sql-agent"),
        llm=llm,
        tool_registry=tool_registry,
        agent_memory=memory,
        user_resolver=user_resolver,
    )

    return agent, memory, sqlite_runner