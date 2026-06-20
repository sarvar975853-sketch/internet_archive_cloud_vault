import requests
import internetarchive as ia
import os
from aegis_vault.utils.logger import logger

class IAStorageEngine:
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key

    def scan_user_folders(self) -> list:
        """
        Scan for user's folders from Internet Archive.
        Searches for items uploaded by the authenticated user.
        """
        logger.info("🔍 Scanning user folders...")
        
        try:
            user_items = []
            search_url = "https://archive.org/advancedsearch.php"
            
            # Strategy 1: Try to get email/uploader from authenticated session
            user_email = self._get_user_email_from_credentials()
            
            if user_email:
                logger.info(f"✓ Got user email: {user_email}")
                user_items = self._search_by_uploader(user_email)
                if user_items:
                    logger.info(f"✅ Found {len(user_items)} folders uploaded by {user_email}")
                    return user_items
            
            # Strategy 2: Try known email from credentials metadata
            logger.info("💡 Trying known email patterns...")
            for email in ['sarvar975853@gmail.com']:
                logger.info(f"Trying: {email}")
                user_items = self._search_by_uploader(email)
                if user_items:
                    logger.info(f"✅ Found {len(user_items)} folders for {email}")
                    return user_items
            
            logger.warning("⚠️  Could not find any folders by email")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error scanning folders: {e}", exc_info=True)
            return []
    
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
            
            response = requests.get(search_url, params=params, timeout=20)
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
            
        except Exception as e:
            logger.error(f"Error searching by uploader: {e}")
        
        return user_items
    
    def _get_username_from_credentials(self) -> str:
        """Extract username from S3 credentials using internetarchive library"""
        logger.info("🔐 Getting username from credentials...")
        
        try:
            # Initialize session with credentials
            session = ia.get_session(config={
                's3': {
                    'access': self.access_key,
                    'secret': self.secret_key
                }
            })
            
            # Try to get username from session attributes
            logger.info(f"Session object type: {type(session)}")
            logger.info(f"Session attributes: {dir(session)[:20]}")
            
            # Check various possible attributes
            for attr in ['username', 'user', 'user_email', 'email', 'screenname']:
                if hasattr(session, attr):
                    val = getattr(session, attr, None)
                    if val:
                        logger.info(f"✓ Found {attr}: {val}")
                        if '@' in str(val) and attr in ['user_email', 'email']:
                            username = str(val).split('@')[0]
                            logger.info(f"✓ Extracted username: {username}")
                            return username
                        else:
                            return str(val)
            
            # Try to get user info via a test call
            logger.info("Attempting to authenticate via item access...")
            response = requests.get(
                "https://archive.org/services/check_cookie.php",
                auth=(self.access_key, self.secret_key),
                timeout=10
            )
            logger.info(f"Cookie check response: {response.status_code}")
            
            # Try accessing archive.org with credentials to get info
            response = requests.get(
                "https://archive.org",
                auth=(self.access_key, self.secret_key),
                timeout=10
            )
            logger.debug(f"Archive.org response status: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error getting username: {e}", exc_info=True)
        
        # If we can't get username, try to search recent uploads anyway
        logger.warning("Could not get username, will search for recent data uploads...")
        return None
    
    def _search_by_username(self, username: str) -> list:
        """Search for all items uploaded by the specific user"""
        user_items = []
        try:
            logger.info(f"📋 Searching for items uploaded by {username}...")
            
            search_url = "https://archive.org/advancedsearch.php"
            params = {
                'q': f'uploader:{username}',
                'fl[]': 'identifier,title,addeddate',
                'rows': '100',
                'output': 'json',
                'sort[]': 'addeddate desc'
            }
            
            logger.debug(f"Search URL: {search_url}")
            logger.debug(f"Query: uploader:{username}")
            
            response = requests.get(search_url, params=params, timeout=20)
            logger.info(f"Search response status: {response.status_code}")
            
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
            
        except Exception as e:
            logger.error(f"Error searching by username: {e}", exc_info=True)
        
        return user_items

    def get_files_in_bucket(self, bucket_id: str) -> list:
        """
        Enhanced file listing with better metadata handling.
        Returns list of encrypted files in the specified bucket/folder.
        """
        url = f"https://archive.org/metadata/{bucket_id}"
        logger.info(f"Fetching metadata for bucket: {bucket_id}")
        
        try:
            response = requests.get(url, timeout=20)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch metadata for {bucket_id}: HTTP {response.status_code}")
                return []
            
            data = response.json()
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
        url = f"https://archive.org/metadata/{bucket_id}"
        logger.info(f"Fetching unencrypted files for bucket: {bucket_id}")
        
        try:
            response = requests.get(url, timeout=20)
            if response.status_code != 200:
                return []
            
            data = response.json()
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
        logger.info(f"Downloading {file_name}.enc from {bucket_id}")
        download_url = f"https://archive.org/download/{bucket_id}/{file_name}.enc"
        
        response = requests.get(download_url, stream=True)
        if response.status_code != 200:
            logger.error(f"Failed to download from {download_url}")
            raise Exception("Could not fetch the cloud asset.")
            
        total_length = response.headers.get('content-length')
        
        with open(save_path, 'wb') as f:
            if total_length is None:
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    if progress_callback:
                        progress_callback(dl, total_length)

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
