import 'dart:io';
import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
import 'package:pointycastle/export.dart';
import 'package:crypto/crypto.dart' as dart_crypto;
import 'exceptions.dart';
import 'config.dart';

Uint8List _generateSecureBytes(int count) {
  final rng = FortunaRandom();
  final mathRandom = math.Random.secure();
  final seed = Uint8List.fromList(List.generate(32, (_) => mathRandom.nextInt(256)));
  rng.seed(KeyParameter(seed));
  final result = Uint8List(count);
  rng.nextBytes(result);
  return result;
}

class CryptoEngine {
  final AppConfig _config = AppConfig();
  
  Uint8List _deriveKey(String password, Uint8List salt) {
    final pbkdf2 = PBKDF2KeyDerivator(HMac(SHA256Digest(), 64));
    pbkdf2.init(Pbkdf2Parameters(salt, _config.pbkdf2Iterations, 32));
    return pbkdf2.process(Uint8List.fromList(utf8.encode(password)));
  }

  String calculateSha256(String filePath) {
    final file = File(filePath);
    final bytes = file.readAsBytesSync();
    final digest = dart_crypto.sha256.convert(bytes);
    return digest.toString();
  }

  void _ensureDirectory(String path) {
    final dir = File(path).parent;
    if (!dir.existsSync()) dir.createSync(recursive: true);
  }

  /// Encrypts file at [filePath] with [password], writes to [outputPath].
  /// Returns the SHA-256 hex digest of the original file.
  String encryptFile(String filePath, String password, String outputPath) {
    try {
      final fileData = File(filePath).readAsBytesSync();
      final sha256Hash = calculateSha256(filePath);

      // Generate random salt and nonce
      final salt = _generateSecureBytes(_config.encryptionSaltBytes);
      final nonce = _generateSecureBytes(12); // GCM standard nonce size

      // Derive key from password
      final key = _deriveKey(password, salt);

      // AES-256-GCM encrypt
      final cipher = GCMBlockCipher(AESEngine())
        ..init(true, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));

      // Process all data
      final encrypted = Uint8List(cipher.getOutputSize(fileData.length));
      final len = cipher.processBytes(fileData, 0, fileData.length, encrypted, 0);
      cipher.doFinal(encrypted, len);

      // Write: salt + nonce + encrypted (includes GCM tag)
      _ensureDirectory(outputPath);
      final outputFile = File(outputPath);
      final outBytes = Uint8List(salt.length + nonce.length + encrypted.length);
      outBytes.setRange(0, salt.length, salt);
      outBytes.setRange(salt.length, salt.length + nonce.length, nonce);
      outBytes.setRange(salt.length + nonce.length, outBytes.length, encrypted);
      outputFile.writeAsBytesSync(outBytes);

      return sha256Hash;
    } on FileSystemException {
      rethrow;
    } catch (e) {
      throw CryptoException('Encryption failed: $e', cause: e);
    }
  }

  /// Decrypts encrypted file at [encryptedFilePath] with [password],
  /// writes plaintext to [outputPath]. Returns true on success.
  bool decryptFile(String encryptedFilePath, String password, String outputPath) {
    try {
      final fileData = File(encryptedFilePath).readAsBytesSync();

      if (fileData.length < _config.encryptionSaltBytes + 12 + 16) {
        throw DecryptionException('File too small or corrupted');
      }

      // Parse: salt + nonce + encrypted(tag appended)
      final salt = fileData.sublist(0, _config.encryptionSaltBytes);
      final nonce = fileData.sublist(_config.encryptionSaltBytes, _config.encryptionSaltBytes + 12);
      final encrypted = fileData.sublist(_config.encryptionSaltBytes + 12);

      // Derive key
      final key = _deriveKey(password, salt);

      // AES-256-GCM decrypt
      final cipher = GCMBlockCipher(AESEngine())
        ..init(false, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));

      final decrypted = Uint8List(cipher.getOutputSize(encrypted.length));
      final len = cipher.processBytes(encrypted, 0, encrypted.length, decrypted, 0);
      final finalLen = cipher.doFinal(decrypted, len);

      // GCM authenticates, so if we got here, integrity is verified
      _ensureDirectory(outputPath);
      File(outputPath).writeAsBytesSync(decrypted.sublist(0, finalLen));
      return true;
    } on FileSystemException {
      rethrow;
    } on DecryptionException {
      rethrow;
    } on ArgumentError {
      throw DecryptionException('Wrong password or corrupted file');
    } catch (e) {
      throw CryptoException('Decryption failed: $e', cause: e);
    }
  }
}