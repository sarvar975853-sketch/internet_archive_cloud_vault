import 'package:flutter_test/flutter_test.dart';
import 'package:aegis_vault/core/exceptions.dart';

void main() {
  group('Exception Hierarchy', () {
    test('CryptoException extends AegisException', () {
      expect(const CryptoException('test'), isA<AegisException>());
    });

    test('DecryptionException extends CryptoException', () {
      expect(const DecryptionException('test'), isA<CryptoException>());
      expect(const DecryptionException('test'), isA<AegisException>());
    });

    test('IntegrityException extends CryptoException', () {
      expect(const IntegrityException('test'), isA<CryptoException>());
      expect(const IntegrityException('test'), isA<AegisException>());
    });

    test('StorageException hierarchy', () {
      expect(const UploadException('test'), isA<StorageException>());
      expect(const DownloadException('test'), isA<StorageException>());
      expect(const FolderNotFoundException('test'), isA<StorageException>());
      expect(const DeleteException('test'), isA<StorageException>());
      expect(const StorageException('test'), isA<AegisException>());
    });

    test('QueueException hierarchy', () {
      expect(const TaskTimeoutException('test'), isA<QueueException>());
      expect(const QueueException('test'), isA<AegisException>());
    });

    test('Exceptions carry messages', () {
      const msg = 'test error message';
      expect(const CryptoException(msg).toString(), contains(msg));
      expect(const DecryptionException(msg).toString(), contains(msg));
      expect(const UploadException(msg).toString(), contains(msg));
    });
  });
}
