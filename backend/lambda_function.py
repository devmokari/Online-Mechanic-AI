"""AWS Lambda handler for Online Mechanic AI.

This module orchestrates the diagnostic pipeline:
    1. Validate and persist incoming media to S3.
    2. Build a multimodal prompt combining user text and media references.
    3. Dispatch the prompt to OpenAI's GPT-4o model for analysis.
    4. Return a structured diagnostic response ready for the frontend.

The handler is intentionally lightweight so it can run comfortably inside the
Lambda execution environment.  Most heavy lifting is delegated to helper
functions that can be unit tested in isolation.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import botocore.exceptions
import openai
from dotenv import load_dotenv

from utils.s3_helper import S3Object, upload_media_from_base64

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
S3_BUCKET = os.getenv("S3_BUCKET")


def _init_openai_client() -> openai.OpenAI:
    """Initialise and cache the OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return openai.OpenAI(api_key=api_key)


@dataclass
class DiagnosticRequest:
    """Represents the body of the incoming API Gateway event."""

    description: str
    media_base64: Optional[str] = None
    media_filename: Optional[str] = None

    @classmethod
    def from_event(cls, event: Dict[str, Any]) -> "DiagnosticRequest":
        try:
            body = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                body = base64.b64decode(body).decode("utf-8")
            payload = json.loads(body)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Request body is not valid JSON") from exc

        description = payload.get("description", "").strip()
        if not description:
            raise ValueError("Description is required")

        return cls(
            description=description,
            media_base64=payload.get("media"),
            media_filename=payload.get("filename"),
        )


@dataclass
class DiagnosticResponse:
    """Structured response returned to API Gateway."""

    summary: str
    potential_causes: list[str]
    safety_checks: list[str]
    recommended_actions: list[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "potential_causes": self.potential_causes,
            "safety_checks": self.safety_checks,
            "recommended_actions": self.recommended_actions,
        }


def _build_messages(request: DiagnosticRequest, media_object: Optional[S3Object]) -> list[Dict[str, Any]]:
    """Construct the multimodal chat messages for GPT-4o."""
    user_content: list[Dict[str, Any]] = [
        {"type": "text", "text": f"User description: {request.description}"},
    ]

    if media_object:
        user_content.append(
            {
                "type": "input_image",
                "image_url": {
                    "url": media_object.presigned_url,
                },
            }
        )

    return [
        {
            "role": "system",
            "content": (
                "You are an experienced automotive mechanic. Analyse the user's "
                "description and the provided media to produce a concise diagnostic "
                "report."
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def _invoke_openai(messages: list[Dict[str, Any]]) -> DiagnosticResponse:
    client = _init_openai_client()

    text: str = ""

    responses_api = getattr(client, "responses", None)
    if responses_api and hasattr(responses_api, "create"):
        completion = responses_api.create(
            model=OPENAI_MODEL,
            input=messages,
            max_output_tokens=800,
        )
        text = getattr(completion, "output_text", "") or ""
    else:
        chat_api = getattr(client, "chat", None)
        if not chat_api or not hasattr(chat_api, "completions"):
            raise RuntimeError("OpenAI client does not support responses or chat completions APIs")

        completion = chat_api.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=800,
        )

        if completion.choices:
            message = completion.choices[0].message
            content = getattr(message, "content", "")
            if isinstance(content, list):
                text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            else:
                text = content or ""

    text = text.strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty response")

    # Basic parsing: expect a JSON document; fallback to plain text summary.
    try:
        parsed = json.loads(text)
        return DiagnosticResponse(
            summary=parsed.get("summary", text),
            potential_causes=list(parsed.get("potential_causes", [])),
            safety_checks=list(parsed.get("safety_checks", [])),
            recommended_actions=list(parsed.get("recommended_actions", [])),
        )
    except json.JSONDecodeError:
        return DiagnosticResponse(
            summary=text,
            potential_causes=[],
            safety_checks=[],
            recommended_actions=[],
        )


def lambda_handler(event: Dict[str, Any], _context: Optional[Any]) -> Dict[str, Any]:
    """Entry point for AWS Lambda."""
    LOGGER.info("Received event: %s", event.keys())

    try:
        request = DiagnosticRequest.from_event(event)
        media_object: Optional[S3Object] = None

        if request.media_base64 and request.media_filename:
            if not S3_BUCKET:
                raise RuntimeError("S3_BUCKET environment variable is not set")

            media_object = upload_media_from_base64(
                bucket=S3_BUCKET,
                base64_payload=request.media_base64,
                filename=request.media_filename,
            )

        messages = _build_messages(request, media_object)
        response = _invoke_openai(messages)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response.as_dict()),
        }

    except (ValueError, RuntimeError, botocore.exceptions.BotoCoreError) as exc:
        LOGGER.exception("Error processing diagnostic request")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(exc)}),
        }



if __name__ == "__main__":
    sample_event = {
        "body": json.dumps({
            "description": "Sample issue description",
            "media": None,
        })
    }
    result = lambda_handler(sample_event, None)
    print(json.dumps(result, indent=2))
