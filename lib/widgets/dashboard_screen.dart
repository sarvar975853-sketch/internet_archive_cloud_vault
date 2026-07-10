import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class DashboardScreen extends StatelessWidget {
  final Map<String, int> folderFileCounts;
  final String totalStorage;
  final Map<String, bool> engineStatus;

  const DashboardScreen({
    super.key,
    this.folderFileCounts = const {},
    this.totalStorage = '0 B',
    this.engineStatus = const {},
  });

  @override
  Widget build(BuildContext context) {
    final totalFolders = folderFileCounts.length;
    final totalFiles = folderFileCounts.values.fold(0, (a, b) => a + b);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Welcome
          Text('Dashboard', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28)),
          const SizedBox(height: 24),
          // Stat cards
          Row(
            children: [
              Expanded(child: _StatCard(icon: Icons.folder, label: 'Folders', value: '$totalFolders')),
              const SizedBox(width: 16),
              Expanded(child: _StatCard(icon: Icons.insert_drive_file, label: 'Files', value: '$totalFiles')),
              const SizedBox(width: 16),
              Expanded(child: _StatCard(icon: Icons.storage, label: 'Storage Used', value: totalStorage)),
              const SizedBox(width: 16),
              Expanded(child: _StatCard(
                icon: Icons.shield,
                label: 'Vault Status',
                value: 'Active',
                valueColor: AppColors.success,
              )),
            ],
          ),
          const SizedBox(height: 32),
          // Cloud folders
          Text('Cloud Folders', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          if (folderFileCounts.isEmpty)
            Container(
              padding: const EdgeInsets.all(32),
              decoration: const BoxDecoration(
                color: AppColors.cardBg,
                borderRadius: BorderRadius.all(Radius.circular(12)),
                border: Border.all(color: AppColors.borderDefault),
              ),
              child: Center(
                child: Text('No folders found. Create one or refresh.',
                    style: Theme.of(context).textTheme.bodyMedium),
              ),
            )
          else
            Wrap(
              spacing: 12, runSpacing: 12,
              children: folderFileCounts.entries.map((e) => _FolderCard(
                name: e.key,
                fileCount: e.value,
              )).toList(),
            ),
          const SizedBox(height: 32),
          // Engine Status
          if (engineStatus.isNotEmpty) ...[
            Text('Download Engine Status', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            Row(
              children: engineStatus.entries.map((e) => Padding(
                padding: const EdgeInsets.only(right: 16),
                child: _EngineBadge(
                  name: e.key,
                  available: e.value,
                ),
              )).toList(),
            ),
          ],
          const SizedBox(height: 32),
          // Quick actions
          Text('Quick Actions', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          Row(
            children: [
              const _ActionChip(icon: Icons.upload_file, label: 'Upload Files'),
              const SizedBox(width: 12),
              const _ActionChip(icon: Icons.link, label: 'URL Upload'),
              const SizedBox(width: 12),
              const _ActionChip(icon: Icons.download, label: 'Browse Files'),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;
  const _StatCard({required this.icon, required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.all(Radius.circular(12)),
        border: Border.all(color: AppColors.borderDefault),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppColors.primary, size: 24),
          const SizedBox(height: 12),
          Text(value, style: TextStyle(
            fontSize: 28, fontWeight: FontWeight.w700,
            color: valueColor ?? AppColors.textPrimary,
          )),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}

class _FolderCard extends StatelessWidget {
  final String name;
  final int fileCount;
  const _FolderCard({required this.name, required this.fileCount});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 180,
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.all(Radius.circular(12)),
        border: Border.all(color: AppColors.borderDefault),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.folder, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                    overflow: TextOverflow.ellipsis),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text('$fileCount files', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}

class _EngineBadge extends StatelessWidget {
  final String name;
  final bool available;
  const _EngineBadge({required this.name, required this.available});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: const BorderRadius.all(Radius.circular(8)),
        border: Border.all(color: available ? AppColors.success.withOpacity(0.3) : AppColors.error.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            available ? Icons.check_circle : Icons.cancel,
            size: 16,
            color: available ? AppColors.success : AppColors.error,
          ),
          const SizedBox(width: 8),
          Text(name, style: TextStyle(fontSize: 13, color: available ? AppColors.textPrimary : AppColors.textSecondary)),
        ],
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _ActionChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () {},
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.textPrimary,
        side: const BorderSide(color: AppColors.borderDefault),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      ),
    );
  }
}
