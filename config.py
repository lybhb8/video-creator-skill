"""
Configuration loader for video generation.
"""
import yaml
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class OutputConfig:
    resolution: List[int]
    fps: int
    format: str
    codec: str
    bitrate: str
    output_dir: str
    final_filename: str


@dataclass
class ManimConfig:
    quality: str
    renderer: str
    quality_dir: str
    background_color: str
    font: str
    code_font: str
    text_color: str
    accent_color: str
    success_color: str
    error_color: str
    warning_color: str
    terminal_bg: str
    terminal_text: str
    terminal_prompt: str


@dataclass
class TimingConfig:
    intro: float
    hardware: float
    questions: float
    models: float
    speed_results: float
    accuracy: float
    ministral_3b: float
    comparison: float
    ranking: float
    outro: float
    tech_specs: float


@dataclass
class TTSConfig:
    voice: str
    rate: str
    volume: str
    pitch: str
    output_format: str


@dataclass
class SubtitleConfig:
    font_size: int
    font_color: str
    outline_color: str
    outline_width: int
    position: str = "bottom"
    margin_bottom: int = 80
    max_chars_per_line: int = 30


@dataclass
class AssetsConfig:
    fonts_dir: str
    images_dir: str
    audio_dir: str
    temp_dir: str


@dataclass
class LoggingConfig:
    level: str
    file: str


@dataclass
class Config:
    output: OutputConfig
    manim: ManimConfig
    timing: TimingConfig
    tts: TTSConfig
    subtitles: SubtitleConfig
    chart_colors: List[str]
    assets: AssetsConfig
    logging: LoggingConfig


def load_config(config_path: str = "config.yaml") -> Config:
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return Config(
        output=OutputConfig(**data['output']),
        manim=ManimConfig(**data['manim']),
        timing=TimingConfig(**data['timing']),
        tts=TTSConfig(**data['tts']),
        subtitles=SubtitleConfig(**data['subtitles']),
        chart_colors=data['chart_colors'],
        assets=AssetsConfig(**data['assets']),
        logging=LoggingConfig(**data['logging']),
    )


# Global config instance
_config: Config = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config