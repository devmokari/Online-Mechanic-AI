"""Store the OpenAI API key in the Lambda environment."""
from __future__ import annotations

import sys

import boto3


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit("Usage: python set_openai_key.py <api-key>")

    key = argv[1]
    lambda_name = "mechanic-ai-lambda"

    client = boto3.client("lambda")
    client.update_function_configuration(
        FunctionName=lambda_name,
        Environment={"Variables": {"OPENAI_API_KEY": key}},
    )
    print("✅ OpenAI key updated successfully in AWS Lambda.")


if __name__ == "__main__":
    main(sys.argv)
