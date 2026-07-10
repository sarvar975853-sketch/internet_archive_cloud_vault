import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:crypto/crypto.dart' as dart_crypto;
import 'config.dart';
import 'exceptions.dart';
import 'fast_downloader.dart';

class IAStorageEngine {
  final AppConfig _config = AppConfig();
  final String accessKey;
  final String secretKey;
  final http.Client _client;
  final Map<String, _CacheEntry> _metadataCache = {};
  String? uploaderEmail;
  List<String>? _cachedFolders;
  DateTime? _folderCacheTime;

  IAStorageEngine(this.accessKey, this.secretKey, {this.uploaderEmail, http.Client? client})
      : _client = client ?? http.Client();

  // ─── Folder Management ──────────────────────────────────────

  Future<List<String>> scanUserFolders({bool forceRefresh = false}) async {
    if (!forceRefresh && _cachedFolders != null && _folderCacheTime != null) {
      final elapsed = DateTime.now().difference(_folderCacheTime!);
      if (elapsed.inSeconds < _config.folderCacheTtlSeconds) {
        return _cachedFolders!;
      }
    }
    return _refreshFolders();
  }

  Future<List<String>> _refreshFolders() async {
    try {
      final email = uploaderEmail ?? await _getUserEmailFromCredentials();
      if (email == null) return List.from(_config.knownFolders);
      
      final items = await _searchByUploader(email);
      final folders = items.map((item) => item.split('/').last).toList();
      _cachedFolders = folders.isNotEmpty ? folders : List.from(_config.knownFolders);
      _folderCacheTime = DateTime.now();
      return _cachedFolders!;
    } catch (e) {
      return List.from(_config.knownFolders);
    }
  }

  Future<String?> _getUserEmailFromCredentials() async {
    try {
      final uri = Uri.parse('https://archive.org/account/s3.php');
      final response = await _client.get(uri, headers: {
        'Authorization': _buildAuthHeader('', ''),
        'User-Agent': _config.userAgent,
      });
      // Try to extract email from response
      final body = response.body;
      final emailMatch = RegExp(r'([\w.+-]+@[\w-]+\.[\w.]+)').firstMatch(body);
      return emailMatch?.group(1);
    } catch (_) {
      return null;
    }
  }

