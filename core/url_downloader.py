"""
URL Downloader Engine - Enhanced v2.0.0
Handles downloading files from various cloud storage and direct links.
Supported providers:
  - Direct HTTP/HTTPS links
  - Google Drive (public/shared links)
  - Mediafire (public links)
  - Terabox (public links)
  - Dropbox (public/shared links)
  - OneDrive (public/shared links)
  - MEGA (public links)
  - pCloud (public links)
  - WeTransfer (public links)
  - Generic cloud providers (any URL that resolves to a downloadable file)
"""

import os
import re
import json
import tempfile
from typing import Optional
import requests
from urllib.parse import urlparse, parse_qs, unquote
from aegis_vault.utils.logger import logger

# Common browser-like headers to bypass basic bot detection
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
}

# Maximum redirect hops to follow manually
MAX_REDIRECTS = 10


class URLDownloader:
    """Downloads files from URLs into a local temp directory, resolving
    provider-specific redirect chains when necessary."""

    def __init__(self, download_dir: Optional[str] = None):
        self.download_dir = download_dir or tempfile.mkdtemp(prefix="aegis_url_")
        os.makedirs(self.download_dir, exist_ok=True)

    # ─── Public API ──────────────────────────────────────────────────────
    def download(self, url: str, progress_callback=None) -> dict:
        """
        Download a file from *url* to a temp location.

        Returns a dict:
            {
                "success": True/False,
                "file_path": "/absolute/path/to/downloaded_file",
                "file_name": "original_name.ext",
                "file_size": 12345,
                "error": ""  (or error message)
            }
        """
        url = url.strip()
        if not url:
            return self._error("URL is empty.")

        try:
            provider = self._detect_provider(url)
            logger.info(f"Detected provider: {provider} for URL: {url}")

            if provider == "google_drive":
                return self._download_google_drive(url, progress_callback)
            elif provider == "mediafire":
                return self._download_mediafire(url, progress_callback)
            elif provider == "terabox":
                return self._download_terabox(url, progress_callback)
            elif provider == "mega":
                return self._download_mega(url, progress_callback)
            elif provider == "megadb":
                return self._download_megadb(url, progress_callback)
            elif provider == "dropbox":
                return self._download_dropbox(url, progress_callback)
            elif provider == "onedrive":
                return self._download_onedrive(url, progress_callback)
            elif provider in ("mega", "pcloud", "wetransfer", "box", "sendspace", "zippyshare", "fourshared"):
                # These providers generally work with direct download approach
                # or require their own API/client which we handle as direct download with HTML parsing
                return self._download_direct(url, progress_callback)
            else:
                return self._download_direct(url, progress_callback)

        except Exception as e:
            logger.error(f"URL download failed: {e}")
            return self._error(str(e))

    # ─── Provider Detection ──────────────────────────────────────────────
    @staticmethod
    def _detect_provider(url: str) -> str:
        parsed = urlparse(url)
        host = parsed.hostname or ""

        if "drive.google.com" in host or "docs.google.com" in host:
            return "google_drive"
        if "mediafire.com" in host:
            return "mediafire"
        if "terabox" in host or "teraboxapp" in host or "1024tera" in host or "freeterabox" in host:
            return "terabox"
        if "dropbox.com" in host or "dl.dropboxusercontent.com" in host:
            return "dropbox"
        if "1drv.ms" in host or "onedrive.live.com" in host or "sharepoint.com" in host:
            return "onedrive"
        if "mega.nz" in host or "mega.io" in host:
            return "mega"
        if "pcloud.com" in host or "filelink.io" in host:
            return "pcloud"
        if "wetransfer.com" in host or "we.tl" in host:
            return "wetransfer"
        if "box.com" in host:
            return "box"
        if "sendspace.com" in host:
            return "sendspace"
        if "zippyshare.com" in host:
            return "zippyshare"
        if "4shared.com" in host:
            return "fourshared"
        if "megadb.net" in host:
            return "megadb"
        return "direct"

    # ─── Google Drive ────────────────────────────────────────────────────
    def _download_google_drive(self, url: str, progress_callback) -> dict:
        """
        Handles /file/d/<ID>/..., open?id=<ID>, and /uc?id=<ID> style links.
        Follows the virus-scan confirmation redirect for large files.
        """
        file_id = self._extract_gdrive_id(url)
        if not file_id:
            return self._error("Could not extract Google Drive file ID from URL.")

        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        resp = session.get(download_url, stream=True, allow_redirects=True, timeout=30)

        # Google shows a confirmation page for large files
        if resp.headers.get("Content-Type", "").startswith("text/html"):
            confirm_token = self._find_gdrive_confirm_token(resp)
            if confirm_token:
                download_url = (
                    f"https://drive.google.com/uc?export=download"
                    f"&id={file_id}&confirm={confirm_token}"
                )
                resp = session.get(download_url, stream=True, allow_redirects=True, timeout=30)
            else:
                # Try the uuid-based download form
                form_action = re.search(r'action="(https://drive\.usercontent\.google\.com/download[^"]+)"', resp.text)
                if form_action:
                    download_url = form_action.group(1).replace("&amp;", "&")
                    resp = session.get(download_url, stream=True, allow_redirects=True, timeout=30)

        if resp.status_code != 200:
            return self._error(f"Google Drive returned HTTP {resp.status_code}")

        filename = self._filename_from_headers(resp) or f"gdrive_{file_id}"
        return self._stream_to_file(resp, filename, progress_callback)

    @staticmethod
    def _extract_gdrive_id(url: str) -> Optional[str]:
        # /file/d/<ID>/...
        m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
        if m:
            return m.group(1)
        # open?id=<ID> or uc?id=<ID>
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "id" in qs:
            return qs["id"][0]
        return None

    @staticmethod
    def _find_gdrive_confirm_token(resp) -> Optional[str]:
        for key, value in resp.cookies.items():
            if key.startswith("download_warning"):
                return value
        m = re.search(r'confirm=([0-9A-Za-z_-]+)&', resp.text)
        if m:
            return m.group(1)
        return None

    # ─── Mediafire ───────────────────────────────────────────────────────
    def _download_mediafire(self, url: str, progress_callback) -> dict:
        """
        Scrape the Mediafire download page for the real download button URL.
        """
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return self._error(f"Mediafire page returned HTTP {resp.status_code}")

        # The real download link lives in an <a> tag with id="downloadButton"
        # or a JS variable.
        download_url = None

        # Method 1: aria-label or id="downloadButton"
        m = re.search(r'href="(https?://download\d*\.mediafire\.com/[^"]+)"', resp.text)
        if m:
            download_url = m.group(1)

        if not download_url:
            # Method 2: Look for the direct link in a script block
            m = re.search(r"window\.location\.href\s*=\s*'(https?://download[^']+)'", resp.text)
            if m:
                download_url = m.group(1)

        if not download_url:
            # Method 3: any download*.mediafire.com link
            m = re.search(r'(https?://download\d*\.mediafire\.com/[^\s"\'<>]+)', resp.text)
            if m:
                download_url = m.group(1)

        if not download_url:
            return self._error("Could not find the Mediafire download link. The file may be private or deleted.")

        resp = session.get(download_url, stream=True, timeout=30)
        if resp.status_code != 200:
            return self._error(f"Mediafire download returned HTTP {resp.status_code}")

        filename = self._filename_from_headers(resp) or self._filename_from_url(download_url) or "mediafire_file"
        return self._stream_to_file(resp, filename, progress_callback)

    # ─── Terabox ─────────────────────────────────────────────────────────
    def _download_terabox(self, url: str, progress_callback) -> dict:
        """
        Terabox / 1024Tera / FreeTerabox links.
        These typically have API endpoints or redirect chains.
        We attempt to resolve the final download URL by following redirects.
        """
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        # First, visit the share page to get cookies
        resp = session.get(url, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            return self._error(f"Terabox page returned HTTP {resp.status_code}")

        # Try to extract the direct download link from the page source
        download_url = None

        # Look for common patterns in Terabox page source
        patterns = [
            r'"dlink"\s*:\s*"(https?://[^"]+)"',
            r'"downloadLink"\s*:\s*"(https?://[^"]+)"',
            r'href="(https?://[^"]*terabox[^"]*download[^"]*)"',
            r'window\.open\(["\']?(https?://[^"\')\s]+download[^"\')\s]*)',
        ]

        for pattern in patterns:
            m = re.search(pattern, resp.text)
            if m:
                download_url = m.group(1).replace("\\u002F", "/").replace("\\/", "/")
                break

        if not download_url:
            # Fallback: try API endpoint
            # Extract surl from the URL
            parsed = urlparse(url)
            surl = parse_qs(parsed.query).get("surl", [None])[0]
            short_id = parsed.path.rstrip("/").split("/")[-1] if not surl else surl

            api_url = f"https://www.terabox.com/api/shorturlinfo?shorturl={short_id}&root=1"
            api_resp = session.get(api_url, timeout=15)
            if api_resp.status_code == 200:
                try:
                    data = api_resp.json()
                    file_list = data.get("list", [])
                    if file_list:
                        download_url = file_list[0].get("dlink")
                except Exception:
                    pass

        if not download_url:
            return self._error(
                "Could not resolve the Terabox download link. "
                "The file may be private, password-protected, or the link has expired."
            )

        resp = session.get(download_url, stream=True, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return self._error(f"Terabox download returned HTTP {resp.status_code}")

        filename = self._filename_from_headers(resp) or self._filename_from_url(download_url) or "terabox_file"
        return self._stream_to_file(resp, filename, progress_callback)

    # ─── MEGA ────────────────────────────────────────────────────────────
    def _download_mega(self, url: str, progress_callback) -> dict:
        """
        Download files from MEGA using mega-public-client library.
        Supports public file and folder links with automatic decryption.
        """
        try:
            from mega_client import MegaClient
        except ImportError:
            return self._error(
                "MEGA downloads require mega-public-client. "
                "Install it: pip install mega-public-client"
            )

        logger.info(f"MEGA: Downloading from {url[:60]}...")

        try:
            with MegaClient() as client:
                result = client.download_file(url, self.download_dir)

            filename = os.path.basename(result.path)
            file_size = os.path.getsize(result.path)

            logger.info(f"MEGA: Downloaded {filename} ({file_size} bytes)")

            return {
                "success": True,
                "file_path": result.path,
                "file_name": filename,
                "file_size": file_size,
                "error": "",
            }

        except Exception as e:
            err_msg = str(e)
            logger.error(f"MEGA download failed: {err_msg}")

            if "not found" in err_msg.lower() or "404" in err_msg:
                return self._error("MEGA: File not found or link expired.")
            elif "access" in err_msg.lower() or "denied" in err_msg.lower():
                return self._error("MEGA: Access denied. File may be private.")
            elif "decrypt" in err_msg.lower():
                return self._error("MEGA: Decryption failed. Key may be invalid.")
            else:
                return self._error(f"MEGA download failed: {err_msg}")

    # ─── MegaDB ─────────────────────────────────────────────────────────
    def _download_megadb(self, url: str, progress_callback) -> dict:
        """
        MegaDB (megadb.net) uses Cloudflare Turnstile protection which requires
        a full browser to solve. Direct HTTP downloads are not possible.

        Returns a helpful error message with a workaround.
        """
        return self._error(
            "MegaDB uses Cloudflare Turnstile protection that cannot be "
            "bypassed with direct HTTP requests.\n\n"
            "Workaround:\n"
            "1. Open the MegaDB link in your browser\n"
            "2. Solve the Turnstile challenge and download the file\n"
            "3. Use 'Upload to Vault' to upload the downloaded file"
        )

    # ─── Dropbox ─────────────────────────────────────────────────────────
    def _download_dropbox(self, url: str, progress_callback) -> dict:
        """
        Handles Dropbox shared links.
        Convert web URL to direct download URL by replacing dl=0 with dl=1
        """
        # Convert to direct download URL
        if "?dl=0" in url:
            download_url = url.replace("?dl=0", "?dl=1")
        elif "?dl=1" not in url:
            download_url = url + ("&" if "?" in url else "?") + "dl=1"
        else:
            download_url = url

        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        resp = session.get(download_url, stream=True, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return self._error(f"Dropbox download returned HTTP {resp.status_code}")

        filename = self._filename_from_headers(resp) or self._filename_from_url(url) or "dropbox_file"
        return self._stream_to_file(resp, filename, progress_callback)

    # ─── OneDrive ────────────────────────────────────────────────────────
    def _download_onedrive(self, url: str, progress_callback) -> dict:
        """
        Handles OneDrive/SharePoint shared links.
        Convert share URL to direct download URL.
        """
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        # For 1drv.ms shortened links, first resolve to full URL
        if "1drv.ms" in url:
            resp = session.head(url, allow_redirects=True, timeout=30)
            url = resp.url

        # Convert OneDrive share URL to direct download
        # Replace /view with /download or add download=1 parameter
        if "/view" in url:
            download_url = url.replace("/view", "/download")
        elif "sharepoint.com" in url:
            download_url = url + ("&" if "?" in url else "?") + "download=1"
        else:
            # Try adding download parameter
            download_url = url + ("&" if "?" in url else "?") + "download=1"

        resp = session.get(download_url, stream=True, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return self._error(f"OneDrive download returned HTTP {resp.status_code}")

        filename = self._filename_from_headers(resp) or self._filename_from_url(url) or "onedrive_file"
        return self._stream_to_file(resp, filename, progress_callback)

    # ─── Direct / Generic Download ───────────────────────────────────────
    def _download_direct(self, url: str, progress_callback) -> dict:
        """
        Follow redirects and download whatever the final URL serves.
        Uses IDM-style parallel download for maximum speed.
        """
        from aegis_vault.core.fast_downloader import fast_download

        # First, resolve the final URL (handle HTML pages with embedded download links)
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        resp = session.get(url, stream=True, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return self._error(f"Server returned HTTP {resp.status_code}")

        content_type = resp.headers.get("Content-Type", "")
        final_url = url

        if "text/html" in content_type:
            html = resp.text
            download_url = self._find_download_link_in_html(html, url)
            if download_url:
                final_url = download_url
            else:
                resp.close()
                return self._error(
                    "The URL returned an HTML page instead of a file. "
                    "It may require authentication or the file may not be publicly available."
                )
        resp.close()

        # Determine filename
        filename = self._filename_from_url(final_url) or "downloaded_file"
        filename = self._sanitize_filename(filename)

        # Avoid overwriting
        file_path = os.path.join(self.download_dir, filename)
        base, ext = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{ext}"
            counter += 1

        def _progress(downloaded, total, speed_bps):
            if progress_callback and total > 0:
                progress_callback(downloaded, total)

        result = fast_download(
            final_url, file_path,
            progress_callback=_progress,
            headers=BROWSER_HEADERS,
            max_threads=16,
        )

        if result["success"]:
            result["file_name"] = filename
            logger.info(
                f"Downloaded {filename} ({result['file_size']} bytes, "
                f"{result.get('speed_bps', 0) / 1024 / 1024:.1f} MB/s)"
            )

        return result

    @staticmethod
    def _find_download_link_in_html(html: str, source_url: str) -> Optional[str]:
        """Try common patterns to extract a real download link from an HTML page."""
        patterns = [
            r'href="(https?://[^"]+download[^"]*)"',
            r'<a[^>]*id="download[^"]*"[^>]*href="([^"]+)"',
            r'window\.location\.href\s*=\s*["\']?(https?://[^"\';\s]+)',
            r'data-url="(https?://[^"]+)"',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                link = m.group(1)
                # Make sure it's not the same page
                if link != source_url:
                    return link
        return None

    # ─── Shared Helpers ──────────────────────────────────────────────────
    def _stream_to_file(self, resp, filename: str, progress_callback) -> dict:
        """Stream a response body to a file on disk with progress reporting."""
        # Sanitize filename
        filename = self._sanitize_filename(filename)
        file_path = os.path.join(self.download_dir, filename)

        # Avoid overwriting — add a suffix if needed
        base, ext = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{ext}"
            counter += 1

        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 64 * 1024  # 64 KB chunks

        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)

        actual_size = os.path.getsize(file_path)
        logger.info(f"Downloaded {filename} ({actual_size} bytes) to {file_path}")

        return {
            "success": True,
            "file_path": file_path,
            "file_name": filename,
            "file_size": actual_size,
            "error": "",
        }

    @staticmethod
    def _filename_from_headers(resp) -> Optional[str]:
        cd = resp.headers.get("Content-Disposition", "")
        if not cd:
            return None

        # filename*=UTF-8''encoded_name
        m = re.search(r"filename\*\s*=\s*(?:UTF-8''|utf-8'')(.+?)(?:;|$)", cd, re.IGNORECASE)
        if m:
            return unquote(m.group(1).strip().strip('"'))

        # filename="name"
        m = re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
        if m:
            return unquote(m.group(1).strip().strip('"'))

        return None

    @staticmethod
    def _filename_from_url(url: str) -> Optional[str]:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        name = os.path.basename(path)
        if name and "." in name:
            return name
        return None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        # Remove characters that are invalid in filenames
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
        name = name.strip(". ")
        if not name:
            name = "downloaded_file"
        # Limit length
        if len(name) > 200:
            base, ext = os.path.splitext(name)
            name = base[:200 - len(ext)] + ext
        return name

    @staticmethod
    def _error(msg: str) -> dict:
        return {
            "success": False,
            "file_path": "",
            "file_name": "",
            "file_size": 0,
            "error": msg,
        }
