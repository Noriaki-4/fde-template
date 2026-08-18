"""AWS Bedrock LLM Service"""

from typing import Any
import boto3
import json

from backend.services.llm import LLMService


class BedrockLLMService(LLMService):
    """AWS Bedrock LLM Implementation"""

    def __init__(self, model_id: str, region: str = "ap-northeast-1"):
        self.model_id = model_id
        self.region = region
        self.bedrock = boto3.client("bedrock-runtime", region_name=region)

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Get completion from Bedrock Claude"""
        try:
            request_body = {
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": kwargs.get("max_tokens", 1024),
                "messages": [{"role": "user", "content": prompt}],
            }

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            result = json.loads(response["body"].read())
            if result.get("content"):
                return result["content"][0].get("text", "")
            return ""
        except Exception as e:
            raise Exception(f"Bedrock invocation error: {str(e)}")

    async def stream(self, prompt: str, **kwargs: Any):
        """Stream completion from Bedrock"""
        try:
            request_body = {
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": kwargs.get("max_tokens", 1024),
                "messages": [{"role": "user", "content": prompt}],
            }

            response = self.bedrock.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            for event in response.get("body"):
                chunk = json.loads(event["chunk"]["bytes"])
                if chunk.get("type") == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")
        except Exception as e:
            raise Exception(f"Bedrock streaming error: {str(e)}")

    async def health_check(self) -> bool:
        """Verify Bedrock access"""
        try:
            self.bedrock.list_foundation_models()
            return True
        except Exception:
            return False
