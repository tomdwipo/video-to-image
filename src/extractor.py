import cv2
from pathlib import Path
from typing import Literal, Optional


class VideoExtractor:
    """Extract frames from video files with various strategies."""

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
        self.cap: Optional[cv2.VideoCapture] = None

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _open_video(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.video_path}")
        return cap

    def _get_frame_count(self) -> int:
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def _get_fps(self) -> float:
        return float(self.cap.get(cv2.CAP_PROP_FPS))

    def _get_duration(self) -> float:
        frame_count = self._get_frame_count()
        fps = self._get_fps()
        return frame_count / fps if fps > 0 else 0

    def _format_filename(self, index: int, total: int) -> str:
        padding = len(str(total))
        ext = self.FORMAT_EXTENSIONS[self.output_format]
        return f"frame_{index:0{padding}d}{ext}"

    def extract_by_interval(
        self,
        interval_seconds: float = 1.0,
    ) -> list[Path]:
        self.cap = self._open_video()
        fps = self._get_fps()
        interval_frames = int(fps * interval_seconds)

        if interval_frames < 1:
            interval_frames = 1

        extracted = []
        frame_position = 0
        frame_index = 1

        while True:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            ret, frame = self.cap.read()

            if not ret:
                break

            output_path = self.output_dir / self._format_filename(
                frame_index, 999
            )
            cv2.imwrite(str(output_path), frame)
            extracted.append(output_path)

            frame_position += interval_frames
            frame_index += 1

        self.cap.release()
        return extracted

    def extract_by_count(
        self,
        count: int,
    ) -> list[Path]:
        if count < 1:
            raise ValueError("Count must be at least 1")

        self.cap = self._open_video()
        total_frames = self._get_frame_count()
        interval = max(1, total_frames // count)

        extracted = []

        for i in range(count):
            frame_position = min(i * interval, total_frames - 1)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            ret, frame = self.cap.read()

            if ret:
                output_path = self.output_dir / self._format_filename(i + 1, count)
                cv2.imwrite(str(output_path), frame)
                extracted.append(output_path)

        self.cap.release()
        return extracted

    def extract_at_timestamp(
        self,
        timestamp: str,
    ) -> Path:
        self.cap = self._open_video()
        fps = self._get_fps()

        if isinstance(timestamp, str) and ":" in timestamp:
            parts = timestamp.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
                target_time = hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(float, parts)
                target_time = minutes * 60 + seconds
            else:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
        else:
            target_time = float(timestamp)

        frame_position = int(target_time * fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)

        ret, frame = self.cap.read()

        if not ret:
            raise ValueError(f"Cannot extract frame at timestamp: {timestamp}")

        output_path = self.output_dir / f"frame_at_{timestamp.replace(':', '-')}{self.FORMAT_EXTENSIONS[self.output_format]}"
        cv2.imwrite(str(output_path), frame)

        self.cap.release()
        return output_path

    def get_video_info(self) -> dict:
        self.cap = self._open_video()
        info = {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._get_fps(),
            "frame_count": self._get_frame_count(),
            "duration": self._get_duration(),
        }
        self.cap.release()
        return info
