"""AWS Bedrock AgentCore Runtime"""

from typing import Any
import boto3
import json

from backend.services.agent import AgentService


class AgentCoreService(AgentService):
    """AWS Bedrock AgentCore Implementation"""

    def __init__(self, agent_runtime_arn: str, region: str = "ap-northeast-1"):
        self.agent_runtime_arn = agent_runtime_arn
        self.region = region
        self.client = boto3.client("bedrock-agentcore", region_name=region)

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke AgentCore runtime agent"""
        try:
            session_id = context.get("session_id", "default") if context else "default"
            payload = json.dumps({"query": query}).encode("utf-8")

            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_runtime_arn,
                runtimeSessionId=session_id,
                payload=payload,
                contentType="application/json",
                accept="application/json",
            )

            body = json.loads(response["response"].read())
            return {"query": query, "response": body.get("output", body), "success": True}
        except Exception as e:
            return {
                "query": query,
                "response": f"Agent error: {str(e)}",
                "success": False,
            }

    async def stream(self, query: str, context: dict[str, Any] | None = None):
        """Stream AgentCore runtime response"""
        try:
            session_id = context.get("session_id", "default") if context else "default"
            payload = json.dumps({"query": query}).encode("utf-8")

            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_runtime_arn,
                runtimeSessionId=session_id,
                payload=payload,
                contentType="application/json",
                accept="application/json",
            )

            for chunk in response["response"].iter_chunks():
                if chunk:
                    yield chunk.decode("utf-8")
        except Exception as e:
            yield f"Streaming error: {str(e)}"

    async def health_check(self) -> bool:
        """Verify AgentCore runtime access"""
        try:
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_runtime_arn,
                runtimeSessionId="health-check",
                payload=json.dumps({"query": "ping"}).encode("utf-8"),
                contentType="application/json",
                accept="application/json",
            )
            response["response"].read()
            return True
        except Exception:
            return False
