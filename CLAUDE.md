# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Video-to-image CLI tool that extracts frames from video files using OpenCV. Supports three extraction modes: interval-based (every N seconds), count-based (N evenly distributed frames), and timestamp-based (single frame at specific time).

## Development Commands

```bash
# Install/update dependencies (uses uv)
uv sync

# Run the CLI
uv run python run.py video.mp4 --interval 1

# Run with specific extraction modes
uv run python run.py video.mp4 --count 10
uv run python run.py video.mp4 --timestamp "01:30"
uv run python run.py video.mp4 --info
```

Alternative with pip (not recommended):
```bash
pip install -r requirements.txt
python run.py video.mp4 --interval 1
```

## Architecture

```
run.py                  # CLI entry point: argparse setup, progress bars, error handling
src/extractor.py        # Core logic: VideoExtractor class with three extraction strategies
```

**Key separation:** `run.py` handles CLI concerns (argparse, tqdm progress, user output) while `VideoExtractor` handles pure video processing (OpenCV operations, file I/O). This makes `VideoExtractor` testable and reusable as a library.

### VideoExtractor Class

Located in `src/extractor.py`. Key methods:

- `extract_by_interval(interval_seconds)` - Extract frames every N seconds
- `extract_by_count(count)` - Extract N evenly distributed frames across video duration
- `extract_at_timestamp(timestamp)` - Extract single frame at HH:MM:SS or MM:SS or seconds
- `get_video_info()` - Return dict with width, height, fps, frame_count, duration

The class manages its own VideoCapture lifecycle (`_open_video()` and `cap.release()`). All extraction methods validate the video file exists before processing.

### CLI Flow (run.py)

1. `setup_parser()` - Configures argparse with mutually exclusive extraction modes
2. `parse_timestamp()` - Converts "HH:MM:SS", "MM:SS", or float to seconds
3. `process_video()` - Orchestrates extraction per video, handles errors, shows progress
4. `main()` - Validates inputs, creates output dir, aggregates results

For batch processing (multiple videos), each video gets its own subdirectory to prevent frame filename collisions.

## Project Structure

- `pyproject.toml` - UV project config, dependencies defined here (not requirements.txt)
- `requirements.txt` - Kept for pip compatibility, should match pyproject.toml
- `.venv/` - UV-managed virtual environment (gitignored)
- `uv.lock` - Auto-generated lock file for reproducible builds (gitignored)
