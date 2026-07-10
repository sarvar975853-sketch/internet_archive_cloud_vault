import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/toast.dart';

class ExplorerScreen extends StatefulWidget {
  final String? currentFolder;
  final List<Map<String, dynamic>> files;
  final void Function(List<String> filenames, String password, bool samePassword)? onDownload;
  final void Function(String filename)? onDelete;
  final bool isLoading;

  const ExplorerScreen({
    super.key,
    this.currentFolder,
    this.files = const [],
    this.onDownload,
    this.onDelete,
    this.isLoading = false,
  });

  @override
  State<ExplorerScreen> createState() => _ExplorerScreenState();
}

class _ExplorerScreenState extends State<ExplorerScreen> {
  final _searchController = TextEditingController();
  final _passwordController = TextEditingController();
  final Set<int> _selectedIndices = {};
  bool _samePassword = true;
  bool _obscurePassword = true;
  bool _showPasswordPrompt = false;

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
    _passwordController.dispose();
    super.dispose();
  }

  void _download() {
    if (_selectedIndices.isEmpty) {
      ToastManager.warning(context, 'No files selected');
      return;
    }
    final files = _selectedIndices.map((i) => _filteredFiles[i]['name']?.toString() ?? '').toList();

    if (_samePassword) {
      if (_passwordController.text.isEmpty) {
        ToastManager.warning(context, 'Please enter decryption password');
        return;
      }
      widget.onDownload?.call(files, _passwordController.text, true);
      ToastManager.info(context, '${files.length} file(s) queued for download');
    } else {
      widget.onDownload?.call(files, '', false);
      ToastManager.info(context, '${files.length} file(s) queued. Password will be prompted per file.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      // Header
      Container(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
        child: Row(children: [
          Expanded(
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Search encrypted files...',
                prefixIcon: Icon(Icons.search, size: 20),
                isDense: true,
              ),
              onChanged: (_) => setState(() {}),
            ),
          ),
          const SizedBox(width: 12),
          if (widget.currentFolder != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.15),
                borderRadius: BorderRadius.all(Radius.circular(8)),
              ),
              child: Text(widget.currentFolder!, style: const TextStyle(fontSize: 13, color: AppColors.primary)),
            ),
        ]),
      ),
      const SizedBox(height: 16),
      // Actions bar
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Row(children: [
          Text('${widget.files.length} encrypted files', style: Theme.of(context).textTheme.titleMedium),
          const Spacer(),
          if (_selectedIndices.isNotEmpty) ...[
            Text('${_selectedIndices.length} selected', style: const TextStyle(fontSize: 13, color: AppColors.primary)),
            const SizedBox(width: 16),
            TextButton.icon(
              onPressed: () => setState(() => _showPasswordPrompt = !_showPasswordPrompt),
              icon: const Icon(Icons.download, size: 18),
              label: const Text('Download'),
            ),
            const SizedBox(width: 8),
            TextButton.icon(
              onPressed: _download,
              icon: const Icon(Icons.download, size: 18),
              label: const Text('Download Selected'),
              style: TextButton.styleFrom(foregroundColor: AppColors.primary),
            ),
          ],
        ]),
      ),
      // Password prompt
      if (_showPasswordPrompt)
        Container(
          margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
          padding: const EdgeInsets.all(16),
          decoration: const BoxDecoration(
            color: AppColors.surfaceBg,
            borderRadius: BorderRadius.all(Radius.circular(8)),
            border: Border.all(color: AppColors.borderDefault),
          ),
          child: Column(children: [
            Row(children: [
              const Text('Decryption Password', style: TextStyle(fontSize: 14)),
              const Spacer(),
              const Text('Same for all', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
              Switch(value: _samePassword, onChanged: (v) => setState(() => _samePassword = v), activeColor: AppColors.primary),
            ]),
            if (_samePassword) ...[
              const SizedBox(height: 8),
              TextField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                decoration: InputDecoration(
                  hintText: 'Enter decryption password',
                  suffixIcon: IconButton(
                    icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, size: 20),
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _download,
                child: Text('Download ${_selectedIndices.length} file(s)'),
              ),
            ),
          ]),
        ),
      const SizedBox(height: 8),
      // File list
      Expanded(
        child: widget.isLoading
            ? const Center(child: CircularProgressIndicator())
            : widget.files.isEmpty
                ? Center(
                    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(Icons.folder_open, size: 64, color: AppColors.textMuted.withOpacity(0.3)),
                      const SizedBox(height: 16),
                      const Text('No encrypted files found', style: TextStyle(fontSize: 16, color: AppColors.textMuted)),
                    ]),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    itemCount: _filteredFiles.length,
                    itemBuilder: (context, index) {
                      final file = _filteredFiles[index];
                      final name = file['name']?.toString() ?? '';
                      final size = file['size']?.toString() ?? '';
                      final isSelected = _selectedIndices.contains(index);
                      return Container(
                        margin: const EdgeInsets.only(bottom: 4),
                        decoration: BoxDecoration(
                          color: isSelected ? AppColors.primary.withOpacity(0.05) : AppColors.cardBg,
                          borderRadius: BorderRadius.all(Radius.circular(8)),
                          border: Border.all(color: isSelected ? AppColors.primary.withOpacity(0.3) : AppColors.borderDefault),
                        ),
                        child: ListTile(
                          onTap: () {
                            setState(() {
                              if (isSelected) {
                                _selectedIndices.remove(index);
                              } else {
                                _selectedIndices.add(index);
                              }
                            });
                          },
                          leading: Checkbox(
                            value: isSelected,
                            onChanged: (_) {
                              setState(() {
                                if (isSelected) {
                                  _selectedIndices.remove(index);
                                } else {
                                  _selectedIndices.add(index);
                                }
                              });
                            },
                            activeColor: AppColors.primary,
                          ),
                          title: Text(name, style: const TextStyle(fontSize: 14), overflow: TextOverflow.ellipsis),
                          subtitle: Text(size, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                          trailing: PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'copy') {
                                ToastManager.info(context, 'Filename copied');
                              } else if (value == 'delete') {
                                widget.onDelete?.call(name);
                              }
                            },
                            itemBuilder: (context) => [
                              const PopupMenuItem(value: 'copy', child: Text('Copy Filename')),
                              const PopupMenuItem(value: 'delete', child: Text('Delete')),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
      ),
    ]);
  }
}
