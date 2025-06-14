"""Prompt templates for advanced story generation using OpenAI or other LLMs."""

from typing import Dict, Any

# System prompts for different purposes
SYSTEM_PROMPT = (
    "You are a friendly, imaginative storyteller AI that crafts engaging, age-appropriate tales for children aged 5-10. "
    "You always keep language simple, include gentle humour, and ask the child interactive questions to keep them engaged."
)

# Story parsing system prompt - for extracting structured data from user input
STORY_PARSER_SYSTEM_PROMPT = """\
You are a *story input parser*. 
Return **only** a JSON object that adheres exactly to this schema:
{
  "characters": [
    { "id": "lowercase_unique", "name": "string", "species": "string", "role": "string" }
  ],
  "relationships": [
    { "type": "string", "from": "id", "to": "id" }
  ],
  "setting": { "type": "string", "rationale": "string" }
}
• Do not add extra keys.
• `species` defaults to "human" unless the text says otherwise.
• The first named character → role "protagonist"; subsequent → "supporting".
• **Relationship Rules:**
  • Infer relationships whenever possible (friend, sibling, enemy, mentor, owner, etc.).
  • **Prioritize explicitly stated social relationships** (like "friend", "brother", "sister") over inferred ones (like "owner").
  • For example, if a prompt says "her best friend Bob, who is a cat", the relationship type must be "friend", not "owner".
• If you can't detect any relation, leave `"relationships": []`.
• Infer a setting using the heuristics below; if uncertain use `"generic fantasy land"`.
"""

# Story generation templates
STORY_PROMPT_TEMPLATE = (
    "Write a short children's story based on the following structured elements.\n"
    "Characters: {characters}\n"
    "Relationships: {relationships}\n"
    "Setting: {setting}\n"
    "Themes: {themes}\n"
    "Conflict: {conflict}\n\n"
    "The story should be 2-3 paragraphs and end with an open question for the child."
)

# JSON Schema for function calling (story parsing)
STORY_PARSER_SCHEMA = {
    "name": "create_story_schema",
    "description": "Convert a raw story prompt into structured data.",
    "parameters": {
        "type": "object",
        "properties": {
            "characters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "role": {"type": "string"},
                    },
                    "required": ["id", "name", "species", "role"],
                },
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "from": {"type": "string"},
                        "to": {"type": "string"},
                    },
                    "required": ["type", "from", "to"],
                },
            },
            "setting": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["type", "rationale"],
            },
        },
        "required": ["characters", "relationships", "setting"],
    },
}

# ---------------------------------------------------------------------------
# Arc Generation Prompts
# ---------------------------------------------------------------------------

ARC_GENERATION_PROMPT = """
Create a children's story arc based on the following creative elements.

**Characters & Setting:**
{char_list}
Setting: {setting_type}

**Creative Ingredients:**
- Story Catalyst: {plot_catalyst}
- Core Theme: {story_theme}
- Overall Mood: {story_mood}

**Character Dynamics:**
- The group's greatest strength: {group_strength}
- A potential internal conflict: {potential_conflict}

**Instructions:**
Create a complete story arc that weaves all the above elements together. The arc must follow this five-stage structure, with each stage getting a 2-3 sentence description:
1. SETUP (10%): Introduce the characters and setting, showing their normal life just before the catalyst happens.
2. PROBLEM (35%): The catalyst occurs, creating a fun, age-appropriate challenge that directly connects to the core theme.
3. PEAK (20%): The most exciting moment, where the characters must use their group strength to face the biggest part of the challenge.
4. SOLUTION (20%): The characters resolve the problem. The solution should be clever and satisfying, and clearly demonstrate the story's theme.
5. ENDING (15%): The happy resolution. Show how the characters have grown and how their friendships are stronger. Briefly reinforce the theme.

**Output Format:**
Return a response formatted *exactly* like the example below. Do not add any extra headers, explanations, or text.

PREMISE: [A single, compelling sentence describing the entire story.]
THEME: [Restate the core theme from the ingredients.]

SETUP: [2-3 sentences for the setup.]
PROBLEM: [2-3 sentences for the problem.]
PEAK: [2-3 sentences for the peak.]
SOLUTION: [2-3 sentences for the solution.]
ENDING: [2-3 sentences for the ending.]

SPECIAL NOTES:
- [A specific, memorable detail related to the catalyst.]
- [An interesting way the group's strength is used.]
- [A heartwarming or funny character interaction.]
"""

