import os
from pathlib import Path
from typing import List, Dict

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp format: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def generate_ass_subtitles(
    segments: List[Dict],
    clip_start: float,
    clip_end: float,
    output_ass_path: str,
    font_name: str = "Arial Black",
    font_size: int = 18,
    words_per_group: int = 3
) -> str:
    """
    Generates dynamic ASS subtitle file with karaoke / word-level timing
    matching the viral TikTok / YouTube Shorts style.
    """
    # Filter words within the clip start and end time
    clip_words = []
    for seg in segments:
        for w in seg.get("words", []):
            if w["start"] >= clip_start and w["end"] <= clip_end:
                # Adjust timestamps relative to clip start (0.00s)
                clip_words.append({
                    "word": w["word"].upper(),  # UPPERCASE looks great for Shorts
                    "start": max(0.0, w["start"] - clip_start),
                    "end": max(0.0, w["end"] - clip_start),
                })

    # Header for ASS
    # Colors in ASS are &HAABBGGRR (Alpha, Blue, Green, Red)
    # White = &H00FFFFFF, Yellow = &H0000D7FF (or &H0000FFFF), Green = &H0000FF00
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsStyle,{font_name},70,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    if not clip_words:
        # Fallback to segment-level subtitles if word-level timestamps aren't available
        for seg in segments:
            if seg["start"] >= clip_start and seg["end"] <= clip_end:
                start_str = format_ass_time(max(0.0, seg["start"] - clip_start))
                end_str = format_ass_time(max(0.0, seg["end"] - clip_start))
                text = seg["text"].strip().upper()
                events.append(f"Dialogue: 0,{start_str},{end_str},ShortsStyle,,0,0,0,,{{\\b1\\c&H0000FFFF&}}{text}")
    else:
        # Group words into small 2-4 word rhythmic bursts
        i = 0
        while i < len(clip_words):
            group = clip_words[i : i + words_per_group]
            i += words_per_group

            group_start = group[0]["start"]
            group_end = group[-1]["end"]

            # For each word in the group, create a dialogue line where the current active word is highlighted yellow
            for active_idx, active_word in enumerate(group):
                w_start = format_ass_time(active_word["start"])
                w_end = format_ass_time(active_word["end"])

                # Build line with active word in neon yellow/green and others in white
                line_parts = []
                for idx, w in enumerate(group):
                    if idx == active_idx:
                        # Highlight active word with bright yellow and slight scale
                        line_parts.append(f"{{\\c&H0000FFFF&\\fscx108\\fscy108}}{w['word']}{{\\rShortsStyle}}")
                    else:
                        line_parts.append(f"{{\\c&H00FFFFFF&}}{w['word']}")

                rendered_text = " ".join(line_parts)
                events.append(f"Dialogue: 0,{w_start},{w_end},ShortsStyle,,0,0,0,,{rendered_text}")

    full_ass_content = ass_header + "\n".join(events) + "\n"

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(full_ass_content)

    return output_ass_path
