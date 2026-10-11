import os
import subprocess
import uuid
from pathlib import Path
from config import OUTPUT_DIR, TEMP_DIR
from smart_cropper import build_layout_filter
from subtitle_generator import generate_ass_subtitles

def escape_ffmpeg_path(path: str) -> str:
    """Escapes file path for FFmpeg filter arguments on Windows."""
    p = path.replace("\\", "/")
    p = p.replace(":", r"\:")
    return p

def cut_clip(
    video_path: str,
    start_time: float,
    end_time: float,
    clip_title: str,
    layout_mode: str = "9:16_blurred",
    add_subtitles: bool = True,
    segments: list = None,
    progress_callback = None
) -> str:
    """
    Cuts video segment, applies chosen layout framework,
    burns dynamic animated subtitles, and exports final high-res MP4 clip.
    """
    clip_id = str(uuid.uuid4())[:6]
    clean_title = "".join(c for c in clip_title if c.isalnum() or c in (" ", "_", "-")).strip()[:40]
    output_filename = f"clip_{clean_title}_{clip_id}.mp4".replace(" ", "_")
    output_path = str(OUTPUT_DIR / output_filename)
    duration = end_time - start_time

    if progress_callback:
        progress_callback(f"Rendering '{clip_title}' ({duration:.1f}s)...")

    # Generate subtitles if requested
    ass_path = None
    if add_subtitles and segments:
        ass_path = str(TEMP_DIR / f"sub_{clip_id}.ass")
        generate_ass_subtitles(segments, start_time, end_time, ass_path)

    # Build filtergraph based on layout mode
    filter_expr, is_complex, out_w, out_h = build_layout_filter(
        layout_mode=layout_mode,
        video_path=video_path,
        start_time=start_time,
        duration=duration
    )

    if is_complex:
        if ass_path and os.path.exists(ass_path):
            escaped_ass = escape_ffmpeg_path(ass_path)
            filter_graph = f"{filter_expr}[v_layout];[v_layout]ass='{escaped_ass}'[outv]"
        else:
            filter_graph = f"{filter_expr}[outv]"

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_time:.2f}",
            "-to", f"{end_time:.2f}",
            "-i", video_path,
            "-filter_complex", filter_graph,
            "-map", "[outv]",
            "-map", "0:a?",
            "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]
    else:
        vf_parts = [filter_expr]
        if ass_path and os.path.exists(ass_path):
            escaped_ass = escape_ffmpeg_path(ass_path)
            vf_parts.append(f"ass='{escaped_ass}'")
        vf_str = ",".join(vf_parts)

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_time:.2f}",
            "-to", f"{end_time:.2f}",
            "-i", video_path,
            "-vf", vf_str,
            "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]

    # Try GPU NVENC first; fallback to CPU libx264 if needed
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"NVENC failed, falling back to CPU encoder: {e.stderr[:200]}")
        cmd_cpu = [arg.replace("h264_nvenc", "libx264") for arg in cmd]
        if "-preset" in cmd_cpu:
            idx = cmd_cpu.index("-preset")
            cmd_cpu[idx+1] = "fast"
        if "-cq" in cmd_cpu:
            idx = cmd_cpu.index("-cq")
            cmd_cpu[idx] = "-crf"
        subprocess.run(cmd_cpu, capture_output=True, text=True, check=True)

    return output_path