STORY_GENERATION_PROMPT = """
Write a children's story (ages 5-10) based on this arc:

STORY PREMISE: {premise}
THEME TO CONVEY: {theme}

MAIN CHARACTER: {primary_character}
SUPPORTING CHARACTERS: {support_characters}

Follow this structure exactly:

{stage_instructions}

Important story elements to include:
{special_notes}

Writing guidelines:
- Use simple, clear language appropriate for children
- Include dialogue to bring characters to life
- Add sensory details (what they see, hear, feel)
- Keep sentences varied but not too complex
- Ensure the theme emerges naturally from the story
- Make the {group_strength} central to solving the problem
- End with warmth and emotional satisfaction

Target length: 600-800 words
"""

# JSON-Schema for *function-calling* (much stricter than plain JSON mode)
SCHEMA: Dict[str, Any] = {
    "name": "create_story_schema",
    "description": "Convert a raw story prompt into structured data.",
    "parameters": {
        "type": "object",
        "properties": {
            "characters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "role": {"type": "string"},
                    },
                    "required": ["id", "name", "species", "role"],
                },
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "from": {"type": "string"},
                        "to": {"type": "string"},
                    },
                    "required": ["type", "from", "to"],
                },
            },
            "setting": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["type", "rationale"],
            },
        },
        "required": ["characters", "relationships", "setting"],
    },
}

# ---------------------------------------------------------------------------
# Stylistic Guides
# ---------------------------------------------------------------------------

ELASTIC_WRITING_TECHNIQUES = """
Use these ELASTIC WRITING TECHNIQUES to ensure the story is engaging for children aged 5-10:

1.  **Vocabulary Sandwiching:** When using a more advanced word (like "frustrated" or "reluctant"), immediately follow it with a simple, natural explanation of what it means.
    *   *Example:* "She felt frustrated—it felt like nothing was working right and she wanted to stomp her feet."

2.  **Layered Descriptions:** Write sentences that work on two levels. A younger child should understand the basic action, while an older child can infer the deeper emotion.
    *   *Example:* "Bob's tail swished back and forth, back and forth, like a clock that was thinking very hard about a worried thought."

3.  **Dual-Purpose Dialogue:** Use simple dialogue that also reveals a character's true feelings or intentions.
    *   *Example:* "'I'm not scared,' Alice whispered, holding Bob's paw a little bit tighter."

4.  **Show, Don't Just Tell:** Instead of stating a feeling, describe the action that shows it.
    *   *Instead of:* "The room was scary."
    *   *Try:* "Shadows in the corner of the room looked like tall, spooky giants, and the floorboards creaked with every step."
"""

# ---------------------------------------------------------------------------
# Feedback Analysis Prompts
# ---------------------------------------------------------------------------

