import 'dart:io';
import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
import 'package:pointycastle/export.dart';
import 'package:crypto/crypto.dart' as dart_crypto;
import 'exceptions.dart';
import 'config.dart';

Uint8List _generateSecureBytes(int count) {
  final random = math.Random.secure();
  final bytes = Uint8List(count);
  for (var i = 0; i < count; i++) {
    bytes[i] = random.nextInt(256);
  }
  return bytes;
}

void _incrementCounter(Uint8List counter) {
  for (var i = counter.length - 1; i >= 0; i--) {
    if (++counter[i] != 0) break;
  }
}

Uint8List _ctrCrypt(Uint8List key, Uint8List iv, Uint8List data) {
  final aes = AESEngine();
  aes.init(true, KeyParameter(key));

  final counter = Uint8List(iv.length);
  counter.setRange(0, iv.length, iv);

  final out = Uint8List(data.length);
  final keystream = Uint8List(16);

  for (var i = 0; i < data.length; i += 16) {
    aes.processBlock(counter, 0, keystream, 0);
    _incrementCounter(counter);
    final remaining = data.length - i;
    final chunkLen = remaining < 16 ? remaining : 16;
    for (var j = 0; j < chunkLen; j++) {
      out[i + j] = data[i + j] ^ keystream[j];
    }
  }
  return out;
}

class CryptoEngine {
  final AppConfig _config = AppConfig();
  final int _pbkdf2Iterations;
  static const int _ivBytes = 16;
  static const int _hmacBytes = 32;
  static const int _keyBytes = 32;

  CryptoEngine({int? pbkdf2Iterations})
      : _pbkdf2Iterations = pbkdf2Iterations ?? AppConfig().pbkdf2Iterations;

  Uint8List _deriveKey(String password, Uint8List salt) {
    final pbkdf2 = PBKDF2KeyDerivator(HMac(SHA256Digest(), 64));
    pbkdf2.init(Pbkdf2Parameters(salt, _pbkdf2Iterations, _keyBytes));
    return pbkdf2.process(Uint8List.fromList(utf8.encode(password)));
  }

  Uint8List _deriveHmacKey(String password, Uint8List salt) {
    final pbkdf2 = PBKDF2KeyDerivator(HMac(SHA256Digest(), 64));
    final hmacSalt = Uint8List.fromList([...salt, 0x01]);
    pbkdf2.init(Pbkdf2Parameters(hmacSalt, _pbkdf2Iterations, _keyBytes));
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

  String encryptFile(String filePath, String password, String outputPath) {
    try {
      final fileData = File(filePath).readAsBytesSync();
      final sha256Hash = calculateSha256(filePath);

      final salt = _generateSecureBytes(_config.encryptionSaltBytes);
      final iv = _generateSecureBytes(_ivBytes);
      final encKey = _deriveKey(password, salt);
      final hmacKey = _deriveHmacKey(password, salt);

      final ciphertext = _ctrCrypt(encKey, iv, fileData);

      final mac = HMac(SHA256Digest(), 64);
      mac.init(KeyParameter(hmacKey));
      mac.update(iv, 0, iv.length);
      mac.update(ciphertext, 0, ciphertext.length);
      final hmacResult = Uint8List(_hmacBytes);
      mac.doFinal(hmacResult, 0);

      _ensureDirectory(outputPath);
      final outputFile = File(outputPath);
      final outBytes = Uint8List(salt.length + iv.length + ciphertext.length + hmacResult.length);
      outBytes.setRange(0, salt.length, salt);
      outBytes.setRange(salt.length, salt.length + iv.length, iv);
      outBytes.setRange(salt.length + iv.length, salt.length + iv.length + ciphertext.length, ciphertext);
      outBytes.setRange(salt.length + iv.length + ciphertext.length, outBytes.length, hmacResult);
      outputFile.writeAsBytesSync(outBytes);

      return sha256Hash;
    } on FileSystemException {
      rethrow;
    } catch (e) {
      throw CryptoException('Encryption failed: $e', cause: e);
    }
  }

  bool decryptFile(String encryptedFilePath, String password, String outputPath) {
    try {
      final fileData = File(encryptedFilePath).readAsBytesSync();
      final minLen = _config.encryptionSaltBytes + _ivBytes + _hmacBytes;
      if (fileData.length < minLen) {
        throw const DecryptionException('File too small or corrupted');
      }

      final salt = fileData.sublist(0, _config.encryptionSaltBytes);
      final iv = fileData.sublist(_config.encryptionSaltBytes, _config.encryptionSaltBytes + _ivBytes);
      final cipherLen = fileData.length - _config.encryptionSaltBytes - _ivBytes - _hmacBytes;
      final ciphertext = fileData.sublist(_config.encryptionSaltBytes + _ivBytes, _config.encryptionSaltBytes + _ivBytes + cipherLen);
      final storedHmac = fileData.sublist(_config.encryptionSaltBytes + _ivBytes + cipherLen);

      final encKey = _deriveKey(password, salt);
      final hmacKey = _deriveHmacKey(password, salt);

      final mac = HMac(SHA256Digest(), 64);
      mac.init(KeyParameter(hmacKey));
      mac.update(iv, 0, iv.length);
      mac.update(ciphertext, 0, ciphertext.length);
      final computedHmac = Uint8List(_hmacBytes);
      mac.doFinal(computedHmac, 0);

      if (!_constantTimeEquals(computedHmac, storedHmac)) {
        throw const DecryptionException('Wrong password or corrupted file');
      }

      final plaintext = _ctrCrypt(encKey, iv, ciphertext);
      _ensureDirectory(outputPath);
      File(outputPath).writeAsBytesSync(plaintext);
      return true;
    } on FileSystemException {
      rethrow;
    } on DecryptionException {
      rethrow;
    } catch (e) {
      throw CryptoException('Decryption failed: $e', cause: e);
    }
  }

  bool _constantTimeEquals(Uint8List a, Uint8List b) {
    if (a.length != b.length) return false;
    var result = 0;
    for (var i = 0; i < a.length; i++) {
      result |= a[i] ^ b[i];
    }
    return result == 0;
  }
}
