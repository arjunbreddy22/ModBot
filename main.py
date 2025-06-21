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

        # Update rules if provided
        if server_rules:
            self.update_rules_text(server_rules)
        else:
            # default baked-in system prompt
            self.system_prompt = """You are an expert Discord moderation agent.

Moderation rules:
- Hate speech → Ban
- Harassment → Ban
- Spam → Ban
- Mild insults → Delete
- Repeated minor violations → Warn
- Normal messages → OK

Respond ONLY with one word: OK, Delete, Warn, or Ban."""

            # Build empty agent — no tools
            self.agent = ReActAgent.from_tools(
                tools=[],
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

        # Store rules_text into self.server_rules
        self.server_rules = rules_text

        # Build new system prompt — replacing old baked-in rules
        self.system_prompt = f"""You are an expert Discord moderation agent.

Follow these exact moderation rules:

{rules_text}

Respond ONLY with one word: OK, Delete, Warn, or Ban."""

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
