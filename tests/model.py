import logging
import os

import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate(prompt: str) -> str:
    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        output = response.output_text
        logging.info(
            {
                "prompt": prompt,
                "output": output,
            }
        )
        return output
    except Exception as e:
        logging.error(f"Model call failed: {e}")
        return "Error: model request failed"
