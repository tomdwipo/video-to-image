# Step-by-Step Implementation Plan with Before/After Code

## Step 1: Create Project Directory Structure

**BEFORE:**
```
video-to-image/
└── (empty)
```

**AFTER:**
```
video-to-image/
├── src/
│   └── __init__.py
├── input/
├── output/
├── run.py
├── requirements.txt
└── README.md
```

**Technical Rationale:** Separate source code from data directories. `input/` and `output/` keep user files organized. `src/` contains logic for better maintainability.

**Commands:**
```bash
mkdir -p src input output
touch src/__init__.py
```

---

## Step 2: Create requirements.txt

**BEFORE:**
```
(file does not exist)
```

**AFTER:**
```txt
# Core dependencies
opencv-python>=4.8.0          # Video processing
tqdm>=4.65.0                  # Progress bar

# Optional: for additional video formats
imageio>=2.31.0               # Fallback video reader
imageio-ffmpeg>=0.4.9         # FFmpeg binaries for imageio
```

**Technical Rationale:** OpenCV (`cv2`) is the industry standard for video processing. `tqdm` provides visual progress feedback. Pinning minimum versions ensures API compatibility.

---

## Step 3: Create Core Extractor Module

**BEFORE:**
```
(src/extractor.py does not exist)
```

**AFTER:**
```python
# src/extractor.py
"""
Video frame extractor using OpenCV.
Supports interval-based, count-based, and timestamp-based extraction.
"""

import cv2
import os
from pathlib import Path
from typing import Literal, Optional


class VideoExtractor:
    """Extract frames from video files with various strategies."""

    # ✅ Supported output formats
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
        """
        Initialize extractor with video source and output configuration.

        Args:
            video_path: Path to input video file
            output_dir: Directory for extracted frames
            output_format: Image format (jpg or png)
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.output_format = output_format
        self.cap: Optional[cv2.VideoCapture] = None

        # ✅ Validate video exists before opening
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # ✅ Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _open_video(self) -> cv2.VideoCapture:
        """Open video capture and validate it's readable."""
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.video_path}")
        return cap

    def _get_frame_count(self) -> int:
        """Get total number of frames in video."""
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def _get_fps(self) -> float:
        """Get video frames per second."""
        return float(self.cap.get(cv2.CAP_PROP_FPS))

    def _get_duration(self) -> float:
        """Get video duration in seconds."""
        frame_count = self._get_frame_count()
        fps = self._get_fps()
        return frame_count / fps if fps > 0 else 0

    def _format_filename(self, index: int, total: int) -> str:
        """
        Generate sequential filename with padding.

        Args:
            index: Current frame number
            total: Total frames (for padding calculation)

        Returns:
            Filename like 'frame_001.jpg'
        """
        padding = len(str(total))
        ext = self.FORMAT_EXTENSIONS[self.output_format]
        return f"frame_{index:0{padding}d}{ext}"

    def extract_by_interval(
        self,
        interval_seconds: float = 1.0,
    ) -> list[Path]:
        """
        Extract frames at regular time intervals.

        Args:
            interval_seconds: Seconds between each extracted frame

        Returns:
            List of paths to extracted images
        """
        self.cap = self._open_video()
        fps = self._get_fps()
        interval_frames = int(fps * interval_seconds)

        if interval_frames < 1:
            interval_frames = 1  # ✅ At least 1 frame

        extracted = []
        frame_position = 0
        frame_index = 1

        while True:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            ret, frame = self.cap.read()

            if not ret:
                break  # ✅ End of video

            output_path = self.output_dir / self._format_filename(
                frame_index, 999  # ✅ Fixed padding for interval mode
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
        """
        Extract evenly distributed frames across video duration.

        Args:
            count: Number of frames to extract

        Returns:
            List of paths to extracted images
        """
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
        timestamp: str,  # Format: "HH:MM:SS" or "MM:SS" or "Seconds"
    ) -> Path:
        """
        Extract single frame at specific timestamp.

        Args:
            timestamp: Time in "HH:MM:SS", "MM:SS", or seconds as float/string

        Returns:
            Path to extracted image
        """
        self.cap = self._open_video()
        fps = self._get_fps()

        # ✅ Parse timestamp format
        if isinstance(timestamp, str) and ":" in timestamp:
            parts = timestamp.split(":")
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(float, parts)
                target_time = hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(float, parts)
                target_time = minutes * 60 + seconds
            else:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
        else:
            # Direct seconds value
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
        """Return metadata about the video file."""
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
```

