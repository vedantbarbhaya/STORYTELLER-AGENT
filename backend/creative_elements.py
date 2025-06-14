"""
This file contains lists of creative elements to inject variability into
story arc generation, making each story unique.
"""
import random

# --- Plot Catalysts: The event that kicks off the story ---
PLOT_CATALYSTS = [
    "a mysterious, glowing seed is found",
    "an unexpected visitor with a strange request arrives",
    "a secret message written in code is discovered",
    "the main character wakes up with a new, funny superpower (like talking to squirrels)",
    "a magical map appears, showing a place that isn't supposed to exist",
    "a magical instrument is found, but no one knows how it works",
    "a travelling fair comes to town with enchanted games and prizes",
    "a grumpy gnome loses something very important and asks for help",
    "a strange weather event happens, like colorful rain or floating bubbles",
    "an ancient tree starts talking and shares a secret",
]

# --- Core Themes: The underlying message of the story ---
THEMES = [
    "the importance of telling the truth, even when it's hard",
    "learning to share with friends makes things more fun",
    "being brave even when you're a little scared",
    "the joy of trying something new for the first time",
    "teamwork can solve any problem, big or small",
    "everyone has a special talent that is useful",
    "kindness is a superpower that can make anyone's day better",
    "it's okay to make mistakes, as long as you learn from them",
    "patience is key when working towards a big goal",
    "listening carefully to others is a great way to show you care",
]

# --- Story Moods: The overall feeling or tone of the story ---
MOODS = [
    "Silly and Zany",
    "Gentle and Heartwarming",
    "Mysterious and Wondrous",
    "Action-Packed and Exciting",
    "Playful and Fun",
    "Quiet and Thoughtful",
]

# --- Dynamic Strengths and Conflicts for Characters ---
GROUP_STRENGTHS = [
    "their unbreakable friendship and loyalty",
    "their clever and creative problem-solving skills",
    "their combined magical abilities and talents",
    "their courage and determination in the face of challenges",
    "their different perspectives that lead to unique ideas",
    "their ability to communicate and listen to each other well",
]

POTENTIAL_CONFLICTS = [
    "a simple misunderstanding that snowballs into a bigger problem",
    "getting a little lost in a new and unfamiliar place",
    "a magical mishap or a spell that goes slightly wrong",
    "disagreeing on the best way to solve a problem",
    "a friendly competition that gets a little too competitive",
    "facing a challenge that seems too big for them at first",
]

def get_random_elements() -> dict:
    """Returns a dictionary with a random selection of creative elements."""
    return {
        "catalyst": random.choice(PLOT_CATALYSTS),
        "theme": random.choice(THEMES),
        "mood": random.choice(MOODS),
        "strength": random.choice(GROUP_STRENGTHS),
        "conflict": random.choice(POTENTIAL_CONFLICTS),
    } 