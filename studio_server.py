import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure Torch CUDA DLLs are loaded
try:
    import torch
    torch_lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    if os.path.exists(torch_lib):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_lib)
        if torch_lib not in os.environ.get("PATH", ""):
            os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")
except Exception as e:
    print(f"Torch DLL initialization: {e}")

from config import BASE_DIR, OUTPUT_DIR, TEMP_DIR
from downloader import download_youtube_audio_fast, download_youtube_section_fast, sanitize_filename
from transcriber import AudioTranscriber
from highlight_detector import analyze_highlights_gemini, analyze_highlights_local_heuristic
from video_cutter import cut_clip
from seo_agent import generate_shorts_seo_metadata

app = FastAPI(title="SynClip.ai Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

# Default API Key from environment (optional)
DEFAULT_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def shift_segments_for_clip(segments: list, clip_start: float, clip_end: float) -> list:
    """Shifts timestamp coordinates so that clip_start becomes 0.0."""
    shifted = []
    for s in segments:
        if s["end"] >= clip_start and s["start"] <= clip_end:
            shifted_words = []
            for w in s.get("words", []):
                if w["end"] >= clip_start and w["start"] <= clip_end:
                    shifted_words.append({
                        "word": w["word"],
                        "start": max(0.0, round(w["start"] - clip_start, 2)),
                        "end": max(0.0, round(w["end"] - clip_start, 2)),
                        "probability": w.get("probability", 1.0)
                    })
            shifted.append({
                "start": max(0.0, round(s["start"] - clip_start, 2)),
                "end": max(0.0, round(s["end"] - clip_start, 2)),
                "text": s["text"],
                "words": shifted_words
            })
    return shifted

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_file = TEMPLATES_DIR / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

@app.get("/api/status")
async def get_system_status():
    cuda_avail = False
    device_name = "CPU Only"
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        if cuda_avail:
            device_name = torch.cuda.get_device_name(0)
    except Exception:
        pass
    return {
        "status": "online",
        "gpu_available": cuda_avail,
        "gpu_name": device_name,
        "whisper_ready": True,
        "default_key_set": bool(DEFAULT_API_KEY)
    }

@app.post("/api/upload")
async def upload_video_file(file: UploadFile = File(...)):
    clean_name = sanitize_filename(file.filename)
    dest_path = TEMP_DIR / clean_name
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"status": "success", "file_path": str(dest_path), "filename": clean_name}

@app.post("/api/seo")
async def generate_seo_endpoint(
    clip_title: str = Form(...),
    hook_text: str = Form(""),
    clip_transcript: str = Form(""),
    gemini_key: Optional[str] = Form(None)
):
    key = gemini_key.strip() if gemini_key and gemini_key.strip() else DEFAULT_API_KEY
    loop = asyncio.get_event_loop()
    metadata = await loop.run_in_executor(
        None,
        lambda: generate_shorts_seo_metadata(
            clip_title=clip_title,
            hook_text=hook_text,
            clip_transcript=clip_transcript,
            api_key=key
        )
    )
    return metadata

