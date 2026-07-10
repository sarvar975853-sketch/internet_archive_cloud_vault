import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'package:html/parser.dart' as html_parser;
import '../core/config.dart';
import '../core/exceptions.dart';

class URLDownloader {
  final AppConfig _config = AppConfig();
  final http.Client _client;
  final String downloadDir;

  URLDownloader({http.Client? client, String? downloadDir})
      : _client = client ?? http.Client(),
        downloadDir = downloadDir ?? Directory.systemTemp.path;

  static const Map<String, Map<String, String>> providerInfo = {
    'google_drive': {'name': 'Google Drive', 'color': '#4285F4'},
    'mediafire': {'name': 'MediaFire', 'color': '#FF6600'},
    'terabox': {'name': 'Terabox', 'color': '#FF4500'},
    'dropbox': {'name': 'Dropbox', 'color': '#0061FF'},
    'onedrive': {'name': 'OneDrive', 'color': '#0078D4'},
    'mega': {'name': 'MEGA', 'color': '#D90007'},
    'pcloud': {'name': 'pCloud', 'color': '#009BDE'},
    'wetransfer': {'name': 'WeTransfer', 'color': '#409EFF'},
    'box': {'name': 'Box', 'color': '#0061D5'},
    'sendspace': {'name': 'SendSpace', 'color': '#0077B5'},
    'zippyshare': {'name': 'ZippyShare', 'color': '#FF6600'},
    '4shared': {'name': '4Shared', 'color': '#0B6AB5'},
    'megadb': {'name': 'MegaDB', 'color': '#8B0000'},
    'direct': {'name': 'Direct Link', 'color': '#666666'},
  };

  String detectProvider(String url) {
    if (url.contains('drive.google.com') || url.contains('docs.google.com')) return 'google_drive';
    if (url.contains('mediafire.com')) return 'mediafire';
    if (url.contains('terabox') || url.contains('dubox.com')) return 'terabox';
    if (url.contains('dropbox.com')) return 'dropbox';
    if (url.contains('1drv.ms') || url.contains('onedrive.live.com')) return 'onedrive';
    if (url.contains('mega.nz')) return 'mega';
    if (url.contains('pcloud.com')) return 'pcloud';
    if (url.contains('wetransfer.com')) return 'wetransfer';
    if (url.contains('box.com')) return 'box';
    if (url.contains('sendspace.com')) return 'sendspace';
    if (url.contains('zippyshare.com') || url.contains('zippyshare')) return 'zippyshare';
    if (url.contains('4shared.com')) return '4shared';
    if (url.contains('megadb.net')) return 'megadb';
    return 'direct';
  }

  Future<Map<String, dynamic>> download(String url, {void Function(int, int)? progressCallback}) async {
    final provider = detectProvider(url);
    try {
      switch (provider) {
        case 'google_drive':
          return _downloadGoogleDrive(url, progressCallback);
        case 'mediafire':
          return _downloadMediafire(url, progressCallback);
        case 'terabox':
          return _downloadTerabox(url, progressCallback);
        case 'dropbox':
          return _downloadDropbox(url, progressCallback);
        case 'onedrive':
          return _downloadOnedrive(url, progressCallback);
        case 'mega':
          return _downloadMega(url, progressCallback);
        case 'megadb':
          return _downloadMegadb(url, progressCallback);
        case 'direct':
          return _downloadDirect(url, progressCallback);
        default:
          return _downloadDirect(url, progressCallback);
      }
    } on NetworkException {
      rethrow;
    } catch (e) {
      throw NetworkException('Download failed: $e', cause: e);
    }
  }

  Future<Map<String, dynamic>> _downloadGoogleDrive(String url, void Function(int, int)? cb) async {
    final fileId = _extractGdriveId(url);
    if (fileId == null) return _error('Could not extract Google Drive file ID');

    // Direct download URL
    final downloadUrl = 'https://drive.usercontent.google.com/download?id=$fileId&confirm=t';
    final response = await _client.get(Uri.parse(downloadUrl), headers: {
      'User-Agent': _config.userAgent,
    });

    if (response.statusCode == 200) {
      final filename = _extractFilename(response, 'gdrive_$fileId');
      final path = p.join(downloadDir, filename);
      await File(path).writeAsBytes(response.bodyBytes);
      cb?.call(response.bodyBytes.length, response.bodyBytes.length);
      return {'success': true, 'path': path, 'filename': filename};
    }

    // Try virus scan confirmation page
    final confirmToken = _findGdriveConfirmToken(response.body);
    if (confirmToken != null) {
      final confirmUrl = 'https://drive.usercontent.google.com/download?id=$fileId&confirm=$confirmToken';
      final confirmResp = await _client.get(Uri.parse(confirmUrl), headers: {
        'User-Agent': _config.userAgent,
      });
      final filename = _extractFilename(confirmResp, 'gdrive_$fileId');
      final path = p.join(downloadDir, filename);
      await File(path).writeAsBytes(confirmResp.bodyBytes);
      cb?.call(confirmResp.bodyBytes.length, confirmResp.bodyBytes.length);
      return {'success': true, 'path': path, 'filename': filename};
    }

    return _error('Google Drive download failed');
  }

  String? _extractGdriveId(String url) {
    final patterns = [
      RegExp(r'/d/([a-zA-Z0-9_-]+)'),
      RegExp(r'id=([a-zA-Z0-9_-]+)'),
      RegExp(r'file/d/([a-zA-Z0-9_-]+)'),
    ];
    for (final pattern in patterns) {
      final match = pattern.firstMatch(url);
      if (match != null) return match.group(1);
    }
    return null;
  }

