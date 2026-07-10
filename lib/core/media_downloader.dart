import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:uuid/uuid.dart';
import '../core/config.dart';
import '../core/exceptions.dart';

enum Platform { youtube, instagram, tiktok, twitter, reddit, twitch, spotify, jiosaavn, wynk, generic }

enum DownloadStatus { queued, extracting, downloading, processing, completed, error, cancelled }

class StreamFormat {
  final String formatId;
  final String label;
  final String quality;
  final String ext;
  final bool hasVideo;
  final bool hasAudio;
  final double? fps;
  final String? vcodec;
  final String? acodec;
  final int? filesize;
  final double? tbr;

  StreamFormat({
    required this.formatId, required this.label, required this.quality,
    required this.ext, required this.hasVideo, required this.hasAudio,
    this.fps, this.vcodec, this.acodec, this.filesize, this.tbr,
  });

  factory StreamFormat.fromJson(Map<String, dynamic> json) {
    return StreamFormat(
      formatId: json['format_id']?.toString() ?? '',
      label: json['label']?.toString() ?? json['format']?.toString() ?? '',
      quality: json['quality']?.toString() ?? json['height']?.toString() ?? 'unknown',
      ext: json['ext']?.toString() ?? 'mp4',
      hasVideo: json['has_video'] == true,
      hasAudio: json['has_audio'] == true,
      fps: (json['fps'] as num?)?.toDouble(),
      vcodec: json['vcodec']?.toString(),
      acodec: json['acodec']?.toString(),
      filesize: json['filesize'] as int?,
      tbr: (json['tbr'] as num?)?.toDouble(),
    );
  }
}

class DownloadTask {
  final String id;
  final String url;
  String? title;
  final Platform platform;
  DownloadStatus status;
  double progress;
  double speed;
  String? eta;
  int totalSize;
  int downloaded;
  String? format;
  String? quality;
  String? outputPath;
  String? error;
  List<StreamFormat> formats;
  DateTime? startTime;
  Process? _process;

  DownloadTask({
    required this.id, required this.url, this.title,
    required this.platform, this.status = DownloadStatus.queued,
    this.progress = 0, this.speed = 0, this.eta,
    this.totalSize = 0, this.downloaded = 0,
    this.format, this.quality, this.outputPath, this.error,
    this.formats = const [], this.startTime,
  });

  void cancel() {
    if (_process != null) {
      _process!.kill(ProcessSignal.sigterm);
      _process = null;
    }
    status = DownloadStatus.cancelled;
  }
}

class MediaDownloader {
  final AppConfig _config = AppConfig();
  final String downloadDir;
  final int maxConcurrent;
  final int aria2Chunks;
  final void Function(DownloadTask)? onProgress;
  final Map<String, DownloadTask> _tasks = {};
  String? _ytdlpPath;
  String? _ffmpegPath;
  String? _aria2cPath;

  MediaDownloader({
    required this.downloadDir,
    this.maxConcurrent = 3,
    this.aria2Chunks = 16,
    this.onProgress,
  }) {
    _resolveBinaries();
  }

  void _resolveBinaries() {
    _ytdlpPath = _which('yt-dlp');
    _ffmpegPath = _which('ffmpeg');
    _aria2cPath = _which('aria2c');
  }

  String? _which(String name) {
    final paths = (Platform.environment['PATH'] ?? '').split(':');
    for (final dir in paths) {
      final fullPath = p.join(dir, name);
      if (File(fullPath).existsSync()) return fullPath;
      if (Platform.isWindows && File('$fullPath.exe').existsSync()) return '$fullPath.exe';
    }
    return null;
  }

  Map<String, bool> getEngineStatus() {
    return {
      'yt-dlp': _ytdlpPath != null,
      'ffmpeg': _ffmpegPath != null,
      'aria2c': _aria2cPath != null,
    };
  }

