class AppVersion {
  static const String version = '3.5.0';
  static const String buildDate = '2026-07-21';
  static const String author = 'Samar';
  static const String appName = 'Aegis Vault';
  static const String description =
      'Modern Cloud Storage with Zero-Knowledge Encryption';

  static String get fullVersion => '$appName v$version';
  static String get versionString => 'v$version ($buildDate)';
}

void printVersionInfo() {
  // ignore: avoid_print
  print('${AppVersion.appName} v${AppVersion.version}');
}