import 'dart:io';
import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
import 'package:pointycastle/export.dart';
import 'config.dart';
import 'exceptions.dart';

Uint8List _generateSecureBytes(int count) {
  final rng = FortunaRandom();
  final mathRandom = math.Random.secure();
  final seed = Uint8List.fromList(List.generate(32, (_) => mathRandom.nextInt(256)));
  rng.seed(KeyParameter(seed));
  return rng.nextBytes(count);
}

class CredentialManager {
  final AppConfig _config = AppConfig();
  String? _cachedAccessKey;
  String? _cachedSecretKey;
  bool _loaded = false;

  Future<String> get _machineKeyPath => _config.keyFile;
  Future<String> get _credentialPath => _config.credentialFile;

  Future<void> _ensureDir(String path) async {
    final dir = File(path).parent;
    if (!await dir.exists()) await dir.create(recursive: true);
  }

  /// Loads or creates the local machine key (32 random bytes, base64-encoded).
  Future<Uint8List> _loadOrCreateKey() async {
    final path = await _machineKeyPath;
    final file = File(path);
    if (await file.exists()) {
      final content = await file.readAsString();
      return base64Decode(content.trim());
    } else {
      final mathRandom = math.Random.secure();
      final seed = Uint8List.fromList(List.generate(32, (_) => mathRandom.nextInt(256)));
      final secureRandom = FortunaRandom()
        ..seed(KeyParameter(seed));
      
      final key = secureRandom.nextBytes(32);
      
      await _ensureDir(path);
      await file.writeAsString(base64Encode(key));
      return key;
    }
  }

  /// Encrypts credentials with the machine key (AES-256-GCM).
  Future<Uint8List> _encryptWithKey(Uint8List key, String data) async {
    final nonce = _generateSecureBytes(12);

    final plaintext = utf8.encode(data);
    final cipher = GCMBlockCipher(AESEngine())
      ..init(true, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));

    final encrypted = Uint8List(cipher.getOutputSize(plaintext.length));
    final len = cipher.processBytes(plaintext, 0, plaintext.length, encrypted, 0);
    cipher.doFinal(encrypted, len);

    final result = Uint8List(nonce.length + encrypted.length);
    result.setRange(0, nonce.length, nonce);
    result.setRange(nonce.length, result.length, encrypted);
    return result;
  }

  /// Decrypts data with machine key.
  Future<String> _decryptWithKey(Uint8List key, Uint8List data) async {
    if (data.length < 12 + 16) {
      throw CredentialException('Credential file corrupted');
    }
    final nonce = data.sublist(0, 12);
    final encrypted = data.sublist(12);

    final cipher = GCMBlockCipher(AESEngine())
      ..init(false, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));

    final decrypted = Uint8List(cipher.getOutputSize(encrypted.length));
    final len = cipher.processBytes(encrypted, 0, encrypted.length, decrypted, 0);
    final finalLen = cipher.doFinal(decrypted, len);

    return utf8.decode(decrypted.sublist(0, finalLen));
  }

  /// Saves credentials (access, secret) to encrypted local file.
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

  /// Loads credentials from encrypted local file.
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

  /// Returns cached or loaded credentials.
  Future<Map<String, String?>> getCredentials() async {
    if (!_loaded) return loadCredentials();
    return {'access_key': _cachedAccessKey, 'secret_key': _cachedSecretKey};
  }

  /// Clears credentials: zeroizes key file and credential file, then deletes them.
  Future<void> clearCredentials() async {
    try {
      final keyPath = await _machineKeyPath;
      final credPath = await _credentialPath;

      // Zeroize key file
      final keyFile = File(keyPath);
      if (await keyFile.exists()) {
        final len = await keyFile.length();
        final zeroData = Uint8List(len > 0 ? len : 44);
        await keyFile.writeAsBytes(zeroData);
        await keyFile.delete();
      }

      // Zeroize credential file
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
}