import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

class AppConfig {
  // Singleton
  static AppConfig? _instance;
  factory AppConfig() => _instance ??= AppConfig._internal();
  AppConfig._internal();

  // Identity
  final String appName = 'Aegis Vault';
  final String version = '3.5.5';

  // Paths - lazy resolution
  String? _configDir;
  Future<String> get configDir async {
    _configDir ??= (await getApplicationSupportDirectory()).path;
    return _configDir!;
  }

  Future<String> get credentialFile async =>
      p.join(await configDir, '.aegis_config.enc');
  Future<String> get keyFile async =>
      p.join(await configDir, '.aegis_sys.key');
  Future<String> get localFolderCache async =>
      p.join(await configDir, '.aegis_folders.json');
  Future<String> get logFile async =>
      p.join(await configDir, '.aegis_vault.log');

  // Crypto
  final int pbkdf2Iterations = 600000;
  final int encryptionSaltBytes = 16;
  final int sha256HexLength = 64;
  final int fernetKeyLength = 32;

  // Internet Archive
  final String iaCollection = 'opensource';
  final String iaMediaType = 'data';

  // Cache TTLs (seconds)
  final int cacheTtlSeconds = 60;
  final int folderCacheTtlSeconds = 300;
  final int metadataCacheTtlSeconds = 600;

  // Known folders
  final List<String> knownFolders = const [
    'Movies', 'TV Series', 'Documents', 'Photos', 'Music',
    'Games', 'Software', 'Books', 'Other',
  ];

  // Fast Downloader
  final int fastDownloadDefaultThreads = 16;
  final int fastDownloadChunkSize = 2 * 1024 * 1024; // 2MB
  final int fastDownloadSingleThreadThreshold = 1024 * 1024; // 1MB

  // URL Downloader
  final int urlDownloadChunkSize = 64 * 1024; // 64KB

  // Queue Worker
  final int queueMaxWorkers = 6;
  final int queueRetryMax = 3;
  final double queueTaskTimeout = 300.0; // seconds

  // Parallel Fetch
  final int parallelFetchMaxWorkers = 16;

  // Network
  final int requestTimeout = 15; // seconds
  final int requestPoolConnections = 10;
  final int requestPoolMaxsize = 20;
  final int requestMaxRetries = 2;
  final String userAgent = 'AegisVault/3.5.5';

  // Session
  String? uploaderEmail;
}