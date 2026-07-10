import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'config.dart';
import 'exceptions.dart';

class FastDownloader {
  final AppConfig _config = AppConfig();
  final http.Client _client;

  FastDownloader({http.Client? client}) : _client = client ?? http.Client();

  Future<Map<String, dynamic>> download(
    String url, String savePath, {
    void Function(int, int)? progressCallback,
    Map<String, String>? extraHeaders,
  }) async {
    try {
      // HEAD request to check server capabilities
      final headResp = await _client.send(http.Request('HEAD', Uri.parse(url)));
      final acceptRanges = headResp.headers['accept-ranges'] ?? '';
      final contentLengthStr = headResp.headers['content-length'];
      final totalSize = contentLengthStr != null ? int.tryParse(contentLengthStr) ?? -1 : -1;

      final filename = _extractFilename(url, headResp.headers);
      final fullPath = p.join(savePath, filename);

      // Small file or no range support → single thread
      if (totalSize < _config.fastDownloadSingleThreadThreshold || acceptRanges != 'bytes') {
        return _downloadSingleThread(url, fullPath, totalSize, progressCallback, extraHeaders);
      }

      // Large file with range support → parallel download
      return _downloadParallel(url, fullPath, totalSize, progressCallback, extraHeaders);
    } catch (e) {
      throw NetworkException('Fast download failed: $e', cause: e);
    }
  }

  Future<Map<String, dynamic>> _downloadParallel(
    String url, String savePath, int totalSize,
    void Function(int, int)? progressCallback,
    Map<String, String>? extraHeaders,
  ) async {
    final numThreads = _config.fastDownloadDefaultThreads;
    final chunkSize = (totalSize / numThreads).ceil();
    
    // Pre-allocate file
    final file = File(savePath);
    if (!await file.exists()) {
      await file.create(recursive: true);
    }
    final raf = await file.open(mode: FileMode.write);
    await raf.truncate(totalSize);
    await raf.close();

    // Download chunks
    final results = await Future.wait(
      List.generate(numThreads, (i) {
        final start = i * chunkSize;
        final end = i == numThreads - 1 ? totalSize - 1 : (start + chunkSize - 1);
        return _downloadChunk(url, savePath, start, end, i, extraHeaders);
      }),
    );

    var totalDownloaded = 0;
    for (final chunk in results) {
      totalDownloaded += chunk;
    }
    progressCallback?.call(totalSize, totalSize);

    return {'success': true, 'path': savePath, 'size': totalSize};
  }

  Future<int> _downloadChunk(
    String url, String savePath, int start, int end, int chunkIndex,
    Map<String, String>? extraHeaders,
  ) async {
    final headers = <String, String>{
      'Range': 'bytes=$start-$end',
      'User-Agent': _config.userAgent,
      if (extraHeaders != null) ...extraHeaders,
    };

    final request = http.Request('GET', Uri.parse(url));
    request.headers.addAll(headers);
    final response = await _client.send(request);

    if (response.statusCode != 206 && response.statusCode != 200) {
      throw NetworkException('Chunk download failed: HTTP ${response.statusCode}');
    }

    final file = File(savePath);
    final raf = await file.open(mode: FileMode.writeOnly);
    await raf.setPosition(start);

    int downloaded = 0;
    await for (final chunk in response.stream) {
      await raf.writeFrom(chunk);
      downloaded += chunk.length;
    }
    await raf.close();

    return downloaded;
  }

  Future<Map<String, dynamic>> _downloadSingleThread(
    String url, String savePath, int totalSize,
    void Function(int, int)? progressCallback,
    Map<String, String>? extraHeaders,
  ) async {
    final headers = <String, String>{
      'User-Agent': _config.userAgent,
      if (extraHeaders != null) ...extraHeaders,
    };

    final request = http.Request('GET', Uri.parse(url));
    request.headers.addAll(headers);
    final response = await _client.send(request);

    if (response.statusCode != 200) {
      throw NetworkException('Download failed: HTTP ${response.statusCode}');
    }

    final file = File(savePath);
    if (!await file.exists()) {
      await file.create(recursive: true);
    }
    final sink = file.openWrite();
    int downloaded = 0;

    await for (final chunk in response.stream) {
      sink.add(chunk);
      downloaded += chunk.length;
      progressCallback?.call(downloaded, totalSize);
    }
    await sink.close();

    return {'success': true, 'path': savePath, 'size': downloaded};
  }

  String _extractFilename(String url, Map<String, String> headers) {
    final cd = headers['content-disposition'];
    if (cd != null) {
      final match = RegExp(r"filename[^;=\n]*=(([\"']).*?\2|[^;\n]*)").firstMatch(cd);
      if (match != null) {
        return match.group(1)?.replaceAll('"', '').trim() ?? 'download';
      }
    }
    return p.basename(Uri.parse(url).path);
  }

  void dispose() {
    _client.close();
  }
}

/// Module-level convenience function
Future<Map<String, dynamic>> fastDownload(
  String url, String savePath, {
  void Function(int, int)? progressCallback,
}) async {
  final downloader = FastDownloader();
  return downloader.download(url, savePath, progressCallback: progressCallback);
}
