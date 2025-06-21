'''
import random
from typing import List, Optional

class ModerationAgent:
    """
    Placeholder ModerationAgent for testing integration with the bot.
    Contains stubs for init, moderate_message, and update_rules.
    """
    def __init__(self):
        """
        Initialize the moderation agent.
        Args:
            rules_source: Optional path or text representing server rules.
        """
        self.rules_source = None
        print(f"[ModerationAgent] Initialized with rules_source={self.rules_source}")

    async def moderate_message(self, message: str, context: Optional[List[str]] = None) -> str:
        """
        Decide what to do with an incoming message.
        Returns one of: "OK", "DELETE", "WARN", "BAN".
        """
        # Placeholder logic: choose action at random
        return "OK"

    async def update_rules(self, rules_source: str) -> None:
        """
        Update the agent's rules.
        Args:
            rules_source: New source for server rules (path or text).
        """
        self.rules_source = rules_source
        print(f"[ModerationAgent] update_rules called; new rules_source={self.rules_source}")
        # TODO: implement actual rules loading logic
        return
'''

# agent_service.py

from os import environ
from dotenv import load_dotenv
from typing import List, Optional, cast

# Load env vars
load_dotenv()
OPENAI_API_KEY = environ["OPENAI_API_KEY"]

from llama_index.core import VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata, BaseTool
from llama_index.llms.openai import OpenAI
from llama_index.core.schema import Document

class ModerationAgent:
    def __init__(
        self,
        server_rules: Optional[str] = None,  # server rules passed as a big string
        model_name: str = "gpt-4o",
    ):
        # Load LLM
        self.llm = OpenAI(model=model_name)

        # Base system prompt — define moderation behavior
        self.system_prompt = """
        You are an expert Discord moderation agent.

        Moderation rules:
        - Hate speech → Ban
        - Harassment → Ban
        - Spam → Ban
        - Mild insults → Delete
        - Repeated minor violations → Warn
        - Normal messages → OK

        If you have access to a server_rules tool, you may use it to look up specific rules.

        Respond ONLY with one word: OK, Delete, Warn, or Ban.
        """

        # Build tools list (empty by default)
        tools: List[BaseTool] = []

        if server_rules:
            print("Loading server rules from text...")
            rules_doc = Document(
                text=server_rules,
                metadata={"source": "server_rules_channel"}
            )

            rules_index = VectorStoreIndex.from_documents([rules_doc])
            rules_engine = rules_index.as_query_engine(similarity_top_k=3)

            rules_tool = QueryEngineTool(
                query_engine=rules_engine,
                metadata=ToolMetadata(
                    name="server_rules",
                    description="Provides information about server moderation policies.",
                ),
            )

            tools.append(rules_tool)

        # Build agent
        self.agent = ReActAgent.from_tools(
            tools=cast(List[BaseTool], tools),
            llm=self.llm,
            verbose=True,
            system_prompt=self.system_prompt,
            max_turns=3,
        )

    def moderate_message(self, message: str, context: Optional[List[str]] = None) -> str:
        VALID_ACTIONS = {"OK", "Delete", "Warn", "Ban"}

        if context is None:
            context = []

        # Use last 5 messages for context
        context_text = "\n".join(context[-5:])

        # Build full prompt
        full_prompt = f"""
Context:
{context_text}

New Message:
"{message}"

Decide moderation action.

You MUST respond with exactly one of these words (no other text):
OK, Delete, Warn, or Ban
"""

        # Call agent
        response = self.agent.chat(full_prompt)
        action = str(response).strip()

        # Hard fallback — only allow valid actions
        if action not in VALID_ACTIONS:
            print(f"[WARNING] Invalid action returned: {action}. Defaulting to OK.")
            action = "OK"

        print(f"Moderation decision: {action}")
        return action

    def update_rules_text(self, rules_text: str) -> None:
        """Load server rules from a plain text string (instead of a file)."""
        print("Loading new server rules from text...")

        # Convert rules_text into a document object for indexing
        rules_doc = Document(text=rules_text, metadata={"source": "server_rules_channel"})

        # Build new index
        rules_index = VectorStoreIndex.from_documents([rules_doc])
        rules_engine = rules_index.as_query_engine(similarity_top_k=3)

        # Build tool
        rules_tool = QueryEngineTool(
            query_engine=rules_engine,
            metadata=ToolMetadata(
                name="server_rules",
                description="Provides information about server moderation policies.",
            ),
        )

        # Create new agent with updated rules tool
        tools: List[BaseTool] = [rules_tool]
        self.agent = ReActAgent.from_tools(
            tools=cast(List[BaseTool], tools),
            llm=self.llm,
            verbose=True,
            system_prompt=self.system_prompt,
            max_turns=3,
        )

        print("Server rules updated successfully from text.")


