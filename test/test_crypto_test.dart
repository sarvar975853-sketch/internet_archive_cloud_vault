import 'package:flutter_test/flutter_test.dart';
import 'dart:io';
import 'package:aegis_vault/core/crypto.dart';
import 'package:aegis_vault/core/exceptions.dart';

void main() {
  late CryptoEngine crypto;
  late String tempDir;

  setUp(() {
    crypto = CryptoEngine(pbkdf2Iterations: 10000);
    tempDir = Directory.systemTemp.path + '/aegis_test_${DateTime.now().millisecondsSinceEpoch}';
    Directory(tempDir).createSync();
  });

  tearDown(() {
    if (Directory(tempDir).existsSync()) {
      Directory(tempDir).listSync(recursive: true).forEach((f) => (f as File).deleteSync());
      Directory(tempDir).deleteSync();
    }
  });

  test('encrypt and decrypt roundtrip', () {
    final inputPath = '$tempDir/test.txt';
    final encPath = '$tempDir/test.enc';
    final decPath = '$tempDir/test_dec.txt';
    File(inputPath).writeAsStringSync('Hello Aegis Vault!');

    final sha256 = crypto.encryptFile(inputPath, 'password123', encPath);
    expect(sha256, isA<String>());
    expect(sha256.length, 64);

    final result = crypto.decryptFile(encPath, 'password123', decPath);
    expect(result, isTrue);
    expect(File(decPath).readAsStringSync(), 'Hello Aegis Vault!');
  });

  test('wrong password throws DecryptionException', () {
    final inputPath = '$tempDir/test.txt';
    final encPath = '$tempDir/test.enc';
    File(inputPath).writeAsStringSync('secret data');

    crypto.encryptFile(inputPath, 'correct_password', encPath);

    expect(
      () => crypto.decryptFile(encPath, 'wrong_password', '$tempDir/out.txt'),
      throwsA(isA<DecryptionException>()),
    );
  });

  test('corrupted file throws DecryptionException', () {
    final encPath = '$tempDir/corrupt.enc';
    File(encPath).writeAsBytesSync(List.filled(100, 0));

    expect(
      () => crypto.decryptFile(encPath, 'any', '$tempDir/out.txt'),
      throwsA(isA<DecryptionException>()),
    );
  });

  test('nonexistent input throws FileSystemException', () {
    expect(
      () => crypto.encryptFile('/nonexistent/file.txt', 'pwd', '$tempDir/out.enc'),
      throwsA(isA<FileSystemException>()),
    );
  });

  test('empty file encrypt and decrypt', () {
    final inputPath = '$tempDir/empty.txt';
    final encPath = '$tempDir/empty.enc';
    final decPath = '$tempDir/empty_dec.txt';
    File(inputPath).writeAsBytesSync([]);

    crypto.encryptFile(inputPath, 'password', encPath);
    final result = crypto.decryptFile(encPath, 'password', decPath);
    expect(result, isTrue);
    expect(File(decPath).readAsBytesSync(), isEmpty);
  });

  test('large file (1MB) roundtrip', () {
    final inputPath = '$tempDir/large.bin';
    final encPath = '$tempDir/large.enc';
    final decPath = '$tempDir/large_dec.bin';
    final data = List.generate(1024 * 1024, (i) => i % 256);
    File(inputPath).writeAsBytesSync(data);

    crypto.encryptFile(inputPath, 'password', encPath);
    final result = crypto.decryptFile(encPath, 'password', decPath);
    expect(result, isTrue);
    expect(File(decPath).readAsBytesSync(), data);
  });
}
