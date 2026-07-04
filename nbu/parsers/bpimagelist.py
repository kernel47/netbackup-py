from __future__ import annotations

from nbu.models.images import Image, image_from_mapping
from nbu.parsers.common import split_key_value_lines


def parse(text: str) -> list[Image]:
    images: list[Image] = []
    for record in split_key_value_lines(text):
        image_id = record.get("image_id") or record.get("backup_id") or record.get("id")
        if not image_id:
            continue
        images.append(image_from_mapping(record | {"imageId": image_id}, source="ssh"))
    return images

