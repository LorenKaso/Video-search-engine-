from __future__ import annotations

from src.config import VIDEO_PATH, YOUTUBE_QUERY
from src.pipeline.download import download_youtube_search


def main() -> None:
    print("Step 1: Downloading video from YouTube...")
    video_file = download_youtube_search(
        query=YOUTUBE_QUERY,
        out_path=VIDEO_PATH,
        max_duration_sec=None,  
    )
    print(f"Downloaded: {video_file}")


if __name__ == "__main__":
    main()
