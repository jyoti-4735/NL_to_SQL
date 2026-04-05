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
    async def resolve_user(self, request_context=None):
        return User(
            id="default-user",
            username="default-user",
            email="default@example.com",
            group_memberships=["admin", "user"],
            permissions=["read", "write"]
        )

def build_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    llm = GeminiLlmService(
        model="gemini-2.5-flash",
        api_key=api_key
    )

    sqlite_runner = SqliteRunner(database_path=DB_PATH)
    memory = DemoAgentMemory()
    tool_registry = ToolRegistry()

    run_sql_tool = RunSqlTool(sql_runner=sqlite_runner)
    visualize_tool = VisualizeDataTool()
    save_question_tool = SaveQuestionToolArgsTool()
    search_saved_tool = SearchSavedCorrectToolUsesTool()

    tool_registry.register_local_tool(run_sql_tool, access_groups=["admin", "user"])
    tool_registry.register_local_tool(visualize_tool, access_groups=["admin", "user"])
    tool_registry.register_local_tool(save_question_tool, access_groups=["admin"])
    tool_registry.register_local_tool(search_saved_tool, access_groups=["admin", "user"])

    user_resolver = DefaultUserResolver()

    agent = Agent(
        llm_service=llm,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=memory,
        config=AgentConfig()
    )

    return agent, memory, sqlite_runner