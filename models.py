"""
Data models for the video script structure.
Parses the structured YAML into typed Python objects.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import yaml
from pathlib import Path


class ContentType(Enum):
    VISUAL = "画面描述"
    NARRATION = "解说词"
    TECH_TABLE = "技术参数表"
    INTRO = "intro"


@dataclass
class SectionContent:
    type: ContentType
    text: str
    tts_text: Optional[str] = None  # override text used for TTS audio (pronunciation fixes)


@dataclass
class VideoSection:
    title: str
    time_range: str
    content: List[SectionContent]
    visual_prompts: List[str] = field(default_factory=list)
    skip_subtitles: bool = False  # Skip subtitle overlay for scenes with own text
    visual_entries: List[str] = field(default_factory=list)  # On-screen text from scene
    
    @property
    def narration_text(self) -> str:
        """Extract all narration text concatenated."""
        narrations = [c.text for c in self.content if c.type == ContentType.NARRATION]
        return "\n\n".join(narrations)
    
    @property
    def narration_tts_text(self) -> str:
        """Text used for TTS audio generation (uses tts_text override if present).

        Lets us correct pronunciation (e.g. homophone substitution for 多音字)
        without changing the subtitle text. Falls back to narration_text.
        """
        narrations = [
            (c.tts_text if c.tts_text is not None else c.text)
            for c in self.content if c.type == ContentType.NARRATION
        ]
        return "\n\n".join(narrations)
    
    @property
    def visual_text(self) -> str:
        """Extract all visual description text."""
        visuals = [c.text for c in self.content if c.type == ContentType.VISUAL]
        return "\n\n".join(visuals)
    
    @property
    def duration_estimate(self) -> float:
        """Estimate duration in seconds based on narration word count."""
        # Chinese: ~300 chars/min = 5 chars/sec
        # English: ~130 words/min = 2.2 words/sec
        text = self.narration_text
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if w.isascii()])
        return (chinese_chars / 5) + (english_words / 2.2)


@dataclass
class ValidationInfo:
    total_sections: int
    sections_with_visual_prompts: int
    sections_with_narration: int
    hierarchical_structure: str
    markdown_headers_mapped: bool
    visual_prompts_extracted: bool
    nested_lists_handled: bool
    malformed_entries_rejected: bool


@dataclass
class VideoScript:
    sections: List[VideoSection]
    validation: ValidationInfo
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "VideoScript":
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        sections = []
        for sec_data in data.get('sections', []):
            content = []
            for c in sec_data.get('content', []):
                ctype_str = c.get('type', '')
                try:
                    ctype = ContentType(ctype_str)
                except ValueError:
                    ctype = ContentType.VISUAL  # default
                content.append(SectionContent(
                    type=ctype,
                    text=c.get('text', ''),
                    tts_text=c.get('tts_text'),
                ))
            
            sections.append(VideoSection(
                title=sec_data.get('title', ''),
                time_range=sec_data.get('time_range', ''),
                content=content,
                visual_prompts=sec_data.get('visual_prompts', []),
                skip_subtitles=sec_data.get('skip_subtitles', False),
                visual_entries=sec_data.get('visual_entries', []),
            ))
        
        val_data = data.get('validation', {})
        validation = ValidationInfo(
            total_sections=val_data.get('total_sections', 0),
            sections_with_visual_prompts=val_data.get('sections_with_visual_prompts', 0),
            sections_with_narration=val_data.get('sections_with_narration', 0),
            hierarchical_structure=val_data.get('hierarchical_structure', 'unknown'),
            markdown_headers_mapped=val_data.get('markdown_headers_mapped', False),
            visual_prompts_extracted=val_data.get('visual_prompts_extracted', False),
            nested_lists_handled=val_data.get('nested_lists_handled', False),
            malformed_entries_rejected=val_data.get('malformed_entries_rejected', False),
        )
        
        return cls(sections=sections, validation=validation)
    
    def get_total_duration(self) -> float:
        return sum(s.duration_estimate for s in self.sections)
    
    def get_section_by_title(self, title: str) -> Optional[VideoSection]:
        for s in self.sections:
            if title in s.title:
                return s
        return None