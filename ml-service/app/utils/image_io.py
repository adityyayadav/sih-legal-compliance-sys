import asyncio
import inspect
from io import BytesIO
from pathlib import Path
from typing import Union
import cv2
import numpy as np
from PIL import Image
from fastapi import UploadFile, HTTPException
from starlette.datastructures import UploadFile as StarletteUploadFile

async def load_image(image_input: Union[UploadFile, StarletteUploadFile, bytes, str, Path, np.ndarray, Image.Image]) -> np.ndarray:
    """
    Converts various input formats (FastAPI/Starlette UploadFile, bytes, file path, PIL Image, np.ndarray)
    into a standardized uint8 BGR/RGB numpy array.
    """
    if isinstance(image_input, np.ndarray):
        return image_input

    if isinstance(image_input, (UploadFile, StarletteUploadFile)) or hasattr(image_input, "read"):
        read_fn = getattr(image_input, "read", None)
        if callable(read_fn):
            if inspect.iscoroutinefunction(read_fn) or asyncio.iscoroutinefunction(read_fn):
                contents = await read_fn()
            else:
                contents = read_fn()
                if asyncio.iscoroutine(contents):
                    contents = await contents
            
            seek_fn = getattr(image_input, "seek", None)
            if callable(seek_fn):
                if inspect.iscoroutinefunction(seek_fn) or asyncio.iscoroutinefunction(seek_fn):
                    await seek_fn(0)
                else:
                    seek_res = seek_fn(0)
                    if asyncio.iscoroutine(seek_res):
                        await seek_res
            return _bytes_to_numpy(contents)

    if isinstance(image_input, (bytes, bytearray)):
        return _bytes_to_numpy(image_input)

    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {p}")
        img = cv2.imread(str(p))
        if img is None:
            raise ValueError(f"Could not decode image at {p}")
        return img

    if isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))

    raise TypeError(f"Unsupported image input type: {type(image_input)}")


def load_image_sync(image_input: Union[UploadFile, StarletteUploadFile, bytes, str, Path, np.ndarray, Image.Image]) -> np.ndarray:
    """Synchronous version for test scripts and batch loaders."""
    if isinstance(image_input, np.ndarray):
        return image_input
    if isinstance(image_input, (UploadFile, StarletteUploadFile)) or hasattr(image_input, "file"):
        file_obj = getattr(image_input, "file", image_input)
        if hasattr(file_obj, "read"):
            contents = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            return _bytes_to_numpy(contents)
    if isinstance(image_input, (bytes, bytearray)):
        return _bytes_to_numpy(image_input)
    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {p}")
        img = cv2.imread(str(p))
        if img is None:
            raise ValueError(f"Could not decode image at {p}")
        return img
    if isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))
    raise TypeError(f"Unsupported image input type: {type(image_input)}")


def _bytes_to_numpy(image_bytes: bytes) -> np.ndarray:
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            # Fallback with PIL in case OpenCV fails on specific encoding
            pil_img = Image.open(BytesIO(image_bytes))
            img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"INVALID_IMAGE: {str(e)}")
