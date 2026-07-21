import requests
import internetarchive as ia
import os
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from aegis_vault.utils.logger import logger

# Known working folders — used as instant fallback while network loads
_KNOWN_FOLDERS = [
    "aegis_photos", "aegis_vault", "naya-folder-1234", "samar-vault",
    "aegis-cloud", "samar-ka-folder2026", "world_20260524", "uwp4294310"
]

class IAStorageEngine:
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self._metadata_cache = {}  # bucket -> (files, timestamp)
        self._folder_cache = None  # cached folder list
        self._folder_cache_time = 0
        self._cache_ttl = 60  # seconds
        self._local_cache_path = os.path.expanduser("~/.aegis_folders.json")
        # Persistent session with connection pooling for faster requests
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2
        )
        self._session.mount('https://', adapter)
        self._session.mount('http://', adapter)
        self._session.headers.update({
            'User-Agent': 'AegisVault/3.5.5',
            'Accept': 'application/json',
        })
        # Load local cache instantly on init
        self._load_local_cache()

    def _load_local_cache(self):
        """Load folder list from local disk — instant, no network."""
        try:
            if os.path.exists(self._local_cache_path):
                with open(self._local_cache_path, "r") as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    self._folder_cache = data
                    self._folder_cache_time = time.time()
                    logger.info(f"✓ Loaded {len(data)} folders from local cache")
                    return
        except Exception:
            pass
        # Use known folders as ultimate fallback
        self._folder_cache = list(_KNOWN_FOLDERS)
        self._folder_cache_time = time.time()
        logger.info(f"✓ Using known folders ({len(_KNOWN_FOLDERS)} folders)")

    def _save_local_cache(self, folders):
        """Save folder list to local disk for next startup."""
        try:
            with open(self._local_cache_path, "w") as f:
                json.dump(folders, f)
        except Exception:
            pass

    def scan_user_folders(self) -> list:
        """
        Scan for user's folders from Internet Archive.
        Returns cached/local list immediately, refreshes in background.
        """
        # Return cached if fresh (5 min)
        if self._folder_cache is not None and (time.time() - self._folder_cache_time) < 300:
            logger.info(f"✓ Using cached folder list ({len(self._folder_cache)} folders)")
            return self._folder_cache

        # Return local cache immediately, refresh in background
        if self._folder_cache is not None:
            logger.info(f"✓ Using local cache ({len(self._folder_cache)} folders), refreshing...")
            threading.Thread(target=self._refresh_folders, daemon=True).start()
            return self._folder_cache

        # No cache at all — use known folders and refresh
        self._folder_cache = list(_KNOWN_FOLDERS)
        threading.Thread(target=self._refresh_folders, daemon=True).start()
        return self._folder_cache

    def _refresh_folders(self):
        """Background refresh from archive.org."""
        try:
            search_url = "https://archive.org/advancedsearch.php"
            params = {
                'q': 'uploader:"sarvar975853@gmail.com"',
                'fl[]': 'identifier,title,addeddate',
                'rows': '100',
                'output': 'json',
                'sort[]': 'addeddate desc'
            }
            response = self._session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            res = response.json()
            docs = res.get('response', {}).get('docs', [])
            folders = [d['identifier'] for d in docs if d.get('identifier')]

            if folders:
                self._folder_cache = folders
                self._folder_cache_time = time.time()
                self._save_local_cache(folders)
                logger.info(f"✅ Refreshed {len(folders)} folders from archive.org")
            else:
                logger.warning("⚠️  Archive.org returned 0 folders, keeping local cache")
        except Exception as e:
            logger.warning(f"⚠️  Background refresh failed: {e}, keeping local cache")
    
    def _get_user_email_from_credentials(self) -> str:
        """Extract email from S3 credentials"""
        try:
            logger.info("🔐 Getting user email from credentials...")
            session = ia.get_session(config={
                's3': {
                    'access': self.access_key,
                    'secret': self.secret_key
                }
            })
            
            # Check for email in session
            if hasattr(session, 'user_email') and session.user_email:
                logger.info(f"✓ Found user_email: {session.user_email}")
                return session.user_email
            
        except Exception as e:
            logger.debug(f"Could not get email: {e}")
        
        return None
    
    def _search_by_uploader(self, uploader_email: str) -> list:
        """Search for all items uploaded by the specific email"""
        user_items = []
        try:
            logger.info(f"📋 Searching for items uploaded by {uploader_email}...")
            
            search_url = "https://archive.org/advancedsearch.php"
            params = {
                'q': f'uploader:"{uploader_email}"',
                'fl[]': 'identifier,title,addeddate',
                'rows': '100',
                'output': 'json',
                'sort[]': 'addeddate desc'
            }
            
            logger.debug(f"Query: uploader:{uploader_email}")
            
            # Retry logic with exponential backoff
            last_error = None
            for attempt in range(3):
                try:
                    response = self._session.get(search_url, params=params, timeout=15)
                    response.raise_for_status()
                    res = response.json()
                    response_obj = res.get('response', {})
                    num_found = response_obj.get('numFound', 0)
                    docs = response_obj.get('docs', [])
                    
                    logger.info(f"✓ Query returned {num_found} total, {len(docs)} in this batch")
                    
                    for doc in docs:
                        identifier = doc.get('identifier')
                        title = doc.get('title', identifier)
                        if identifier:
                            user_items.append(identifier)
                            logger.debug(f"  • {identifier} ({title})")
                    
                    break  # Success, exit retry loop
                    
                except requests.exceptions.Timeout:
                    last_error = f"Attempt {attempt + 1}/3: Connection timed out"
                    logger.warning(f"⚠️  {last_error}")
                    if attempt < 2:
                        time.sleep(0.5)  # Fast retry
                    continue
                except requests.exceptions.ConnectionError as e:
                    last_error = f"Attempt {attempt + 1}/3: Connection failed"
                    logger.warning(f"⚠️  {last_error}")
                    if attempt < 2:
                        time.sleep(0.5)
                    continue
                except Exception as e:
                    last_error = f"Attempt {attempt + 1}/3: {e}"
                    logger.warning(f"⚠️  {last_error}")
                    if attempt < 2:
                        time.sleep(0.5)
                    continue
            
            if not user_items and last_error:
                logger.error(f"Error searching by uploader: {last_error}")
        
        except Exception as e:
            logger.error(f"Error searching by uploader: {e}")
        
        return user_items

    def _get_bucket_metadata(self, bucket_id: str) -> dict:
        """
        Fetch and cache raw metadata for a bucket using the shared session.
        Both get_files_in_bucket and get_files_unencrypted share this cache
        so the same /metadata/ endpoint is hit only ONCE per bucket.
        """
        now = time.time()

        # Check in-memory cache (10 min TTL)
        if bucket_id in self._metadata_cache:
            cached_data, cached_at = self._metadata_cache[bucket_id]
            if now - cached_at < 600:
                return cached_data

        url = f"https://archive.org/metadata/{bucket_id}"
        for attempt in range(3):
            try:
                response = self._session.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    self._metadata_cache[bucket_id] = (data, now)
                    return data
                elif response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited on {bucket_id}, waiting {wait}s")
                    time.sleep(wait)
                    continue
                else:
                    logger.warning(f"HTTP {response.status_code} for {bucket_id}")
                    return None
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                wait = 1 + attempt
                logger.warning(f"Attempt {attempt+1}/3 failed for {bucket_id}: {e}")
                if attempt < 2:
                    time.sleep(wait)
                continue
            except Exception as e:
                logger.error(f"Error fetching metadata for {bucket_id}: {e}")
                return None
        return None

    def get_files_in_bucket(self, bucket_id: str) -> list:
        """
        Enhanced file listing with better metadata handling.
        Returns list of encrypted files in the specified bucket/folder.
        """
        logger.info(f"Fetching metadata for bucket: {bucket_id}")

        try:
            data = self._get_bucket_metadata(bucket_id)
            if data is None:
                return []
            
            files = data.get("files", [])
            
            clean_list = []
            for f in files:
                name = f.get("name", "")
                # Only show .enc files (our encrypted files)
                if name.endswith(".enc"):
                    size_bytes = f.get("size", 0)
                    # Convert size to human-readable format
                    size_str = self._format_size(size_bytes) if isinstance(size_bytes, (int, str)) else "Unknown"
                    
                    clean_list.append({
                        "name": name[:-4],  # Remove .enc extension
                        "size": size_str,
                        "size_bytes": size_bytes,
                        "mtime": f.get("mtime", "Unknown"),
                        "format": f.get("format", "Unknown")
                    })
            
            logger.info(f"✓ Found {len(clean_list)} encrypted files in {bucket_id}")
            return clean_list
            
        except Exception as e:
            logger.error(f"Error fetching files for {bucket_id}: {e}")
            return []

    def get_files_unencrypted(self, bucket_id: str) -> list:
        """
        Returns list of non-encrypted files (no .enc extension) in the bucket.
        Used by the Files tab to browse unencrypted uploads.
        """
        logger.info(f"Fetching unencrypted files for bucket: {bucket_id}")
        
        try:
            data = self._get_bucket_metadata(bucket_id)
            if data is None:
                return []
            
            files = data.get("files", [])
            
            clean_list = []
            for f in files:
                name = f.get("name", "")
                # Skip .enc files, directories, and IA metadata files
                if (name.endswith(".enc") or name.endswith("/") 
                    or name.startswith("_") or name.startswith(".")):
                    continue
                
                size_bytes = f.get("size", 0)
                size_str = self._format_size(size_bytes) if isinstance(size_bytes, (int, str)) else "Unknown"
                
                clean_list.append({
                    "name": name,
                    "size": size_str,
                    "size_bytes": size_bytes,
                    "mtime": f.get("mtime", "Unknown"),
                    "format": f.get("format", "Unknown")
                })
            
            logger.info(f"✓ Found {len(clean_list)} unencrypted files in {bucket_id}")
            return clean_list

        except Exception as e:
            logger.error(f"Error fetching unencrypted files for {bucket_id}: {e}")
            return []

    def get_files_parallel(self, bucket_ids: list, max_workers: int = 16) -> dict:
        """
        Fetch metadata for multiple buckets in parallel.
        Returns {bucket_id: [files]} dict.
        Uses _get_bucket_metadata for caching so the cache stays consistent.
        """
        now = time.time()
        results = {}
        to_fetch = []

        for bid in bucket_ids:
            if bid in self._metadata_cache:
                cached_data, cached_at = self._metadata_cache[bid]
                if now - cached_at < self._cache_ttl:
                    files_raw = cached_data.get("files", []) if isinstance(cached_data, dict) else []
                    clean = []
                    for f in files_raw:
                        name = f.get("name", "")
                        if name.endswith(".enc"):
                            size_bytes = f.get("size", 0)
                            size_str = self._format_size(size_bytes) if isinstance(size_bytes, (int, str)) else "Unknown"
                            clean.append({
                                "name": name[:-4],
                                "size": size_str,
                                "size_bytes": size_bytes,
                                "mtime": f.get("mtime", "Unknown"),
                                "format": f.get("format", "Unknown"),
                            })
                    results[bid] = clean
                    continue
            to_fetch.append(bid)

        if not to_fetch:
            logger.info(f"✓ All {len(bucket_ids)} buckets served from cache")
            return results

        logger.info(f"⚡ Parallel fetch: {len(to_fetch)} buckets, {max_workers} workers")

        def _fetch_one(bid):
            data = self._get_bucket_metadata(bid)
            if data is None:
                return bid, []
            files_raw = data.get("files", [])
            clean = []
            for f in files_raw:
                name = f.get("name", "")
                if name.endswith(".enc"):
                    size_bytes = f.get("size", 0)
                    size_str = self._format_size(size_bytes) if isinstance(size_bytes, (int, str)) else "Unknown"
                    clean.append({
                        "name": name[:-4],
                        "size": size_str,
                        "size_bytes": size_bytes,
                        "mtime": f.get("mtime", "Unknown"),
                        "format": f.get("format", "Unknown"),
                    })
            return bid, clean

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_fetch_one, bid): bid for bid in to_fetch}
            for future in as_completed(futures):
                bid, files = future.result()
                results[bid] = files

        logger.info(f"✓ Parallel fetch complete: {len(results)} buckets")
        return results

    @staticmethod
    def _format_size(size_bytes) -> str:
        """Convert bytes to human-readable format."""
        try:
            size = int(size_bytes)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.2f} GB"
        except (ValueError, TypeError):
            return "Unknown"

    def upload_file(self, temp_encrypted_path: str, original_filename: str, bucket_id: str, progress_callback=None):
        logger.info(f"Uploading {original_filename}.enc to {bucket_id}")
        metadata = {
            'collection': 'opensource',
            'title': f'Encrypted App Backup Bundle - {bucket_id}',
            'mediatype': 'data',
            'description': 'Zero-knowledge client encrypted cloud repository.'
        }
        
        try:
            # Get file size for progress tracking
            file_size = os.path.getsize(temp_encrypted_path)
            
            # Custom progress callback wrapper
            def upload_progress(sent_bytes):
                if progress_callback:
                    progress_callback(sent_bytes, file_size)
            
            ia.upload(
                bucket_id, 
                files={original_filename + ".enc": temp_encrypted_path}, 
                metadata=metadata, 
                access_key=self.access_key, 
                secret_key=self.secret_key,
                verbose=True,
                checksum=True
            )
            
            # Report 100% completion
            if progress_callback:
                progress_callback(file_size, file_size)
            
            return f"https://archive.org/details/{bucket_id}"
        except Exception as e:
            logger.error(f"Upload failed for {original_filename}: {e}")
            raise

    def upload_file_raw(self, local_path: str, original_filename: str, bucket_id: str, progress_callback=None):
        """
        Upload a file without encryption (no .enc extension).
        Used when 'Upload without password' is enabled.
        """
        logger.info(f"Uploading {original_filename} (unencrypted) to {bucket_id}")
        metadata = {
            'collection': 'opensource',
            'title': f'App Backup Bundle - {bucket_id}',
            'mediatype': 'data',
            'description': 'Unencrypted cloud repository upload.'
        }
        
        try:
            file_size = os.path.getsize(local_path)
            
            ia.upload(
                bucket_id,
                files={original_filename: local_path},
                metadata=metadata,
                access_key=self.access_key,
                secret_key=self.secret_key,
                verbose=True,
                checksum=True
            )
            
            if progress_callback:
                progress_callback(file_size, file_size)
            
            return f"https://archive.org/details/{bucket_id}"
        except Exception as e:
            logger.error(f"Upload failed for {original_filename}: {e}")
            raise

    def download_file(self, bucket_id: str, file_name: str, save_path: str, progress_callback=None):
        from aegis_vault.core.fast_downloader import fast_download

        logger.info(f"Downloading {file_name}.enc from {bucket_id}")
        download_url = f"https://archive.org/download/{bucket_id}/{file_name}.enc"

        def _progress(downloaded, total, speed_bps):
            if progress_callback:
                progress_callback(downloaded, total)

        result = fast_download(download_url, save_path, progress_callback=_progress, max_threads=16)

        if not result["success"]:
            raise Exception(f"Download failed: {result['error']}")

        speed = result.get('speed_bps', 0)
        logger.info(f"✓ Downloaded {file_name} ({result['file_size']} bytes, {speed / 1024 / 1024:.1f} MB/s)")
        return result

    def download_file_raw(self, bucket_id: str, file_name: str, save_path: str, progress_callback=None):
        """Download a file WITHOUT the .enc suffix (for unencrypted files)."""
        from aegis_vault.core.fast_downloader import fast_download

        logger.info(f"Downloading {file_name} (raw) from {bucket_id}")
        download_url = f"https://archive.org/download/{bucket_id}/{file_name}"

        def _progress(downloaded, total, speed_bps):
            if progress_callback:
                progress_callback(downloaded, total)

        result = fast_download(download_url, save_path, progress_callback=_progress, max_threads=16)

        if not result["success"]:
            raise Exception(f"Download failed: {result['error']}")

        speed = result.get('speed_bps', 0)
        logger.info(f"✓ Downloaded {file_name} ({result['file_size']} bytes, {speed / 1024 / 1024:.1f} MB/s)")
        return result

    def create_folder(self, folder_name: str) -> str:
        """
        Create a new IA item (folder) by uploading a placeholder file.
        Internet Archive items are created on first upload, so we upload
        a small .keep marker file to initialize the bucket.
        """
        import tempfile
        folder_name = folder_name.strip().lower().replace(" ", "-")
        logger.info(f"Creating folder: {folder_name}")

        marker_content = b"This file marks the creation of the Aegis Vault folder."
        with tempfile.NamedTemporaryFile(delete=False, suffix=".keep") as tmp:
            tmp.write(marker_content)
            tmp_path = tmp.name

        try:
            ia.upload(
                folder_name,
                files={".keep": tmp_path},
                metadata={
                    'collection': 'opensource',
                    'title': f'Aegis Vault — {folder_name}',
                    'mediatype': 'data',
                    'description': f'Cloud vault folder created by Aegis Vault.',
                },
                access_key=self.access_key,
                secret_key=self.secret_key,
                verbose=True,
            )
            # Update local cache
            if self._folder_cache and folder_name not in self._folder_cache:
                self._folder_cache.append(folder_name)
                self._save_local_cache(self._folder_cache)
            logger.info(f"✓ Created folder: {folder_name}")
            return folder_name
        except Exception as e:
            logger.error(f"Failed to create folder {folder_name}: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def delete_file(self, bucket_id: str, filename: str, encrypted: bool = True):
        """
        Delete a file from an IA bucket via S3 API.
        If encrypted=True, appends .enc to the filename before deleting.
        """
        actual_name = filename + ".enc" if encrypted else filename
        logger.info(f"Deleting {actual_name} from {bucket_id}")

        url = f"https://s3.us.archive.org/{bucket_id}/{actual_name}"
        response = requests.delete(url, auth=(self.access_key, self.secret_key), timeout=30)

        if response.status_code in (200, 204):
            logger.info(f"✓ Deleted {actual_name} from {bucket_id}")
            return True
        else:
            raise Exception(f"Delete failed: HTTP {response.status_code} — {response.text[:200]}")