  Future<List<String>> _searchByUploader(String email) async {
    final query = 'uploader:$email AND mediatype:${_config.iaMediaType}';
    final uri = Uri.parse('https://archive.org/advancedsearch.php').replace(queryParameters: {
      'q': query,
      'fl[]': 'identifier',
      'rows': '1000',
      'page': '1',
      'output': 'json',
    });

    final response = await _client.get(uri, headers: {
      'User-Agent': _config.userAgent,
    });

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final docs = data['response']?['docs'] as List? ?? [];
      return docs.map((d) => d['identifier']?.toString() ?? '').where((id) => id.isNotEmpty).toList();
    }
    return [];
  }

  // ─── Metadata ───────────────────────────────────────────────

  Future<Map<String, dynamic>?> getBucketMetadata(String bucketId) async {
    final cached = _metadataCache[bucketId];
    if (cached != null && !cached.isExpired) return cached.data;

    try {
      final uri = Uri.parse('https://archive.org/metadata/$bucketId');
      final response = await _client.get(uri, headers: {
        'User-Agent': _config.userAgent,
      });

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _metadataCache[bucketId] = _CacheEntry(data, DateTime.now());
        return data;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  // ─── File Listing ───────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getFilesInBucket(String bucketId) async {
    final metadata = await getBucketMetadata(bucketId);
    if (metadata == null) return [];

    final files = metadata['files'] as List? ?? [];
    return files
        .where((f) {
          final name = f['name']?.toString() ?? '';
          return name.endsWith('.enc');
        })
        .map((f) => {
              'name': f['name']?.toString() ?? '',
              'size': _formatSize((f['size'] as num?)?.toDouble() ?? 0),
              'source': f['source']?.toString() ?? '',
              'mtime': f['mtime']?.toString() ?? '',
            })
        .toList();
  }

  Future<List<Map<String, dynamic>>> getFilesUnencrypted(String bucketId) async {
    final metadata = await getBucketMetadata(bucketId);
    if (metadata == null) return [];

    final files = metadata['files'] as List? ?? [];
    return files
        .where((f) {
          final name = f['name']?.toString() ?? '';
          return !name.endsWith('.enc') && !name.endsWith('/');
        })
        .map((f) => ({
              'name': f['name']?.toString() ?? '',
              'size': _formatSize((f['size'] as num?)?.toDouble() ?? 0),
              'source': f['source']?.toString() ?? '',
              'mtime': f['mtime']?.toString() ?? '',
            }))
        .toList();
  }

  Future<Map<String, List<Map<String, dynamic>>>> getFilesParallel(
      List<String> bucketIds, int maxWorkers) async {
    final results = <String, List<Map<String, dynamic>>>{};
    final semaphore = _Semaphore(maxWorkers);
    final futures = <Future<void>>[];

    for (final id in bucketIds) {
      futures.add(semaphore.acquire(() async {
        results[id] = await getFilesInBucket(id);
      }));
    }

    await Future.wait(futures);
    return results;
  }

  String _formatSize(double bytes) {
    if (bytes < 1024) return '${bytes.toStringAsFixed(0)} B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB';
  }

  // ─── Upload ─────────────────────────────────────────────────

  Future<Map<String, dynamic>> uploadFile(
    String tempPath, String filename, String bucket, {
    void Function(int, int)? progressCallback,
  }) async {
    try {
      final file = File(tempPath);
      final fileSize = await file.length();
      final bytes = await File(tempPath).readAsBytes();

      final uri = Uri.parse('https://s3.us.archive.org/$bucket/$filename');
      final auth = _buildAuthHeader('PUT', '/$bucket/$filename');

      final response = await _client.put(
        uri,
        headers: {
          'Authorization': auth,
          'x-amz-auto-make-bucket': '1',
          'Content-Length': fileSize.toString(),
          'Content-Type': 'application/octet-stream',
          'User-Agent': _config.userAgent,
        },
        body: bytes,
      );

      if (response.statusCode == 200) {
        progressCallback?.call(fileSize, fileSize);
        return {'success': true, 'filename': filename};
      } else {
        throw UploadException('Upload failed: ${response.statusCode} ${response.body}');
      }
    } on UploadException {
      rethrow;
    } catch (e) {
      throw UploadException('Upload error: $e', cause: e);
    }
  }

  Future<Map<String, dynamic>> uploadFileRaw(
    String localPath, String filename, String bucket, {
    void Function(int, int)? progressCallback,
  }) async {
    return uploadFile(localPath, filename, bucket, progressCallback: progressCallback);
  }

  // ─── Download ───────────────────────────────────────────────

  Future<Map<String, dynamic>> downloadFile(
    String bucket, String filename, String savePath, {
    void Function(int, int)? progressCallback,
  }) async {
    final downloadUrl = 'https://archive.org/download/$bucket/$filename.enc';
    return _doDownload(downloadUrl, savePath, progressCallback);
  }

  Future<Map<String, dynamic>> downloadFileRaw(
    String bucket, String filename, String savePath, {
    void Function(int, int)? progressCallback,
  }) async {
    final downloadUrl = 'https://archive.org/download/$bucket/$filename';
    return _doDownload(downloadUrl, savePath, progressCallback);
  }

  Future<Map<String, dynamic>> _doDownload(
    String url, String savePath, void Function(int, int)? progressCallback,
  ) async {
    try {
      final downloader = FastDownloader();
      return await downloader.download(url, savePath, progressCallback: progressCallback);
    } catch (e) {
      throw DownloadException('Download failed: $e', cause: e);
    }
  }

  // ─── Folder Creation ────────────────────────────────────────

  Future<String> createFolder(String folderName) async {
    try {
      final sanitized = folderName.replaceAll(RegExp(r'[^\w\s-]'), '').trim();
      final bucketId = sanitized.toLowerCase().replaceAll(' ', '_');
      final markerContent = jsonEncode({
        'folder': sanitized,
        'created': DateTime.now().toIso8601String(),
        'type': _config.iaMediaType,
      });

      final uri = Uri.parse('https://s3.us.archive.org/$bucketId/folder_marker.json');
      final auth = _buildAuthHeader('PUT', '/$bucketId/folder_marker.json');

      final response = await _client.put(
        uri,
        headers: {
          'Authorization': auth,
          'x-amz-auto-make-bucket': '1',
          'Content-Type': 'application/json',
          'User-Agent': _config.userAgent,
        },
        body: markerContent,
      );

      if (response.statusCode == 200) {
        return bucketId;
      } else {
        throw StorageException('Failed to create folder: ${response.statusCode}');
      }
    } catch (e) {
      if (e is StorageException) rethrow;
      throw StorageException('Failed to create folder: $e', cause: e);
    }
  }

  // ─── Delete ─────────────────────────────────────────────────

  Future<bool> deleteFile(String bucket, String filename, {bool encrypted = true}) async {
    try {
      final targetName = encrypted ? '$filename.enc' : filename;
      final uri = Uri.parse('https://s3.us.archive.org/$bucket/$targetName');
      final auth = _buildAuthHeader('DELETE', '/$bucket/$targetName');

      final response = await _client.delete(uri, headers: {
        'Authorization': auth,
        'User-Agent': _config.userAgent,
      });

      return response.statusCode == 200 || response.statusCode == 204;
    } catch (e) {
      throw DeleteException('Failed to delete file: $e', cause: e);
    }
  }

  // ─── Auth Helpers ───────────────────────────────────────────

  String _buildAuthHeader(String method, String resource) {
    final stringToSign = '$method\n\napplication/octet-stream\n\nx-amz-auto-make-bucket:1\n/$resource';
    final hmac = dart_crypto.Hmac(dart_crypto.sha256, utf8.encode(secretKey));
    final digest = hmac.convert(utf8.encode(stringToSign));
    final signature = base64Encode(digest.bytes);
    return 'AWS $accessKey:$signature';
  }

  void dispose() {
    _client.close();
  }
}

// ─── Internal Helpers ────────────────────────────────────────

class _CacheEntry {
  final Map<String, dynamic> data;
  final DateTime timestamp;
  
  _CacheEntry(this.data, this.timestamp);

  bool get isExpired {
    return DateTime.now().difference(timestamp).inSeconds > 600;
  }
}

class _Semaphore {
  final int max;
  int _current = 0;
  final List<Completer<void>> _waiters = [];

  _Semaphore(this.max);

  Future<void> acquire(Future<void> Function() fn) async {
    if (_current >= max) {
      final completer = Completer<void>();
      _waiters.add(completer);
      await completer.future;
    }
    _current++;
    try {
      await fn();
    } finally {
      _current--;
      if (_waiters.isNotEmpty) {
        _waiters.removeAt(0).complete();
      }
    }
  }
}
