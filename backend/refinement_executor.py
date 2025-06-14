"""
This module is responsible for executing a multi-step action plan
to refine a story.
"""
from __future__ import annotations
import logging
import json
from typing import List, Dict, Any

from arc_generator import StoryArc, StoryStage
from story_generator import StoryGenerator

logger = logging.getLogger(__name__)

class RefinementExecutor:
    """Executes a refinement plan to modify a story."""

    def __init__(self, story_generator: StoryGenerator):
        self.story_generator = story_generator

    def execute_plan(
        self,
        action_plan: List[Dict[str, Any]],
        original_story: str,
        story_arc: StoryArc,
    ) -> str:
        """
        Sequentially executes each action in the plan.
        
        It efficiently performs all simple string replacements first, then
        aggregates all rewrite tasks and performs them in a single pass.
        """
        current_story_text = original_story
        rewrite_feedback = {}

        # First, execute all simple string replacements for efficiency
        for action in action_plan:
            if action.get("strategy") == "STRING_REPLACEMENT":
                payload = action.get("payload", {})
                find_text = payload.get("find")
                replace_text = payload.get("replace")
                if find_text and replace_text:
                    logger.info(f"Executing STRING_REPLACEMENT: Replacing '{find_text}' with '{replace_text}'")
                    current_story_text = current_story_text.replace(find_text, replace_text)
            elif action.get("strategy") == "SECTION_REWRITE":
                # Aggregate all rewrite instructions
                payload = action.get("payload", {})
                for stage, critiques in payload.items():
                    if stage not in rewrite_feedback:
                        rewrite_feedback[stage] = []
                    rewrite_feedback[stage].extend(critiques)

        # Now, if there are any rewrite tasks, perform them once
        if rewrite_feedback:
            logger.info(f"Executing SECTION_REWRITE with feedback: {json.dumps(rewrite_feedback, indent=2)}")
            
            stage_order = list(StoryStage)
            first_dirty_stage = next((s for s in stage_order if rewrite_feedback.get(s.name)), stage_order[0])
            
            # This logic for finding 'good chapters' is complex and can be improved.
            # A more robust solution might pass the chapter dictionary.
            initial_context = "" 

            regenerated_chapters = self.story_generator.generate_story_from_arc(
                arc=story_arc,
                original_user_prompt=story_arc.premise,
                previous_feedback=rewrite_feedback,
                start_stage=first_dirty_stage,
                initial_context=initial_context
            )
            
            # Stitch the original "good" part of the story with the rewritten part.
            good_text_marker = f"--- START: {first_dirty_stage.name} ---"
            # Split by the marker; the first part is the text to keep.
            parts = original_story.split(good_text_marker, 1)
            good_text_up_to_marker = parts[0] if len(parts) > 1 else ""

            rewritten_text = "\n\n".join(regenerated_chapters.values())
            
            if first_dirty_stage == StoryStage.SETUP:
                current_story_text = rewritten_text
            else:
                current_story_text = good_text_up_to_marker.strip() + "\n\n" + rewritten_text
        
        return current_story_text 