#llm.py
import os
from openai import OpenAI
from typing import List, Dict, Tuple, Union # Import Union for more flexible type hinting
import json # Import json for pretty printing

class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def chat(self, messages: List[Dict], temperature: float = 0.7) -> Tuple[str, int, int]:
        print("DEBUG: Messages sent to OpenAI API:")
        print(json.dumps(messages, indent=2)) # Pretty print the messages list
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )

            raw_content = response.choices[0].message.content

            # Robustly extract content: it could be a string or a list of content blocks
            if isinstance(raw_content, str):
                extracted_content = raw_content.strip()
            elif isinstance(raw_content, list) and len(raw_content) > 0 and isinstance(raw_content[0], dict) and raw_content[0].get('type') == 'text':
                # Concatenate text from all text blocks if there are multiple, otherwise take the first.
                extracted_content = " ".join([block.get('text', '') for block in raw_content if isinstance(block, dict) and block.get('type') == 'text']).strip()
                if len(raw_content) > 1:
                    print("WARNING: LLM response had multiple content blocks. Concatenating them.")
            else:
                # Fallback for unexpected content types
                extracted_content = str(raw_content).strip()
                print(f"WARNING: Unexpected LLM response content type. Raw content: {raw_content}")

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            return extracted_content, prompt_tokens, completion_tokens
        except Exception as e:
            print(f"DEBUG: Error during OpenAI API call: {e}")
            raise # Re-raise the exception after logging
