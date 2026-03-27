#!/usr/bin/env python3
"""MCP Server for video-to-image frame extraction."""

import json
import sys
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent))
from src.extractor import VideoExtractor

mcp = FastMCP("video-to-image")

OUTPUT_BASE = Path(tempfile.gettempdir()) / "video-to-image-mcp"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)


@mcp.tool()
def video_info(video_path: str) -> str:
    """Get video metadata (resolution, fps, duration, frame count).

    Args:
        video_path: Absolute path to the video file.
    """
    extractor = VideoExtractor(video_path=video_path, output_dir=OUTPUT_BASE)
    info = extractor.get_video_info()
    return json.dumps(info, indent=2)


@mcp.tool()
def extract_frames_by_count(video_path: str, count: int = 10, output_format: str = "jpg") -> str:
    """Extract N evenly-distributed frames from a video. Good for getting an overview of a video's content.

    Args:
        video_path: Absolute path to the video file.
        count: Number of frames to extract (default: 10).
        output_format: Image format - "jpg" or "png" (default: "jpg").
    """
    video_name = Path(video_path).stem
    output_dir = OUTPUT_BASE / video_name / "by_count"
    output_dir.mkdir(parents=True, exist_ok=True)

    for f in output_dir.iterdir():
        f.unlink()

    extractor = VideoExtractor(
        video_path=video_path,
        output_dir=output_dir,
        output_format=output_format,
    )
    frames = extractor.extract_by_count(count)
    paths = [str(p) for p in frames]
    return json.dumps({"extracted": len(paths), "output_dir": str(output_dir), "frames": paths})


@mcp.tool()
def extract_frames_by_interval(video_path: str, interval_seconds: float = 2.0, output_format: str = "jpg") -> str:
    """Extract frames at a regular interval from a video.

    Args:
        video_path: Absolute path to the video file.
        interval_seconds: Extract one frame every N seconds (default: 2.0).
        output_format: Image format - "jpg" or "png" (default: "jpg").
    """
    video_name = Path(video_path).stem
    output_dir = OUTPUT_BASE / video_name / "by_interval"
    output_dir.mkdir(parents=True, exist_ok=True)

    for f in output_dir.iterdir():
        f.unlink()

    extractor = VideoExtractor(
        video_path=video_path,
        output_dir=output_dir,
        output_format=output_format,
    )
    frames = extractor.extract_by_interval(interval_seconds)
    paths = [str(p) for p in frames]
    return json.dumps({"extracted": len(paths), "output_dir": str(output_dir), "frames": paths})


@mcp.tool()
def extract_frame_at_timestamp(video_path: str, timestamp: str, output_format: str = "jpg") -> str:
    """Extract a single frame at a specific timestamp.

    Args:
        video_path: Absolute path to the video file.
        timestamp: Time position - formats: "HH:MM:SS", "MM:SS", or seconds as string (e.g. "5.5").
        output_format: Image format - "jpg" or "png" (default: "jpg").
    """
    video_name = Path(video_path).stem
    output_dir = OUTPUT_BASE / video_name / "at_timestamp"
    output_dir.mkdir(parents=True, exist_ok=True)

    extractor = VideoExtractor(
        video_path=video_path,
        output_dir=output_dir,
        output_format=output_format,
    )
    path = extractor.extract_at_timestamp(timestamp)
    return json.dumps({"frame": str(path)})


if __name__ == "__main__":
    mcp.run(transport="stdio")