from __future__ import annotations
from src.config import SCENES_DIR, VIDEO_PATH, YOUTUBE_QUERY, CAPTIONS_JSON
from src.pipeline.download import download_youtube_search
from src.pipeline.scenes import detect_and_save_scenes
from src.pipeline.captions import caption_scenes
from rapidfuzz import fuzz
import re
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

    # Step 4: Search the video using a word (EXACT 'in' then FUZZY RapidFuzz)
    captions = json.loads(CAPTIONS_JSON.read_text(encoding="utf-8"))

    _WORD_RE = re.compile(r"[a-z0-9]+")

    def best_token_score(query: str, caption: str) -> float:
        """
        Compute best fuzzy score between query and ANY token in caption.
        Uses WRatio (good for typos like mrio->mario).
        Filters tokens by similar length to reduce noise.
        """
        q = query.lower().strip()
        tokens = [t for t in _WORD_RE.findall(caption.lower()) if len(t) >= 4]
        if not tokens:
            return 0.0

        qlen = len(q)
        # keep tokens with length close to query (±2 chars) to reduce false positives
        cand = [t for t in tokens if abs(len(t) - qlen) <= 2]
        if not cand:
            cand = tokens

        return float(max(fuzz.WRatio(q, tok) for tok in cand))

    print("Search the video using a word:")
    while True:
        word = input().strip()
        if not word:
            break

        word_l = word.lower()

        # 1) EXACT search using 'in'
        exact_matches = [
            scene_file
            for scene_file, caption in captions.items()
            if word_l in caption.lower()
        ]

        if exact_matches:
            print(f"EXACT ('in') -> Found {len(exact_matches)} matching scenes.")
            for s in exact_matches[:10]:
                print(f"- {s}")
            continue

        # 2) FUZZY fallback using RapidFuzz (token-based)
        scored = []
        if len(word_l) < 4:
            print("FUZZY skipped: query too short. Try a longer word.")
            continue
        for scene_file, caption in captions.items():
            score = best_token_score(word_l, caption)
            scored.append((score, scene_file))

        scored.sort(reverse=True)

        print("FUZZY (RapidFuzz tokens) -> Top candidates:")
        for score, scene_file in scored[:10]:
            print(f"- {scene_file} (score={score:.1f})")

        threshold = 85
        top_k = 12
        matches = [scene_file for score, scene_file in scored if score >= threshold][:top_k]

        print(f"FUZZY (RapidFuzz tokens) -> Found {len(matches)} matching scenes (top {top_k}).")
        for s in matches:
            print(f"- {s}: {captions[s]}")


if __name__ == "__main__":
    main()
