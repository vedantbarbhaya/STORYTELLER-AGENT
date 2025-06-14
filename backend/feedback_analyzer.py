"""
This module contains the FeedbackAnalyzer, a component responsible for
classifying user feedback and preparing it for the story modification engine.

It uses a two-step "Classifier-then-Executor" pattern:
1.  A cheap, fast LLM call classifies the user's intent into a specific category.
2.  A second, more sophisticated LLM call uses a tailored prompt based on that
    category to generate a structured, actionable rewrite plan.
"""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, List

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from prompts import get_feedback_analysis_prompt

logger = logging.getLogger(__name__)

class FeedbackAnalyzer:
    """Analyzes user feedback to create a structured, multi-step plan for story revision."""

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            self.client = None
            logger.warning("OpenAI API key not found. FeedbackAnalyzer will be disabled.")
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def is_available(self) -> bool:
        return self.client is not None

    def analyze_user_feedback(self, user_feedback: str, original_story: str) -> List[Dict[str, Any]]:
        """
        Analyzes feedback using a Chain of Thought prompt to produce a multi-step action plan.
        """
        if not self.is_available():
            raise RuntimeError("FeedbackAnalyzer is not available due to missing API key.")

        prompt = get_feedback_analysis_prompt()
        
        user_content = f"""
<OriginalStory>
{original_story}
</OriginalStory>

<UserFeedback>
{user_feedback}
</UserFeedback>
"""

        try:
            completion = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            response_text = completion.choices[0].message.content.strip()
            parsed_json = json.loads(response_text)
            
            logger.info(f"AI Reasoning: {parsed_json.get('reasoning', 'None provided.')}")

            action_plan = parsed_json.get("action_plan", [])
            if not isinstance(action_plan, list):
                logger.error("The 'action_plan' in the AI response was not a list.")
                raise TypeError("The 'action_plan' in the AI response was not a list.")

            return action_plan
        except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as e:
            logger.error(f"Error parsing multi-action plan from LLM: {e}")
            # Fallback to a single, simple rewrite action
            return [
                {
                    "strategy": "SECTION_REWRITE",
                    "payload": {
                        "GLOBAL": [f"User requested a change, but it could not be structured. Original request: '{user_feedback}'"]
                    }
                }
            ] 