**Technical Rationale:**
- **Type hints** enable IDE autocomplete and catch errors early
- **Path objects** handle cross-platform paths correctly
- **Context management** via explicit release prevents resource leaks
- **Three extraction strategies** cover all acceptance criteria

---

## Step 4: Create CLI Entry Point

**BEFORE:**
```
(run.py does not exist)
```

**AFTER:**
```python
#!/usr/bin/env python3
"""
Video to Image CLI
Extract frames from video files with configurable options.
"""

import argparse
import sys
from pathlib import Path
from tqdm import tqdm

from src.extractor import VideoExtractor


# ✅ ASCII art for brand recognition
BANNER = """
╔═════════════════════════════════════════╗
║   Video to Image Frame Extractor v1.0   ║
╚═════════════════════════════════════════╝
"""


def parse_timestamp(value: str) -> float:
    """
    Parse timestamp string to seconds.

    Accepts: "HH:MM:SS", "MM:SS", or numeric seconds
    """
    if ":" in value:
        parts = value.split(":")
        try:
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s
        except ValueError:
            pass
    return float(value)


def setup_parser() -> argparse.ArgumentParser:
    """Configure CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="video-to-image",
        description="Extract frames from video files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract every second
  python run.py video.mp4 --interval 1.0

  # Extract 10 evenly distributed frames
  python run.py video.mp4 --count 10

  # Extract single frame at 1:30
  python run.py video.mp4 --timestamp "01:30"

  # Batch process multiple videos
  python run.py video1.mp4 video2.mp4 --interval 2
        """,
    )

    # ✅ Positional: video file(s)
    parser.add_argument(
        "videos",
        nargs="+",
        type=Path,
        help="Path(s) to video file(s)",
    )

    # ✅ Extraction mode (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "-i", "--interval",
        type=float,
        help="Extract frame every N seconds",
    )
    mode_group.add_argument(
        "-c", "--count",
        type=int,
        help="Extract exactly N frames, evenly distributed",
    )
    mode_group.add_argument(
        "-t", "--timestamp",
        type=parse_timestamp,
        help="Extract single frame at timestamp (format: HH:MM:SS or MM:SS or seconds)",
    )

    # ✅ Optional arguments
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["jpg", "png"],
        default="jpg",
        help="Output image format (default: jpg)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show video information and exit",
    )

    return parser


def process_video(
    video_path: Path,
    args: argparse.Namespace,
    video_index: int = 1,
) -> bool:
    """
    Process a single video file.

    Returns:
        True if successful, False otherwise
    """
    try:
        # ✅ Determine output directory (per video or shared)
        if len(args.videos) > 1:
            output_dir = args.output / video_path.stem
        else:
            output_dir = args.output

        extractor = VideoExtractor(
            video_path=video_path,
            output_dir=output_dir,
            output_format=args.format,
        )

        # ✅ Show info mode
        if args.info:
            info = extractor.get_video_info()
            print(f"\n📹 {video_path.name}")
            print(f"   Resolution: {info['width']}x{info['height']}")
            print(f"   FPS: {info['fps']:.2f}")
            print(f"   Duration: {info['duration']:.2f}s")
            print(f"   Total Frames: {info['frame_count']}")
            return True

        # ✅ Extract based on mode
        if args.timestamp is not None:
            print(f"\n⏱️  Extracting frame at {args.timestamp}s from {video_path.name}")
            path = extractor.extract_at_timestamp(args.timestamp)
            print(f"   ✅ Saved: {path}")
            return True

        elif args.interval:
            info = extractor.get_video_info()
            total_frames = int(info["duration"] / args.interval)
            print(f"\n🎬 Extracting every {args.interval}s from {video_path.name}")
            print(f"   Estimated frames: ~{total_frames}")

            # ✅ Progress bar for multiple videos
            with tqdm(
                total=total_frames,
                desc=f"  [{video_index}/{len(args.videos)}]",
                unit="frame",
            ) as pbar:
                # ✅ Override extract method to update progress
                original_extract = extractor.extract_by_interval
                extracted = []
                import cv2
                cap = extractor._open_video()
                fps = extractor._get_fps()
                interval_frames = int(fps * args.interval) or 1
                frame_position = 0
                frame_index = 1

                while True:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
                    ret, frame = cap.read()
                    if not ret:
                        break
                    output_path = output_dir / extractor._format_filename(frame_index, 999)
                    cv2.imwrite(str(output_path), frame)
                    extracted.append(output_path)
                    frame_position += interval_frames
                    frame_index += 1
                    pbar.update(1)
                cap.release()

            print(f"   ✅ Extracted {len(extracted)} frames to {output_dir}")
            return extracted

        elif args.count:
            print(f"\n🎯 Extracting {args.count} frames from {video_path.name}")
            frames = extractor.extract_by_count(args.count)
            print(f"   ✅ Saved {len(frames)} frames to {output_dir}")
            return frames

        return False

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return False
    except ValueError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error processing {video_path.name}: {e}", file=sys.stderr)
        return False


def main():
    """CLI entry point."""
    print(BANNER)

    parser = setup_parser()
    args = parser.parse_args()

    # ✅ Validate video files exist
    missing = [v for v in args.videos if not v.exists()]
    if missing:
        print(f"\n❌ Video files not found:", file=sys.stderr)
        for f in missing:
            print(f"   - {f}", file=sys.stderr)
        sys.exit(1)

    # ✅ Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # ✅ Process each video
    results = []
    for i, video in enumerate(args.videos, 1):
        result = process_video(video, args, i)
        results.append(result)

    # ✅ Exit with appropriate code
    if all(results):
        print("\n✨ All videos processed successfully!")
        sys.exit(0)
    elif any(results):
        print(f"\n⚠️  {sum(not r for r in results)} video(s) failed")
        sys.exit(1)
    else:
        print("\n❌ All videos failed to process", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Technical Rationale:**
- **argparse** provides standard CLI interface with auto-generated help
- **Mutually exclusive group** prevents conflicting extraction modes
- **TQDM progress bars** give user feedback during long operations
- **Per-video subdirectories** prevent frame filename collisions in batch mode
- **Exit codes** enable scripting and CI/CD integration

---

## Step 5: Create README Documentation

**BEFORE:**
```
(README.md does not exist)
```

**AFTER:**
```markdown
# Video to Image CLI

