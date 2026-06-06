# Yuyu-Mind Screen Plugin

English | [中文](#中文)

The Screen Plugin lets Yuyu-Mind capture the current desktop screen and optionally summarize it with an OpenAI-compatible vision model. It is designed as an external plugin that can be copied into the Yuyu-Mind plugin directory without coupling the core app to a specific screen-reading implementation.

## Features

- Captures the current desktop screen with `mss`, with Pillow `ImageGrab` as a fallback.
- Resizes screenshots before sending them to the vision model.
- Supports OpenAI-compatible chat completions vision endpoints, including Gemini's OpenAI-compatible endpoint.
- Supports optional HTTP/HTTPS proxy configuration.
- Can return a concise screen summary, metadata, and optionally base64 PNG image data.
- Declares chat and proactive context triggers in `plugin.json`, so Yuyu-Mind can decide when to call the plugin.

## Repository Layout

```text
Screen-Plugin/
  plugin.json          Plugin manifest and protocol metadata
  config.example.json  Safe example config without secrets
  main.py              Plugin runtime implementation
  __init__.py          Python package marker
  requirements.txt     Optional Python dependencies
```

## Install

Install optional screenshot dependencies in the same Python environment used by the Yuyu-Mind Agent:

```powershell
python -m pip install -r requirements.txt
```

Copy this plugin folder into Yuyu-Mind:

```text
Yuyu-Mind/
  agent/
    plugins/
      screen/
        plugin.json
        config.json
        main.py
        __init__.py
```

Then create your local config:

```powershell
Copy-Item config.example.json config.json
```

Do not commit `config.json` if it contains API keys.

## Configure

Example `config.json`:

```json
{
  "captureMaxWidth": 1280,
  "returnImage": false,
  "vision": {
    "apiKey": "",
    "baseUrl": "https://api.openai.com/v1",
    "model": "",
    "proxy": "",
    "maxTokens": 420,
    "timeoutSeconds": 45
  }
}
```

The plugin also supports environment variables. New `YUYU_*` names are preferred, while old `MOCHI_*` names remain compatible:

```env
YUYU_SCREEN_VISION_API_KEY=your_api_key
YUYU_SCREEN_VISION_BASE_URL=https://api.openai.com/v1
YUYU_SCREEN_VISION_MODEL=gpt-4.1-mini
YUYU_SCREEN_CAPTURE_MAX_WIDTH=1280
YUYU_SCREEN_RETURN_IMAGE=false
YUYU_SCREEN_VISION_PROXY=
```

For Gemini through its OpenAI-compatible endpoint:

```env
YUYU_SCREEN_VISION_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
YUYU_SCREEN_VISION_MODEL=gemini-2.5-flash-lite
```

If your network requires a local proxy:

```env
YUYU_SCREEN_VISION_PROXY=http://127.0.0.1:7897
```

## API

When installed in Yuyu-Mind, the plugin can be called through the Agent plugin endpoint:

```http
POST http://127.0.0.1:8765/plugins/screen/observe
Content-Type: application/json

{
  "prompt": "Describe the visible screen.",
  "includeImage": false,
  "maxWidth": 1280
}
```

Typical response:

```json
{
  "ok": true,
  "plugin": "screen",
  "action": "observe",
  "summary": "A code editor is open with a terminal panel at the bottom.",
  "metadata": {
    "backend": "mss",
    "width": 1280,
    "height": 720
  },
  "vision": {
    "enabled": true,
    "provider": "openai-compatible-vision",
    "model": "gpt-4.1-mini"
  }
}
```

## Plugin Manifest

This plugin uses:

```json
{
  "schemaVersion": "yuyu.plugin.v1",
  "name": "screen"
}
```

Yuyu-Mind also accepts the legacy `mochi.plugin.v1` schema for older plugins.

## Security Notes

- The plugin captures the visible desktop screen. Use it only when you understand what may be shown on screen.
- API keys belong in `config.json` or local environment variables, never in Git.
- `config.example.json` intentionally contains no secrets.
- If `returnImage` is enabled, plugin responses may include screenshot image data.

---

## 中文

读屏插件可以让 Yuyu-Mind 捕获当前桌面画面，并可选地交给兼容 OpenAI Chat Completions 格式的视觉模型进行总结。它作为外部插件维护，避免把具体读屏实现和 Yuyu-Mind 主程序强耦合。

## 功能

- 使用 `mss` 捕获当前桌面屏幕，失败时回退到 Pillow `ImageGrab`。
- 发送给视觉模型前自动缩放截图。
- 支持 OpenAI-compatible 视觉接口，包括 Gemini 的 OpenAI-compatible endpoint。
- 支持 HTTP/HTTPS 代理。
- 返回简洁的屏幕总结、截图元数据，并可选返回 base64 PNG 图片。
- 在 `plugin.json` 中声明聊天触发词和主动吐槽触发概率，由 Yuyu-Mind 决定何时调用。

## 仓库结构

```text
Screen-Plugin/
  plugin.json          插件协议与元数据
  config.example.json  不含密钥的配置示例
  main.py              插件运行时代码
  __init__.py          Python 包标记
  requirements.txt     可选 Python 依赖
```

## 安装

在 Yuyu-Mind Agent 使用的 Python 环境中安装依赖：

```powershell
python -m pip install -r requirements.txt
```

把插件目录复制到 Yuyu-Mind：

```text
Yuyu-Mind/
  agent/
    plugins/
      screen/
        plugin.json
        config.json
        main.py
        __init__.py
```

然后创建本地配置：

```powershell
Copy-Item config.example.json config.json
```

如果 `config.json` 中包含 API Key，不要提交它。

## 配置

`config.json` 示例：

```json
{
  "captureMaxWidth": 1280,
  "returnImage": false,
  "vision": {
    "apiKey": "",
    "baseUrl": "https://api.openai.com/v1",
    "model": "",
    "proxy": "",
    "maxTokens": 420,
    "timeoutSeconds": 45
  }
}
```

也可以使用环境变量。推荐使用新的 `YUYU_*`，旧的 `MOCHI_*` 仍然兼容：

```env
YUYU_SCREEN_VISION_API_KEY=your_api_key
YUYU_SCREEN_VISION_BASE_URL=https://api.openai.com/v1
YUYU_SCREEN_VISION_MODEL=gpt-4.1-mini
YUYU_SCREEN_CAPTURE_MAX_WIDTH=1280
YUYU_SCREEN_RETURN_IMAGE=false
YUYU_SCREEN_VISION_PROXY=
```

Gemini OpenAI-compatible endpoint 示例：

```env
YUYU_SCREEN_VISION_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
YUYU_SCREEN_VISION_MODEL=gemini-2.5-flash-lite
```

如果需要本地代理：

```env
YUYU_SCREEN_VISION_PROXY=http://127.0.0.1:7897
```

## 调用方式

安装到 Yuyu-Mind 后，可以通过 Agent 插件接口调用：

```http
POST http://127.0.0.1:8765/plugins/screen/observe
Content-Type: application/json

{
  "prompt": "Describe the visible screen.",
  "includeImage": false,
  "maxWidth": 1280
}
```

## 安全提示

- 插件会捕获当前可见桌面，请确认屏幕上没有不希望发送给视觉模型的敏感内容。
- API Key 只应放在本地 `config.json` 或环境变量里。
- `config.example.json` 不包含任何密钥。
- 开启 `returnImage` 后，插件返回值可能包含截图图片数据。
