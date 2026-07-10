import 'package:flutter_test/flutter_test.dart';
import 'package:aegis_vault/core/credentials.dart';
import 'dart:io';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late CredentialManager manager;
  late String tempDir;

  setUp(() {
    tempDir = Directory.systemTemp.path + '/aegis_cred_test_${DateTime.now().millisecondsSinceEpoch}';
    Directory(tempDir).createSync();
    manager = CredentialManager();
  });

  tearDown(() {
    if (Directory(tempDir).existsSync()) {
      Directory(tempDir).listSync(recursive: true).forEach((f) => (f as File).deleteSync());
      Directory(tempDir).deleteSync();
    }
  });

  test('save and load credentials', () async {
    await manager.saveCredentials('test_access', 'test_secret');
    final creds = await manager.getCredentials();
    expect(creds['access_key'], 'test_access');
    expect(creds['secret_key'], 'test_secret');
  });

  test('no credentials returns nulls', () async {
    final creds = await manager.loadCredentials();
    expect(creds['access_key'], isNull);
    expect(creds['secret_key'], isNull);
  });

  test('clear credentials deletes files', () async {
    await manager.saveCredentials('access', 'secret');
    await manager.clearCredentials();
    final creds = await manager.getCredentials();
    expect(creds['access_key'], isNull);
    expect(creds['secret_key'], isNull);
  });

  test('special characters in credentials', () async {
    await manager.saveCredentials('user+123!@#', 'secret_with_special_chars!@#\$%^');
    final creds = await manager.getCredentials();
    expect(creds['access_key'], 'user+123!@#');
    expect(creds['secret_key'], 'secret_with_special_chars!@#\$%^');
  });

  test('persistence across instances', () async {
    final m1 = CredentialManager();
    await m1.saveCredentials('persist_access', 'persist_secret');

    final m2 = CredentialManager();
    final creds = await m2.getCredentials();
    expect(creds['access_key'], 'persist_access');
    expect(creds['secret_key'], 'persist_secret');
  });
}
