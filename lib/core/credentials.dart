import 'dart:io';
import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
import 'package:pointycastle/export.dart';
import 'config.dart';
import 'exceptions.dart';

Uint8List _generateSecureBytes(int count) {
  final random = math.Random.secure();
  final bytes = Uint8List(count);
  for (var i = 0; i < count; i++) {
    bytes[i] = random.nextInt(256);
  }
  return bytes;
}

class CredentialManager {
  final AppConfig _config = AppConfig();
  String? _cachedAccessKey;
  String? _cachedSecretKey;
  bool _loaded = false;
  static const int _ivBytes = 16;
  static const int _hmacBytes = 32;

  Future<String> get _machineKeyPath => _config.keyFile;
  Future<String> get _credentialPath => _config.credentialFile;

  Future<void> _ensureDir(String path) async {
    final dir = File(path).parent;
    if (!await dir.exists()) await dir.create(recursive: true);
  }

  Future<Uint8List> _loadOrCreateKey() async {
    final path = await _machineKeyPath;
    final file = File(path);
    if (await file.exists()) {
      final content = await file.readAsString();
      return base64Decode(content.trim());
    } else {
      final key = _generateSecureBytes(32);
      await _ensureDir(path);
      await file.writeAsString(base64Encode(key));
      return key;
    }
  }

  Future<Uint8List> _encryptWithKey(Uint8List key, String data) async {
    final iv = _generateSecureBytes(_ivBytes);
    final plaintext = utf8.encode(data);

    final cipher = SICBlockCipher(AESEngine())
      ..init(true, ParametersWithIV(KeyParameter(key), iv));

    final out = Uint8List(plaintext.length);
    for (var i = 0; i < plaintext.length; i++) {
      out[i] = cipher.returnByte(plaintext[i]);
    }

    final mac = HMac(SHA256Digest(), 64);
    mac.init(KeyParameter(key));
    mac.update(iv, 0, iv.length);
    mac.update(out, 0, out.length);
    final hmacResult = Uint8List(_hmacBytes);
    mac.doFinal(hmacResult, 0);

    final result = Uint8List(iv.length + out.length + hmacResult.length);
    result.setRange(0, iv.length, iv);
    result.setRange(iv.length, iv.length + out.length, out);
    result.setRange(iv.length + out.length, result.length, hmacResult);
    return result;
  }

  Future<String> _decryptWithKey(Uint8List key, Uint8List data) async {
    if (data.length < _ivBytes + _hmacBytes) {
      throw const CredentialException('Credential file corrupted');
    }
    final iv = data.sublist(0, _ivBytes);
    final ctLen = data.length - _ivBytes - _hmacBytes;
    final ciphertext = data.sublist(_ivBytes, _ivBytes + ctLen);
    final storedHmac = data.sublist(_ivBytes + ctLen);

    final mac = HMac(SHA256Digest(), 64);
    mac.init(KeyParameter(key));
    mac.update(iv, 0, iv.length);
    mac.update(ciphertext, 0, ciphertext.length);
    final computedHmac = Uint8List(_hmacBytes);
    mac.doFinal(computedHmac, 0);

    if (!_constantTimeEquals(computedHmac, storedHmac)) {
      throw const CredentialException('Credential file corrupted');
    }

    final cipher = SICBlockCipher(AESEngine())
      ..init(false, ParametersWithIV(KeyParameter(key), iv));

    final plaintext = Uint8List(ciphertext.length);
    for (var i = 0; i < ciphertext.length; i++) {
      plaintext[i] = cipher.returnByte(ciphertext[i]);
    }

    return utf8.decode(plaintext);
  }

  Future<void> saveCredentials(String access, String secret) async {
    try {
      final machineKey = await _loadOrCreateKey();
      final json = jsonEncode({'access_key': access, 'secret_key': secret});
      final encrypted = await _encryptWithKey(machineKey, json);

      final path = await _credentialPath;
      await _ensureDir(path);
      await File(path).writeAsBytes(encrypted);

      _cachedAccessKey = access;
      _cachedSecretKey = secret;
      _loaded = true;
    } catch (e) {
      throw CredentialException('Failed to save credentials: $e', cause: e);
    }
  }

  Future<Map<String, String?>> loadCredentials() async {
    try {
      final credentialPath = await _credentialPath;
      final credFile = File(credentialPath);
      if (!await credFile.exists()) {
        return {'access_key': null, 'secret_key': null};
      }

      final machineKey = await _loadOrCreateKey();
      final encrypted = await credFile.readAsBytes();
      final jsonStr = await _decryptWithKey(machineKey, encrypted);
      final data = jsonDecode(jsonStr) as Map<String, dynamic>;

      _cachedAccessKey = data['access_key'] as String?;
      _cachedSecretKey = data['secret_key'] as String?;
      _loaded = true;

      return {'access_key': _cachedAccessKey, 'secret_key': _cachedSecretKey};
    } catch (e) {
      if (e is CredentialException) rethrow;
      throw CredentialException('Failed to load credentials: $e', cause: e);
    }
  }

  Future<Map<String, String?>> getCredentials() async {
    if (!_loaded) return loadCredentials();
    return {'access_key': _cachedAccessKey, 'secret_key': _cachedSecretKey};
  }

  Future<void> clearCredentials() async {
    try {
      final keyPath = await _machineKeyPath;
      final credPath = await _credentialPath;

      final keyFile = File(keyPath);
      if (await keyFile.exists()) {
        final len = await keyFile.length();
        final zeroData = Uint8List(len > 0 ? len : 44);
        await keyFile.writeAsBytes(zeroData);
        await keyFile.delete();
      }

      final credFile = File(credPath);
      if (await credFile.exists()) {
        final len = await credFile.length();
        final randomData = _generateSecureBytes(len > 0 ? len : 128);
        await credFile.writeAsBytes(randomData);
        await credFile.delete();
      }

      _cachedAccessKey = null;
      _cachedSecretKey = null;
      _loaded = false;
    } catch (e) {
      throw CredentialException('Failed to clear credentials: $e', cause: e);
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
