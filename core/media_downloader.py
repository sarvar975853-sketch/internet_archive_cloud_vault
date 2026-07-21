"""
OmniFetch Media Downloader Engine — v1.0.0
Unified media extraction engine powered by yt-dlp + aria2c + FFmpeg.

Supports:
  - YouTube (video/audio, playlists, chapters)
  - Instagram (reels, posts, stories)
  - TikTok, Twitter/X, Reddit, Twitch clips
  - Spotify metadata → high-bitrate audio mapping
  - JioSaavn / Wynk stream extraction
  - Any platform yt-dlp recognizes

Architecture:
  1. yt-dlp extracts stream manifests + metadata
  2. aria2c handles multi-threaded chunked downloads (up to 16 connections)
  3. FFmpeg muxes separate video+audio streams, transcodes containers
"""

import os
import re
import json
import subprocess
import tempfile
import shutil
import time
import uuid
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable
from urllib.parse import urlparse

from aegis_vault.utils.logger import logger


# ─── Data Types ────────────────────────────────────────────────────────────────

class Platform(Enum):
    YOUTUBE    = "youtube"
    INSTAGRAM  = "instagram"
    TIKTOK     = "tiktok"
    TWITTER    = "twitter"
    REDDIT     = "reddit"
    TWITCH     = "twitch"
    SPOTIFY    = "spotify"
    JIOSAAVN   = "jiosaavn"
    WYNK       = "wynk"
    GENERIC    = "generic"


class DownloadStatus(Enum):
    QUEUED       = "queued"
    EXTRACTING   = "extracting"
    DOWNLOADING  = "downloading"
    PROCESSING   = "processing"
    COMPLETED    = "completed"
    ERROR        = "error"
    CANCELLED    = "cancelled"
    PAUSED       = "paused"


@dataclass
class StreamFormat:
    """A single available stream format from yt-dlp manifest."""
    format_id: str
    label: str
    quality: str
    ext: str
    has_video: bool
    has_audio: bool
    fps: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    tbr: Optional[float] = None  # total bitrate in kbps


