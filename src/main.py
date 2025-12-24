from __future__ import annotations
from src.config import SCENES_DIR, VIDEO_PATH, YOUTUBE_QUERY, CAPTIONS_JSON
from src.pipeline.download import download_youtube_search
from src.pipeline.scenes import detect_and_save_scenes
from src.pipeline.captions import caption_scenes
import json

def main() -> None:
    # Step 1: download (skip if exists)
    if not VIDEO_PATH.exists():
        print("Step 1: Downloading video from YouTube...")
        video_file = download_youtube_search(
            query=YOUTUBE_QUERY,
            out_path=VIDEO_PATH,
            max_duration_sec=None,
        )
        print(f"Downloaded: {video_file}")
    else:
        print(f"Step 1: Video already exists. Skipping download: {VIDEO_PATH}")

    # Step 2: scene detect (skip if exists)
    existing = list(SCENES_DIR.glob("*.jpg"))
    if not existing:
        print("Step 2: Detecting scenes and saving images...")
        scenes = detect_and_save_scenes(
            video_path=VIDEO_PATH,
            scenes_dir=SCENES_DIR,
            threshold=27.0,
            min_scene_len_frames=12,
        )
        print(f"Detected {len(scenes)} scenes")
    else:
        print(f"Step 2: Scenes already exist: {len(existing)}")

    # Step 3: Caption each scene image using Moondream
    total_images = len(list(SCENES_DIR.glob("*.jpg")))
    existing_captions = {}
    if CAPTIONS_JSON.exists():
        try:
            existing_captions = json.loads(CAPTIONS_JSON.read_text(encoding="utf-8"))
        except Exception:
            existing_captions = {}

    if CAPTIONS_JSON.exists() and len(existing_captions) >= total_images:
        print(f"Step 3: Captions JSON already complete ({len(existing_captions)}/{total_images}). Skipping: {CAPTIONS_JSON}")
    else:
        print(f"Step 3: Generating captions with Moondream... ({len(existing_captions)}/{total_images} already exist)")
        caption_scenes(SCENES_DIR, CAPTIONS_JSON)
        print(f"Saved captions to: {CAPTIONS_JSON}")
if __name__ == "__main__":
    main()
