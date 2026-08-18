"""AWS AgentCore Runtime"""

from typing import Any
import boto3
import json

from backend.agent.runtime import AgentRuntime


class AgentCoreRuntime(AgentRuntime):
    """AWS AgentCore Runtime Implementation"""

    def __init__(self, agent_id: str, region: str = "ap-northeast-1"):
        self.agent_id = agent_id
        self.region = region
        self.client = boto3.client("agentcore", region_name=region)

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke AgentCore agent"""
        try:
            payload = {
                "agentId": self.agent_id,
                "input": query,
                "sessionId": context.get("session_id", "default") if context else "default",
            }

            response = self.client.invoke_agent(**payload)

            result = {"query": query, "response": "", "success": True}

            for event in response.get("events", []):
                if event.get("type") == "agent_output":
                    result["response"] = event.get("output", {}).get("text", "")

            return result
        except Exception as e:
            return {
                "query": query,
                "response": f"Agent error: {str(e)}",
                "success": False,
            }

    async def stream(self, query: str, context: dict[str, Any] | None = None):
        """Stream AgentCore response"""
        try:
            payload = {
                "agentId": self.agent_id,
                "input": query,
                "sessionId": context.get("session_id", "default") if context else "default",
            }

            response = self.client.invoke_agent(**payload)

            for event in response.get("events", []):
                if event.get("type") == "agent_output":
                    output = event.get("output", {}).get("text", "")
                    if output:
                        yield output
                elif event.get("type") == "agent_trace":
                    trace = event.get("trace", {}).get("thinking", "")
                    if trace:
                        yield f"[Trace] {trace}"
        except Exception as e:
            yield f"Streaming error: {str(e)}"

    async def health_check(self) -> bool:
        """Verify AgentCore access"""
        try:
            self.client.get_agent(agentId=self.agent_id)
            return True
        except Exception:
            return False
