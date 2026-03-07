"""
Base Agent - Foundation class for all Affiliate Marketing Agency agents.
Provides common interface, state management, and LLM interaction patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config.settings import AgencyConfig


@dataclass
class AgentMessage:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_name: str
    task: str
    output: Any
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents in the Affiliate Marketing Agency."""

    def __init__(self, name: str, config: AgencyConfig, llm_client: Any = None,
                 db_conn: Any = None):
        self.name = name
        self.config = config
        self.llm_client = llm_client
        self.db_conn = db_conn
        self.memory: list[AgentMessage] = []
        self.results: list[AgentResult] = []
        self._load_from_db()

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Define the agent's system prompt / persona."""
        ...

    @abstractmethod
    def execute(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute the agent's primary task."""
        ...

    def _load_from_db(self) -> None:
        """Restore memory and results from the database."""
        if not self.db_conn:
            return
        from utils.persistence import load_memory, load_results
        for row in load_memory(self.db_conn, self.name):
            self.memory.append(AgentMessage(
                role=row["role"], content=row["content"],
                timestamp=row["timestamp"], metadata=row["metadata"],
            ))
        for row in load_results(self.db_conn, self.name):
            self.results.append(AgentResult(
                agent_name=row["agent_name"], task=row["task"],
                output=row["output"], success=row["success"],
                timestamp=row["timestamp"], errors=row["errors"],
                metadata=row["metadata"],
            ))

    def _persist_memory(self, msg: AgentMessage) -> None:
        if not self.db_conn:
            return
        from utils.persistence import save_memory
        save_memory(self.db_conn, self.name, msg.role, msg.content,
                    msg.timestamp, msg.metadata)

    def _persist_result(self, result: AgentResult) -> None:
        if not self.db_conn:
            return
        from utils.persistence import save_result
        save_result(self.db_conn, result.agent_name, result.task,
                    result.output, result.success, result.timestamp,
                    result.errors, result.metadata)

    def add_to_memory(self, role: str, content: str, **metadata: Any) -> None:
        msg = AgentMessage(role=role, content=content, metadata=metadata)
        self.memory.append(msg)
        self._persist_memory(msg)

    def get_memory_context(self, last_n: int = 10) -> list[dict[str, str]]:
        messages = self.memory[-last_n:]
        return [{"role": m.role, "content": m.content} for m in messages]

    def call_llm(self, prompt: str, system: str | None = None) -> str:
        """Call the LLM with the agent's system prompt and given user prompt."""
        sys_prompt = system or self.system_prompt
        self.add_to_memory("user", prompt)

        if self.llm_client is None:
            # Return a structured placeholder when no LLM client is configured
            response = f"[{self.name}] LLM response placeholder for: {prompt[:100]}..."
        else:
            messages = [{"role": "system", "content": sys_prompt}]
            messages.extend(self.get_memory_context())
            try:
                response = self._invoke_llm(messages)
            except Exception as e:
                self.log(f"LLM call failed: {e}")
                response = f"[{self.name}] LLM call failed: {type(e).__name__}: {str(e)[:200]}"

        self.add_to_memory("assistant", response)
        return response

    def _invoke_llm(self, messages: list[dict[str, str]]) -> str:
        """Override this method to integrate with specific LLM providers."""
        if hasattr(self.llm_client, "messages"):
            # Anthropic client
            system_msg = ""
            chat_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    chat_messages.append(m)
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system_msg,
                messages=chat_messages,
            )
            return response.content[0].text
        elif hasattr(self.llm_client, "chat"):
            # OpenAI client
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return response.choices[0].message.content
        return str(self.llm_client)

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {message}")
