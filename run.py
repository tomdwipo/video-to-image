#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from tqdm import tqdm

from src.extractor import VideoExtractor


BANNER = """
╔═════════════════════════════════════════╗
║   Video to Image Frame Extractor v1.0   ║
╚═════════════════════════════════════════╝
"""


def parse_timestamp(value: str) -> float:
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

    parser.add_argument(
        "videos",
        nargs="+",
        type=Path,
        help="Path(s) to video file(s)",
    )

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
    try:
        if len(args.videos) > 1:
            output_dir = args.output / video_path.stem
        else:
            output_dir = args.output

        extractor = VideoExtractor(
            video_path=video_path,
            output_dir=output_dir,
            output_format=args.format,
        )

        if args.info:
            info = extractor.get_video_info()
            print(f"\n📹 {video_path.name}")
            print(f"   Resolution: {info['width']}x{info['height']}")
            print(f"   FPS: {info['fps']:.2f}")
            print(f"   Duration: {info['duration']:.2f}s")
            print(f"   Total Frames: {info['frame_count']}")
            return True

        if args.timestamp is not None:
            print(f"\n⏱️  Extracting frame at {args.timestamp}s from {video_path.name}")
            path = extractor.extract_at_timestamp(args.timestamp)
            print(f"   ✅ Saved: {path}")
            return True

        elif args.interval:
            info = extractor.get_video_info()
            total_video_frames = info["frame_count"]
            duration = info["duration"]
            estimated_frames = int(duration / args.interval)

            interval_frames = max(1, total_video_frames // estimated_frames)

            print(f"\n🎬 Extracting every {args.interval}s from {video_path.name}")
            print(f"   Estimated frames: ~{estimated_frames}")

            with tqdm(
                total=estimated_frames,
                desc=f"  [{video_index}/{len(args.videos)}]",
                unit="frame",
            ) as pbar:
                extracted = []
                import cv2
                cap = extractor._open_video()
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
    print(BANNER)

    parser = setup_parser()
    args = parser.parse_args()

    missing = [v for v in args.videos if not v.exists()]
    if missing:
        print(f"\n❌ Video files not found:", file=sys.stderr)
        for f in missing:
            print(f"   - {f}", file=sys.stderr)
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    results = []
    for i, video in enumerate(args.videos, 1):
        result = process_video(video, args, i)
        results.append(result)

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