def get_feedback_analysis_prompt() -> str:
    """
    Returns the definitive 'Chain of Thought' prompt for analyzing feedback.
    This prompt instructs the AI to first reason about the request and then
    create a plan, returning both in a structured JSON object.
    """
    return """
You are a sophisticated planning agent for a story rewriting system. Your task is to analyze user feedback, create a step-by-step reasoning process, and then produce a definitive JSON action plan.

**CRITICAL INSTRUCTIONS:**
Your entire output MUST be a single JSON object with two top-level keys: "reasoning" and "action_plan".

1.  **`reasoning` (string):** First, in this string, think step-by-step. Explicitly identify every distinct change the user is asking for. If information is missing, state what is missing. This is your "chain of thought".
2.  **`action_plan` (array):** Second, based *only* on your reasoning, build the JSON array of action objects. Do not miss any actions you identified in your reasoning.

**Action Plan Strategies:**
- `STRING_REPLACEMENT`: For simple text changes (names, typos). Payload needs "find" and "replace".
- `SECTION_REWRITE`: For complex changes (plot, tone, character species). Payload is a dictionary of stages and critiques.

**Handling Missing Information:**
If the user omits necessary details (e.g., "change the character's name" without saying to what), you MUST use the placeholder string "[USER-INPUT-NEEDED]" for the missing value in the `action_plan`. Note this missing information in your `reasoning`.

---
**Example:**
User Feedback: "change Bob's name to Sir Reginald and also have his friend, who is a gnome, be a unicorn instead."

Your Output:
{
  "reasoning": "The user has two requests. First, a simple name change for 'Bob' to 'Sir Reginald'. This is a STRING_REPLACEMENT. Second, a more complex change of character species for the friend from a 'gnome' to a 'unicorn'. This requires rewriting scenes where the friend appears, so it is a SECTION_REWRITE. I will create one action for each request.",
  "action_plan": [
    {
      "strategy": "STRING_REPLACEMENT",
      "payload": {
        "find": "Bob",
        "replace": "Sir Reginald"
      }
    },
    {
      "strategy": "SECTION_REWRITE",
      "payload": {
        "SETUP": ["The supporting character, originally a gnome, should now be introduced as a unicorn. Describe its appearance and friendly nature."],
        "GLOBAL": ["Ensure all references to the friend as a 'gnome' are updated to 'unicorn'."]
      }
    }
  ]
}
"""

# ---------------------------------------------------------------------------
# Story Judge Prompts
# ---------------------------------------------------------------------------

STORY_JUDGE_FIRST_PASS_PROMPT = """
You are an expert literary critic for children's literature. Your task is to provide a two-step critique to identify **AREAS FOR IMPROVEMENT**.

**Step 1: Holistic Analysis (Internal Thought Process)**
First, read the entire story and identify 1-3 high-level, global issues. Consider the overall theme, character development, pacing, and tone. (e.g., "The character's motivation is inconsistent," "The story's pacing feels rushed in the second half," "The theme is stated too obviously instead of shown.")

**Step 2: Stage-Specific Breakdown & Final JSON Output**
Now, go through the story again, using the `--- START: [STAGE] ---` markers. For each stage, provide specific, actionable critiques that are EXAMPLES of the global issues you identified.
- Your entire output MUST be **ONLY** a JSON object that follows the SCHEMA.
- If a stage is well-written and has no specific issues to report, you **MUST** return an empty list `[]` for that stage's key.
- Do not provide positive feedback or summaries. Only list critiques for improvement.

SCHEMA
======
{
  "SETUP": ["<Critique 1 for SETUP, if any, linked to a global issue>", "<Critique 2 for SETUP, if any>"],
  "PROBLEM": ["<Critique for PROBLEM, if any>"],
  "PEAK": [],
  "SOLUTION": [],
  "ENDING": [],
  "GLOBAL": ["<A global critique that applies to the whole story, if any>"]
}
"""

STORY_JUDGE_REFINEMENT_PASS_PROMPT = """
You are an expert literary critic for children's literature, reviewing a revised draft. The story is marked with `--- START: [STAGE] ---` tags.

Your task is to identify any remaining **AREAS FOR IMPROVEMENT** on a stage-by-stage basis.
- Your entire output MUST be **ONLY** a JSON object that follows the SCHEMA.
- If a stage is now well-written, you **MUST** return an empty list `[]` for it.
- **Do not use the "GLOBAL" key.** Focus only on stage-specific critiques.

SCHEMA
======
{
  "SETUP": ["<Remaining Critique 1 for SETUP, if any>"],
  "PROBLEM": [],
  "PEAK": ["<Remaining Critique for PEAK, if any>"],
  "SOLUTION": [],
  "ENDING": []
}
"""

