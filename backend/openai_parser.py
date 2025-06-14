"""OpenAI-based story parser for extracting structured story elements from user input."""

import json
import logging
from typing import Dict, Any, Literal
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from prompts import STORY_PARSER_SYSTEM_PROMPT, STORY_PARSER_SCHEMA


class OpenAIStoryParser:
    """Advanced story parser using OpenAI's API for natural language understanding."""
    
    def __init__(self):
        """Initialize the OpenAI client with configuration."""
        if not OPENAI_API_KEY:
            logging.warning("OpenAI API key not found. OpenAI parsing will not be available.")
            self.client = None
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            logging.info(f"OpenAI parser initialized with model: {OPENAI_MODEL}")
    
    def is_available(self) -> bool:
        """Check if OpenAI parsing is available."""
        return self.client is not None
    
    def parse_prompt(
        self,
        prompt: str,
        *,
        mode: Literal["json", "function"] = "json",
        temperature: float = None,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Parse a story prompt into structured elements using OpenAI.
        
        Parameters
        ----------
        prompt : str
            User-supplied story description.
        mode : "json" | "function"
            • "json"     → simpler, leverages JSON mode.  
            • "function" → stricter, uses structured output / function calling.
        temperature : float
            Override default temperature for this request.
        max_retries : int
            Number of retry attempts on failure.
            
        Returns
        -------
        Dict containing parsed story elements: characters, relationships, setting.
        """
        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured. Cannot use OpenAI parsing.")
        
        # Use configured temperature or override
        temp = temperature if temperature is not None else OPENAI_TEMPERATURE
        
        messages = [
            {"role": "system", "content": STORY_PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(max_retries + 1):
            try:
                if mode == "json":
                    completion = self.client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=messages,
                        temperature=temp,
                        response_format={"type": "json_object"},
                    )
                    raw_json = completion.choices[0].message.content
                    return json.loads(raw_json)
                    
                else:  # function calling mode
                    completion = self.client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=messages,
                        tools=[{"type": "function", "function": STORY_PARSER_SCHEMA}],
                        tool_choice={"type": "function", "function": {"name": "create_story_schema"}},
                        temperature=temp,
                    )
                    tool_call = completion.choices[0].message.tool_calls[0]
                    return json.loads(tool_call.function.arguments)
                    
            except Exception as exc:
                logging.warning(f"OpenAI parse attempt {attempt + 1} failed: {exc}")
                if attempt == max_retries:
                    raise RuntimeError(f"OpenAI parsing failed after {max_retries + 1} attempts: {exc}")


# Demo function for testing
def demo_parser():
    """Quick demonstration of the OpenAI parser."""
    parser = OpenAIStoryParser()
    
    if not parser.is_available():
        print("OpenAI API key not configured. Skipping demo.")
        return
    
    sample = "A story about a girl named Alice and her best friend Bob, who happens to be a cat"
    
    print("=== OpenAI Story Parser Demo ===")
    print(f"Input: {sample}")
    print("\n=== JSON Mode ===")
    try:
        result = parser.parse_prompt(sample, mode="json")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Function Calling Mode ===")
    try:
        result = parser.parse_prompt(sample, mode="function")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    demo_parser() 