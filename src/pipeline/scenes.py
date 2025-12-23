from __future__ import annotations
from pathlib import Path
from typing import List, Tuple

from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.scene_manager import save_images


def detect_and_save_scenes(
    video_path: Path,
    scenes_dir: Path,
    threshold: float,
    min_scene_len_frames: int,
) -> List[Tuple[int, int]]:
    scenes_dir.mkdir(parents=True, exist_ok=True)

    video = open_video(str(video_path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len_frames))
    manager.detect_scenes(video)

    scene_list = manager.get_scene_list()

    # Save 1 representative image per scene
    save_images(
        scene_list=scene_list,
        video=video,
        output_dir=str(scenes_dir),
        image_name_template="scene_$SCENE_NUMBER",
        num_images=1,
        show_progress=True,
    )

    # Return (start_frame, end_frame) for debugging
    return [(s.get_frames(), e.get_frames()) for s, e in scene_list]
