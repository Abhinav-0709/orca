"""Agent Chat Protocol (ACP) router and message envelopes for Fetch multi-agent communication."""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine
from pydantic import BaseModel, Field

from orca.logging.logger import get_logger
from orca.models.agent_contract import AgentError, AgentRequest, AgentResponse, AgentStatus

logger = get_logger(__name__, agent="acp_router")


class ACPMessageType(str, Enum):
    """ACP message type classification."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    ACK = "ack"


class ACPMessage(BaseModel):
    """Standard Agent Chat Protocol (ACP) message envelope."""

    message_id: str = Field(default_factory=lambda: f"acp-{uuid.uuid4().hex[:12]}")
    protocol: str = Field(default="acp/orca/v1", description="Protocol version identifier")
    source: str = Field(description="Sending agent identifier (e.g. 'commander')")
    destination: str = Field(description="Receiving agent identifier (e.g. 'ocean', 'weather')")
    message_type: ACPMessageType = Field(default=ACPMessageType.REQUEST)
    request_id: str = Field(description="Originating request trace ID")
    payload: dict[str, Any] = Field(description="Serialized AgentRequest or AgentResponse payload")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return self.model_dump()


class ACPRouter:
    """Dispatches ACP messages between Commander and registered Specialist Agents."""

    def __init__(self, default_timeout_seconds: float = 10.0) -> None:
        self.default_timeout = default_timeout_seconds
        # Mapping: agent_name -> handler_callable(AgentRequest) -> Coroutine[Any, Any, AgentResponse]
        self._handlers: dict[str, Callable[[AgentRequest], Coroutine[Any, Any, AgentResponse]]] = {}

    def register_agent(
        self,
        name: str,
        handler: Callable[[AgentRequest], Coroutine[Any, Any, AgentResponse]],
    ) -> None:
        """Register a specialist agent to receive and process ACP messages.

        Args:
            name: Agent identifier (e.g. 'ocean', 'weather', 'maritime', 'evidence').
            handler: Async function or agent process method taking AgentRequest and returning AgentResponse.
        """
        self._handlers[name] = handler
        logger.info(f"Registered agent '{name}' on ACPRouter")

    def unregister_agent(self, name: str) -> None:
        """Unregister an agent."""
        if name in self._handlers:
            del self._handlers[name]

    def is_agent_registered(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._handlers

    async def send_request(
        self,
        source: str,
        destination: str,
        agent_request: AgentRequest,
        timeout_seconds: float | None = None,
    ) -> AgentResponse:
        """Wrap and route an AgentRequest over ACP to the destination specialist.

        Args:
            source: Initiating agent (typically 'commander').
            destination: Target agent ('ocean', 'weather', 'maritime', 'evidence').
            agent_request: Standard AgentRequest model.
            timeout_seconds: Timeout for response (defaults to self.default_timeout).

        Returns:
            AgentResponse: Response from specialist agent or structured ACP timeout/failure envelope.
        """
        timeout = timeout_seconds or self.default_timeout
        trace_id = agent_request.request_id

        # Construct outgoing ACP envelope
        msg = ACPMessage(
            source=source,
            destination=destination,
            message_type=ACPMessageType.REQUEST,
            request_id=trace_id,
            payload=agent_request.model_dump(),
        )

        logger.info(
            f"ACP dispatch [{msg.message_id}] from '{source}' to '{destination}' (req: {trace_id})"
        )

        handler = self._handlers.get(destination)
        if not handler:
            err_msg = f"Agent '{destination}' not registered on ACPRouter"
            logger.error(err_msg)
            return AgentResponse(
                agent=destination,
                status=AgentStatus.UNAVAILABLE,
                request_id=trace_id,
                error=AgentError(type="AGENT_NOT_FOUND", message=err_msg, retryable=False),
                confidence=0.0,
            )

        try:
            # Execute with timeout enforcement
            resp: AgentResponse = await asyncio.wait_for(
                handler(agent_request),
                timeout=timeout,
            )
            logger.info(
                f"ACP response received from '{destination}' for req '{trace_id}': status={resp.status.value}"
            )
            return resp

        except asyncio.TimeoutError:
            logger.warning(
                f"ACP request to '{destination}' timed out after {timeout}s for req '{trace_id}'"
            )
            return AgentResponse(
                agent=destination,
                status=AgentStatus.TIMEOUT,
                request_id=trace_id,
                error=AgentError(
                    type="TIMEOUT",
                    message=f"Specialist agent '{destination}' failed to respond within {timeout} seconds",
                    retryable=True,
                ),
                confidence=0.0,
            )

        except Exception as exc:
            logger.exception(
                f"ACP error invoking agent '{destination}' for req '{trace_id}': {exc}"
            )
            return AgentResponse(
                agent=destination,
                status=AgentStatus.FAILED,
                request_id=trace_id,
                error=AgentError(
                    type="AGENT_EXECUTION_ERROR",
                    message=f"Agent '{destination}' threw an unhandled exception: {str(exc)}",
                    retryable=False,
                    details={"exception_type": type(exc).__name__},
                ),
                confidence=0.0,
            )
