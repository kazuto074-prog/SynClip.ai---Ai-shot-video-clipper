# SynClip.ai - AI Short Video Clipper

**SynClip.ai** is an open-source, locally hosted AI video clipper studio powered by NVIDIA GPU CUDA hardware acceleration. Turn long YouTube videos or local video files into high-retention vertical (9:16) shorts, reels, and TikToks with dynamic animated subtitles and AI SEO recommendations.

---

## ✨ Features

- **⚡ Fast Audio-First Extraction**: Downloads compressed audio in seconds without downloading long videos upfront.
- **🎙️ GPU-Accelerated Transcription**: Word-level timestamps powered by Faster-Whisper on NVIDIA Tensor Cores.
- **🧠 AI Virality Detection**: Highlights key hooks and moments using Gemini 3.8 Flash (with offline heuristic fallback).
- **📱 9:16 Reframe & Frosted Blur**: Cinematic vertical reframing with background blur (`boxblur=25:5`).
- **💬 Animated Karaoke Captions**: Word-by-word highlighted ASS subtitle burning.
- **🚀 NVENC Hardware Acceleration**: High-speed video rendering with NVIDIA NVENC encoder.
- **🤖 YouTube Shorts SEO Agent**: Generates 3 high-CTR titles, optimized descriptions, trending hashtags, and 1-click copy for YouTube Studio.
- **🎬 In-Browser Playback & Direct Download**: Stream clips directly in the web UI with 1-click MP4 download.
- **🔒 100% Free & Local**: No recurring subscriptions or paywalls.

---

## 🛠️ Quick Start

### 1. Requirements
- Python 3.10 or higher
- NVIDIA GPU with CUDA support (e.g., RTX 3050, 4060, etc.)
- FFmpeg installed and available in PATH

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key (Optional)
Copy `.env.example` to `.env` and add your Google Gemini API Key:
```bash
cp .env.example .env
```
*(You can also input your Gemini key directly in the web UI Settings modal).*

### 4. Run the Studio
**On Windows:**
Double-click `run.bat` or run:
```bash
python studio_server.py
```

Open your browser at **http://127.0.0.1:7860**.

---

## 📁 Project Structure

```
├── config.py                 # Core paths, GPU device, and model configs
├── downloader.py             # High-speed audio & section downloader (yt-dlp)
├── transcriber.py            # Faster-Whisper CUDA speech recognition
├── highlight_detector.py     # Gemini virality detection & local fallback
├── smart_cropper.py          # 9:16 layout, face tracking, and frosted blur filters
├── subtitle_generator.py     # Animated ASS karaoke subtitle engine
├── video_cutter.py           # FFmpeg NVENC cutter and subtitle burner
├── seo_agent.py              # YouTube Shorts Title, Description & Tag Generator
├── studio_server.py          # FastAPI server with SSE progress & streaming video
├── templates/
│   └── index.html            # Dark SaaS web UI
└── run.bat                   # 1-Click Windows launcher
```

---

## 📄 License
MIT License
