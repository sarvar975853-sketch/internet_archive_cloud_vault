import 'package:flutter/material.dart';
import 'package:desktop_drop/desktop_drop.dart';
import 'package:file_picker/file_picker.dart';
import '../theme/app_theme.dart';
import '../widgets/toast.dart';

class UploadFileItem {
  final String name;
  final String path;
  final int size;
  UploadFileItem({required this.name, required this.path, required this.size});
}

class UploadScreen extends StatefulWidget {
  final void Function(List<String> files, String folder, String password, bool encrypt)? onUpload;
  final List<String> folders;

  const UploadScreen({super.key, this.onUpload, this.folders = const []});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final List<UploadFileItem> _files = [];
  final _passwordController = TextEditingController();
  final _folderController = TextEditingController();
  bool _encrypt = true;
  bool _obscurePassword = true;
  bool _isDragging = false;

  @override
  void dispose() {
    _passwordController.dispose();
    _folderController.dispose();
    super.dispose();
  }

  void _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(allowMultiple: true);
    if (result != null && mounted) {
      setState(() {
        for (final file in result.files) {
          if (file.path != null) {
            _files.add(UploadFileItem(name: file.name, path: file.path!, size: file.size));
          }
        }
      });
    }
  }

  void _removeFile(int index) {
    setState(() => _files.removeAt(index));
  }

  void _clearAll() {
    setState(() => _files.clear());
  }

  void _submit() {
    if (_files.isEmpty) {
      ToastManager.warning(context, 'No files selected');
      return;
    }
    final folder = _folderController.text.trim();
    if (folder.isEmpty) {
      ToastManager.warning(context, 'Please enter a target folder');
      return;
    }
    if (_encrypt && _passwordController.text.isEmpty) {
      ToastManager.warning(context, 'Please enter an encryption password');
      return;
    }
    widget.onUpload?.call(
      _files.map((f) => f.path).toList(),
      folder,
      _passwordController.text,
      _encrypt,
    );
    ToastManager.success(context, '${_files.length} files queued for upload');
    _clearAll();
  }

  String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB';
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Upload Files', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28)),
          const SizedBox(height: 8),
          Text('Encrypt and upload files to your Internet Archive vault.', style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 24),
          DropTarget(
            onDragEntered: (_) => setState(() => _isDragging = true),
            onDragExited: (_) => setState(() => _isDragging = false),
            onDragDone: (detail) {
              setState(() {
                _isDragging = false;
                for (final file in detail.files) {
                  _files.add(UploadFileItem(name: file.name, path: file.path, size: 0));
                }
              });
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              height: 160,
              decoration: BoxDecoration(
                color: _isDragging ? AppColors.primary.withOpacity(0.05) : AppColors.cardBg,
                borderRadius: BorderRadius.all(Radius.circular(16)),
                border: Border.all(
                  color: _isDragging ? AppColors.primary : AppColors.borderDefault,
                  width: _isDragging ? 2 : 1,
                ),
              ),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.cloud_upload, size: 48, color: _isDragging ? AppColors.primary : AppColors.textMuted),
                    const SizedBox(height: 12),
                    const Text('Drop files here or', style: TextStyle(fontSize: 15, color: AppColors.textSecondary)),
                    const SizedBox(height: 8),
                    ElevatedButton.icon(
                      onPressed: _pickFiles,
                      icon: const Icon(Icons.folder_open, size: 18),
                      label: const Text('Browse Files'),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          if (_files.isNotEmpty) ...[
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('${_files.length} file(s) selected', style: Theme.of(context).textTheme.titleMedium),
              TextButton(onPressed: _clearAll, child: const Text('Clear All')),
            ]),
            const SizedBox(height: 8),
            Container(
              constraints: const BoxConstraints(maxHeight: 200),
              decoration: const BoxDecoration(
                color: AppColors.cardBg, borderRadius: BorderRadius.all(Radius.circular(8)),
                border: Border.all(color: AppColors.borderDefault),
              ),
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: _files.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final file = _files[index];
                  return ListTile(
                    dense: true,
                    leading: const Icon(Icons.insert_drive_file, size: 20, color: AppColors.primary),
                    title: Text(file.name, style: const TextStyle(fontSize: 14), overflow: TextOverflow.ellipsis),
                    subtitle: Text(_formatSize(file.size), style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                    trailing: IconButton(icon: const Icon(Icons.close, size: 16), onPressed: () => _removeFile(index)),
                  );
                },
              ),
            ),
            const SizedBox(height: 20),
          ],
          Row(children: [
            Expanded(
              child: Autocomplete<String>(
                optionsBuilder: (textEditingValue) => widget.folders.where(
                  (f) => f.toLowerCase().contains(textEditingValue.text.toLowerCase()),
                ),
                fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
                  if (_folderController.text.isEmpty && controller.text.isNotEmpty) {
                    _folderController.text = controller.text;
                  }
                  return TextField(
                    controller: controller, focusNode: focusNode,
                    decoration: const InputDecoration(
                      labelText: 'Target Folder', hintText: 'e.g. Documents',
                      prefixIcon: Icon(Icons.folder, size: 20),
                    ),
                    onChanged: (v) => _folderController.text = v,
                    onSubmitted: (_) => onSubmitted(),
                  );
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: TextField(
                controller: _passwordController,
                obscureText: _obscurePassword && _encrypt,
                enabled: _encrypt,
                decoration: InputDecoration(
                  labelText: 'Encryption Password', hintText: _encrypt ? 'Enter password' : 'No encryption',
                  prefixIcon: const Icon(Icons.lock, size: 20),
                  suffixIcon: _encrypt ? IconButton(
                    icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility, size: 20),
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                  ) : null,
                ),
              ),
            ),
          ]),
          const SizedBox(height: 12),
          Row(children: [
            Switch(value: _encrypt, onChanged: (v) => setState(() => _encrypt = v), activeColor: AppColors.primary),
            const SizedBox(width: 8),
            const Text('Encrypt files before upload', style: TextStyle(fontSize: 14)),
            if (!_encrypt) const Padding(
              padding: EdgeInsets.only(left: 12),
              child: Text('(Upload raw / unencrypted)', style: TextStyle(fontSize: 12, color: AppColors.warning)),
            ),
          ]),
          const SizedBox(height: 24),
          SizedBox(
            width: 200, height: 48,
            child: ElevatedButton.icon(
              onPressed: _submit,
              icon: const Icon(Icons.cloud_upload, size: 20),
              label: const Text('Upload to Vault'),
            ),
          ),
        ],
      ),
    );
  }
}