@app.get("/api/video/{filename}")
async def stream_video(filename: str, request: Request):
    """HTTP 206 Partial Content video streaming for smooth seeking in browser."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video clip not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header:
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0])
        end = int(byte_range[1]) if byte_range[1] else file_size - 1
        length = end - start + 1

        def iterfile():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk_size = min(64 * 1024, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iterfile(), status_code=206, headers=headers)
    else:
        return FileResponse(file_path, media_type="video/mp4", filename=filename)

@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """Direct forced file attachment download for browser."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video clip not found")
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/recent_clips")
async def get_recent_clips():
    """Returns list of already rendered MP4 clips with titles and metadata."""
    clips = []
    if OUTPUT_DIR.exists():
        mp4_files = sorted(OUTPUT_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
        for idx, f in enumerate(mp4_files[:10]):
            stem = f.stem
            clean_title = stem.replace("clip_", "").replace("_", " ")
            words = clean_title.split()
            if len(words) > 1 and len(words[-1]) == 6 and all(c in '0123456789abcdefABCDEF' for c in words[-1]):
                clean_title = " ".join(words[:-1])
            clean_title = clean_title.strip()
            
            size_mb = round(os.path.getsize(f) / (1024 * 1024), 1)
            clips.append({
                "id": idx + 1,
                "title": clean_title,
                "score": 92 + (idx % 7),
                "hook": f"Key takeaway: {clean_title}",
                "duration": f"{size_mb} MB",
                "filename": f.name,
                "video_url": f"/api/video/{f.name}",
                "download_url": f"/api/download/{f.name}",
                "seo": {
                    "titles": [
                        f"{clean_title} 🔥 #shorts",
                        f"Why You Need To Know This: {clean_title} #viral",
                        f"The Secret To {clean_title} 🤯"
                    ],
                    "description": f"Must watch moment from {clean_title}.\n\nSubscribe for daily viral breakdown shorts!\n\n#shorts #viral #trending #fyp",
                    "hashtags": ["#shorts", "#viral", "#trending", "#fyp", "#shortsvideo"],
                    "viral_tip": "Ask viewers to comment their opinion in the first 5 seconds."
                }
            })
    return {"clips": clips}


@app.post("/api/generate")
async def generate_clips_endpoint(
    youtube_url: Optional[str] = Form(None),
    local_file_path: Optional[str] = Form(None),
    layout_mode: str = Form("9:16_blurred"),
    add_subtitles: bool = Form(True),
    clip_count: int = Form(3),
    min_duration: int = Form(20),
    max_duration: int = Form(60),
    whisper_model: str = Form("base"),
    gemini_key: Optional[str] = Form(None)
):
    api_key = (gemini_key.strip() if gemini_key and gemini_key.strip() else DEFAULT_API_KEY)

    async def event_generator():
        try:
            loop = asyncio.get_event_loop()
            is_youtube = False
            unique_session_id = str(uuid.uuid4())[:6]

            # 1. High Speed Audio Ingestion
            if youtube_url and youtube_url.strip():
                is_youtube = True
                yield f"data: {json.dumps({'step': 1, 'percent': 15, 'message': '⚡ Ultra-Fast: Extracting lightweight audio stream (~15 MB)...'})}\n\n"
                await asyncio.sleep(0.05)

                a_path, meta = await loop.run_in_executor(
                    None, download_youtube_audio_fast, youtube_url.strip()
                )
                source_title = meta.get("title", "YouTube Video")
            elif local_file_path and os.path.exists(local_file_path):
                v_path = local_file_path
                source_title = os.path.basename(local_file_path)
                a_path = os.path.splitext(local_file_path)[0] + "_audio.mp3"
                import subprocess
                subprocess.run([
                    "ffmpeg", "-y", "-i", v_path,
                    "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1",
                    a_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                yield f"data: {json.dumps({'error': 'Please provide a valid YouTube URL or upload a video file.'})}\n\n"
                return

            # 2. Lightning GPU Transcription
            yield f"data: {json.dumps({'step': 2, 'percent': 35, 'message': f'⚡ RTX 3050 CUDA Transcribing speech (Whisper {whisper_model})...'})}\n\n"
            await asyncio.sleep(0.05)

            transcriber = AudioTranscriber(model_size=whisper_model)
            transcript = await loop.run_in_executor(
                None, transcriber.transcribe, a_path
            )

            if not transcript.get("segments"):
                yield f"data: {json.dumps({'error': 'No speech detected in audio. Please try another video.'})}\n\n"
                return

            # 3. Gemini 3.8 Flash Highlight Detection
            yield f"data: {json.dumps({'step': 3, 'percent': 55, 'message': '🧠 Gemini 3.8 Flash analyzing viral retention hooks & punchlines...'})}\n\n"
            await asyncio.sleep(0.05)

            clips_data = []
            if api_key:
                try:
                    clips_data = await loop.run_in_executor(
                        None,
                        lambda: analyze_highlights_gemini(
                            transcript,
                            api_key=api_key,
                            min_duration=min_duration,
                            max_duration=max_duration,
                            num_clips=clip_count
                        )
                    )
                except Exception as e:
                    print(f"Gemini API error, falling back to local heuristic: {e}")
                    clips_data = await loop.run_in_executor(
                        None,
                        lambda: analyze_highlights_local_heuristic(
                            transcript,
                            min_duration=min_duration,
                            max_duration=max_duration,
                            num_clips=clip_count
                        )
                    )
            else:
                clips_data = await loop.run_in_executor(
                    None,
                    lambda: analyze_highlights_local_heuristic(
                        transcript,
                        min_duration=min_duration,
                        max_duration=max_duration,
                        num_clips=clip_count
                    )
                )

            if not clips_data:
                yield f"data: {json.dumps({'error': 'No clips found. Try adjusting min/max duration.'})}\n\n"
                return

            # 4. Fast Section Download & NVENC GPU Rendering
            total_clips = len(clips_data)
            completed_clips = []

            for idx, clip in enumerate(clips_data):
                pct = int(60 + (idx / total_clips) * 38)
                c_title = clip.get("title", f"Clip #{idx+1}")
                dur = float(clip["end"]) - float(clip["start"])

                if is_youtube:
                    yield f"data: {json.dumps({'step': 4, 'percent': pct, 'message': f'⚡ Downloading clip section {idx+1}/{total_clips} ({dur:.0f}s)...'})}\n\n"
                    raw_section_path = str(TEMP_DIR / f"sec_{unique_session_id}_{idx}.mp4")
                    
                    # Download ONLY the 30-60 second section needed
                    await loop.run_in_executor(
                        None,
                        lambda: download_youtube_section_fast(
                            url=youtube_url.strip(),
                            start_sec=float(clip["start"]),
                            end_sec=float(clip["end"]),
                            output_path=raw_section_path
                        )
                    )

                    shifted_segments = shift_segments_for_clip(
                        transcript.get("segments", []),
                        float(clip["start"]),
                        float(clip["end"])
                    )

                    yield f"data: {json.dumps({'step': 4, 'percent': pct + 4, 'message': f'🎬 NVENC GPU rendering {idx+1}/{total_clips}: {c_title}...'})}\n\n"
                    
                    out_path = await loop.run_in_executor(
                        None,
                        lambda: cut_clip(
                            video_path=raw_section_path,
                            start_time=0.0,
                            end_time=dur,
                            clip_title=c_title,
                            layout_mode=layout_mode,
                            add_subtitles=add_subtitles,
                            segments=shifted_segments
                        )
                    )
                else:
                    yield f"data: {json.dumps({'step': 4, 'percent': pct, 'message': f'🎬 NVENC GPU rendering {idx+1}/{total_clips}: {c_title}...'})}\n\n"
                    out_path = await loop.run_in_executor(
                        None,
                        lambda: cut_clip(
                            video_path=v_path,
                            start_time=float(clip["start"]),
                            end_time=float(clip["end"]),
                            clip_title=c_title,
                            layout_mode=layout_mode,
                            add_subtitles=add_subtitles,
                            segments=transcript.get("segments", [])
                        )
                    )

                filename = os.path.basename(out_path)

                # Generate AI SEO recommendations for YouTube Shorts
                seo_meta = await loop.run_in_executor(
                    None,
                    lambda: generate_shorts_seo_metadata(
                        clip_title=c_title,
                        hook_text=clip.get("hook", ""),
                        clip_transcript=clip.get("text", ""),
                        api_key=api_key
                    )
                )

                completed_clips.append({
                    "id": idx + 1,
                    "title": c_title,
                    "score": clip.get("virality_score", 90),
                    "hook": clip.get("hook", ""),
                    "reason": clip.get("reason", "High-retention viral moment"),
                    "duration": f"{dur:.1f}s",
                    "filename": filename,
                    "video_url": f"/api/video/{filename}",
                    "download_url": f"/api/download/{filename}",
                    "seo": seo_meta
                })

            # Done!
            yield f"data: {json.dumps({'step': 5, 'percent': 100, 'done': True, 'clips': completed_clips, 'source_title': source_title})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("studio_server:app", host="127.0.0.1", port=7860, reload=False)
