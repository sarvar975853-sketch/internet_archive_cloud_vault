import 'dart:io';
import 'dart:async';
import 'dart:convert';
import 'package:path/path.dart' as p;
import '../core/config.dart';

enum LogLevel { debug, info, warning, error }

class AegisLogger {
  static AegisLogger? _instance;
  factory AegisLogger() => _instance ??= AegisLogger._();
  AegisLogger._();

  final AppConfig _config = AppConfig();
  File? _logFile;
  IOSink? _sink;
  StreamController<LogEntry>? _controller;
  int _currentSize = 0;
  static const int _maxSize = 5 * 1024 * 1024; // 5MB
  static const int _maxBackups = 3;

  Future<void> init() async {
    final logPath = await _config.logFile;
    final dir = File(logPath).parent;
    if (!await dir.exists()) await dir.create(recursive: true);

    _logFile = File(logPath);
    if (await _logFile!.exists()) {
      _currentSize = await _logFile!.length();
    }
    _sink = _logFile!.openWrite(mode: FileMode.append);
    _controller = StreamController<LogEntry>.broadcast();
  }

  Stream<LogEntry> get stream => _controller!.stream;

  void _log(LogLevel level, String message, {dynamic error, StackTrace? stackTrace}) {
    final entry = LogEntry(
      timestamp: DateTime.now(),
      level: level,
      message: message,
      error: error,
      stackTrace: stackTrace,
    );

    // Console output
    final formatted = _formatEntry(entry);
    // ignore: avoid_print
    print(formatted);

    // File output
    _sink?.writeln(formatted);
    _sink?.flush();
    _currentSize += formatted.length + 1;

    // Rotate if needed
    if (_currentSize >= _maxSize) {
      _rotateLogs();
    }

    _controller?.add(entry);
  }

  void _rotateLogs() async {
    await _sink?.close();
    final logPath = await _config.logFile;

    // Shift backups
    for (int i = _maxBackups - 1; i >= 1; i--) {
      final oldFile = File('$logPath.$i');
      final newFile = File('$logPath.${i + 1}');
      if (await oldFile.exists()) await oldFile.rename(newFile.path);
    }
    if (await File(logPath).exists()) {
      await File(logPath).rename('$logPath.1');
    }

    _currentSize = 0;
    _logFile = File(logPath);
    _sink = _logFile!.openWrite(mode: FileMode.append);
  }

  String _formatEntry(LogEntry entry) {
    final timestamp = entry.timestamp.toIso8601String().split('.').first;
    final level = entry.level.name.toUpperCase().padRight(7);
    final msg = entry.error != null
        ? '${entry.message} | ${entry.error}'
        : entry.message;
    return '[$timestamp] [$level] $msg';
  }

  void debug(String msg) => _log(LogLevel.debug, msg);
  void info(String msg) => _log(LogLevel.info, msg);
  void warning(String msg, {dynamic error}) => _log(LogLevel.warning, msg, error: error);
  void error(String msg, {dynamic error, StackTrace? stackTrace}) =>
      _log(LogLevel.error, msg, error: error, stackTrace: stackTrace);

  void dispose() {
    _sink?.close();
    _controller?.close();
  }
}

class LogEntry {
  final DateTime timestamp;
  final LogLevel level;
  final String message;
  final dynamic error;
  final StackTrace? stackTrace;

  LogEntry({
    required this.timestamp,
    required this.level,
    required this.message,
    this.error,
    this.stackTrace,
  });
}

/// Singleton logger instance
final AegisLogger logger = AegisLogger();
