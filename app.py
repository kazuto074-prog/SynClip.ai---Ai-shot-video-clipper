import os
import sys

# Ensure Torch CUDA DLLs are loaded before anything else
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

import gradio as gr
from config import DEFAULT_WHISPER_MODEL, DEFAULT_MIN_DURATION, DEFAULT_MAX_DURATION, OUTPUT_DIR
from downloader import download_youtube_video
from transcriber import AudioTranscriber
from highlight_detector import analyze_highlights_gemini, analyze_highlights_local_heuristic
from video_cutter import cut_clip

CUSTOM_CSS = """
/* Clipper AI Modern Dark Studio Styling */
body, .gradio-container {
    background-color: #0f1117 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e2e8f0 !important;
}

.studio-header {
    text-align: center;
    padding: 24px 0 16px 0;
    margin-bottom: 20px;
    border-bottom: 1px solid #1e293b;
}

.studio-header h1 {
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #a855f7 0%, #3b82f6 50%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}

.studio-header p {
    font-size: 1.05rem;
    color: #94a3b8;
}

.control-panel {
    background-color: #181d2a !important;
    border: 1px solid #283046 !important;
    border-radius: 14px !important;
    padding: 20px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
}

.results-panel {
    background-color: #181d2a !important;
    border: 1px solid #283046 !important;
    border-radius: 14px !important;
    padding: 20px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
}

.clip-card {
    background-color: #1f2638 !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin-bottom: 20px !important;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.clip-card:hover {
    border-color: #8b5cf6 !important;
    transform: translateY(-2px);
}

.generate-btn {
    background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1.15rem !important;
    padding: 14px 28px !important;
    border-radius: 10px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
    cursor: pointer !important;
}

.generate-btn:hover {
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6) !important;
}
"""

FRAMEWORK_CHOICES = {
    "📱 9:16 Vertical (Blurred Background - Podcast & Talk Shows)": "9:16_blurred",
    "👤 9:16 Vertical (Smart Face Center - Auto Speaker Track)": "9:16_face",
    "👥 9:16 Vertical (Split-Screen - Top Video & Bottom Ambient)": "9:16_split",
    "⏹️ 1:1 Square (Instagram & LinkedIn Social Feed)": "1:1_square",
    "🎬 4:5 Portrait (Instagram & Facebook Feed)": "4:5_portrait",
    "🖥️ 16:9 Landscape (Original Aspect Ratio Cut)": "16:9_original",
}

