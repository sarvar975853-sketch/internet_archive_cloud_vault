class AegisException implements Exception {
  final String message;
  final dynamic cause;
  const AegisException(this.message, {this.cause});
  @override
  String toString() => 'AegisException: $message';
}

// Crypto
class CryptoException extends AegisException {
  const CryptoException(super.message, {super.cause});
}
class DecryptionException extends CryptoException {
  const DecryptionException(super.message, {super.cause});
}
class IntegrityException extends CryptoException {
  const IntegrityException(super.message, {super.cause});
}

// Storage
class StorageException extends AegisException {
  const StorageException(super.message, {super.cause});
}
class UploadException extends StorageException {
  const UploadException(super.message, {super.cause});
}
class DownloadException extends StorageException {
  const DownloadException(super.message, {super.cause});
}
class FolderNotFoundException extends StorageException {
  const FolderNotFoundException(super.message, {super.cause});
}
class DeleteException extends StorageException {
  const DeleteException(super.message, {super.cause});
}

// Credentials
class CredentialException extends AegisException {
  const CredentialException(super.message, {super.cause});
}

// Queue
class QueueException extends AegisException {
  const QueueException(super.message, {super.cause});
}
class TaskTimeoutException extends QueueException {
  const TaskTimeoutException(super.message, {super.cause});
}

// Network
class NetworkException extends AegisException {
  const NetworkException(super.message, {super.cause});
}

// Config
class ConfigException extends AegisException {
  const ConfigException(super.message, {super.cause});
}