"""
Fast Multi-Threaded Download Engine (IDM-style)
Uses HTTP Range requests to download file chunks in parallel,
then assembles them into the final file.

Features:
  - Automatic Range request detection (HEAD probe)
  - Configurable thread count (default 16)
  - Chunk-level progress tracking
  - Speed calculation (bytes/sec)
  - Automatic fallback to single-threaded if Range not supported
"""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable

import requests

from aegis_vault.utils.logger import logger

DEFAULT_THREADS = 16
CHUNK_SIZE = 2 * 1024 * 1024  # 2 MB per chunk (minimum split unit)
SINGLE_THREAD_THRESHOLD = 1024 * 1024  # Files < 1 MB stay single-threaded


class FastDownloader:
    """
    IDM-style parallel download engine.

    Usage:
        dl = FastDownloader()
        result = dl.download(url, "/path/to/save", progress_callback=cb)
    """

    def __init__(self, max_threads: int = DEFAULT_THREADS, timeout: int = 30):
        self.max_threads = max_threads
        self.timeout = timeout
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_threads,
            pool_maxsize=max_threads,
            max_retries=1,
        )
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    def download(
        self,
        url: str,
        save_path: str,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        headers: Optional[dict] = None,
    ) -> dict:
        """
        Download a file from url to save_path using parallel chunks.

        Args:
            url: The download URL
            save_path: Full path to save the file
            progress_callback: Optional callback(downloaded_bytes, total_bytes, speed_bps)
            headers: Optional extra headers for the request

        Returns:
            dict with keys: success, file_path, file_name, file_size, error, speed_bps
        """
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        try:
            # Probe the server with HEAD to check Range support and get file size
            head_resp = self._session.head(
                url, headers=headers, timeout=self.timeout, allow_redirects=True
            )

            total_size = int(head_resp.headers.get("Content-Length", 0))
            accept_ranges = head_resp.headers.get("Accept-Ranges", "").lower() == "bytes"
            server_status = head_resp.status_code

            # If HEAD fails (405, 403, etc.), try GET with stream and read size
            if server_status not in (200, 206):
                head_resp = self._session.get(
                    url, headers=headers, timeout=self.timeout,
                    allow_redirects=True, stream=True,
                )
                total_size = int(head_resp.headers.get("Content-Length", 0))
                accept_ranges = head_resp.headers.get("Accept-Ranges", "").lower() == "bytes"
                head_resp.close()

            filename = self._extract_filename(url, head_resp if server_status in (200, 206) else None)

            if total_size <= 0:
                logger.warning("Server did not provide Content-Length — single-threaded fallback")
                return self._download_single_thread(url, save_path, progress_callback, headers)

            if total_size < SINGLE_THREAD_THRESHOLD or not accept_ranges:
                logger.info(
                    f"Single-threaded: {'small file' if total_size < SINGLE_THREAD_THRESHOLD else 'no Range support'} "
                    f"({total_size} bytes)"
                )
                return self._download_single_thread(url, save_path, progress_callback, headers)

            # ── Multi-threaded download ──
            return self._download_parallel(
                url, save_path, total_size, progress_callback, headers
            )

        except Exception as e:
            logger.error(f"FastDownloader failed: {e}, falling back to single-threaded")
            return self._download_single_thread(url, save_path, progress_callback, headers)

    # ─── Parallel (IDM-style) download ───────────────────────────────────

    def _download_parallel(
        self, url: str, save_path: str, total_size: int,
        progress_callback, extra_headers,
    ) -> dict:
        num_threads = min(self.max_threads, max(1, total_size // CHUNK_SIZE))
        chunk_size = total_size // num_threads

        logger.info(
            f"Parallel download: {total_size} bytes in {num_threads} chunks "
            f"({chunk_size} bytes each)"
        )

        # Pre-allocate the file
        with open(save_path, "wb") as f:
            f.truncate(total_size)

        downloaded_counter = {"bytes": 0}
        lock = threading.Lock()
        start_time = time.time()

        def _progress_reporter():
            """Periodically report progress."""
            while True:
                time.sleep(0.3)
                with lock:
                    done = downloaded_counter["bytes"]
                elapsed = time.time() - start_time
                speed = done / elapsed if elapsed > 0 else 0
                if progress_callback:
                    try:
                        progress_callback(done, total_size, speed)
                    except Exception:
                        pass
                if done >= total_size:
                    break

        progress_thread = threading.Thread(target=_progress_reporter, daemon=True)
        progress_thread.start()

        def _download_chunk(chunk_index: int) -> int:
            start = chunk_index * chunk_size
            end = start + chunk_size - 1 if chunk_index < num_threads - 1 else total_size - 1
            retries = 3

            for attempt in range(retries):
                try:
                    h = dict(extra_headers or {})
                    h["Range"] = f"bytes={start}-{end}"

                    resp = self._session.get(
                        url, headers=h, timeout=self.timeout, stream=True
                    )

                    if resp.status_code not in (200, 206):
                        raise Exception(f"HTTP {resp.status_code}")

                    chunk_downloaded = 0
                    with open(save_path, "r+b") as f:
                        f.seek(start)
                        for data in resp.iter_content(chunk_size=64 * 1024):
                            if data:
                                f.write(data)
                                chunk_downloaded += len(data)
                                with lock:
                                    downloaded_counter["bytes"] += len(data)
                    resp.close()
                    return chunk_downloaded

                except Exception as e:
                    logger.warning(
                        f"Chunk {chunk_index} attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < retries - 1:
                        time.sleep(1)

            logger.error(f"Chunk {chunk_index} failed after {retries} retries")
            return 0

        # Execute all chunks in parallel
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {
                executor.submit(_download_chunk, i): i
                for i in range(num_threads)
            }
            for future in as_completed(futures):
                future.result()  # propagate exceptions

        elapsed = time.time() - start_time
        final_size = os.path.getsize(save_path)
        speed = final_size / elapsed if elapsed > 0 else 0

        if progress_callback:
            try:
                progress_callback(final_size, total_size, speed)
            except Exception:
                pass

        logger.info(
            f"Parallel download complete: {final_size} bytes "
            f"in {elapsed:.1f}s ({speed / 1024 / 1024:.1f} MB/s)"
        )

        return {
            "success": True,
            "file_path": save_path,
            "file_name": os.path.basename(save_path),
            "file_size": final_size,
            "error": "",
            "speed_bps": speed,
        }

    # ─── Single-threaded fallback ─────────────────────────────────────────

    def _download_single_thread(
        self, url: str, save_path: str, progress_callback, extra_headers,
    ) -> dict:
        start_time = time.time()
        downloaded = 0

        def _cb(recv, total):
            nonlocal downloaded
            downloaded = recv
            elapsed = time.time() - start_time
            speed = recv / elapsed if elapsed > 0 else 0
            if progress_callback:
                try:
                    progress_callback(recv, total, speed)
                except Exception:
                    pass

        try:
            resp = self._session.get(
                url, headers=extra_headers or {}, timeout=self.timeout,
                stream=True, allow_redirects=True,
            )
            if resp.status_code not in (200, 206):
                raise Exception(f"HTTP {resp.status_code}")

            total = int(resp.headers.get("Content-Length", 0))

            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        _cb(downloaded, total)
            resp.close()

            elapsed = time.time() - start_time
            speed = downloaded / elapsed if elapsed > 0 else 0

            return {
                "success": True,
                "file_path": save_path,
                "file_name": os.path.basename(save_path),
                "file_size": downloaded,
                "error": "",
                "speed_bps": speed,
            }

        except Exception as e:
            return {
                "success": False,
                "file_path": save_path,
                "file_name": os.path.basename(save_path),
                "file_size": 0,
                "error": str(e),
                "speed_bps": 0,
            }

    # ─── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_filename(url: str, resp=None) -> str:
        # Try Content-Disposition
        if resp is not None:
            cd = resp.headers.get("Content-Disposition", "")
            if cd:
                import re
                from urllib.parse import unquote
                m = re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
                if m:
                    return unquote(m.group(1).strip())
                m = re.search(r"filename\*\s*=\s*(?:UTF-8''|utf-8'')(.+?)(?:;|$)", cd)
                if m:
                    return unquote(m.group(1).strip())

        # Try URL path
        from urllib.parse import urlparse, unquote as uq
        path = uq(urlparse(url).path)
        name = os.path.basename(path)
        if name and "." in name:
            return name
        return "downloaded_file"


# ─── Module-level convenience ──────────────────────────────────────────

_default_downloader = None

def get_downloader(max_threads: int = DEFAULT_THREADS) -> FastDownloader:
    """Get or create the module-level singleton downloader."""
    global _default_downloader
    if _default_downloader is None:
        _default_downloader = FastDownloader(max_threads=max_threads)
    return _default_downloader

def fast_download(
    url: str,
    save_path: str,
    progress_callback: Optional[Callable] = None,
    headers: Optional[dict] = None,
    max_threads: int = DEFAULT_THREADS,
) -> dict:
    """Convenience function for one-shot parallel downloads."""
    dl = get_downloader(max_threads)
    return dl.download(url, save_path, progress_callback, headers)
