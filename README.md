# SynClip.ai — AI Short Video Clipper Studio 🎬⚡

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-CUDA%2012-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Faster--Whisper](https://img.shields.io/badge/Whisper-GPU%20TensorRT-7928CA?style=for-the-badge&logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**100% Free, Local & GPU-Accelerated AI Video Clipper Studio.**  
*Transform long YouTube podcasts, interviews, and gaming streams into viral 9:16 Shorts, Reels, and TikToks with automated karaoke subtitles and high-CTR YouTube SEO recommendations.*

[Key Features](#-detailed-features) • [Comparison](#-synclipai-vs-cloud-clippers) • [Installation](#-installation-guide) • [Framing Frameworks](#-aspect-ratio--framing-modes) • [Tech Stack](#-technology-stack)

</div>

---

## 📖 Overview

**SynClip.ai** runs entirely on your local machine using hardware-accelerated **NVIDIA CUDA** and **NVENC** encoding. Unlike cloud services (such as Opus Clip or ClipCraft) that charge monthly subscriptions and impose watermark or credit limitations, SynClip.ai is **completely free, unlimited, and private**.

```
[ Long YouTube / Local Video ]
              │
              ▼ (2-3s audio extraction)
[ Faster-Whisper GPU Transcription ]
              │
              ▼ (Word-level timestamps & VAD)
[ Gemini 3.8 Flash Virality Reasoning ]
              │
              ▼ (Hook detection & 30s section extraction)
[ Smart 9:16 Reframing + Frosted Blur (boxblur=25:5) ]
              │
              ▼ (NVENC hardware subtitle burning)
[ In-Browser Video Player + 1-Click MP4 Download + AI Shorts SEO Agent ]
```

---

## ⚡ SynClip.ai vs. Cloud Clippers

| Feature | SynClip.ai (This Project) | Opus Clip / ClipCraft | Standard Python Scripts |
| :--- | :---: | :---: | :---: |
| **Pricing** | **100% Free & Open Source** | $19 – $49 / month | Free |
| **Usage Limits** | **Unlimited Minutes** | 60–150 credits/month | Unlimited |
| **Privacy** | **100% Local (Your Machine)** | Cloud Servers | Local |
| **Hardware Acceleration** | **NVIDIA NVENC + CUDA cuBLAS** | Cloud GPU Farm | CPU Only (Slow) |
| **Audio-First Ingestion** | **2–4 Seconds (~15 MB)** | Slow Full Upload | Downloads Full Video (GBs) |
| **Background Blur Quality** | **Frosted Glass (`boxblur=25:5`)** | Fixed Blur | Black Bars / Cropped |
| **Captions** | **Animated TikTok/Shorts Karaoke** | Pre-rendered | Static SRT |
| **SEO Generator** | **Gemini 3.8 Shorts SEO Agent** | Basic Title Only | None |
| **Web UI** | **Full Dark SaaS Dashboard** | Web Dashboard | Terminal CLI Only |

---

## ✨ Detailed Features

### 1. Core Processing Pipeline

| Stage | Technology | Speed / Performance | Description |
| :--- | :--- | :--- | :--- |
| **Ingestion** | `yt-dlp` (Audio-First) | 2–4 seconds (~15 MB) | Extracts compressed audio stream instantly without downloading heavy 1080p video files upfront. |
| **Speech-to-Text** | `Faster-Whisper` + `CUDA` | ~10x realtime speed | Word-level timestamp generation using half-precision `float16` on NVIDIA Tensor Cores with VAD filtering. |
| **Hook Detection** | `Google Gemini 3.8 Flash` | 1–2 seconds | Analyzes transcript density, opening questions, and emotional hooks to assign virality scores (0–100). |
| **Local Fallback** | Offline Heuristic Algorithm | Instant (<100ms) | Identifies question peaks, spoken density, and sentence cadence when offline or without API keys. |
| **Reframing** | FFmpeg Complex Filtergraph | Hardware-accelerated | Crops or ambiently blurs 16:9 widescreen content into vertical 9:16, 1:1, or split-screen layouts. |
| **Subtitles** | Advanced SubStation (`.ass`) | Real-time burn | Renders neon active-word highlighted animated karaoke subtitles directly onto video frames. |
| **Encoding** | `h264_nvenc` (NVIDIA GPU) | Up to 180+ FPS | Fast hardware video encoding with `-pix_fmt yuv420p` and `-movflags +faststart` for browser streaming. |

---

### 2. 📱 Aspect Ratio & Framing Modes

| Mode Name | Aspect Ratio | Resolution | Recommended Content | FFmpeg Filter Strategy |
| :--- | :---: | :---: | :--- | :--- |
| **9:16 Podcast (Blur)** *(Default)* | `9:16` | 1080 × 1920 | Podcasts, interviews, talk shows | Background: scaled 1080x1920 with smooth frosted `boxblur=25:5`. Foreground: scaled centered overlay. |
| **9:16 Smart Face Tracker** | `9:16` | 1080 × 1920 | Vlogs, solo speakers, reaction videos | Dynamically centers the primary active speaker inside a vertical 1080x1920 crop window. |
| **9:16 Split Screen** | `9:16` | 1080 × 1920 | Dual host interviews, gameplay + cam | Stacks speaker feed on top half and ambient background/gameplay on bottom half. |
| **1:1 Square Feed** | `1:1` | 1080 × 1080 | Instagram & LinkedIn social feeds | 1:1 square framing with blurred peripheral ambient padding. |
| **16:9 Original Landscape** | `16:9` | 1920 × 1080 | YouTube, Twitter, presentations | Preserves widescreen frame while burning animated captions and rendering highlight cuts. |

---

### 3. 🤖 AI Shorts SEO Agent

Every generated clip automatically includes an integrated SEO Drawer optimized for the YouTube algorithm:

| SEO Module | Output Format | Purpose & Strategy |
| :--- | :--- | :--- |
| **Viral Titles** | 3 Distinct Title Options | High-CTR headlines leveraging curiosity gaps, contrarian hooks, and question formats (`<50` characters with `#shorts`). |
| **SEO Description** | 3-Sentence Optimized Body | Keywords matched to YouTube Shorts search indexing with clear call-to-action (CTA) to subscribe and comment. |
| **Trending Hashtags** | 6–8 Tag Chips | Curated blend of general tags (`#shorts`, `#viral`, `#trending`) and niche-specific tags. |
| **Spoken Hook Quote** | Text Card | Highlights the spoken hook sentence from the first 3 seconds of the clip. |
| **Master 1-Click Copy** | Clipboard Action | Copies Title, Description, and Hashtags in one formatted block ready to paste into YouTube Studio. |

---

## 💻 Hardware & Benchmark Recommendations

| Hardware Tier | GPU Model | VRAM | Whisper Model | Cut Duration (30s Clip) |
| :--- | :--- | :---: | :---: | :---: |
| **Entry Level** | NVIDIA GTX 1650 / 1660 | 4 GB | `tiny` / `base` | ~12–18s |
| **Recommended** | **NVIDIA RTX 3050 (Laptop/Desktop)** | **6 GB** | **`base` / `small`** | **~6–9s** |
| **High Performance** | NVIDIA RTX 4060 / 3070 | 8 GB | `small` / `medium` | ~3–5s |
| **CPU Only (Fallback)** | Intel Core i5/i7 / AMD Ryzen | 16 GB RAM | `tiny` | ~35–60s |

---

## 🛠️ Installation Guide

Follow these step-by-step instructions to set up and run SynClip.ai on your machine.

### Step 1: Clone the Repository

Open your terminal or command prompt and clone the repository:

```bash
git clone https://github.com/kazuto074-prog/SynClip.ai---Ai-shot-video-clipper.git
cd SynClip.ai---Ai-shot-video-clipper
```

---

### Step 2: Verify System Prerequisites

Ensure you have the following installed:
1. **Python 3.10 or higher** ([Download Python](https://www.python.org/downloads/))
2. **NVIDIA Graphics Driver** with CUDA support ([NVIDIA Drivers](https://www.nvidia.com/Download/index.aspx))
3. **FFmpeg & FFprobe**:
   - **Windows:** Download the essentials build from [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) and add the `bin/` folder to your system `PATH`.
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt update && sudo apt install -y ffmpeg`

Verify FFmpeg in your terminal:
```bash
ffmpeg -version
ffprobe -version
```

---

### Step 3: Create & Activate a Virtual Environment

It is recommended to use an isolated Python virtual environment:

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 4: Install PyTorch with CUDA Acceleration

Install PyTorch built with CUDA support:

**CUDA 12.1+ (Recommended for RTX 30/40 Series):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

*(For CPU-only environments, run: `pip install torch torchvision torchaudio`).*

---

### Step 5: Install Project Dependencies

Install the remaining dependencies via `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

### Step 6: Configure Environment Variables (Optional)

SynClip.ai works out-of-the-box with offline heuristic detection. To enable **Gemini 3.8 Flash** virality reasoning and the **AI Shorts SEO Agent**:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your free Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   *(You can generate a free key at [Google AI Studio](https://aistudio.google.com/)).*

> *Note: You can also enter or update your Gemini API key directly in the web UI Settings modal at any time.*

---

## 🚀 Running SynClip.ai

### Windows 1-Click Launch
Double-click the included launcher:
```text
run.bat
```

### Manual Command Line Launch
Run the FastAPI studio server directly:
```bash
python studio_server.py
```

Once running, navigate to:
👉 **`http://127.0.0.1:7860`**

---

## 🎯 How to Use

1. **Paste URL or Upload Video**:
   - Paste any YouTube link (podcast, lecture, interview, vlog) into the input box.
   - Or click the folder icon to select a local MP4 file.
2. **Select Aspect Ratio Framing**:
   - Choose your preferred framing from the sidebar drawer (e.g., `9:16 Podcast (Blur)`).
3. **Click "Get Viral Clips →"**:
   - Watch real-time SSE progress as audio is downloaded, transcribed on your GPU, viral hooks are identified, and clips are rendered with NVENC.
4. **Preview & Download**:
   - Play clips directly in the in-browser 9:16 player.
   - Click **"Download MP4"** for instant 1-click attachment downloading.
5. **Copy SEO Package**:
   - Review viral titles, descriptions, and hashtags generated by the SEO Agent.
   - Click **"Copy Everything for YouTube Shorts"** and paste directly into YouTube Studio.

---

## 📁 Project Architecture

```
SynClip.ai/
├── config.py                 # Core paths, GPU device, and model configs
├── downloader.py             # High-speed audio & section downloader (yt-dlp)
├── transcriber.py            # Faster-Whisper CUDA speech recognition engine
├── highlight_detector.py     # Gemini virality detection & offline heuristic fallback
├── smart_cropper.py          # 9:16 layout, face tracking, and frosted blur filters
├── subtitle_generator.py     # Dynamic ASS animated karaoke subtitle engine
├── video_cutter.py           # FFmpeg NVENC cutter and subtitle burner
├── seo_agent.py              # YouTube Shorts Title, Description & Hashtag Generator
├── studio_server.py          # FastAPI backend with SSE streaming & HTTP 206 video server
├── templates/
│   └── index.html            # Dark SaaS responsive frontend
├── requirements.txt          # Python dependencies
├── run.bat                   # 1-Click Windows launcher
├── .env.example              # Sample environment template
└── .gitignore                # Production ignore rules (prevents secrets/media leakage)
```

---

## 🔧 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `cublas64_12.dll not found` | PyTorch DLL directory not in Windows PATH | SynClip.ai automatically registers `site-packages/torch/lib` via `os.add_dll_directory()`. Ensure PyTorch CUDA is installed via Step 4. |
| `FFExecutableNotFoundError` | FFmpeg / FFprobe missing from PATH | Download FFmpeg from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and place `ffmpeg.exe` and `ffprobe.exe` into a directory included in your PATH. |
| `Gemini 503 / Quota Exceeded` | Google API temporary rate limit | The studio automatically falls back to the built-in offline heuristic moment detector without interruption. |
| Video does not seek smoothly | Missing faststart flags | All exports use `-movflags +faststart` with HTTP 206 Partial Content streaming for instant scrubbing. |

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ for creators and video editors. Star ⭐ the repository if you found it useful!
</div>
