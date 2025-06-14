"""Unified story parser that combines spaCy-based and OpenAI-based parsing approaches."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import our existing parsers
from story_parser import InputParser, StoryElements  # spaCy-based parser
from openai_parser import OpenAIStoryParser  # OpenAI-based parser


@dataclass
class ParseResult:
    """Unified result from story parsing."""
    success: bool
    elements: Optional[StoryElements]
    openai_data: Optional[Dict[str, Any]]
    parser_used: str
    error: Optional[str] = None


class UnifiedStoryParser:
    """
    Unified parser that intelligently chooses between parsing approaches.
    
    Priority:
    1. Try OpenAI parser if available (more accurate for complex inputs)
    2. Fall back to spaCy parser (always available, no API costs)
    3. Provide merged results when possible
    """
    
    def __init__(self, prefer_openai: bool = True):
        """Initialize both parsers."""
        self.prefer_openai = prefer_openai
        
        # Initialize spaCy parser (always available)
        try:
            self.spacy_parser = InputParser()
            self.spacy_available = True
            logging.info("spaCy parser initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize spaCy parser: {e}")
            self.spacy_parser = None
            self.spacy_available = False
        
        # Initialize OpenAI parser (requires API key)
        try:
            self.openai_parser = OpenAIStoryParser()
            self.openai_available = self.openai_parser.is_available()
            if self.openai_available:
                logging.info("OpenAI parser initialized successfully")
            else:
                logging.info("OpenAI parser not available (no API key)")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI parser: {e}")
            self.openai_parser = None
            self.openai_available = False
    
    def parse(self, prompt: str, force_parser: Optional[str] = None) -> ParseResult:
        """
        Parse story prompt using the best available method.
        
        Parameters
        ----------
        prompt : str
            User's story prompt
        force_parser : str, optional
            Force use of specific parser: "openai" or "spacy"
            
        Returns
        -------
        ParseResult with parsing results and metadata
        """
        # Determine which parser to use
        if force_parser == "openai":
            if self.openai_available:
                return self._parse_with_openai(prompt)
            else:
                return ParseResult(
                    success=False,
                    elements=None,
                    openai_data=None,
                    parser_used="none",
                    error="OpenAI parser not available"
                )
        
        elif force_parser == "spacy":
            if self.spacy_available:
                return self._parse_with_spacy(prompt)
            else:
                return ParseResult(
                    success=False,
                    elements=None,
                    openai_data=None,
                    parser_used="none",
                    error="spaCy parser not available"
                )
        
        # Auto-select parser based on availability and preference
        if self.prefer_openai and self.openai_available:
            result = self._parse_with_openai(prompt)
            if result.success:
                return result
            # If OpenAI fails, fall back to spaCy
            logging.warning("OpenAI parsing failed, falling back to spaCy")
        
        # Use spaCy parser
        if self.spacy_available:
            return self._parse_with_spacy(prompt)
        
        # No parsers available
        return ParseResult(
            success=False,
            elements=None,
            openai_data=None,
            parser_used="none",
            error="No parsers available"
        )
    
    def _parse_with_openai(self, prompt: str) -> ParseResult:
        """Parse using OpenAI."""
        try:
            # Override temperature for factual parsing to ensure consistency.
            openai_data = self.openai_parser.parse_prompt(prompt, mode="json", temperature=0.1)
            return ParseResult(
                success=True,
                elements=None,  # Could convert OpenAI format to StoryElements if needed
                openai_data=openai_data,
                parser_used="openai"
            )
        except Exception as e:
            logging.error(f"OpenAI parsing failed: {e}")
            return ParseResult(
                success=False,
                elements=None,
                openai_data=None,
                parser_used="openai",
                error=str(e)
            )
    
    def _parse_with_spacy(self, prompt: str) -> ParseResult:
        """Parse using spaCy."""
        try:
            elements = self.spacy_parser.parse(prompt)
            return ParseResult(
                success=True,
                elements=elements,
                openai_data=None,
                parser_used="spacy"
            )
        except Exception as e:
            logging.error(f"spaCy parsing failed: {e}")
            return ParseResult(
                success=False,
                elements=None,
                openai_data=None,
                parser_used="spacy",
                error=str(e)
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all parsers."""
        return {
            "spacy_available": self.spacy_available,
            "openai_available": self.openai_available,
            "preferred_parser": "openai" if self.prefer_openai else "spacy",
            "fallback_available": self.spacy_available and self.openai_available
        }


# Convenience function for quick parsing
def parse_story_prompt(prompt: str, prefer_openai: bool = True) -> ParseResult:
    """Quick story parsing with unified parser."""
    parser = UnifiedStoryParser(prefer_openai=prefer_openai)
    return parser.parse(prompt)


# Demo function
def demo_unified_parser():
    """Demonstrate the unified parser."""
    parser = UnifiedStoryParser()
    
    print("=== Unified Parser Status ===")
    status = parser.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    print("\n=== Testing Unified Parser ===")
    test_prompt = "A story about a girl named Alice and her best friend Bob, who happens to be a cat"
    
    result = parser.parse(test_prompt)
    print(f"Parser used: {result.parser_used}")
    print(f"Success: {result.success}")
    
    if result.success:
        if result.openai_data:
            print("OpenAI result:")
            import json
            print(json.dumps(result.openai_data, indent=2))
        elif result.elements:
            print("spaCy result:")
            print(f"Characters: {result.elements.characters}")
            print(f"Setting: {result.elements.setting}")
    else:
        print(f"Error: {result.error}")


if __name__ == "__main__":
    demo_unified_parser() 