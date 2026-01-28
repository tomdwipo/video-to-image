# Video to Image CLI

Extract frames from video files via command line. Supports MP4, AVI, MOV, MKV formats.

## Installation

```bash
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
