from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List
import cv2
from google import genai
from src.utils.collage import build_collage


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict:
    m = _JSON_RE.search(text or "")
    if not m:
        raise ValueError("No JSON found in model response.")
    return json.loads(m.group(0))


def extract_frames_at_timestamps(video_path: Path, timestamps_s: List[float], out_dir: Path) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0.0

    saved: List[Path] = []
    for i, t in enumerate(timestamps_s, start=1):
        t = float(t)
        if duration > 0:
            t = max(0.0, min(t, max(0.0, duration - 0.05)))

        frame_idx = int(round(t * fps)) if fps > 0 else 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        out_path = out_dir / f"hit_{i:03d}_{t:.2f}s.jpg"
        cv2.imwrite(str(out_path), frame)
        saved.append(out_path)

    cap.release()
    return saved


def run_video_mode(video_path: Path) -> None:
    print("Using a video model. What would you like me to find in the video?")
    user_query = input().strip()
    if not user_query:
        return

    client = genai.Client()  

    # Upload the video once
    uploaded = client.files.upload(file=str(video_path))

    prompt = f"""
You are a video-understanding assistant.
Find moments in the video that match the user's request.

User request: {user_query}

Return ONLY valid JSON in this exact schema:
{{
  "timestamps_seconds": [number, number, ...],
  "notes": "short explanation"
}}

Rules:
- Provide 4 to 12 timestamps.
- Each timestamp should be a moment that best matches the request.
- Use seconds from start of video (decimals allowed).
- Do not include any text outside the JSON.
""".strip()

    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[uploaded, prompt],
    )

    data = _extract_json(resp.text or "")
    timestamps = data.get("timestamps_seconds", [])
    if not isinstance(timestamps, list) or not timestamps:
        print("No timestamps returned from the model.")
        return

    # Extract frames for those timestamps
    hits_dir = Path("data") / "video_hits"
    frames = extract_frames_at_timestamps(video_path, [float(x) for x in timestamps], hits_dir)
    if not frames:
        print("Failed to extract frames from timestamps.")
        return

    # Build collage.png (required output name)
    out_path = Path("collage.png")
    build_collage(frames, out_path)
    print(f"Saved collage to: {out_path.resolve()}")
    print(f"Frames saved to: {hits_dir.resolve()}")