Extract frames from video files via command line. Supports MP4, AVI, MOV, MKV formats.

## Installation

```bash
# Clone repository
git clone <repo-url>
cd video-to-image

# Install dependencies
pip install -r requirements.txt
```

## Requirements
- Python 3.8+
- OpenCV (installed via requirements.txt)

## Usage

```bash
python run.py <video_file> [options]
```

### Extraction Modes

**Extract every N seconds:**
```bash
python run.py video.mp4 --interval 1.0    # Every 1 second
python run.py video.mp4 -i 0.5           # Every 0.5 seconds
```

**Extract N evenly distributed frames:**
```bash
python run.py video.mp4 --count 10       # 10 frames across video
python run.py video.mp4 -c 5             # 5 frames across video
```

**Extract single frame at timestamp:**
```bash
python run.py video.mp4 --timestamp "01:30"   # At 1 minute 30 seconds
python run.py video.mp4 -t "00:15"           # At 15 seconds
python run.py video.mp4 -t 90                # At 90 seconds
```

### Options

| Option | Description |
|--------|-------------|
| `-i, --interval` | Extract frame every N seconds |
| `-c, --count` | Extract exactly N frames |
| `-t, --timestamp` | Extract frame at timestamp (HH:MM:SS or MM:SS or seconds) |
| `-o, --output` | Output directory (default: `./output`) |
| `-f, --format` | Output format: `jpg` or `png` (default: `jpg`) |
| `--info` | Show video metadata |
| `-h, --help` | Show help message |

### Examples

**Show video information:**
```bash
python run.py video.mp4 --info
```

