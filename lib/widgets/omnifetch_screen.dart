import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/toast.dart';

class OmniFetchTab extends StatefulWidget {
  final void Function(String url, String? quality, String? format, String? outputDir)? onSubmit;
  const OmniFetchTab({super.key, this.onSubmit});

  @override
  State<OmniFetchTab> createState() => _OmniFetchTabState();
}

class _OmniFetchTabState extends State<OmniFetchTab> with SingleTickerProviderStateMixin {
  final _urlController = TextEditingController();
  String _activeNav = 'input';
  String? _detectedPlatform;
  String _selectedQuality = '1080p';
  String _selectedFormat = 'mp4';
  String _selectedDestination = 'Downloads';

  final List<OmniTask> _tasks = [];

  static const _qualities = ['2160p (4K)', '1440p (2K)', '1080p', '720p', '480p', '360p', 'Audio Only'];
  static const _formats = ['mp4', 'mkv', 'mp3', 'flac', 'wav', 'm4a', 'opus'];

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  void _detectPlatform(String url) {
    if (url.contains('youtube.com') || url.contains('youtu.be')) {
      setState(() => _detectedPlatform = 'YouTube');
    } else if (url.contains('instagram.com')) {
      setState(() => _detectedPlatform = 'Instagram');
    } else if (url.contains('tiktok.com')) {
      setState(() => _detectedPlatform = 'TikTok');
    } else if (url.contains('twitter.com') || url.contains('x.com')) {
      setState(() => _detectedPlatform = 'Twitter/X');
    } else if (url.contains('reddit.com')) {
      setState(() => _detectedPlatform = 'Reddit');
    } else if (url.contains('twitch.tv')) {
      setState(() => _detectedPlatform = 'Twitch');
    } else if (url.contains('spotify.com')) {
      setState(() => _detectedPlatform = 'Spotify');
    } else if (url.contains('jiosaavn.com')) {
      setState(() => _detectedPlatform = 'JioSaavn');
    } else {
      setState(() => _detectedPlatform = null);
    }
  }

  void _submit() {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      ToastManager.warning(context, 'Please enter a URL');
      return;
    }
    final quality = _selectedQuality == 'Audio Only' ? 'audio' : '${_selectedQuality.replaceAll(RegExp(r'[^\d]'), '')}p';
    final format = _selectedQuality == 'Audio Only' ? (_selectedFormat == 'mp4' ? 'mp3' : _selectedFormat) : _selectedFormat;