def process_video_pipeline(
    youtube_url: str,
    uploaded_file,
    layout_label: str,
    add_subs: bool,
    clip_count: int,
    min_dur: int,
    max_dur: int,
    whisper_model_name: str,
    gemini_api_key: str,
    progress=gr.Progress(track_tqdm=True)
):
    try:
        layout_mode = FRAMEWORK_CHOICES.get(layout_label, "9:16_blurred")

        # Step 1: Video Ingestion
        if youtube_url and youtube_url.strip():
            progress(0.05, desc="Step 1/4: Downloading YouTube video...")
            video_path, audio_path, meta = download_youtube_video(
                youtube_url.strip(),
                progress_callback=lambda msg: progress(0.15, desc=f"Step 1/4: {msg}")
            )
            video_title = meta.get("title", "Video")
        elif uploaded_file is not None:
            progress(0.05, desc="Step 1/4: Ingesting uploaded file...")
            video_path = uploaded_file.name if hasattr(uploaded_file, "name") else str(uploaded_file)
            video_title = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.splitext(video_path)[0] + "_audio.mp3"
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1",
                audio_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        else:
            return "❌ Please paste a YouTube URL or upload a video file.", []

        # Step 2: GPU Transcription
        progress(0.25, desc=f"Step 2/4: Transcribing speech with Whisper ({whisper_model_name}) on RTX 3050 GPU...")
        transcriber = AudioTranscriber(model_size=whisper_model_name)
        transcript = transcriber.transcribe(
            audio_path,
            progress_callback=lambda msg: progress(0.45, desc=f"Step 2/4: {msg}")
        )

        if not transcript.get("segments"):
            return "⚠️ No speech detected in video audio. Please try another video with spoken dialogue.", []

        # Step 3: Highlight Analysis
        progress(0.60, desc="Step 3/4: AI detecting viral hooks, punchlines, and retention moments...")
        clips_data = []
        if gemini_api_key and gemini_api_key.strip():
            try:
                clips_data = analyze_highlights_gemini(
                    transcript,
                    api_key=gemini_api_key.strip(),
                    min_duration=min_dur,
                    max_duration=max_dur,
                    num_clips=clip_count
                )
            except Exception as e:
                print(f"Gemini API fallback to local heuristic: {e}")
                clips_data = analyze_highlights_local_heuristic(
                    transcript,
                    min_duration=min_dur,
                    max_duration=max_dur,
                    num_clips=clip_count
                )
        else:
            clips_data = analyze_highlights_local_heuristic(
                transcript,
                min_duration=min_dur,
                max_duration=max_dur,
                num_clips=clip_count
            )

        if not clips_data:
            return "⚠️ No clips found with the current duration parameters. Try widening Min/Max duration.", []

        # Step 4: Video Cutting & Layout Framework Render
        rendered_clips = []
        total_clips = len(clips_data)
        for idx, clip in enumerate(clips_data):
            pct = 0.65 + (idx / total_clips) * 0.32
            c_title = clip.get("title", f"Clip #{idx+1}")
            progress(pct, desc=f"Step 4/4: Rendering clip {idx+1}/{total_clips} with {layout_label[:15]}... ({c_title})")

            out_video = cut_clip(
                video_path=video_path,
                start_time=float(clip["start"]),
                end_time=float(clip["end"]),
                clip_title=c_title,
                layout_mode=layout_mode,
                add_subtitles=add_subs,
                segments=transcript.get("segments", []),
                progress_callback=lambda msg: progress(pct, desc=msg)
            )

            dur = float(clip["end"]) - float(clip["start"])
            rendered_clips.append({
                "video": out_video,
                "title": c_title,
                "score": clip.get("virality_score", 88),
                "hook": clip.get("hook", ""),
                "duration": f"{dur:.1f}s",
                "reason": clip.get("reason", "High retention hook"),
            })

        progress(1.0, desc="Complete! All clips are ready to preview and download.")
        status_msg = f"### ✅ Success! Generated {len(rendered_clips)} Viral Clips\n**Source:** *{video_title}* | **Layout:** *{layout_label.split('(')[0].strip()}*"
        return status_msg, rendered_clips

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"### ❌ Error Encountered\n```{str(e)}```", []


