import 'package:flutter_test/flutter_test.dart';
import 'package:aegis_vault/core/config.dart';

void main() {
  group('AppConfig', () {
    test('singleton returns same instance', () {
      final config1 = AppConfig();
      final config2 = AppConfig();
      expect(config1, same(config2));
    });

    test('default values are set', () {
      final config = AppConfig();
      expect(config.appName, 'Aegis Vault');
      expect(config.version, '3.5.5');
      expect(config.pbkdf2Iterations, 600000);
      expect(config.encryptionSaltBytes, 16);
      expect(config.queueMaxWorkers, 6);
      expect(config.queueRetryMax, 3);
      expect(config.requestTimeout, 15);
      expect(config.fastDownloadDefaultThreads, 16);
    });

    test('known folders are populated', () {
      final config = AppConfig();
      expect(config.knownFolders.length, greaterThan(0));
      expect(config.knownFolders, contains('Documents'));
      expect(config.knownFolders, contains('Photos'));
    });

    test('uploader email defaults to null', () {
      final config = AppConfig();
      expect(config.uploaderEmail, isNull);
    });

    test('uploader email can be set', () {
      final config = AppConfig();
      config.uploaderEmail = 'test@example.com';
      expect(config.uploaderEmail, 'test@example.com');
    });
  });
}
