import json
import subprocess
import shutil
from pathlib import Path
from typing import Literal


class VideoExtractor:
    """Extract frames from video files using ffmpeg for fast seeking."""

    FORMAT_EXTENSIONS: dict[str, str] = {
        "jpg": ".jpg",
        "jpeg": ".jpg",
        "png": ".png",
    }

    def __init__(
        self,
        video_path: str | Path,
        output_dir: str | Path = "output",
        output_format: Literal["jpg", "png"] = "jpg",
    ):
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.output_format = output_format

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise RuntimeError("ffmpeg and ffprobe must be installed and on PATH")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _run_ffprobe(self) -> dict:
        """Get video metadata via ffprobe JSON output."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            str(self.video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout)

    def _get_video_stream(self) -> dict:
        """Return the first video stream from ffprobe output."""
        probe = self._run_ffprobe()
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "video":
                return stream
        raise ValueError(f"No video stream found in: {self.video_path}")

    def _format_filename(self, index: int, total: int) -> str:
        padding = len(str(total))
        ext = self.FORMAT_EXTENSIONS[self.output_format]
        return f"frame_{index:0{padding}d}{ext}"

    def _quality_args(self) -> list[str]:
        """Return ffmpeg quality args for the output format."""
        if self.output_format in ("jpg", "jpeg"):
            return ["-q:v", "5"]
        return []

    def extract_by_interval(self, interval_seconds: float = 1.0) -> list[Path]:
        """Extract one frame every N seconds using ffmpeg fps filter."""
        ext = self.FORMAT_EXTENSIONS[self.output_format]
        pattern = str(self.output_dir / f"frame_%03d{ext}")

        cmd = [
            "ffmpeg", "-i", str(self.video_path),
            "-vf", f"fps=1/{interval_seconds}",
            *self._quality_args(),
            pattern, "-y",
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)

        frames = sorted(self.output_dir.glob(f"frame_*{ext}"))
        return frames

    def extract_by_count(self, count: int) -> list[Path]:
        """Extract N evenly-distributed frames using ffmpeg select filter."""
        if count < 1:
            raise ValueError("Count must be at least 1")

        info = self.get_video_info()
        duration = info["duration"]

        if duration <= 0:
            raise ValueError(f"Invalid video duration: {duration}")

        extracted = []
        for i in range(count):
            timestamp = (i / count) * duration
            ext = self.FORMAT_EXTENSIONS[self.output_format]
            filename = self._format_filename(i + 1, count)
            output_path = self.output_dir / filename

            cmd = [
                "ffmpeg",
                "-ss", f"{timestamp:.3f}",
                "-i", str(self.video_path),
                "-frames:v", "1",
                *self._quality_args(),
                str(output_path), "-y",
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)

            if output_path.exists():
                extracted.append(output_path)

        return extracted

    def extract_at_timestamp(self, timestamp: str) -> Path:
        """Extract a single frame at a specific timestamp using ffmpeg -ss."""
        if isinstance(timestamp, str) and ":" in timestamp:
            seek_pos = timestamp
        else:
            seek_pos = str(float(timestamp))

        ext = self.FORMAT_EXTENSIONS[self.output_format]
        safe_ts = timestamp.replace(":", "-")
        output_path = self.output_dir / f"frame_at_{safe_ts}{ext}"

        cmd = [
            "ffmpeg",
            "-ss", seek_pos,
            "-i", str(self.video_path),
            "-frames:v", "1",
            *self._quality_args(),
            str(output_path), "-y",
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)

        if not output_path.exists():
            raise ValueError(
                f"Cannot extract frame at timestamp: {timestamp}. "
                f"ffmpeg stderr: {result.stderr.decode()[-200:]}"
            )

        return output_path

    def get_video_info(self) -> dict:
        """Get video metadata using ffprobe."""
        stream = self._get_video_stream()
        probe = self._run_ffprobe()

        fps_parts = stream.get("r_frame_rate", "0/1").split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 and float(fps_parts[1]) > 0 else 0

        duration = float(probe.get("format", {}).get("duration", 0))
        frame_count = int(stream.get("nb_frames", 0))
        if frame_count == 0 and fps > 0:
            frame_count = int(duration * fps)

        return {
            "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0)),
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
        }
