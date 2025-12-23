from __future__ import annotations

from pathlib import Path
from typing import Optional

from yt_dlp import YoutubeDL


def download_youtube_search(
    query: str,
    out_path: Path,
    max_duration_sec: Optional[int] = None,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        # Use explicit ytsearch:
        "quiet": False,       
        "no_warnings": False,
        "noplaylist": True,
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "outtmpl": str(out_path),
    }

    if max_duration_sec is not None:
        ydl_opts["match_filter"] = lambda info, *args, **kwargs: (
            None
            if (info.get("duration") is not None and info["duration"] <= max_duration_sec)
            else f"Skipping (duration > {max_duration_sec}s)"
        )

    search_term = f"ytsearch1:{query}"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_term, download=False)

        if not info:
            raise RuntimeError(
                "yt-dlp returned no info. The YouTube search likely failed (network/captcha/block)."
            )

        # ytsearch returns a dict with 'entries'
        entries = info.get("entries") or []
        entries = [e for e in entries if e]
        if not entries:
            raise RuntimeError("No YouTube results found for the query.")

        first = entries[0]
        ydl.download([first["webpage_url"]])

    # file may not be exactly .mp4 if yt-dlp decides otherwise; detect it
    if out_path.exists():
        return out_path

    candidates = list(out_path.parent.glob(out_path.stem + ".*"))
    if candidates:
        return candidates[0]

    raise FileNotFoundError(f"Download completed but file not found near {out_path}")
