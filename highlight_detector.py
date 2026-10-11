import json
import re
import os
from typing import List, Dict

def analyze_highlights_gemini(transcript_data: dict, api_key: str, min_duration: int = 20, max_duration: int = 60, num_clips: int = 4) -> List[Dict]:
    """
    Uses Google Gemini API to analyze transcript segments and identify the most viral short-form clips.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    segments = transcript_data.get("segments", [])
    if not segments:
        return []

    # Compact transcript format with timestamps for LLM
    formatted_transcript = []
    for s in segments:
        formatted_transcript.append(f"[{s['start']:.1f}s - {s['end']:.1f}s]: {s['text']}")
    transcript_text = "\n".join(formatted_transcript)

    prompt = f"""You are a master social media growth editor specializing in YouTube Shorts, TikTok, and Instagram Reels (like OpusClip).
Analyze the following timestamped video transcript and find the top {num_clips} most viral, engaging standalone clips.

VIRALITY CRITERIA:
1. STRONG HOOK: First 3 seconds must hook the viewer immediately (bold claim, intriguing question, punchy statement).
2. COMPLETE MICRO-STORY: The clip must make total sense standalone without missing context.
3. HIGH RETENTION & PACING: Keep viewers watching until the very last second.
4. DURATION: Each clip should ideally be between {min_duration} and {max_duration} seconds in duration (end - start).
5. EXACT TIMESTAMPS: Use the exact timestamps from the transcript segments.

Output strictly valid JSON with no markdown formatting, matching this exact schema:
[
  {{
    "title": "Short Catchy Click-Worthy Title",
    "hook": "The exact opening line that hooks the audience",
    "start": 12.5,
    "end": 48.0,
    "virality_score": 95,
    "reason": "Why this clip will get high retention and views"
  }}
]

TRANSCRIPT:
{transcript_text}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    try:
        clips = json.loads(response.text)
        clips.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
        return clips
    except Exception as e:
        print(f"Error parsing Gemini JSON: {e}")
        cleaned = re.sub(r"^```json\s*", "", response.text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)

def analyze_highlights_local_heuristic(transcript_data: dict, min_duration: int = 20, max_duration: int = 60, num_clips: int = 4) -> List[Dict]:
    """
    Offline/local heuristic detector that finds engaging segments based on questions,
    speech density, topic hooks, and natural pauses. Works with zero API keys.
    """
    segments = transcript_data.get("segments", [])
    if not segments:
        return []

    video_duration = transcript_data.get("duration", 0)
    if video_duration == 0 and segments:
        video_duration = segments[-1]["end"]

    # Adapt min_duration if video is shorter than default min_duration
    actual_min_duration = min(min_duration, max(5, int(video_duration * 0.5)))
    actual_max_duration = max(actual_min_duration + 5, min_duration, max_duration)

    hook_keywords = [
        "the secret", "the truth", "never", "always", "biggest mistake",
        "why you should", "how to", "stop doing", "nobody tells you",
        "here is why", "imagine if", "what happens when", "the problem with",
        "i discovered", "the key is", "shockingly", "crazy thing is", "don't ever",
        "all right", "so here", "look at", "check this", "listen"
    ]

    candidates = []
    total_segments = len(segments)

    for i in range(total_segments):
        start_time = float(segments[i]["start"])
        initial_text = segments[i]["text"].lower()

        # Score the opening hook
        hook_score = 55
        for kw in hook_keywords:
            if kw in initial_text:
                hook_score += 25
                break
        if "?" in segments[i]["text"]:
            hook_score += 15

        accumulated_text = []

        for j in range(i, total_segments):
            dur = float(segments[j]["end"]) - start_time
            accumulated_text.append(segments[j]["text"])

            if dur >= actual_min_duration:
                if dur <= actual_max_duration:
                    full_text = " ".join(accumulated_text)
                    word_count = len(full_text.split())
                    wpm = (word_count / max(0.1, dur)) * 60

                    pacing_score = 20 if (110 <= wpm <= 190) else 10
                    final_score = min(98, hook_score + pacing_score + (10 if dur >= 20 else 0))

                    candidates.append({
                        "title": f"Highlight {int(start_time//60):02d}:{int(start_time%60):02d}",
                        "hook": segments[i]["text"][:80] + "...",
                        "start": round(start_time, 2),
                        "end": round(float(segments[j]["end"]), 2),
                        "virality_score": int(final_score),
                        "reason": f"Punchy hook with active speech pacing ({int(wpm)} WPM)",
                        "text": full_text
                    })
                else:
                    break

    # If no candidate found via combination, create windowed fallback candidates
    if not candidates and segments:
        chunk_start = float(segments[0]["start"])
        chunk_end = float(segments[-1]["end"])
        chunk_text = " ".join([s["text"] for s in segments])
        candidates.append({
            "title": "Top Video Moment",
            "hook": segments[0]["text"][:80] + "...",
            "start": round(chunk_start, 2),
            "end": round(chunk_end, 2),
            "virality_score": 85,
            "reason": "Complete standalone segment with highest speech energy",
            "text": chunk_text
        })

    # Deduplicate overlapping clips and select top candidates
    candidates.sort(key=lambda x: x["virality_score"], reverse=True)
    selected = []
    for cand in candidates:
        overlap = False
        for s in selected:
            if max(cand["start"], s["start"]) < min(cand["end"], s["end"]) - 8:
                overlap = True
                break
        if not overlap:
            selected.append(cand)
        if len(selected) >= num_clips:
            break

    return selected