    final task = OmniTask(
      url: url, platform: _detectedPlatform ?? 'Unknown',
      quality: _selectedQuality, format: format,
      status: 'queued',
    );
    setState(() => _tasks.insert(0, task));
    widget.onSubmit?.call(url, quality, format, _selectedDestination);
    _urlController.clear();
    ToastManager.success(context, 'Task queued');
  }

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      // Left nav
      Container(
        width: 160,
        color: AppColors.sidebarBg,
        child: Column(children: [
          const SizedBox(height: 20),
          _NavItem(icon: Icons.add_circle_outline, label: 'New Download', isActive: _activeNav == 'input', onTap: () => setState(() => _activeNav = 'input')),
          _NavItem(icon: Icons.downloading, label: 'Active', isActive: _activeNav == 'active', onTap: () => setState(() => _activeNav = 'active')),
          _NavItem(icon: Icons.check_circle_outline, label: 'Completed', isActive: _activeNav == 'completed', onTap: () => setState(() => _activeNav = 'completed')),
          _NavItem(icon: Icons.settings_outlined, label: 'Settings', isActive: _activeNav == 'settings', onTap: () => setState(() => _activeNav = 'settings')),
        ]),
      ),
      // Main content
      Expanded(
        child: _activeNav == 'input' ? _buildInputPanel() :
        _activeNav == 'active' ? _buildTaskList('downloading') :
        _activeNav == 'completed' ? _buildTaskList('completed') :
        _buildSettingsPanel(),
      ),
    ]);
  }

  Widget _buildInputPanel() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('OmniFetch', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28)),
        const SizedBox(height: 8),
        Text('Download media from YouTube, Spotify, Instagram, and more.', style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 24),
        // URL card
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: AppColors.cardBg, borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.borderDefault),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                labelText: 'Media URL',
                hintText: 'Paste YouTube, Spotify, or other URL...',
                prefixIcon: const Icon(Icons.link, size: 20),
                suffixIcon: _detectedPlatform != null
                    ? Container(
                        margin: const EdgeInsets.all(8),
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.15),
                          borderRadius: const BorderRadius.all(Radius.circular(8)),
                        ),
                        child: Center(child: Text(_detectedPlatform!, style: const TextStyle(fontSize: 11, color: AppColors.primary))),
                      )
                    : null,
              ),
              onChanged: _detectPlatform,
              onSubmitted: (_) => _submit(),
            ),
            const SizedBox(height: 20),
            Row(children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _selectedQuality,
                  decoration: const InputDecoration(labelText: 'Quality'),
                  items: _qualities.map((q) => DropdownMenuItem(value: q, child: Text(q, style: const TextStyle(fontSize: 13)))).toList(),
                  onChanged: (v) => setState(() => _selectedQuality = v!),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _selectedFormat,
                  decoration: const InputDecoration(labelText: 'Format'),
                  items: _formats.map((f) => DropdownMenuItem(value: f, child: Text(f, style: const TextStyle(fontSize: 13)))).toList(),
                  onChanged: (v) => setState(() => _selectedFormat = v!),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _selectedDestination,
                  decoration: const InputDecoration(labelText: 'Save to'),
                  items: ['Downloads', 'Music', 'Videos', 'Documents'].map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                  onChanged: (v) => setState(() => _selectedDestination = v!),
                ),
              ),
            ]),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity, height: 48,
              child: ElevatedButton.icon(
                onPressed: _submit,
                icon: const Icon(Icons.download, size: 20),
                label: const Text('Start Download'),
              ),
            ),
          ]),
        ),
        const SizedBox(height: 24),
        if (_tasks.isNotEmpty) ...[
          Text('Recent Tasks', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          ...(_tasks.take(5).map((task) => _TaskEntry(task: task))),
        ],
      ]),
    );
  }

  Widget _buildTaskList(String filterStatus) {
    final filtered = _tasks.where((t) => filterStatus == 'completed' ? t.status == 'completed' : t.status == 'downloading' || t.status == 'queued').toList();
    if (filtered.isEmpty) {
      return Center(
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(filterStatus == 'completed' ? Icons.check_circle_outline : Icons.hourglass_empty,
              size: 64, color: AppColors.textMuted.withOpacity(0.3)),
          const SizedBox(height: 16),
          Text(filterStatus == 'completed' ? 'No completed downloads' : 'No active downloads',
              style: TextStyle(fontSize: 16, color: AppColors.textMuted)),
        ]),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: filtered.length,
      itemBuilder: (context, index) => _TaskEntry(task: filtered[index]),
    );
  }

  Widget _buildSettingsPanel() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Download Settings', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 24),
        _SettingRow(label: 'Download Directory', subtitle: _selectedDestination, trailing: const Icon(Icons.folder, color: AppColors.primary)),
        const Divider(height: 24, color: AppColors.borderDefault),
        const _SettingRow(label: 'Max Concurrent Downloads', subtitle: '3', trailing: Text('3')),
        const Divider(height: 24, color: AppColors.borderDefault),
        const _SettingRow(label: 'Aria2c Chunks', subtitle: '16 per file', trailing: Text('16')),
        const Divider(height: 24, color: AppColors.borderDefault),
        Row(children: [
          const Text('Engine Status', style: TextStyle(fontSize: 14, color: AppColors.textPrimary)),
          const Spacer(),
          const _EngineDot(label: 'yt-dlp', available: true),
          const SizedBox(width: 16),
          const _EngineDot(label: 'FFmpeg', available: true),
          const SizedBox(width: 16),
          const _EngineDot(label: 'aria2c', available: false),
        ]),
      ]),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;
  const _NavItem({required this.icon, required this.label, required this.isActive, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Material(
        color: isActive ? AppColors.sidebarItemActive : Colors.transparent,
        borderRadius: const BorderRadius.all(Radius.circular(8)),
        child: InkWell(
          borderRadius: const BorderRadius.all(Radius.circular(8)),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            child: Row(children: [
              Icon(icon, size: 18, color: isActive ? AppColors.primary : AppColors.textMuted),
              const SizedBox(width: 10),
              Text(label, style: TextStyle(fontSize: 13, color: isActive ? AppColors.textPrimary : AppColors.textSecondary)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _TaskEntry extends StatelessWidget {
  final OmniTask task;
  const _TaskEntry({required this.task});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg, borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.borderDefault),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(_statusIcon, size: 18, color: _statusColor),
          const SizedBox(width: 8),
          Expanded(child: Text(task.url, style: const TextStyle(fontSize: 13), overflow: TextOverflow.ellipsis)),
          Text(task.platform, style: const TextStyle(fontSize: 11, color: AppColors.primary)),
        ]),
        const SizedBox(height: 8),
        if (task.status == 'downloading') ...[
          ClipRRect(
            borderRadius: const BorderRadius.all(Radius.circular(4)),
            child: LinearProgressIndicator(value: 0.45, minHeight: 4, backgroundColor: AppColors.progressBg, valueColor: const AlwaysStoppedAnimation(AppColors.progressFill)),
          ),
          const SizedBox(height: 6),
          Row(children: [
            const Text('45%', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
            const Spacer(),
            const Text('2.5 MB/s', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
            const Spacer(),
            const Text('ETA 00:42', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
          ]),
        ] else if (task.status == 'completed') ...[
          Row(children: [
            const Text('Completed', style: TextStyle(fontSize: 12, color: AppColors.success)),
            const Spacer(),
            Text('${task.quality} | ${task.format}', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
          ]),
        ] else ...[
          const Text('Queued...', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
        ],
      ]),
    );
  }

  IconData get _statusIcon {
    switch (task.status) {
      case 'queued': return Icons.hourglass_empty;
      case 'downloading': return Icons.downloading;
      case 'completed': return Icons.check_circle;
      case 'error': return Icons.error;
      default: return Icons.hourglass_empty;
    }
  }

  Color get _statusColor {
    switch (task.status) {
      case 'queued': return AppColors.textMuted;
      case 'downloading': return AppColors.primary;
      case 'completed': return AppColors.success;
      case 'error': return AppColors.error;
      default: return AppColors.textMuted;
    }
  }
}

class _SettingRow extends StatelessWidget {
  final String label;
  final String subtitle;
  final Widget trailing;
  const _SettingRow({required this.label, required this.subtitle, required this.trailing});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
        Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
      ])),
      const SizedBox(width: 16),
      trailing,
    ]);
  }
}

class _EngineDot extends StatelessWidget {
  final String label;
  final bool available;
  const _EngineDot({required this.label, required this.available});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.circle, size: 10, color: available ? AppColors.success : AppColors.error),
      const SizedBox(width: 4),
      Text(label, style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
    ]);
  }
}

class OmniTask {
  final String url;
  final String platform;
  final String quality;
  final String format;
  final String status;
  OmniTask({required this.url, required this.platform, required this.quality, required this.format, required this.status});
}
