from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import json
from collections import OrderedDict
from typing import Dict, Any

# --- Local Imports ---
from unified_parser import UnifiedStoryParser
from story_parser import StoryElements
from arc_generator import ArcGenerator, StoryArc, StoryStage
from story_generator import StoryGenerator
from story_judge import StoryQualityJudge
from feedback_analyzer import FeedbackAnalyzer
from refinement_executor import RefinementExecutor
from config import OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_API_KEY
from prompts import SYSTEM_PROMPT, STORY_PROMPT_TEMPLATE

# App Initialization
app = FastAPI(title="Storyteller API", description="A magical storytelling API for children")
parser = UnifiedStoryParser(prefer_openai=True)
arc_generator = ArcGenerator()
story_generator = StoryGenerator()
story_judge = StoryQualityJudge()
feedback_analyzer = FeedbackAnalyzer()
refinement_executor = RefinementExecutor(story_generator)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    story_arc: Dict | None = None
    original_story: str | None = None

class RefinementRequest(BaseModel):
    user_feedback: str
    original_story: str
    story_arc: Dict

# Helper Functions
def _assemble_story_for_judge(chapters: dict) -> str:
    ordered_chapters = []
    for stage in StoryStage:
        if stage in chapters:
            chapter_text = chapters[stage]
            ordered_chapters.append(f"--- START: {stage.name} ---\n{chapter_text}\n--- END: {stage.name} ---")
    return "\n\n".join(ordered_chapters)

def _log_arc_blueprint(arc: StoryArc):
    print("\n--- 📝 Story Arc Blueprint ---")
    print(f"  Premise: {arc.premise}")
    print(f"  Theme: {arc.theme}")
    print(f"  Character Dynamics: {arc.dynamics.primary_character} and {', '.join(arc.dynamics.support_characters)} must overcome '{arc.dynamics.potential_conflict}' by using their strength of '{arc.dynamics.group_strength}'.")
    print("  Stages:")
    for stage, description in arc.stages.items():
        print(f"    - {stage.name}: {description}")
    print("  Special Notes:")
    for note in arc.special_notes:
        print(f"    - {note}")

def _log_evaluation_results(evaluation: dict):
    print("\n--- ⚖️ Judge's Verdict ---")
    print(f"  Final Weighted Score: {evaluation.get('final_weighted_score', 0)}/5.0")
    actionable_feedback = evaluation.get('actionable_feedback', {})
    if not actionable_feedback:
        print("  Actionable Feedback: The story looks great! No major issues were found.")
    else:
        print("  Actionable Feedback:")
        for stage, feedback_list in actionable_feedback.items():
            print(f"    - For Stage '{stage}':")
            for feedback in feedback_list:
                print(f"      - {feedback}")

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Magical Storyteller API! 🌟"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    raw_text = message.message.strip()
    logger.info(f"Received new story request: '{raw_text}'")

    try:
        parse_result = parser.parse(raw_text)
        if not parse_result.success or not parse_result.openai_data:
            raise ValueError("Parsing failed or produced no data.")
        story_arc = arc_generator.generate_arc(parse_result.openai_data)
        _log_arc_blueprint(story_arc)
    except Exception as e:
        logger.error(f"Story planning failed: {e}")
        return ChatResponse(response="I'm sorry, I had trouble planning a story from that idea.")

    final_story_chapters = story_generator.generate_story_from_arc(story_arc, raw_text)

    if story_judge.is_available():
        story_for_judge = _assemble_story_for_judge(final_story_chapters)
        evaluation = story_judge.comprehensive_evaluation(story_for_judge, story_arc, is_first_pass=True)
        _log_evaluation_results(evaluation)

        SCORE_THRESHOLD = 4.9
        if evaluation.get("final_weighted_score", 0) < SCORE_THRESHOLD:
            logger.info(f"Story quality below threshold. Attempting surgical rewrite...")
            feedback = evaluation.get("actionable_feedback", {})
            first_dirty_stage = next((s for s in StoryStage if feedback.get(s.name)), None)

            if first_dirty_stage:
                initial_context = ""
                good_chapters = OrderedDict()
                for stage in StoryStage:
                    if stage == first_dirty_stage: break
                    if stage in final_story_chapters:
                        good_chapters[stage] = final_story_chapters[stage]
                        initial_context += good_chapters[stage] + "\n\n"

                regenerated_chapters = story_generator.generate_story_from_arc(
                    story_arc, raw_text, previous_feedback=feedback,
                    start_stage=first_dirty_stage, initial_context=initial_context
                )
                final_story_chapters = {**good_chapters, **regenerated_chapters}
                logger.info("Surgical rewrite complete.")

    final_story_text = "\n\n".join(final_story_chapters.values())
    
    return ChatResponse(
        response=final_story_text,
        story_arc=story_arc.model_dump(),
        original_story=final_story_text
    )

@app.post("/refine-with-feedback", response_model=ChatResponse)
async def refine_with_feedback(request: RefinementRequest):
    logger.info(f"Received refinement request.")
    if not feedback_analyzer.is_available():
        return ChatResponse(response="Sorry, the feedback analyzer is currently unavailable.")

    action_plan = feedback_analyzer.analyze_user_feedback(request.user_feedback, request.original_story)
    
    try:
        story_arc = StoryArc(**request.story_arc)
    except Exception as e:
        logger.error(f"Failed to reconstruct StoryArc: {e}")
        return ChatResponse(response="Error processing the story's structure.")

    final_story_text = refinement_executor.execute_plan(
        action_plan=action_plan,
        original_story=request.original_story,
        story_arc=story_arc
    )
    
    return ChatResponse(
        response=final_story_text,
        story_arc=story_arc.model_dump(),
        original_story=final_story_text
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Storyteller is ready! 🧙‍♂️"}

if __name__ == "__main__":
    logger.info("Starting Storyteller API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False) 