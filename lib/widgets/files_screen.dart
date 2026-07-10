import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/toast.dart';

class FilesScreen extends StatefulWidget {
  final String? currentFolder;
  final List<Map<String, dynamic>> files;
  final void Function(String filename)? onDownload;
  final void Function(String filename)? onDelete;
  final bool isLoading;

  const FilesScreen({
    super.key,
    this.currentFolder,
    this.files = const [],
    this.onDownload,
    this.onDelete,
    this.isLoading = false,
  });

  @override
  State<FilesScreen> createState() => _FilesScreenState();
}

class _FilesScreenState extends State<FilesScreen> {
  final _searchController = TextEditingController();
  final Set<int> _selectedIndices = {};

  List<Map<String, dynamic>> get _filteredFiles {
    final query = _searchController.text.toLowerCase();
    if (query.isEmpty) return widget.files;
    return widget.files.where((f) =>
      (f['name']?.toString() ?? '').toLowerCase().contains(query)
    ).toList();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Container(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
        child: Row(children: [
          Expanded(
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Search files...',
                prefixIcon: Icon(Icons.search, size: 20),
                isDense: true,
              ),
              onChanged: (_) => setState(() {}),
            ),
          ),
          if (widget.currentFolder != null) ...[
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(widget.currentFolder!, style: const TextStyle(fontSize: 13, color: AppColors.primary)),
            ),
          ],
        ]),
      ),
      const SizedBox(height: 16),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Row(children: [
          Text('${widget.files.length} files', style: Theme.of(context).textTheme.titleMedium),
          const Spacer(),
          if (_selectedIndices.isNotEmpty)
            Text('${_selectedIndices.length} selected', style: const TextStyle(fontSize: 13, color: AppColors.primary)),
        ]),
      ),
      const SizedBox(height: 8),
      Expanded(
        child: widget.isLoading
            ? const Center(child: CircularProgressIndicator())
            : widget.files.isEmpty
                ? Center(
                    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(Icons.insert_drive_file, size: 64, color: AppColors.textMuted.withOpacity(0.3)),
                      const SizedBox(height: 16),
                      Text('No files found', style: TextStyle(fontSize: 16, color: AppColors.textMuted)),
                    ]),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    itemCount: _filteredFiles.length,
                    itemBuilder: (context, index) {
                      final file = _filteredFiles[index];
                      final name = file['name']?.toString() ?? '';
                      final size = file['size']?.toString() ?? '';
                      return Container(
                        margin: const EdgeInsets.only(bottom: 4),
                        decoration: BoxDecoration(
                          color: AppColors.cardBg,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppColors.borderDefault),
                        ),
                        child: ListTile(
                          leading: Icon(_iconForFile(name), size: 20, color: AppColors.primary),
                          title: Text(name, style: const TextStyle(fontSize: 14), overflow: TextOverflow.ellipsis),
                          subtitle: Text(size, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                          trailing: PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'download') {
                                widget.onDownload?.call(name);
                                ToastManager.info(context, 'Downloading $name');
                              } else if (value == 'delete') {
                                widget.onDelete?.call(name);
                              }
                            },
                            itemBuilder: (context) => [
                              const PopupMenuItem(value: 'download', child: ListTile(leading: Icon(Icons.download, size: 18), title: Text('Download'))),
                              const PopupMenuItem(value: 'delete', child: ListTile(leading: Icon(Icons.delete, size: 18, color: AppColors.error), title: Text('Delete'))),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
      ),
    ]);
  }

  IconData _iconForFile(String name) {
    final ext = name.split('.').last.toLowerCase();
    switch (ext) {
      case 'jpg': case 'jpeg': case 'png': case 'gif': case 'webp':
        return Icons.image;
      case 'mp4': case 'mkv': case 'webm':
        return Icons.videocam;
      case 'mp3': case 'flac': case 'wav':
        return Icons.audiotrack;
      case 'pdf':
        return Icons.picture_as_pdf;
      case 'zip': case 'rar': case 'tar':
        return Icons.folder_zip;
      case 'doc': case 'docx':
        return Icons.description;
      default:
        return Icons.insert_drive_file;
    }
  }
}