  Future<Map<String, dynamic>> extractInfo(String url) async {
    if (_ytdlpPath == null) {
      return {'success': false, 'error': 'yt-dlp not found'};
    }

    try {
      final result = await Process.run(_ytdlpPath!, [
        '--dump-json',
        '--no-download',
        url,
      ]);

      if (result.exitCode != 0) {
        return {'success': false, 'error': result.stderr.toString()};
      }

      final lines = result.stdout.toString().trim().split('\n');
      if (lines.isEmpty) return {'success': false, 'error': 'No data returned'};

      final data = jsonDecode(lines.last) as Map<String, dynamic>;
      final formats = (data['formats'] as List? ?? [])
          .map((f) => StreamFormat.fromJson(f as Map<String, dynamic>))
          .toList();

      return {
        'success': true,
        'title': data['title']?.toString() ?? 'Unknown',
        'duration': data['duration'],
        'formats': formats,
      };
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  DownloadTask submit(String url, {String? quality, String? format, String? outputDir}) {
    final id = const Uuid().v4();
    final platform = _detectPlatform(url);
    final task = DownloadTask(id: id, url: url, platform: platform,
        quality: quality, format: format, startTime: DateTime.now());
    task.outputPath = outputDir ?? downloadDir;
    _tasks[id] = task;
    return task;
  }

  Platform _detectPlatform(String url) {
    if (url.contains('youtube.com') || url.contains('youtu.be')) return Platform.youtube;
    if (url.contains('instagram.com')) return Platform.instagram;
    if (url.contains('tiktok.com')) return Platform.tiktok;
    if (url.contains('twitter.com') || url.contains('x.com')) return Platform.twitter;
    if (url.contains('reddit.com')) return Platform.reddit;
    if (url.contains('twitch.tv')) return Platform.twitch;
    if (url.contains('spotify.com')) return Platform.spotify;
    if (url.contains('jiosaavn.com')) return Platform.jiosaavn;
    if (url.contains('wynk.in')) return Platform.wynk;
    return Platform.generic;
  }

  DownloadTask? getTask(String id) => _tasks[id];
  List<DownloadTask> getAllTasks() => _tasks.values.toList();

  void startTask(String taskId) {
    final task = _tasks[taskId];
    if (task == null) return;
    _runDownload(task);
  }

  void cancelTask(String taskId) {
    final task = _tasks[taskId];
    task?.cancel();
  }

  Future<void> _runDownload(DownloadTask task) async {
    if (_ytdlpPath == null) {
      task.status = DownloadStatus.error;
      task.error = 'yt-dlp not found';
      onProgress?.call(task);
      return;
    }

    task.status = DownloadStatus.extracting;
    onProgress?.call(task);

    // Extract info
    final info = await extractInfo(task.url);
    if (info['success'] != true) {
      task.status = DownloadStatus.error;
      task.error = info['error']?.toString() ?? 'Extraction failed';
      onProgress?.call(task);
      return;
    }

    task.title = info['title'] as String?;
    task.formats = (info['formats'] as List).cast<StreamFormat>();
    task.status = DownloadStatus.downloading;
    onProgress?.call(task);

    // Build and run yt-dlp command
    try {
      final outputTemplate = p.join(task.outputPath ?? downloadDir, '%(title)s.%(ext)s');
      final args = _buildYtdlpArgs(task, outputTemplate);
      
      task._process = await Process.start(_ytdlpPath!, args);
      task.startTime = DateTime.now();

      // Parse progress from stderr
      task._process!.stderr.transform(utf8.decoder).listen((data) {
        _parseProgress(task, data);
      });

      final exitCode = await task._process!.exitCode;
      if (exitCode == 0 && task.status != DownloadStatus.cancelled) {
        // Post-process with FFmpeg if needed
        if (task.format != null && _isAudioFormat(task.format!) && _ffmpegPath != null) {
          task.status = DownloadStatus.processing;
          onProgress?.call(task);
          // Find downloaded file and transcode
          final downloadedFile = _findDownloadedFile(task.outputPath ?? downloadDir, task.title ?? '');
          if (downloadedFile != null) {
            final transcoded = await _transcodeAudio(downloadedFile, task.format!);
            task.outputPath = transcoded;
          }
        }
        task.status = DownloadStatus.completed;
        task.progress = 100;
      } else if (task.status != DownloadStatus.cancelled) {
        task.status = DownloadStatus.error;
        task.error = 'yt-dlp exited with code $exitCode';
      }
    } catch (e) {
      if (task.status != DownloadStatus.cancelled) {
        task.status = DownloadStatus.error;
        task.error = e.toString();
      }
    }

    onProgress?.call(task);
  }

  List<String> _buildYtdlpArgs(DownloadTask task, String outputTemplate) {
    final args = <String>[
      task.url,
      '-o', outputTemplate,
      '--newline',
      '--no-playlist',
    ];

    // Format selection
    if (task.quality != null || task.format != null) {
      final formatFilter = _buildFormatFilter(task);
      if (formatFilter.isNotEmpty) {
        args.addAll(['-f', formatFilter]);
      }
    }

    // Use aria2c if available
    if (_aria2cPath != null) {
      args.addAll([
        '--external-downloader', 'aria2c',
        '--external-downloader-args', '-x $aria2Chunks -k 1M',
      ]);
    }

    // Embed metadata when possible
    args.add('--embed-metadata');

    return args;
  }

  String _buildFormatFilter(DownloadTask task) {
    final quality = task.quality;
    final fmt = task.format;
    final isAudio = fmt != null && _isAudioFormat(fmt);

    if (isAudio) {
      if (fmt == 'mp3') return 'bestaudio[ext=mp3]/bestaudio';
      if (fmt == 'flac') return 'bestaudio[ext=flac]/bestaudio';
      if (fmt == 'wav') return 'bestaudio[ext=wav]/bestaudio';
      if (fmt == 'm4a') return 'bestaudio[ext=m4a]/bestaudio';
      if (fmt == 'opus') return 'bestaudio[ext=opus]/bestaudio';
      return 'bestaudio';
    }

    // Video quality
    switch (quality) {
      case '2160p' || '4k': return 'bestvideo[height<=2160]+bestaudio/best[height<=2160]';
      case '1440p' || '2k': return 'bestvideo[height<=1440]+bestaudio/best[height<=1440]';
      case '1080p': return 'bestvideo[height<=1080]+bestaudio/best[height<=1080]';
      case '720p': return 'bestvideo[height<=720]+bestaudio/best[height<=720]';
      case '480p': return 'bestvideo[height<=480]+bestaudio/best[height<=480]';
      case '360p': return 'bestvideo[height<=360]+bestaudio/best[height<=360]';
      default: return 'bestvideo+bestaudio/best';
    }
  }

  bool _isAudioFormat(String fmt) => ['mp3', 'flac', 'wav', 'm4a', 'opus', 'audio'].contains(fmt);

  Future<String?> _transcodeAudio(String inputPath, String targetExt) async {
    if (_ffmpegPath == null) return null;
    final outputPath = inputPath.replaceAll(p.extension(inputPath), '.$targetExt');
    
    try {
      final result = await Process.run(_ffmpegPath!, [
        '-i', inputPath,
        '-vn',
        '-acodec', _codecForFormat(targetExt),
        '-y',
        outputPath,
      ]);

      if (result.exitCode == 0) {
        File(inputPath).deleteSync();
        return outputPath;
      }
    } catch (_) {}
    return null;
  }

  String _codecForFormat(String ext) {
    switch (ext) {
      case 'mp3': return 'libmp3lame';
      case 'flac': return 'flac';
      case 'wav': return 'pcm_s16le';
      case 'm4a': return 'aac';
      case 'opus': return 'libopus';
      default: return 'copy';
    }
  }

  void _parseProgress(DownloadTask task, String data) {
    final lines = data.split('\n');
    for (final line in lines) {
      // yt-dlp progress line format: [download] 45.2% of ~12.34MiB at 2.50MiB/s ETA 00:05
      final percentMatch = RegExp(r'(\d+\.?\d*)%').firstMatch(line);
      final speedMatch = RegExp(r'at\s+([\d.]+)([KMG]i?B)/s').firstMatch(line);
      final etaMatch = RegExp(r'ETA\s+(\d+:\d+)').firstMatch(line);

      if (percentMatch != null) {
        task.progress = double.parse(percentMatch.group(1)!);
      }
      if (speedMatch != null) {
        final val = double.parse(speedMatch.group(1)!);
        final unit = speedMatch.group(2)!;
        task.speed = _parseSpeed(val, unit);
      }
      if (etaMatch != null) {
        task.eta = etaMatch.group(1);
      }
    }
    onProgress?.call(task);
  }

  double _parseSpeed(double value, String unit) {
    if (unit.startsWith('K')) return value * 1024;
    if (unit.startsWith('M')) return value * 1024 * 1024;
    if (unit.startsWith('G')) return value * 1024 * 1024 * 1024;
    return value;
  }

  String? _findDownloadedFile(String directory, String titleHint) {
    final dir = Directory(directory);
    if (!dir.existsSync()) return null;
    
    final files = dir.listSync().whereType<File>().toList()
      ..sort((a, b) => b.statSync().modified.compareTo(a.statSync().modified));
    
    return files.isNotEmpty ? files.first.path : null;
  }

  void dispose() {
    for (final task in _tasks.values) {
      task.cancel();
    }
    _tasks.clear();
  }
}
