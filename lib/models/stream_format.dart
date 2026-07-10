class MediaFormat {
  final String formatId;
  final String label;
  final String quality;
  final String ext;
  final bool hasVideo;
  final bool hasAudio;
  final double? fps;
  final String? vcodec;
  final String? acodec;
  final int? filesize;
  final double? tbr;

  MediaFormat({
    required this.formatId,
    required this.label,
    required this.quality,
    required this.ext,
    required this.hasVideo,
    required this.hasAudio,
    this.fps,
    this.vcodec,
    this.acodec,
    this.filesize,
    this.tbr,
  });

  String get displayLabel {
    final type = hasVideo && hasAudio
        ? 'Video'
        : hasVideo ? 'Video Only' : 'Audio Only';
    final size = filesize != null ? _formatSize(filesize!) : '';
    return '$label - $type ${quality}p $ext ${size.isNotEmpty ? "($size)" : ""}';
  }

  static String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB';
  }

  Map<String, dynamic> toJson() => {
    'format_id': formatId,
    'label': label,
    'quality': quality,
    'ext': ext,
    'has_video': hasVideo,
    'has_audio': hasAudio,
    'fps': fps,
    'vcodec': vcodec,
    'acodec': acodec,
    'filesize': filesize,
    'tbr': tbr,
  };
}
