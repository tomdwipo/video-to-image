# Architecture

C4 model documentation for the Video-to-Image CLI tool.

## System Context

The Video-to-Image CLI is a command-line tool that extracts frames from video files.

```ascii
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │                     User (Developer)                            │
    │                    Terminal / Shell                             │
    │                                                                 │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │                         │
                    │   Video-to-Image CLI    │
                    │   (Python Application)  │
                    │                         │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
  ┌─────────────┐       ┌──────────────┐       ┌─────────────┐
  │ Video File  │       │ File System │       │ Frame Images│
  │  .MP4/.MOV  │       │  (output/)  │       │   .JPG/.PNG │
  └─────────────┘       └──────────────┘       └─────────────┘
```

### External Entities

| Entity | Description |
|--------|-------------|
| User | Runs the CLI from terminal with video files and options |
| Video File | Input: MP4, AVI, MOV, MKV formats |
| Frame Images | Output: JPG or PNG images extracted from video |

---

## Containers

Internal structure of the CLI application.

```ascii
    ┌─────────────────────────────────────────────────────────────────┐
    │                          run.py                                 │
    │                      (CLI Entry Point)                          │
    │                                                                 │
    │  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
    │  │  argparse  │  │   tqdm     │  │   sys    │  │  Path    │  │
    │  │  (CLI)     │  │ (progress) │  │ (errors) │  │ (files)  │  │
    │  └─────┬──────┘  └─────┬───────┘  └────┬─────┘  └────┬─────┘  │
    │        └────────────────┴───────────────┴───────────────┘     │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                      src/extractor.py                           │
    │                      (VideoExtractor)                           │
    │                                                                 │
    │  ┌────────────────────────────────────────────────────────┐    │
    │  │                    OpenCV (cv2)                        │    │
    │  │            VideoCapture / VideoWriter                  │    │
    │  └────────────────────────────────────────────────────────┘    │
    │                                                                 │
    │  Methods:                                                       │
    │  • extract_by_interval()   Extract every N seconds             │
    │  • extract_by_count()       Extract N evenly distributed       │
    │  • extract_at_timestamp()   Extract at specific time            │
    │  • get_video_info()         Return video metadata               │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
                         ┌──────────────┐
                         │  File System │
                         │   output/    │
                         └──────────────┘
```

### Container Descriptions

| Container | Technology | Description |
|-----------|------------|-------------|
| run.py | Python 3.8+ | CLI entry point, argument parsing, progress display |
| src/extractor.py | Python + OpenCV | Video processing logic, frame extraction |
| File System | OS filesystem | Input videos and output frame storage |

---

## Components

Detailed view of the VideoExtractor class.

```ascii
    ┌─────────────────────────────────────────────────────────────────┐
    │                        VideoExtractor                           │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │                         State                            │  │
    │  │  • video_path: Path      Input video file path           │  │
    │  │  • output_dir: Path      Output directory path            │  │
    │  │  • output_format: Literal  "jpg" or "png"                 │  │
    │  │  • cap: VideoCapture     OpenCV video capture object      │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                 │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │                      Public Methods                      │  │
    │  │                                                          │  │
    │  │  extract_by_interval(interval_seconds)                  │  │
    │  │       │                                                   │  │
    │  │       ├──▶ Calculate skip: frame_count // (duration / interval) │
    │  │       ├──▶ Loop: seek, read, write each frame            │  │
    │  │       └──▶ Return: list[Path] of extracted frames       │  │
    │  │                                                          │  │
    │  │  extract_by_count(count)                                │  │
    │  │       │                                                   │  │
    │  │       ├──▶ Calculate skip: frame_count // count         │  │
    │  │       ├──▶ Loop: seek, read, write N frames             │  │
    │  │       └──▶ Return: list[Path] of extracted frames       │  │
    │  │                                                          │  │
    │  │  extract_at_timestamp(timestamp)                        │  │
    │  │       │                                                   │  │
    │  │       ├──▶ Parse: "HH:MM:SS" or "MM:SS" to seconds      │  │
    │  │       ├──▶ Calculate: target_time * fps = frame_pos     │  │
    │  │       ├──▶ Seek, read, write single frame               │  │
    │  │       └──▶ Return: Path of extracted frame             │  │
    │  │                                                          │  │
    │  │  get_video_info()                                       │  │
    │  │       │                                                   │  │
    │  │       └──▶ Return: {width, height, fps, frame_count, duration} │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                 │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │                      Private Methods                     │  │
    │  │  _open_video()           Create and validate VideoCapture│  │
    │  │  _get_frame_count()       Get total frame count          │  │
    │  │  _get_fps()               Get frames per second          │  │
    │  │  _get_duration()          Calculate video duration       │  │
    │  │  _format_filename()       Generate "frame_001.jpg" name  │  │
    │  └──────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

Complete flow from user command to extracted frames.

```ascii
    USER INPUT
        │
        ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  $ python run.py video.mp4 --interval 2.0                      │
    └────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  run.py :: main()                                              │
    │  • Parse arguments with argparse                               │
    │  • Validate video files exist                                  │
    │  • Create output directory                                     │
    └────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  run.py :: process_video()                                      │
    │  • Get video info from VideoExtractor                          │
    │  • Calculate interval_frames from frame_count (NOT fps)         │
    │  • Show progress bar with tqdm                                 │
    └────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  OpenCV :: cv2.VideoCapture                                     │
    │  • Open video file                                              │
    │  • Loop: set frame position, read frame                        │
    │  • Write frame to disk with cv2.imwrite()                      │
    │  • Release capture                                              │
    └────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  output/                                                        │
    │  • frame_001.jpg                                                │
    │  • frame_002.jpg                                                │
    │  • frame_003.jpg                                                │
    │  • ...                                                          │
    └─────────────────────────────────────────────────────────────────┘
```

### Extraction Modes

| Mode | CLI Flag | Logic |
|------|----------|-------|
| Interval | `--interval N` | Extract every N seconds |
| Count | `--count N` | Extract N evenly distributed frames |
| Timestamp | `--timestamp T` | Extract single frame at time T |

---

## Important Notes

### VFR Video Handling
iPhone MOV files use Variable Frame Rate (VFR). FPS-based calculations are unreliable.

**Correct (uses frame count):**
```python
interval_frames = total_video_frames // estimated_frames
```

**Incorrect (uses FPS):**
```python
interval_frames = int(fps * interval)  # Fails on VFR videos
```

### Batch Processing
When processing multiple videos, each gets its own subdirectory to prevent frame filename collisions:

```ascii
output/
├── video1/
│   ├── frame_001.jpg
│   └── frame_002.jpg
└── video2/
    ├── frame_001.jpg
    └── frame_002.jpg
```
