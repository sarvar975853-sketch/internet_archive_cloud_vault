import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../theme/app_theme.dart';

class Sidebar extends StatefulWidget {
  final List<String> folders;
  final String? currentFolder;
  final VoidCallback onRefresh;
  final VoidCallback onCreateFolder;
  final void Function(String) onFolderSelected;
  final void Function(String) onManualFolder;
  final VoidCallback onLogout;

  const Sidebar({
    super.key,
    required this.folders,
    this.currentFolder,
    required this.onRefresh,
    required this.onCreateFolder,
    required this.onFolderSelected,
    required this.onManualFolder,
    required this.onLogout,
  });

  @override
  State<Sidebar> createState() => _SidebarState();
}

class _SidebarState extends State<Sidebar> {
  final _folderController = TextEditingController();

  @override
  void dispose() {
    _folderController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 260,
      color: AppColors.sidebarBg,
      child: Column(
        children: [
          // Logo
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.borderDefault)),
            ),
            child: Row(
              children: [
                const Icon(Icons.shield, color: AppColors.primary, size: 28),
                const SizedBox(width: 12),
                Text('Aegis Vault',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 18)),
              ],
            ),
          ),
          // Folder header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('CLOUD FOLDERS',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontSize: 11, letterSpacing: 1.2, fontWeight: FontWeight.w600)),
                Row(
                  children: [
                    _IconButton(Icons.refresh, widget.onRefresh),
                    const SizedBox(width: 4),
                    _IconButton(Icons.create_new_folder, widget.onCreateFolder),
                  ],
                ),
              ],
            ),
          ),
          // Folder list
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              itemCount: widget.folders.length,
              itemBuilder: (context, index) {
                final folder = widget.folders[index];
                final isActive = folder == widget.currentFolder;
                return _FolderItem(
                  name: folder,
                  isActive: isActive,
                  onTap: () => widget.onFolderSelected(folder),
                );
              },
            ),
          ),
          // Manual folder entry
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: TextField(
              controller: _folderController,
              decoration: InputDecoration(
                hintText: 'Enter folder ID...',
                hintStyle: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.arrow_forward, size: 16),
                  onPressed: () {
                    if (_folderController.text.trim().isNotEmpty) {
                      widget.onManualFolder(_folderController.text.trim());
                      _folderController.clear();
                    }
                  },
                ),
              ),
              style: const TextStyle(fontSize: 13),
              onSubmitted: (value) {
                if (value.trim().isNotEmpty) {
                  widget.onManualFolder(value.trim());
                  _folderController.clear();
                }
              },
            ),
          ),
          // Storage donut chart
          const _StorageDonut(used: 60, total: 100),
          const SizedBox(height: 8),
          // Security indicator
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                const Icon(Icons.check_circle, size: 14, color: AppColors.success),
                const SizedBox(width: 8),
                Text('AES-256-GCM Encrypted',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 11)),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                const Icon(Icons.check_circle, size: 14, color: AppColors.success),
                const SizedBox(width: 8),
                Text('PBKDF2-SHA256 600K Iterations',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 11)),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Logout
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: widget.onLogout,
                icon: const Icon(Icons.logout, size: 16),
                label: const Text('Logout'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.textSecondary,
                  side: const BorderSide(color: AppColors.borderDefault),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text('v3.5.5', style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 10)),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _FolderItem extends StatelessWidget {
  final String name;
  final bool isActive;
  final VoidCallback onTap;

  const _FolderItem({required this.name, required this.isActive, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: Material(
        color: isActive ? AppColors.sidebarItemActive : Colors.transparent,
        borderRadius: const BorderRadius.all(Radius.circular(8)),
        child: InkWell(
          borderRadius: const BorderRadius.all(Radius.circular(8)),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Row(
              children: [
                Icon(Icons.folder, size: 18,
                    color: isActive ? AppColors.primary : AppColors.textMuted),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(name,
                      style: TextStyle(
                        fontSize: 13,
                        color: isActive ? AppColors.textPrimary : AppColors.textSecondary,
                      )),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _IconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;
  const _IconButton(this.icon, this.onPressed);

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: const BorderRadius.all(Radius.circular(6)),
        onTap: onPressed,
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: Icon(icon, size: 16, color: AppColors.textMuted),
        ),
      ),
    );
  }
}

class _StorageDonut extends StatelessWidget {
  final double used;
  final double total;
  const _StorageDonut({required this.used, required this.total});

  @override
  Widget build(BuildContext context) {
    final percentage = total > 0 ? used / total : 0.0;
    return SizedBox(
      width: 100, height: 100,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: const Size(100, 100),
            painter: _DonutPainter(percentage: percentage),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('${(percentage * 100).toStringAsFixed(0)}%',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary)),
              const Text('used', style: TextStyle(fontSize: 10, color: AppColors.textMuted)),
            ],
          ),
        ],
      ),
    );
  }
}

class _DonutPainter extends CustomPainter {
  final double percentage;
  _DonutPainter({required this.percentage});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 10;

    // Background circle
    final bgPaint = Paint()
      ..color = AppColors.progressBg
      ..style = PaintingStyle.stroke
      ..strokeWidth = 12;
    canvas.drawCircle(center, radius, bgPaint);

    // Progress arc
    final fgPaint = Paint()
      ..color = AppColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 12
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,
      2 * math.pi * percentage,
      false,
      fgPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _DonutPainter oldDelegate) =>
      oldDelegate.percentage != percentage;
}
