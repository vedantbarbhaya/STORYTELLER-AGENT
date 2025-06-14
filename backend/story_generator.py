"""
This module takes a structured StoryArc and generates the final, full-length story
by iteratively writing it chapter by chapter.
"""
import logging
from typing import List, Dict

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from prompts import ELASTIC_WRITING_TECHNIQUES
from arc_generator import StoryArc, StoryStage

class StoryGenerator:
    """
    Generates a full story from a story arc using a chapter-based approach.
    Can generate a full story from scratch or regenerate from a specific stage onwards.
    """
    def __init__(self):
        """Initializes the OpenAI client."""
        if not OPENAI_API_KEY:
            self.client = None
            logging.warning("OpenAI API key not found. Story generation will not be available.")
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def is_available(self) -> bool:
        """Checks if the story generator can be used."""
        return self.client is not None

    def generate_story_from_arc(
        self, 
        arc: StoryArc, 
        original_user_prompt: str, 
        previous_feedback: dict[str, list[str]] | None = None,
        start_stage: StoryStage = StoryStage.SETUP,
        initial_context: str = ""
    ) -> Dict[StoryStage, str]:
        """
        Generates story chapters, either from the beginning or from a specific stage.

        Returns:
            A dictionary mapping each generated StoryStage to its chapter text.
        """
        if not self.is_available():
            raise RuntimeError("StoryGenerator is not available due to missing OpenAI API key.")

        generated_chapters: Dict[StoryStage, str] = {}
        story_so_far = initial_context

        # Define the order of stages to ensure correct narrative flow
        stage_order = [StoryStage.SETUP, StoryStage.PROBLEM, StoryStage.PEAK, StoryStage.SOLUTION, StoryStage.ENDING]
        
        # Find the index of the stage to start from
        start_index = stage_order.index(start_stage)

        for i in range(start_index, len(stage_order)):
            stage = stage_order[i]

            if stage not in arc.stages:
                continue

            stage_instruction = arc.stages[stage]
            
            prompt = self._build_chapter_prompt(
                story_so_far, stage, stage_instruction, arc, original_user_prompt, previous_feedback
            )

            print(f"\n\n{'='*20} 🤖 PROMPT for Chapter: {stage.name} {'='*20}")
            print(prompt)

            chapter_text = self._make_llm_call(prompt)

            print(f"\n\n{'='*20} 📖 RESPONSE for Chapter: {stage.name} {'='*20}")
            print(chapter_text)
            
            generated_chapters[stage] = chapter_text
            story_so_far += chapter_text + "\n\n"

        return generated_chapters

    def _build_chapter_prompt(
        self, story_so_far: str, stage: StoryStage, instruction: str, arc: StoryArc, 
        original_user_prompt: str, previous_feedback: dict[str, list[str]] | None = None
    ) -> str:
        """Builds the focused prompt for a single chapter."""
        
        # --- Create Feedback Block ---
        feedback_prompt_section = ""

        if previous_feedback:
            current_stage_name = stage.name
            stage_specific_feedback = previous_feedback.get(current_stage_name, [])
            global_feedback = previous_feedback.get("GLOBAL", [])
            
            # Global feedback is passed to every chapter. Stage-specific only to its stage.
            relevant_feedback_points = global_feedback + stage_specific_feedback
            
            if relevant_feedback_points:
                feedback_points_str = "\n".join([f"- {fb}" for fb in relevant_feedback_points])
                feedback_prompt_section = (
                    f"IMPORTANT: This is a regeneration attempt. The previous version had issues. "
                    f"You MUST address the following feedback while writing this '{current_stage_name}' chapter:\n"
                    f"--- FEEDBACK TO ADDRESS ---\n{feedback_points_str}\n---------------------------\n\n"
                )

        # --- Create Main Context Block ---
        char_list = f"  - MAIN CHARACTER: {arc.dynamics.primary_character}\n"
        if arc.dynamics.support_characters:
            char_list += f"  - SUPPORTING CHARACTERS: {', '.join(arc.dynamics.support_characters)}"
        
        context = ""
        story_overview = ""
        if story_so_far:
            context = f"Here is the story so far:\n---\n{story_so_far}\n---\n"
        else:
            context = f"You are starting a new story. The original user request was: '{original_user_prompt}'.\n"
            story_overview = f"""
Here is the high-level plan for the story you are about to write:
- **Story Premise:** {arc.premise}
- **Theme to Convey:** {arc.theme}
- **Character Dynamics:** The story is about {arc.dynamics.primary_character} and their friends ({', '.join(arc.dynamics.support_characters) if arc.dynamics.support_characters else 'none'}). Their group strength is '{arc.dynamics.group_strength}', but they will face conflict related to '{arc.dynamics.potential_conflict}'.
- **Characters:**
{char_list}
"""
        
        prompt = f"""{feedback_prompt_section}{context}{story_overview}
Now, continue the story by writing the **{stage.name}** chapter. This chapter should make up about **{stage.percentage}%** of the total story.

**Instructions for this chapter:**
{instruction}

**Writing Style Guide:**
{ELASTIC_WRITING_TECHNIQUES}
"""
        return prompt.strip()

    def _make_llm_call(self, prompt: str) -> str:
        """Makes the actual API call to the language model."""
        completion = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=OPENAI_TEMPERATURE, # Use creative temperature
        )
        return completion.choices[0].message.content.strip() 