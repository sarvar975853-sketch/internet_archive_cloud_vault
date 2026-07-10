class DownloadItem {
  final String id;
  final String url;
  final String provider;
  final String status; // queued, downloading, completed, error
  final double progress;
  final String? filename;
  final String? error;
  final String? mode; // 'upload' or 'disk'
  final DateTime createdAt;

  DownloadItem({
    required this.id,
    required this.url,
    required this.provider,
    this.status = 'queued',
    this.progress = 0.0,
    this.filename,
    this.error,
    this.mode = 'upload',
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  DownloadItem copyWith({
    String? status,
    double? progress,
    String? filename,
    String? error,
  }) {
    return DownloadItem(
      id: id,
      url: url,
      provider: provider,
      status: status ?? this.status,
      progress: progress ?? this.progress,
      filename: filename ?? this.filename,
      error: error ?? this.error,
      mode: mode,
      createdAt: createdAt,
    );
  }
}