**Batch process multiple videos:**
```bash
python run.py video1.mp4 video2.mp4 video3.mp4 --interval 2
# Output: output/video1/, output/video2/, output/video3/
```

**Extract as PNG:**
```bash
python run.py video.mp4 --interval 5 --format png
```

**Custom output directory:**
```bash
python run.py video.mp4 --interval 1 --output my_frames
```

## Output

Frames are named sequentially: `frame_001.jpg`, `frame_002.jpg`, etc.

For batch processing, each video gets its own subdirectory:
```
output/
├── video1/
│   ├── frame_001.jpg
│   └── frame_002.jpg
└── video2/
    ├── frame_001.jpg
    └── frame_002.jpg
```

## Troubleshooting

**"Cannot open video file"**
- Check file format is supported (MP4, AVI, MOV, MKV)
- Verify video is not corrupted

**"No output frames"**
- Interval may be too large for video duration
- Try `--info` to check video length

**Memory errors with large videos**
- Reduce interval to extract fewer frames
- Use `--count` for fixed frame extraction
```

**Technical Rationale:**
- **Examples first** documentation helps users quickly understand usage
- **Table format** makes options scannable
- **Troubleshooting section** reduces support burden

---

## Step 6: Add .gitignore

**BEFORE:**
```
(.gitignore does not exist)
```

**AFTER:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
.venv

# IDE
.idea/
.vscode/
*.swp

# User files (videos and output)
input/*
output/*
!input/.gitkeep
!output/.gitkeep

# macOS
.DS_Store

# Debug logs
firebase-debug.log
*.log
```

**Technical Rationale:** Ignore user-generated content to keep repo size small. Use `.gitkeep` files to preserve empty directory structure.

---

## Step 7: Add GitKeep Files

**BEFORE:**
```
(input/ and output/ folders are empty and won't be tracked)
```

**AFTER:**
```bash
# Create placeholder files so git tracks empty directories
touch input/.gitkeep output/.gitkeep
```

**Technical Rationale:** Git doesn't track empty directories. `.gitkeep` is a convention to preserve folder structure for users.

---

## Summary of Changes:

| Step | File | Change | Purpose |
|------|------|--------|---------|
| 1 | Directory structure | Create src/, input/, output/ | Organize code and data |
| 2 | requirements.txt | Define dependencies | Enable reproducible installs |
| 3 | src/extractor.py | Core extraction logic | Encapsulate video processing |
| 4 | run.py | CLI entry point | User interface |
| 5 | README.md | Documentation | Usage guide |
| 6 | .gitignore | Exclude generated files | Clean repository |
| 7 | .gitkeep files | Preserve directories | Git tracking |

**Key Insights:**
- **Single responsibility**: `extractor.py` handles logic, `run.py` handles CLI
- **Progressive features**: Interval extraction first, then count/timestamp extensions
- **Error resilience**: Validation at every step (file exists, opens, readable)
- **User feedback**: TQDM progress bars and clear error messages

---

## Testing Considerations

### Manual Testing Checklist

```bash
# Test 1: Interval extraction
python run.py test.mp4 --interval 1
# Verify: Frames extracted, sequential naming

# Test 2: Count extraction
python run.py test.mp4 --count 5
# Verify: Exactly 5 frames

# Test 3: Timestamp extraction
python run.py test.mp4 --timestamp "00:05"
# Verify: Single frame at 5 seconds

# Test 4: Info display
python run.py test.mp4 --info
# Verify: Metadata shown

# Test 5: Batch processing
python run.py test1.mp4 test2.mp4 --interval 2
# Verify: Separate subdirectories created

# Test 6: Error handling
python run.py nonexistent.mp4 --interval 1
# Verify: Clear error message

# Test 7: Format selection
python run.py test.mp4 --interval 1 --format png
# Verify: PNG output

# Test 8: Custom output
python run.py test.mp4 --interval 1 --output custom_dir
# Verify: Files in custom location
```

### Sample Test Video

For testing without real videos, create a 10-second test video:

```python
import cv2
import numpy as np

# Create 10-second test video at 30fps
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test.mp4', fourcc, 30.0, (640, 480))

for i in range(300):  # 10 seconds @ 30fps
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, f"Frame {i}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
    out.write(frame)

out.release()
```
