from __future__ import annotations

import base64
import io
import json
import os
import urllib.error
import urllib.request
from typing import Any


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = _env(name)
        if value:
            return value
    return default


def _config(payload: dict[str, Any]) -> dict[str, Any]:
    config = payload.get("config", {})
    return config if isinstance(config, dict) else {}


def _nested_config(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key, {})
    return value if isinstance(value, dict) else {}


def _config_string(config: dict[str, Any], key: str, env_name: str, default: str = "") -> str:
    value = str(config.get(key, "")).strip()
    return value or _env(env_name, default)


def _config_int(config: dict[str, Any], key: str, env_name: str, default: int) -> int:
    value = config.get(key)
    if value not in (None, ""):
        return int(value)
    return int(_env(env_name, str(default)) or str(default))


def _config_bool(config: dict[str, Any], key: str, env_name: str, default: bool) -> bool:
    value = config.get(key)
    if isinstance(value, bool):
        return value
    if value not in (None, ""):
        return str(value).strip().lower() == "true"
    env_value = _env(env_name, str(default).lower()).lower()
    return env_value == "true"


def _capture_png(max_width: int = 1280) -> tuple[bytes, dict[str, Any]]:
    image = None
    backend = ""
    try:
        import mss
        from PIL import Image

        with mss.mss() as screen:
            monitor = screen.monitors[0]
            shot = screen.grab(monitor)
            image = Image.frombytes("RGB", shot.size, shot.rgb)
            backend = "mss"
    except Exception as first_error:
        try:
            from PIL import ImageGrab

            image = ImageGrab.grab(all_screens=True)
            backend = "pillow"
        except Exception as second_error:
            raise RuntimeError(
                "screen capture failed. Install optional dependencies with "
                "`pip install mss pillow`, then grant screen recording permission if your OS asks for it. "
                f"mss error: {first_error}; pillow error: {second_error}"
            ) from second_error

    if image is None:
        raise RuntimeError("screen capture returned no image")

    original_width, original_height = image.size
    if max_width > 0 and original_width > max_width:
        ratio = max_width / original_width
        image = image.resize((max_width, max(1, int(original_height * ratio))))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue(), {
        "backend": backend,
        "originalWidth": original_width,
        "originalHeight": original_height,
        "width": image.size[0],
        "height": image.size[1],
    }


def _vision_config(config: dict[str, Any]) -> tuple[str, str, str, str, int, int]:
    vision = _nested_config(config, "vision")
    api_key = (
        str(vision.get("apiKey", "")).strip()
        or _env_first("YUYU_SCREEN_VISION_API_KEY", "MOCHI_SCREEN_VISION_API_KEY", "OPENAI_API_KEY")
    )
    base_url = (
        str(vision.get("baseUrl", "")).strip()
        or _env_first("YUYU_SCREEN_VISION_BASE_URL", "MOCHI_SCREEN_VISION_BASE_URL", "OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    ).rstrip("/")
    model = str(vision.get("model", "")).strip() or _env_first("YUYU_SCREEN_VISION_MODEL", "MOCHI_SCREEN_VISION_MODEL")
    proxy = (
        str(vision.get("proxy", "")).strip()
        or _env_first("YUYU_SCREEN_VISION_PROXY", "MOCHI_SCREEN_VISION_PROXY", "HTTPS_PROXY", "HTTP_PROXY")
    )
    max_tokens = int(
        str(vision.get("maxTokens", "")).strip()
        or _env_first("YUYU_SCREEN_VISION_MAX_TOKENS", "MOCHI_SCREEN_VISION_MAX_TOKENS", default="420")
    )
    timeout_seconds = int(
        str(vision.get("timeoutSeconds", "")).strip()
        or _env_first("YUYU_SCREEN_VISION_TIMEOUT", "MOCHI_SCREEN_VISION_TIMEOUT", default="45")
    )
    return api_key, base_url, model, proxy, max_tokens, timeout_seconds


def _summarize_with_vision(image_png: bytes, prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    api_key, base_url, model, proxy, max_tokens, timeout_seconds = _vision_config(config)
    if not api_key or not model:
        return {
            "enabled": False,
            "summary": (
                "Screen image was captured, but no vision model is configured. "
                "Set agent/plugins/screen/config.json vision.model and vision.apiKey, "
                "or use YUYU_SCREEN_VISION_MODEL plus YUYU_SCREEN_VISION_API_KEY or OPENAI_API_KEY."
            ),
        }

    image_url = "data:image/png;base64," + base64.b64encode(image_png).decode("ascii")
    user_prompt = prompt.strip() or (
        "Describe what is visible on the user's screen. Focus on windows, readable text, errors, "
        "current task, and anything the desktop companion should react to. Be concise."
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a desktop screen observation plugin. Summarize only visible screen content.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        opener = urllib.request.build_opener()
        if proxy:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        with opener.open(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"vision API error {error.code}: {detail}") from error

    summary = str(data["choices"][0]["message"]["content"]).strip()
    return {"enabled": True, "provider": "openai-compatible-vision", "model": model, "summary": summary}


def observe(payload: dict[str, Any]) -> dict[str, Any]:
    config = _config(payload)
    prompt = str(payload.get("prompt", "")).strip()
    max_width = int(
        payload.get("maxWidth")
        or str(config.get("captureMaxWidth", "")).strip()
        or _env_first("YUYU_SCREEN_CAPTURE_MAX_WIDTH", "MOCHI_SCREEN_CAPTURE_MAX_WIDTH", default="1280")
    )
    image_png, metadata = _capture_png(max_width=max_width)
    vision = _summarize_with_vision(image_png, prompt, config)
    include_image = bool(payload.get("includeImage", False))
    if not include_image:
        include_image = _config_bool(config, "returnImage", "YUYU_SCREEN_RETURN_IMAGE", False)
        if not include_image:
            include_image = _env("MOCHI_SCREEN_RETURN_IMAGE").lower() == "true"
    result: dict[str, Any] = {
        "ok": True,
        "plugin": "screen",
        "action": "observe",
        "metadata": metadata,
        "vision": vision,
        "summary": vision.get("summary", ""),
    }
    if include_image:
        result["imageBase64"] = base64.b64encode(image_png).decode("ascii")
        result["contentType"] = "image/png"
    return result


ACTIONS = {"observe": observe}
