import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../version.dart';

class SettingsScreen extends StatefulWidget {
  final VoidCallback? onClearCache;
  const SettingsScreen({super.key, this.onClearCache});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        width: 520,
        height: 480,
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.borderDefault),
        ),
        child: Column(children: [
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('Settings', style: Theme.of(context).textTheme.titleLarge),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.of(context).pop(),
              ),
            ]),
          ),
          // Tabs
          TabBar(
            controller: _tabController,
            indicatorColor: AppColors.primary,
            labelColor: AppColors.primary,
            unselectedLabelColor: AppColors.textSecondary,
            tabs: const [
              Tab(text: 'General'),
              Tab(text: 'About'),
            ],
          ),
          const Divider(height: 1, color: AppColors.borderDefault),
          // Content
          Expanded(
            child: TabBarView(controller: _tabController, children: [
              _GeneralTab(onClearCache: widget.onClearCache),
              _AboutTab(),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _GeneralTab extends StatelessWidget {
  final VoidCallback? onClearCache;
  const _GeneralTab({this.onClearCache});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Performance', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        _SettingRow(
          label: 'Max Download Threads',
          subtitle: '16 parallel chunks per download',
          trailing: const Text('16', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
        ),
        const Divider(height: 24, color: AppColors.borderDefault),
        _SettingRow(
          label: 'Queue Workers',
          subtitle: '6 concurrent upload/download tasks',
          trailing: const Text('6', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
        ),
        const Divider(height: 24, color: AppColors.borderDefault),
        _SettingRow(
          label: 'Task Timeout',
          subtitle: '300 seconds per task',
          trailing: const Text('300s', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
        ),
        const SizedBox(height: 32),
        Text('Storage', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        _SettingRow(
          label: 'Clear Local Cache',
          subtitle: 'Remove cached folder list and metadata',
          trailing: TextButton.icon(
            onPressed: onClearCache,
            icon: const Icon(Icons.delete_outline, size: 16),
            label: const Text('Clear'),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
          ),
        ),
        const SizedBox(height: 32),
        Text('Security', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        _SettingRow(
          label: 'PBKDF2 Iterations',
          subtitle: '600,000 iterations (OWASP 2024)',
          trailing: const Icon(Icons.check_circle, color: AppColors.success, size: 20),
        ),
        const Divider(height: 24, color: AppColors.borderDefault),
        _SettingRow(
          label: 'Encryption',
          subtitle: 'AES-256-GCM with SHA-256 integrity',
          trailing: const Icon(Icons.check_circle, color: AppColors.success, size: 20),
        ),
      ]),
    );
  }
}

class _AboutTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(children: [
        const SizedBox(height: 24),
        Icon(Icons.shield, size: 64, color: AppColors.primary),
        const SizedBox(height: 16),
        Text(AppVersion.appName, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.15),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text('v${AppVersion.version}',
              style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600)),
        ),
        const SizedBox(height: 16),
        Text(AppVersion.description, textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 32),
        _AboutRow(label: 'Author', value: AppVersion.author),
        const SizedBox(height: 12),
        _AboutRow(label: 'Build Date', value: AppVersion.buildDate),
        const SizedBox(height: 12),
        _AboutRow(label: 'Backend', value: 'Internet Archive (S3 API)'),
        const SizedBox(height: 12),
        _AboutRow(label: 'Encryption', value: 'AES-256-GCM + PBKDF2-SHA256'),
        const SizedBox(height: 12),
        _AboutRow(label: 'License', value: 'Apache 2.0'),
        const SizedBox(height: 32),
        Text('Built with Flutter • https://aegisvault.app',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 11)),
      ]),
    );
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
        const SizedBox(height: 2),
        Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
      ])),
      const SizedBox(width: 16),
      trailing,
    ]);
  }
}

class _AboutRow extends StatelessWidget {
  final String label;
  final String value;
  const _AboutRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(label, style: const TextStyle(fontSize: 14, color: AppColors.textSecondary)),
      Text(value, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary, fontWeight: FontWeight.w500)),
    ]);
  }
}