  String? _findGdriveConfirmToken(String html) {
    final match = RegExp(r'confirm=([a-zA-Z0-9_-]+)').firstMatch(html);
    return match?.group(1);
  }

  Future<Map<String, dynamic>> _downloadMediafire(String url, void Function(int, int)? cb) async {
    final response = await _client.get(Uri.parse(url), headers: {'User-Agent': _config.userAgent});
    final document = html_parser.parse(response.body);
    final downloadLink = document.querySelector('#downloadButton')?.attributes['href'] ??
        document.querySelector('a[aria-label="Download file"]')?.attributes['href'];
    
    if (downloadLink == null) return _error('Could not find MediaFire download link');
    return _streamToFile(Uri.parse(downloadLink), cb);
  }

  Future<Map<String, dynamic>> _downloadTerabox(String url, void Function(int, int)? cb) async {
    // Terabox requires cookies and complex API; attempt direct download
    final response = await _client.get(Uri.parse(url), headers: {
      'User-Agent': _config.userAgent,
      'Accept': 'text/html,application/xhtml+xml',
    });
    
    final document = html_parser.parse(response.body);
    final downloadLinks = document.querySelectorAll('a[href*="terabox"]');
    for (final link in downloadLinks) {
      final href = link.attributes['href'];
      if (href != null && href.contains('download')) {
        return _streamToFile(Uri.parse(href), cb);
      }
    }
    return _error('Terabox download requires API. Please use a direct link.');
  }

  Future<Map<String, dynamic>> _downloadDropbox(String url, void Function(int, int)? cb) async {
    var dlUrl = url.replaceAll('?dl=0', '?dl=1');
    if (!dlUrl.contains('?dl=1') && !url.contains('?dl=0')) {
      dlUrl = url.endsWith('/') ? '${url}?dl=1' : '$url?dl=1';
    }
    return _streamToFile(Uri.parse(dlUrl), cb);
  }

  Future<Map<String, dynamic>> _downloadOnedrive(String url, void Function(int, int)? cb) async {
    var dlUrl = url.replaceAll('/view', '/download');
    dlUrl = dlUrl.replaceAll('?reserved=1', '');
    return _streamToFile(Uri.parse(dlUrl), cb);
  }

  Future<Map<String, dynamic>> _downloadMega(String url, void Function(int, int)? cb) async {
    // MEGA requires mega-public-client or complex crypto. Local fallback via browser.
    return _error('MEGA downloads require the mega-public-client tool.\nPlease install: pip install mega-public-client');
  }

  Future<Map<String, dynamic>> _downloadMegadb(String url, void Function(int, int)? cb) async {
    return _error('MegaDB (megadb.net) uses Cloudflare Turnstile protection.\nPlease download manually in your browser.');
  }

  Future<Map<String, dynamic>> _downloadDirect(String url, void Function(int, int)? cb) async {
    // Try HEAD request first
    try {
      final headResp = await _client.send(http.Request('HEAD', Uri.parse(url)));
      if (headResp.statusCode == 200) {
        final contentLength = headResp.headers['content-length'];
        if (contentLength != null && int.parse(contentLength) < 50 * 1024 * 1024) {
          return _streamToFile(Uri.parse(url), cb);
        }
      }
    } catch (_) {}

    // Try GET
    return _streamToFile(Uri.parse(url), cb);
  }

  Future<Map<String, dynamic>> _streamToFile(Uri uri, void Function(int, int)? cb) async {
    final request = http.Request('GET', uri);
    request.headers.addAll({
      'User-Agent': _config.userAgent,
      'Accept': '*/*',
    });
    final response = await _client.send(request);

    if (response.statusCode != 200) {
      return _error('HTTP ${response.statusCode}: ${response.reasonPhrase}');
    }

    final contentLength = int.tryParse(response.headers['content-length'] ?? '') ?? -1;
    final filename = _extractFilenameFromHeaders(response.headers, p.basename(uri.path));
    final path = p.join(downloadDir, filename);
    final file = File(path);
    final sink = file.openWrite();
    int downloaded = 0;

    await for (final chunk in response.stream) {
      sink.add(chunk);
      downloaded += chunk.length;
      cb?.call(downloaded, contentLength);
    }
    await sink.close();

    return {'success': true, 'path': path, 'filename': filename, 'size': downloaded};
  }

  String _extractFilenameFromHeaders(Map<String, String> headers, String fallback) {
    final cd = headers['content-disposition'];
    if (cd != null) {
      final match = RegExp(r"filename[^;=\n]*=(([\"']).*?\2|[^;\n]*)").firstMatch(cd);
      if (match != null) {
        return match.group(1)?.replaceAll('"', '').trim() ?? fallback;
      }
    }
    return fallback.isNotEmpty ? fallback : 'download_${DateTime.now().millisecondsSinceEpoch}';
  }

  String _extractFilename(http.Response response, String fallback) {
    return _extractFilenameFromHeaders(response.headers, fallback);
  }

  String sanitizeFilename(String name) {
    return name.replaceAll(RegExp(r'[<>:"/\\|?*]'), '_');
  }

  Map<String, dynamic> _error(String msg) {
    return {'success': false, 'error': msg};
  }

  void dispose() {
    _client.close();
  }
}