def build_app():
    with gr.Blocks(title="Clipper AI - Viral Shorts Studio") as app:
        # Header
        gr.HTML(
            """
            <div class="studio-header">
                <h1>⚡ CLIPPER AI STUDIO</h1>
                <p>100% Free, Local & GPU-Accelerated Viral Video Clipper powered by NVIDIA RTX 3050 & Whisper</p>
            </div>
            """
        )

        with gr.Row():
            # Left Column: Configuration Controls
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 📥 1. Video Source")
                    yt_url = gr.Textbox(
                        label="YouTube Link",
                        placeholder="https://www.youtube.com/watch?v=...",
                        lines=1
                    )
                    file_upload = gr.File(
                        label="Or Upload Local Video File",
                        file_types=["video"]
                    )

                with gr.Group():
                    gr.Markdown("### 📐 2. Video Framework & Layout")
                    layout_select = gr.Radio(
                        choices=list(FRAMEWORK_CHOICES.keys()),
                        value="📱 9:16 Vertical (Blurred Background - Podcast & Talk Shows)",
                        label="Select Video Layout / Aspect Ratio Framework"
                    )

                with gr.Group():
                    gr.Markdown("### 💬 3. Subtitles & Styling")
                    subtitles_chk = gr.Checkbox(
                        value=True,
                        label="🔥 Burn Animated Viral Subtitles (TikTok/Shorts Karaoke Style)"
                    )

                with gr.Accordion("⚙️ Advanced Settings (AI Model & Clip Duration)", open=False):
                    gemini_api_key = gr.Textbox(
                        label="Google Gemini API Key (Optional)",
                        value=os.environ.get("GEMINI_API_KEY", ""),
                        type="password",
                        info="Optional. Powers Gemini 3.8 Flash for virality reasoning and YouTube SEO metadata."
                    )
                    whisper_choice = gr.Dropdown(
                        choices=["tiny", "base", "small", "medium"],
                        value="base",
                        label="Whisper Transcription Model (runs on RTX 3050 GPU)"
                    )
                    clip_count = gr.Slider(
                        minimum=1, maximum=6, value=3, step=1,
                        label="Number of Viral Clips"
                    )
                    with gr.Row():
                        min_duration = gr.Slider(
                            minimum=10, maximum=60, value=20, step=5,
                            label="Min Clip Duration (s)"
                        )
                        max_duration = gr.Slider(
                            minimum=20, maximum=120, value=60, step=5,
                            label="Max Clip Duration (s)"
                        )

                generate_btn = gr.Button("🚀 Generate Viral Clips", variant="primary", size="lg")

            # Right Column: Results Gallery
            with gr.Column(scale=2):
                gr.Markdown("### 🎬 Generated Clips Gallery")
                status_banner = gr.Markdown("Paste a YouTube link or upload a video, then click **Generate Viral Clips**.")

                cards = []
                for i in range(4):
                    with gr.Group(visible=False) as card_group:
                        with gr.Row():
                            with gr.Column(scale=1):
                                title_disp = gr.Markdown(f"### Clip #{i+1}")
                                score_disp = gr.Markdown("🔥 Virality Score: **90/100**")
                                info_disp = gr.Markdown("Analysis...")
                            with gr.Column(scale=2):
                                vid_player = gr.Video(
                                    label=f"🎬 Clip #{i+1} Player",
                                    height=430,
                                    autoplay=False,
                                    interactive=False
                                )
                                dl_button = gr.DownloadButton(
                                    label=f"⬇️ Download Clip #{i+1} (MP4)",
                                    variant="primary",
                                    size="md"
                                )
                        cards.append((card_group, title_disp, score_disp, info_disp, vid_player, dl_button))

        # Event Handlers
        def on_generate(*inputs):
            status, clips = process_video_pipeline(*inputs)
            out_updates = [status]
            for idx, card in enumerate(cards):
                group, title, score, info, player, dl_btn = card
                if idx < len(clips):
                    c = clips[idx]
                    out_updates.extend([
                        gr.update(visible=True),
                        gr.update(value=f"### 🎯 {c['title']}"),
                        gr.update(value=f"🔥 Virality Score: **{c['score']}/100** | ⏱️ **{c['duration']}**"),
                        gr.update(value=f"**🪝 Opening Hook:**\n> *\"{c['hook']}\"*\n\n**💡 Virality Analysis:**\n{c['reason']}"),
                        gr.update(value=c['video']),
                        gr.update(value=c['video'], label=f"⬇️ Download '{c['title'][:25]}' (MP4)")
                    ])
                else:
                    out_updates.extend([
                        gr.update(visible=False),
                        gr.update(), gr.update(), gr.update(), gr.update(value=None), gr.update(value=None)
                    ])
            return out_updates

        output_targets = [status_banner]
        for c in cards:
            output_targets.extend(c)

        generate_btn.click(
            fn=on_generate,
            inputs=[
                yt_url, file_upload, layout_select, subtitles_chk,
                clip_count, min_duration, max_duration,
                whisper_choice, gemini_api_key
            ],
            outputs=output_targets
        )

    return app

if __name__ == "__main__":
    demo = build_app()
    demo.launch(server_name="127.0.0.1", server_port=7860)
