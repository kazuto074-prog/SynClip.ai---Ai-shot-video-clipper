import os
import sys
import time

# Robust CUDA cuBLAS & cuDNN DLL loader for Windows
try:
    import torch
    torch_lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    if os.path.exists(torch_lib):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_lib)
        if torch_lib not in os.environ.get("PATH", ""):
            os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")
except Exception as e:
    print(f"Torch DLL loader warning: {e}")

from faster_whisper import WhisperModel
from config import DEFAULT_WHISPER_MODEL, DEVICE, COMPUTE_TYPE

class AudioTranscriber:
    def __init__(self, model_size: str = DEFAULT_WHISPER_MODEL, device: str = DEVICE, compute_type: str = COMPUTE_TYPE):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def load_model(self):
        if self.model is None:
            # First attempt: GPU CUDA
            try:
                print(f"Loading Faster-Whisper '{self.model_size}' on NVIDIA GPU ({self.device})...")
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            except Exception as e:
                print(f"CUDA initialization failed ({e}), falling back to CPU...")
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str, progress_callback=None) -> dict:
        """
        Transcribes audio file and returns structured segments and word timestamps.
        """
        if progress_callback:
            progress_callback(f"Loading Whisper ({self.model_size})...")
        self.load_model()

        if progress_callback:
            progress_callback("Transcribing speech with word-level timestamps...")

        start_time = time.time()
        segments_generator, info = self.model.transcribe(
            audio_path,
            beam_size=1,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segments = []
        full_text_list = []

        for seg in segments_generator:
            words = []
            if seg.words:
                for w in seg.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 2)
                    })

            seg_dict = {
                "id": seg.id,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "words": words
            }
            segments.append(seg_dict)
            full_text_list.append(seg.text.strip())

        duration = round(time.time() - start_time, 2)
        if progress_callback:
            progress_callback(f"Transcribed in {duration}s ({info.language.upper()}, {info.language_probability*100:.0f}% confidence)")

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "duration": round(info.duration, 2),
            "text": " ".join(full_text_list),
            "segments": segments
        }
