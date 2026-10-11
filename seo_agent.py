import json
import re
from typing import Dict

def generate_shorts_seo_metadata(
    clip_title: str,
    hook_text: str,
    clip_transcript: str = "",
    api_key: str = ""
) -> Dict:
    """
    AI Agent that generates viral YouTube Shorts metadata:
    - 3 High-CTR Title options (under 50 chars, curiosity-driven)
    - High-retention SEO Description
    - High-ranking niche hashtags
    - Best upload timing recommendation
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""You are a world-class YouTube Shorts Growth Strategist and SEO Algorithm Expert.
Your goal is to optimize this short-form video clip to get maximum views, click-through rate (CTR), and viewer retention on YouTube Shorts.

CLIP CONTEXT:
- Working Title: {clip_title}
- Opening Hook: "{hook_text}"
- Dialogue / Transcript: "{clip_transcript[:500]}"

INSTRUCTIONS:
1. TITLES: Provide 3 distinct click-worthy titles:
   - Title 1: Curiosity Gap (leaves viewer wanting more, under 45 chars)
   - Title 2: Bold / Contrarian Statement (emotional or shocking)
   - Title 3: Question / How-To format
   - Include 1 emoji and '#shorts' in each title.
2. DESCRIPTION: A short, 3-sentence description optimized for the Shorts search algorithm with a clear call-to-action (CTA) to subscribe and comment.
3. HASHTAGS: Exactly 6 to 8 trending and niche-specific hashtags (always include #shorts #viral #youtubeshorts followed by niche tags).
4. VIRAL_TIP: 1 tactical tip for the creator (e.g. pinned comment idea, loop tip).

Output strictly valid JSON with no markdown wrapping, matching this exact schema:
{{
  "titles": [
    "Title 1 with emoji #shorts",
    "Title 2 with emoji #shorts",
    "Title 3 with emoji #shorts"
  ],
  "description": "Engaging description text with CTA...",
  "hashtags": ["#shorts", "#viral", "#youtubeshorts", "#topic1", "#topic2", "#topic3"],
  "viral_tip": "One actionable tip to boost retention and comments."
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini SEO Agent fallback: {e}")
        # Clean markdown if returned
        try:
            cleaned = re.sub(r"^```json\s*", "", response.text.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except Exception:
            # High-quality heuristic fallback
            safe_title = clip_title.replace("Clip", "Must Watch")
            return {
                "titles": [
                    f"Wait till you hear this! 🤯 #shorts",
                    f"The secret nobody talks about 🤫 #shorts",
                    f"{safe_title} 🔥 #shorts"
                ],
                "description": f"Here is the truth about this moment! What do you think? Drop your thoughts below 👇\n\nSubscribe for daily shorts!",
                "hashtags": ["#shorts", "#viral", "#trending", "#youtubeshorts", "#facts", "#explore"],
                "viral_tip": "Pin your own question in the comments to drive higher comment volume and algorithm push."
            }
