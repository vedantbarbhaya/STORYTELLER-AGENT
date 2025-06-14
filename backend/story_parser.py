"""spaCy-based story parser for extracting story elements from user input."""

import spacy
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from enum import Enum


# Load spaCy model globally to avoid reloading
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("spaCy model 'en_core_web_sm' loaded successfully")
except OSError:
    logging.error("spaCy model 'en_core_web_sm' not found. Please install with: python -m spacy download en_core_web_sm")
    nlp = None


class CharacterType(Enum):
    """Types of characters in stories."""
    HUMAN_CHILD = "human_child"
    HUMAN_ADULT = "human_adult"
    ANIMAL = "animal"
    MYTHICAL = "mythical"
    OBJECT = "object"
    UNKNOWN = "unknown"


class StoryRole(Enum):
    """Roles characters can play in stories."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MENTOR = "mentor"


@dataclass
class Character:
    """Represents a character in the story."""
    name: str
    character_type: CharacterType = CharacterType.UNKNOWN
    role: StoryRole = StoryRole.SUPPORTING
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.name} ({self.character_type.value}, {self.role.value})"


@dataclass
class Relationship:
    """Represents a relationship between characters."""
    type: str  # friend, sibling, owner, etc.
    character1: str
    character2: str
    
    def __str__(self):
        return f"{self.character1} -[{self.type}]-> {self.character2}"


@dataclass
class StoryElements:
    """Complete analysis of story elements."""
    characters: List[Character] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    setting: str = "unknown"
    themes: Set[str] = field(default_factory=set)
    conflict: str = "unknown"
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class InputParser:
    """spaCy-based natural language parser for story elements."""
    
    def __init__(self):
        """Initialize the parser with spaCy model."""
        if nlp is None:
            raise RuntimeError("spaCy model not available. Please install with: python -m spacy download en_core_web_sm")
        self.nlp = nlp
        
        # Story theme keywords
        self.theme_keywords = {
            'adventure': {'adventure', 'journey', 'quest', 'explore', 'discover', 'map', 'treasure'},
            'animals': {'animal', 'dog', 'cat', 'rabbit', 'fox', 'bear', 'bird', 'forest', 'jungle'},
            'magic': {'magic', 'wizard', 'fairy', 'spell', 'potion', 'crystal', 'enchanted'},
            'space': {'space', 'rocket', 'alien', 'planet', 'galaxy', 'astronaut', 'moon', 'star'}
        }
        
        # Character type indicators
        self.animal_words = {
            'cat', 'dog', 'rabbit', 'fox', 'bear', 'wolf', 'lion', 'tiger', 'elephant',
            'bird', 'owl', 'eagle', 'horse', 'pig', 'cow', 'sheep', 'goat', 'deer',
            'squirrel', 'mouse', 'rat', 'hamster', 'snake', 'fish', 'dolphin', 'whale'
        }
        
        self.mythical_words = {
            'dragon', 'unicorn', 'fairy', 'elf', 'wizard', 'witch', 'giant', 'troll',
            'goblin', 'phoenix', 'griffin', 'centaur', 'mermaid', 'genie'
        }
    
    def parse(self, text: str) -> StoryElements:
        """Parse input text to extract story elements."""
        if not text or not text.strip():
            return StoryElements()
        
        doc = self.nlp(text.lower())
        
        # Extract elements
        characters = self._extract_characters(doc)
        relationships = self._extract_relationships(doc, characters)
        setting = self._extract_setting(doc)
        themes = self._extract_themes(doc)
        conflict = self._extract_conflict(doc)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence(doc, characters, themes)
        
        return StoryElements(
            characters=characters,
            relationships=relationships,
            setting=setting,
            themes=themes,
            conflict=conflict,
            confidence_scores=confidence_scores
        )
    
    def _extract_characters(self, doc) -> List[Character]:
        """Extract and classify characters from the text."""
        characters = []
        
        # Pass 1: Find named entities (people)
        named_characters = {}
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.title()
                named_characters[name] = Character(
                    name=name,
                    character_type=CharacterType.UNKNOWN,  # Will classify in pass 2
                    role=StoryRole.PROTAGONIST if len(named_characters) == 0 else StoryRole.SUPPORTING
                )
        
        # Pass 2: Use dependency parsing to classify character types
        for token in doc:
            if token.pos_ == "NOUN" and token.text in self.animal_words:
                # Look for named entity that this noun describes
                for name, char in named_characters.items():
                    if char.character_type == CharacterType.UNKNOWN:
                        # Check if this animal noun is related to the character name
                        if self._is_noun_describing_character(token, name.lower(), doc):
                            char.character_type = CharacterType.ANIMAL
                            char.attributes["type"] = token.text
                            break
                else:
                    # Standalone animal character without explicit name
                    characters.append(Character(
                        name=token.text.title(),
                        character_type=CharacterType.ANIMAL,
                        role=StoryRole.SUPPORTING,
                        attributes={"type": token.text}
                    ))
        
        # Pass 3: Default remaining unknown characters to human children
        for char in named_characters.values():
            if char.character_type == CharacterType.UNKNOWN:
                char.character_type = CharacterType.HUMAN_CHILD
            characters.append(char)
        
        return characters
    
    def _is_noun_describing_character(self, noun_token, character_name: str, doc) -> bool:
        """Use dependency parsing to check if a noun describes a character."""
        # Check if the noun is in an appositive or descriptive relationship
        for token in doc:
            if character_name in token.text.lower():
                # Look for dependency relationships that connect the character name to the descriptive noun
                if self._tokens_are_related(token, noun_token):
                    return True
        return False
    
    def _tokens_are_related(self, token1, token2) -> bool:
        """Check if two tokens are syntactically related."""
        # Check direct dependencies
        if token1.head == token2 or token2.head == token1:
            return True
        
        # Check if they share a common head within a reasonable distance
        if token1.head == token2.head and abs(token1.i - token2.i) <= 5:
            return True
        
        # Check for compound or conjunction relationships
        for child in token1.children:
            if child == token2:
                return True
        
        for child in token2.children:
            if child == token1:
                return True
        
        return False
    
    def _extract_relationships(self, doc, characters: List[Character]) -> List[Relationship]:
        """Extract relationships between characters."""
        relationships = []
        
        relationship_words = {
            'friend': ['friend', 'buddy', 'pal'],
            'sibling': ['brother', 'sister', 'sibling'],
            'parent': ['mother', 'father', 'parent', 'mom', 'dad'],
            'owner': ['owner', 'belongs to', 'has'],
            'companion': ['companion', 'partner', 'sidekick']
        }
        
        for token in doc:
            for rel_type, keywords in relationship_words.items():
                if token.lemma_ in keywords:
                    # Simple relationship extraction based on proximity
                    char_names = [c.name.lower() for c in characters]
                    nearby_chars = []
                    
                    # Look for character names near the relationship word
                    for i in range(max(0, token.i - 3), min(len(doc), token.i + 4)):
                        for name in char_names:
                            if name in doc[i].text.lower():
                                nearby_chars.append(name.title())
                    
                    # Create relationships between nearby characters
                    if len(nearby_chars) >= 2:
                        relationships.append(Relationship(
                            type=rel_type,
                            character1=nearby_chars[0],
                            character2=nearby_chars[1]
                        ))
        
        return relationships
    
    def _extract_setting(self, doc) -> str:
        """Extract story setting."""
        setting_words = {
            'forest': ['forest', 'woods', 'trees', 'jungle'],
            'home': ['home', 'house', 'room', 'bedroom'],
            'school': ['school', 'classroom', 'playground'],
            'space': ['space', 'planet', 'galaxy', 'spaceship'],
            'fantasy': ['castle', 'kingdom', 'magical', 'enchanted']
        }
        
        for token in doc:
            for setting_type, keywords in setting_words.items():
                if token.lemma_ in keywords:
                    return setting_type
        
        return "unknown"
    
    def _extract_themes(self, doc) -> Set[str]:
        """Extract story themes."""
        themes = set()
        
        for token in doc:
            for theme, keywords in self.theme_keywords.items():
                if token.lemma_ in keywords:
                    themes.add(theme)
        
        return themes
    
    def _extract_conflict(self, doc) -> str:
        """Extract story conflict."""
        conflict_words = ['problem', 'trouble', 'lost', 'missing', 'scared', 'help', 'save']
        
        for token in doc:
            if token.lemma_ in conflict_words:
                return f"problem involving {token.text}"
        
        return "unknown"
    
    def _calculate_confidence(self, doc, characters: List[Character], themes: Set[str]) -> Dict[str, float]:
        """Calculate confidence scores for the analysis."""
        scores = {}
        
        # Character confidence based on named entity recognition
        named_entities = sum(1 for ent in doc.ents if ent.label_ == "PERSON")
        scores['characters'] = min(1.0, named_entities / 2.0)
        
        # Theme confidence based on keyword matches
        theme_matches = len(themes)
        scores['themes'] = min(1.0, theme_matches / 2.0)
        
        # Overall confidence
        scores['overall'] = (scores['characters'] + scores['themes']) / 2.0
        
        return scores


# Demo function
def demo_spacy_parser():
    """Demonstrate the spaCy parser."""
    parser = InputParser()
    
    test_cases = [
        "A story about a girl named Alice and her best friend Bob, who happens to be a cat",
        "Tell me about a brave boy named Max who goes on an adventure in the magical forest",
        "I want a story about space explorers finding alien friends on a distant planet"
    ]
    
    print("=== spaCy Story Parser Demo ===")
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test}")
        result = parser.parse(test)
        print(f"Characters: {[str(c) for c in result.characters]}")
        print(f"Themes: {result.themes}")
        print(f"Setting: {result.setting}")
        print(f"Confidence: {result.confidence_scores.get('overall', 0):.2f}")


if __name__ == "__main__":
    demo_spacy_parser() 