@dataclass
class DownloadTask:
    """Represents one media download job."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    url: str = ""
    title: str = "Unknown"
    platform: Platform = Platform.GENERIC
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: str = "--"
    eta: str = "--"
    total_size: str = "--"
    downloaded: str = "0 B"
    format: str = "best"
    quality: str = "best"
    output_path: str = ""
    error: str = ""
    formats: list = field(default_factory=list)
    start_time: float = 0.0
    _process: Optional[subprocess.Popen] = field(default=None, repr=False)


# ─── Platform Detection ────────────────────────────────────────────────────────

PLATFORM_PATTERNS = {
    Platform.YOUTUBE:   [r"youtube\.com", r"youtu\.be", r"youtube\.shorts"],
    Platform.INSTAGRAM: [r"instagram\.com"],
    Platform.TIKTOK:    [r"tiktok\.com", r"vm\.tiktok\.com"],
    Platform.TWITTER:   [r"twitter\.com", r"x\.com"],
    Platform.REDDIT:    [r"reddit\.com", r"redd\.it"],
    Platform.TWITCH:    [r"twitch\.tv", r"clips\.twitch\.tv"],
    Platform.SPOTIFY:   [r"spotify\.com", r"open\.spotify\.com"],
    Platform.JIOSAAVN:  [r"jiosaavn\.com"],
    Platform.WYNK:      [r"wynk\.in"],
}


def detect_platform(url: str) -> Platform:
    """Detect the media platform from a URL."""
    lower = url.lower().strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lower):
                return platform
    return Platform.GENERIC


# ─── Binary Resolution ─────────────────────────────────────────────────────────

def _find_binary(name: str) -> str:
    """Find a binary on PATH, return its absolute path or empty string."""
    path = shutil.which(name)
    return path or ""


def _yt_dlp_path() -> str:
    """Resolve yt-dlp binary path. Tries common locations."""
    path = _find_binary("yt-dlp")
    if path:
        return path
    # Try Python-installed location
    try:
        import yt_dlp
        return ""  # Will use yt-dlp as Python module
    except ImportError:
        pass
    return ""


def _ffmpeg_path() -> str:
    return _find_binary("ffmpeg") or _find_binary("ffprobe") or ""


def _aria2c_path() -> str:
    return _find_binary("aria2c") or ""


# ─── Engine ────────────────────────────────────────────────────────────────────

class MediaDownloader:
    """
    Unified media downloader engine.
    
    Usage:
        dl = MediaDownloader(progress_callback=my_callback)
        task = dl.submit("https://youtube.com/watch?v=...", quality="1080p")
        dl.start_task(task.id)
    """

    def __init__(
        self,
        download_dir: Optional[str] = None,
        max_concurrent: int = 4,
        aria2_chunks: int = 16,
        progress_callback: Optional[Callable] = None,
    ):
        self.download_dir = download_dir or os.path.join(
            tempfile.gettempdir(), "omnifetch_downloads"
        )
        os.makedirs(self.download_dir, exist_ok=True)

        self.max_concurrent = max_concurrent
        self.aria2_chunks = aria2_chunks
        self.progress_callback = progress_callback

        # Task registry
        self._tasks: dict[str, DownloadTask] = {}
        self._lock = threading.Lock()

        # Resolve binary paths
        self._yt_dlp = _yt_dlp_path()
        self._ffmpeg = _ffmpeg_path()
        self._aria2c = _aria2c_path()

        logger.info(
            f"OmniFetch engine init — yt-dlp: {self._yt_dlp or 'python-module'}, "
            f"ffmpeg: {self._ffmpeg or 'not found'}, "
            f"aria2c: {self._aria2c or 'not found'}"
        )

    # ─── Public API ──────────────────────────────────────────────────────────

    def get_engine_status(self) -> dict:
        """Return availability of each binary."""
        return {
            "yt_dlp": bool(self._yt_dlp) or self._has_ytdlp_module(),
            "ffmpeg": bool(self._ffmpeg),
            "aria2c": bool(self._aria2c),
        }

    def extract_info(self, url: str) -> dict:
        """
        Extract metadata + available formats from a URL.
        Returns dict with: title, platform, formats (list of StreamFormat dicts)
        """
        platform = detect_platform(url)
        logger.info(f"Extracting info for {platform.value}: {url}")

        if self._has_ytdlp_module():
            return self._extract_via_module(url, platform)
        elif self._yt_dlp:
            return self._extract_via_binary(url, platform)
        else:
            return {
                "success": False,
                "error": "yt-dlp not found. Install yt-dlp (pip install yt-dlp) or place the binary on PATH.",
                "title": "",
                "platform": platform.value,
                "formats": [],
            }

    def submit(self, url: str, quality: str = "best", fmt: str = "best",
                output_dir: Optional[str] = None) -> DownloadTask:
        """Submit a URL for download. Returns a DownloadTask."""
        task = DownloadTask(
            url=url.strip(),
            platform=detect_platform(url),
            quality=quality,
            format=fmt,
            output_path=output_dir or self.download_dir,
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[DownloadTask]:
        with self._lock:
            return list(self._tasks.values())

    def cancel_task(self, task_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task._process:
                try:
                    task._process.terminate()
                except Exception:
                    pass
                task.status = DownloadStatus.CANCELLED
                self._emit(task)

    def start_task(self, task_id: str):
        """Begin downloading a submitted task in a background thread."""
        thread = threading.Thread(
            target=self._run_download, args=(task_id,), daemon=True
        )
        thread.start()

    def update_task(self, task_id: str, **kwargs):
        """Update task fields and notify UI."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                for k, v in kwargs.items():
                    setattr(task, k, v)
                self._emit(task)

    # ─── Internal: Download Pipeline ──────────────────────────────────────────

    def _run_download(self, task_id: str):
        """Full download pipeline: extract → download → process."""
        task = self.get_task(task_id)
        if not task:
            return

        try:
            # Step 1: Extract info
            self.update_task(task_id, status=DownloadStatus.EXTRACTING, progress=0)
            info = self.extract_info(task.url)
            if not info.get("success", False):
                self.update_task(task_id, status=DownloadStatus.ERROR,
                                 error=info.get("error", "Extraction failed"))
                return

            self.update_task(task_id,
                             title=info.get("title", task.url),
                             formats=info.get("formats", []))

            # Step 2: Download
            self.update_task(task_id, status=DownloadStatus.DOWNLOADING, progress=5)
            output_path = self._do_download(task)
            if not output_path:
                self.update_task(task_id, status=DownloadStatus.ERROR,
                                 error="Download failed — no output file")
                return

            # Step 3: Post-process (mux/transcode if needed)
            self.update_task(task_id, status=DownloadStatus.PROCESSING, progress=90)
            final_path = self._post_process(task, output_path)

            # Done
            self.update_task(task_id, status=DownloadStatus.COMPLETED,
                             progress=100, output_path=final_path,
                             speed="--", eta="--")
            logger.info(f"Download completed: {final_path}")

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            self.update_task(task_id, status=DownloadStatus.ERROR, error=str(e))

    def _do_download(self, task: DownloadTask) -> Optional[str]:
        """Execute the actual download using yt-dlp (with aria2c if available)."""
        safe_title = self._sanitize(task.title)[:80]
        output_template = os.path.join(task.output_path, f"{safe_title}.%(ext)s")

        # Build yt-dlp command
        cmd = self._build_ytdlp_cmd(task, output_template)
        if not cmd:
            return None

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )
            task._process = process

            # Parse yt-dlp progress output
            for line in process.stdout:
                self._parse_progress_line(task, line.strip())

            process.wait()
            task._process = None

            if process.returncode != 0:
                logger.warning(f"yt-dlp exit code: {process.returncode}")
                return None

            # Find the downloaded file
            return self._find_downloaded_file(task.output_path, safe_title)

        except Exception as e:
            logger.error(f"yt-dlp execution failed: {e}")
            return None

    def _build_ytdlp_cmd(self, task: DownloadTask, output_template: str) -> list[str]:
        """Build the yt-dlp command line."""
        if self._yt_dlp:
            cmd = [self._yt_dlp]
        else:
            cmd = ["python", "-m", "yt_dlp"]

        # Common options
        cmd += [
            "--no-warnings",
            "--newline",
            "--progress",
            "--progress-template", "%(progress._percent_str)s %(progress._speed_str)s %(progress._eta_str)s",
            "-o", output_template,
        ]

        # Use aria2c as downloader if available
        if self._aria2c:
            cmd += [
                "--downloader", "aria2c",
                "--downloader-args", f"aria2c:-x{self.aria2_chunks} -s{self.aria2_chunks} -k1M",
            ]

        # Use FFmpeg for muxing
        if self._ffmpeg:
            cmd += ["--ffmpeg-location", os.path.dirname(self._ffmpeg)]

        # Quality / format selection
        fmt_filter = self._build_format_filter(task)
        if fmt_filter:
            cmd += ["-f", fmt_filter]

        # Best quality fallback
        if task.quality == "best" and task.format == "best":
            cmd += ["-f", "bestvideo+bestaudio/best"]

        # Metadata
        cmd += ["--add-metadata"]

        cmd.append(task.url)
        return cmd

    def _build_format_filter(self, task: DownloadTask) -> str:
        """Build yt-dlp format selector string."""
        q = task.quality.lower()
        fmt = task.format.lower()

        if q == "best" and fmt == "best":
            return "bestvideo+bestaudio/best"

        # Audio-only selectors
        if fmt in ("mp3", "flac", "wav", "m4a", "opus", "audio"):
            if fmt == "mp3":
                return "bestaudio[ext=mp3]/bestaudio"
            elif fmt == "flac":
                return "bestaudio[ext=flac]/bestaudio"
            elif fmt == "wav":
                return "bestaudio[ext=wav]/bestaudio"
            elif fmt == "m4a":
                return "bestaudio[ext=m4a]/bestaudio"
            elif fmt == "opus":
                return "bestaudio[ext=opus]/bestaudio"
            return "bestaudio"

        # Video quality selectors
        quality_map = {
            "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "4k":    "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
        }

        if q in quality_map:
            return quality_map[q]

        return "bestvideo+bestaudio/best"

    def _post_process(self, task: DownloadTask, file_path: str) -> str:
        """Post-process: transcode audio if needed, convert containers."""
        if not self._ffmpeg:
            return file_path

        ext = task.format.lower()
        if ext in ("mp3", "flac", "wav", "m4a", "opus") and not file_path.endswith(f".{ext}"):
            return self._transcode_audio(file_path, ext)

        return file_path

    def _transcode_audio(self, input_path: str, target_ext: str) -> str:
        """Transcode audio using FFmpeg."""
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}.{target_ext}"

        cmd = [self._ffmpeg, "-y", "-i", input_path]

        if target_ext == "mp3":
            cmd += ["-codec:a", "libmp3lame", "-b:a", "320k"]
        elif target_ext == "flac":
            cmd += ["-codec:a", "flac"]
        elif target_ext == "wav":
            cmd += ["-codec:a", "pcm_s16le"]
        elif target_ext == "m4a":
            cmd += ["-codec:a", "aac", "-b:a", "256k"]
        elif target_ext == "opus":
            cmd += ["-codec:a", "libopus", "-b:a", "192k"]

        cmd.append(output_path)

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            os.remove(input_path)
            return output_path
        except Exception as e:
            logger.warning(f"FFmpeg transcode failed: {e}")
            return input_path

    # ─── Internal: Extraction ─────────────────────────────────────────────────

    def _extract_via_module(self, url: str, platform: Platform) -> dict:
        """Extract info using yt-dlp as a Python module."""
        try:
            import yt_dlp

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }

            if self._aria2c:
                ydl_opts["external_downloader"] = "aria2c"
                ydl_opts["external_downloader_args"] = [
                    f"aria2c:-x{self.aria2_chunks} -s{self.aria2_chunks} -k1M"
                ]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {"success": False, "error": "No info extracted", "formats": []}

                title = info.get("title", url)
                formats = []

                for f in info.get("formats", []):
                    formats.append({
                        "format_id": f.get("format_id", ""),
                        "label": f.get("format_note", f.get("resolution", "unknown")),
                        "quality": f.get("resolution", "unknown"),
                        "ext": f.get("ext", "unknown"),
                        "has_video": f.get("vcodec") != "none",
                        "has_audio": f.get("acodec") != "none",
                        "fps": f.get("fps"),
                        "filesize": f.get("filesize") or f.get("filesize_approx"),
                    })

                return {
                    "success": True,
                    "title": title,
                    "platform": platform.value,
                    "formats": formats,
                }

        except ImportError:
            return {"success": False, "error": "yt-dlp Python module not installed", "formats": []}
        except Exception as e:
            return {"success": False, "error": str(e), "formats": []}

    def _extract_via_binary(self, url: str, platform: Platform) -> dict:
        """Extract info using yt-dlp binary via subprocess."""
        cmd = [
            self._yt_dlp,
            "--dump-json",
            "--no-warnings",
            "--no-download",
            url,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip(), "formats": []}

            data = json.loads(result.stdout)
            title = data.get("title", url)
            formats = []

            for f in data.get("formats", []):
                formats.append({
                    "format_id": f.get("format_id", ""),
                    "label": f.get("format_note", f.get("resolution", "unknown")),
                    "quality": f.get("resolution", "unknown"),
                    "ext": f.get("ext", "unknown"),
                    "has_video": f.get("vcodec") != "none",
                    "has_audio": f.get("acodec") != "none",
                    "fps": f.get("fps"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                })

            return {
                "success": True,
                "title": title,
                "platform": platform.value,
                "formats": formats,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Extraction timed out", "formats": []}
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid response from yt-dlp", "formats": []}
        except Exception as e:
            return {"success": False, "error": str(e), "formats": []}

    # ─── Internal: Progress Parsing ───────────────────────────────────────────

    def _parse_progress_line(self, task: DownloadTask, line: str):
        """Parse yt-dlp progress output and update task."""
        if not line:
            return

        # yt-dlp progress format: [download]  42.3% of  120.50MiB at  5.23MiB/s ETA 00:15
        m = re.search(
            r'\[download\]\s+([\d.]+)%\s+of\s+~?([\d.]+\w+)\s+at\s+([\d.]+\w+/s)\s+ETA\s+(\S+)',
            line
        )
        if m:
            pct = float(m.group(1))
            total = m.group(2)
            speed = m.group(3)
            eta = m.group(4)
            self.update_task(task.id, progress=pct, total_size=total,
                             speed=speed, eta=eta, downloaded=f"{pct:.1f}%")
            return

        # Simpler format: [download]  42.3% of  120.50MiB
        m = re.search(r'\[download\]\s+([\d.]+)%\s+of\s+~?([\d.]+\w+)', line)
        if m:
            self.update_task(task.id, progress=float(m.group(1)),
                             total_size=m.group(2))
            return

        # Destination line: [download] Destination: /path/to/file.mp4
        m = re.search(r'\[download\]\s+Destination:\s+(.+)', line)
        if m:
            self.update_task(task.id, output_path=m.group(1).strip())
            return

        # Merge line
        if "[Merger]" in line or "Merging" in line:
            self.update_task(task.id, status=DownloadStatus.PROCESSING)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _find_downloaded_file(self, directory: str, title_hint: str) -> Optional[str]:
        """Find the most recently downloaded file in a directory."""
        if not os.path.isdir(directory):
            return None

        files = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and not f.startswith(".")
        ]
        if not files:
            return None

        # Return most recently modified
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]

    @staticmethod
    def _sanitize(name: str) -> str:
        """Sanitize a filename."""
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
        name = name.strip(". ")
        return name or "download"

    @staticmethod
    def _has_ytdlp_module() -> bool:
        try:
            import yt_dlp
            return True
        except ImportError:
            return False

    def _emit(self, task: DownloadTask):
        """Notify the UI callback about a task update."""
        if self.progress_callback:
            try:
                self.progress_callback(task)
            except Exception as e:
                logger.debug(f"Progress callback error: {e}")
