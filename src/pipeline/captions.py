from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from PIL import Image


def load_moondream_model():
    """
    Load Moondream2 locally (CPU-safe).
    Returns an object that supports: model.caption(PIL_image).
    """
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    model_id = "vikhyatk/moondream2"

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        trust_remote_code=True,
    )

    # IMPORTANT:
    # Load model fully on CPU (no device_map="auto", no meta tensors)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype=torch.float32,
        device_map=None,
        low_cpu_mem_usage=False,
    )

    model = model.to("cpu")
    model.eval()

    class MoonDreamWrapper:
        def __init__(self, model, tokenizer):
            self.model = model
            self.tokenizer = tokenizer

            # Moondream2 exposes these methods via remote code
            if not hasattr(model, "encode_image") or not hasattr(model, "answer_question"):
                raise RuntimeError(
                    "Moondream2 model does not expose encode_image / answer_question"
                )

        def caption(self, image: Image.Image) -> str:
            img = image.convert("RGB")
            image_embeds = self.model.encode_image(img)
            question = "Describe this image in one short sentence."
            answer = self.model.answer_question(
                image_embeds,
                question,
                self.tokenizer,
            )
            return answer.strip()

    return MoonDreamWrapper(model, tokenizer)


def caption_scenes(
    scenes_dir: Path,
    out_json: Path,
) -> Dict[str, str]:
    """
    Create captions for each scene image and save scene_captions.json.
    Returns mapping: scene_filename -> caption
    """
    out_json.parent.mkdir(parents=True, exist_ok=True)

    # Resume support: load existing captions if file exists
    captions: Dict[str, str] = {}
    if out_json.exists():
        captions = json.loads(out_json.read_text(encoding="utf-8"))

    images = sorted(scenes_dir.glob("*.jpg"))
    if not images:
        raise FileNotFoundError(f"No scene images found in {scenes_dir}")

    model = load_moondream_model()

    total = len(images)
    for i, img_path in enumerate(images, start=1):

        # Skip already-captioned images
        if img_path.name in captions:
            continue

        with Image.open(img_path) as im:
            img = im.convert("RGB")

        try:
            caption = model.caption(img)
        except Exception as e:
            print(f"[error] {img_path.name}: {type(e).__name__}: {e}")
            continue

        captions[img_path.name] = caption
        print(f"[{i}/{total}] {img_path.name}: {caption}")

        # Save progress continuously
        out_json.write_text(
            json.dumps(captions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return captions
