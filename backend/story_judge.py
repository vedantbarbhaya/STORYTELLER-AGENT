"""
A lightweight LLM-powered judge that evaluates the quality of a generated
children's story against a research-based rubric.

The judge currently focuses on *scoring* and *feedback generation*.  It is
implemented as a thin wrapper around an LLM call so that the rubric can evolve
rapidly without code changes—only the prompt needs updating.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

import textstat
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from arc_generator import StoryArc, StoryStage
from prompts import STORY_JUDGE_FIRST_PASS_PROMPT, STORY_JUDGE_REFINEMENT_PASS_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper – convert a StoryArc object back to a readable blueprint string.
# ---------------------------------------------------------------------------

def _story_arc_to_blueprint(arc: StoryArc) -> str:
    """Return a compact, human-readable text version of a StoryArc."""
    lines = [
        f"PREMISE: {arc.premise}",
        f"THEME: {arc.theme}",
        f"CHARACTER DYNAMICS: Primary: {arc.dynamics.primary_character}, "
        f"Support: {', '.join(arc.dynamics.support_characters)}, "
        f"Strength: {arc.dynamics.group_strength}, "
        f"Conflict: {arc.dynamics.potential_conflict}",
    ]
    lines.append("STAGES:")
    for stage in StoryStage:
        if stage in arc.stages:
            lines.append(f"  - {stage.name}: {arc.stages[stage]}")
    if arc.special_notes:
        lines.append("SPECIAL NOTES:")
        for note in arc.special_notes:
            lines.append(f"  - {note}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# StoryQualityJudge – primary public class
# ---------------------------------------------------------------------------

class StoryQualityJudge:
    """
    Evaluates a generated story using a combination of an LLM-based rubric
    and objective, automated text analysis.
    """

    # --- Weighted scoring configuration ---
    SCORE_WEIGHTS = {
        'structure': 0.25,
        'theme': 0.20,
        'characters': 0.15,
        'age_appropriateness': 0.15,
        'engagement': 0.10,
        'language_quality': 0.10,
        'safety': 0.05,
    }

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            self.client = None
            logger.warning("OpenAI API key not found. StoryQualityJudge will be disabled.")
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def is_available(self) -> bool:
        return self.client is not None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def comprehensive_evaluation(
        self,
        story: str,
        arc: StoryArc,
        generation_params: Dict[str, Any] | None = None,
        is_first_pass: bool = True,
    ) -> Dict[str, Any]:
        """
        Return a dict with scores, rationales, objective metrics, and a final verdict.
        """
        if not self.is_available():
            raise RuntimeError("StoryQualityJudge is not available – missing API key.")

        llm_feedback = self._get_llm_evaluation(story, arc, generation_params, is_first_pass)
        objective_metrics = self._calculate_objective_metrics(story)
        weighted_score = self._calculate_heuristic_score(llm_feedback)
        
        return {
            "final_weighted_score": round(weighted_score, 2),
            "actionable_feedback": llm_feedback,
            "objective_metrics": objective_metrics,
            "llm_evaluations": llm_feedback,
        }

    # ---------------------------------------------------------------------
    # Private Helper Methods
    # ---------------------------------------------------------------------

    def _get_llm_evaluation(self, story: str, arc: StoryArc, generation_params: Dict[str, Any] | None, is_first_pass: bool) -> Dict[str, Any]:
        """Calls the LLM with the rubric prompt and returns the parsed JSON."""
        logger.info("Getting subjective evaluation from LLM...")

        arc_blueprint = _story_arc_to_blueprint(arc)
        params_block = json.dumps(generation_params or {}, indent=2)
        
        prompt_template = STORY_JUDGE_FIRST_PASS_PROMPT if is_first_pass else STORY_JUDGE_REFINEMENT_PASS_PROMPT

        user_content = f"""STORY ARC BLUEPRINT
--------------------
{arc_blueprint}

STORY
-----
{story}

GENERATION PARAMS
-----------------
{params_block}
"""
        messages = [{"role": "system", "content": prompt_template}, {"role": "user", "content": user_content}]

        try:
            completion = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=min(0.3, OPENAI_TEMPERATURE),
            )
            raw_response = completion.choices[0].message.content.strip()
            logger.info("Raw LLM judge response:\n%s", raw_response)
            return json.loads(raw_response)
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.error(f"Judge returned invalid data: {e}. Returning fallback result.")
            return {"GLOBAL": [f"Evaluation failed: {e}"]}

    def _calculate_objective_metrics(self, story: str) -> Dict[str, Any]:
        """Calculates objective text statistics."""
        logger.info("Calculating objective text metrics...")
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(story),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(story),
            "smog_index": textstat.smog_index(story),
            "dale_chall_readability_score": textstat.dale_chall_readability_score(story),
            "word_count": textstat.lexicon_count(story),
            "sentence_count": textstat.sentence_count(story),
        }

    def _calculate_heuristic_score(self, llm_scores: Dict[str, Any]) -> float:
        """
        Calculates a heuristic score. The less feedback given, the higher the score.
        """
        logger.info("Calculating heuristic score based on feedback volume...")
        
        MAX_SCORE = 5.0
        GLOBAL_FEEDBACK_PENALTY = 0.5
        STAGE_FEEDBACK_PENALTY = 0.25

        score = MAX_SCORE
        
        for stage, feedback_list in llm_scores.items():
            if stage == "GLOBAL":
                score -= len(feedback_list) * GLOBAL_FEEDBACK_PENALTY
            else:
                score -= len(feedback_list) * STAGE_FEEDBACK_PENALTY
        
        return max(1.0, score) 