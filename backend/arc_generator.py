"""
Generates a structured story arc based on parsed user input.
"""
import logging
import json
from typing import Dict, List, Any
from pydantic import BaseModel
from enum import Enum

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from prompts import ARC_GENERATION_PROMPT, STORY_GENERATION_PROMPT
from creative_elements import get_random_elements

class StoryStage(Enum):
    """Defines the five stages of a classic story structure."""
    SETUP = "SETUP"
    PROBLEM = "PROBLEM"
    PEAK = "PEAK"
    SOLUTION = "SOLUTION"
    ENDING = "ENDING"

    @property
    def percentage(self) -> int:
        """Returns the percentage of the story this stage should occupy."""
        return {
            StoryStage.SETUP: 10,
            StoryStage.PROBLEM: 35,
            StoryStage.PEAK: 20,
            StoryStage.SOLUTION: 20,
            StoryStage.ENDING: 15,
        }[self]

    @property
    def purpose(self) -> str:
        """Returns the narrative purpose of this stage."""
        return {
            StoryStage.SETUP: "Introduce characters and their world",
            StoryStage.PROBLEM: "Present the challenge",
            StoryStage.PEAK: "Reach the exciting climax",
            StoryStage.SOLUTION: "Resolve the problem",
            StoryStage.ENDING: "Show the new normal",
        }[self]

class CharacterDynamics(BaseModel):
    """Represents the relationships and potential conflicts between characters."""
    primary_character: str
    support_characters: List[str]
    group_strength: str
    potential_conflict: str

class StoryArc(BaseModel):
    """A complete, structured story arc with all necessary components for generation."""
    premise: str
    theme: str
    dynamics: CharacterDynamics
    stages: Dict[StoryStage, str]
    special_notes: List[str]

class ArcGenerator:
    """
    Generates a structured story arc using an LLM.
    """
    def __init__(self):
        """Initializes the LLM client."""
        if not OPENAI_API_KEY:
            self.client = None
            logging.warning("OpenAI API key not found. Arc generation will not be available.")
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def is_available(self) -> bool:
        """Checks if the arc generator can be used."""
        return self.client is not None

    def generate_arc(self, parsed_input: Dict[str, Any]) -> StoryArc:
        """
        Generates a complete story arc from parsed user input in a single LLM call.
        """
        if not self.is_available():
            raise RuntimeError("ArcGenerator is not available due to missing OpenAI API key.")

        print("\n--- 🔍 Arc Generator Input ---")
        print(f"  Parsed Input: {json.dumps(parsed_input, indent=2)}")

        characters = parsed_input.get("characters", [])
        setting = parsed_input.get("setting", {})
        
        # Get random creative elements to drive variability
        creative_elements = get_random_elements()
        print("\n--- 🎲 Selected Creative Elements ---")
        print(f"  - Catalyst: {creative_elements['catalyst']}")
        print(f"  - Theme: {creative_elements['theme']}")
        print(f"  - Mood: {creative_elements['mood']}")
        print(f"  - Group Strength: {creative_elements['strength']}")
        print(f"  - Potential Conflict: {creative_elements['conflict']}")
        
        dynamics = self._identify_dynamics(characters, creative_elements)
        print("\n--- 🧑‍🤝‍🧑 Identified Character Dynamics ---")
        print(f"  - Primary Character: {dynamics.primary_character}")
        print(f"  - Support Characters: {', '.join(dynamics.support_characters)}")
        print(f"  - Group Strength: {dynamics.group_strength}")
        print(f"  - Potential Conflict: {dynamics.potential_conflict}")

        char_list = "\n".join([
            f"- {c['name']}: a {c.get('species', 'mysterious')} {c.get('role', 'character')}"
            for c in characters
        ])

        arc_prompt = ARC_GENERATION_PROMPT.format(
            char_list=char_list,
            setting_type=setting.get('type', 'a magical place'),
            plot_catalyst=creative_elements['catalyst'],
            story_theme=creative_elements['theme'],
            story_mood=creative_elements['mood'],
            group_strength=dynamics.group_strength,
            potential_conflict=dynamics.potential_conflict
        )
        
        print("\n--- 🤖 Sending Prompt to OpenAI for Arc Generation ---")
        print(arc_prompt)

        completion = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": arc_prompt}],
            temperature=OPENAI_TEMPERATURE,
        )
        response_text = completion.choices[0].message.content

        print("\n--- 📄 Received Raw Response from OpenAI ---")
        print(response_text)
        
        return self._parse_arc_response(response_text, dynamics)
    
    def _identify_dynamics(self, characters: List[Dict], creative_elements: Dict) -> CharacterDynamics:
        """A simple method to identify character dynamics from a list."""
        if not characters:
            # Fallback if no characters are parsed
            primary = "A brave hero"
            support = []
        else:
            primary = characters[0]["name"]
            support = [c["name"] for c in characters[1:]]
        
        # Use the randomized strength and conflict
        strength = creative_elements['strength']
        conflict = creative_elements['conflict']
        
        return CharacterDynamics(
            primary_character=primary,
            support_characters=support,
            group_strength=strength,
            potential_conflict=conflict
        )
    
    def _parse_arc_response(self, response: str, dynamics: CharacterDynamics) -> StoryArc:
        """Parses the raw LLM string response into a structured StoryArc."""
        lines = response.strip().split('\n')
        
        premise = ""
        theme = ""
        stages = {}
        special_notes = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("PREMISE:"):
                premise = line.replace("PREMISE:", "").strip()
            elif line.startswith("THEME:"):
                theme = line.replace("THEME:", "").strip()
            elif line.startswith("SETUP:"):
                current_section = StoryStage.SETUP
                stages[current_section] = line.replace("SETUP:", "").strip()
            elif line.startswith("PROBLEM:"):
                current_section = StoryStage.PROBLEM
                stages[current_section] = line.replace("PROBLEM:", "").strip()
            elif line.startswith("PEAK:"):
                current_section = StoryStage.PEAK
                stages[current_section] = line.replace("PEAK:", "").strip()
            elif line.startswith("SOLUTION:"):
                current_section = StoryStage.SOLUTION
                stages[current_section] = line.replace("SOLUTION:", "").strip()
            elif line.startswith("ENDING:"):
                current_section = StoryStage.ENDING
                stages[current_section] = line.replace("ENDING:", "").strip()
            elif line.startswith("SPECIAL NOTES:"):
                current_section = "notes"
            elif current_section == "notes" and line.startswith("-"):
                special_notes.append(line.lstrip("- ").strip())
            elif current_section in stages:
                stages[current_section] += " " + line
        
        return StoryArc(
            premise=premise,
            theme=theme,
            dynamics=dynamics,
            stages=stages,
            special_notes=special_notes
        ) 
    

    