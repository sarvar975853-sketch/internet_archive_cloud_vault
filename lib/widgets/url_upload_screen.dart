import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/toast.dart';

class UrlUploadScreen extends StatefulWidget {
  final void Function(List<String> urls, String folder, String password, bool encrypt, String mode)? onSubmit;
  final List<String> folders;

  const UrlUploadScreen({super.key, this.onSubmit, this.folders = const []});

  @override
  State<UrlUploadScreen> createState() => _UrlUploadScreenState();
}

class _UrlUploadScreenState extends State<UrlUploadScreen> {
  final _urlController = TextEditingController();
  final _passwordController = TextEditingController();
  final _folderController = TextEditingController();
  final List<UrlItem> _urls = [];
  bool _encrypt = true;
  bool _obscurePassword = true;
  String _mode = 'upload'; // 'upload' or 'disk'

  static const Map<String, Map<String, String>> providerInfo = {
    'google_drive': {'name': 'Google Drive', 'color': '#4285F4', 'icon': 'cloud'},
    'mediafire': {'name': 'MediaFire', 'color': '#FF6600', 'icon': 'cloud'},
    'mega': {'name': 'MEGA', 'color': '#D90007', 'icon': 'cloud'},
    'dropbox': {'name': 'Dropbox', 'color': '#0061FF', 'icon': 'cloud'},
    'onedrive': {'name': 'OneDrive', 'color': '#0078D4', 'icon': 'cloud'},
    'direct': {'name': 'Direct Link', 'color': '#666666', 'icon': 'link'},
  };

  @override
  void dispose() {
    _urlController.dispose();
    _passwordController.dispose();
    _folderController.dispose();
    super.dispose();
  }

  String _detectProvider(String url) {
    if (url.contains('drive.google.com') || url.contains('docs.google.com')) return 'google_drive';
    if (url.contains('mediafire.com')) return 'mediafire';
    if (url.contains('dropbox.com')) return 'dropbox';
    if (url.contains('1drv.ms') || url.contains('onedrive.live.com')) return 'onedrive';
    if (url.contains('mega.nz')) return 'mega';
    return 'direct';
  }

  void _addUrl() {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      ToastManager.warning(context, 'Please enter a URL');
      return;
    }
    setState(() {
      _urls.add(UrlItem(url: url, provider: _detectProvider(url)));
      _urlController.clear();
    });
  }

  void _removeUrl(int index) {
    setState(() => _urls.removeAt(index));
  }

  void _clearAll() {
    setState(() => _urls.clear());
  }

  void _submit() {
    if (_urls.isEmpty) {
      ToastManager.warning(context, 'No URLs added');
      return;
    }
    if (_mode == 'upload' && _folderController.text.trim().isEmpty) {
      ToastManager.warning(context, 'Please enter a target folder');
      return;
    }
    if (_mode == 'upload' && _encrypt && _passwordController.text.isEmpty) {
      ToastManager.warning(context, 'Please enter an encryption password');
      return;
    }
    widget.onSubmit?.call(
      _urls.map((u) => u.url).toList(),
      _folderController.text.trim(),
      _passwordController.text,
      _encrypt,
      _mode,
    );
    ToastManager.success(context, '${_urls.length} URL(s) queued');
    _clearAll();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('URL Upload', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28)),
        const SizedBox(height: 8),
        Text('Download from URL and upload to vault, or save directly to disk.', style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 24),
        // Provider badges
        Wrap(spacing: 8, runSpacing: 8, children: providerInfo.entries.map((e) => Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: Color(int.parse(e.value['color']!.replaceAll('#', '0xFF'))).withOpacity(0.15),
            borderRadius: const BorderRadius.all(Radius.circular(16)),
            border: Border.all(color: Color(int.parse(e.value['color']!.replaceAll('#', '0xFF'))).withOpacity(0.3)),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.cloud, size: 14, color: Color(int.parse(e.value['color']!.replaceAll('#', '0xFF')))),
            const SizedBox(width: 6),
            Text(e.value['name']!, style: TextStyle(fontSize: 12, color: Color(int.parse(e.value['color']!.replaceAll('#', '0xFF'))))),
          ]),
        )).toList()),
        const SizedBox(height: 20),
        // URL input
        Row(children: [
          Expanded(
            child: TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'File URL', hintText: 'Paste a URL from any supported provider',
                prefixIcon: Icon(Icons.link, size: 20),
              ),
              onSubmitted: (_) => _addUrl(),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(height: 48, child: ElevatedButton(onPressed: _addUrl, child: const Text('Add URL'))),
        ]),
        const SizedBox(height: 20),
        // URL list
        if (_urls.isNotEmpty) ...[
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text('${_urls.length} URL(s)', style: Theme.of(context).textTheme.titleMedium),
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
              shrinkWrap: true, itemCount: _urls.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final item = _urls[index];
                final info = providerInfo[item.provider] ?? providerInfo['direct']!;
                return ListTile(
                  dense: true,
                  leading: Icon(Icons.cloud, size: 20, color: Color(int.parse(info['color']!.replaceAll('#', '0xFF')))),
                  title: Text(item.url, style: const TextStyle(fontSize: 13), overflow: TextOverflow.ellipsis),
                  subtitle: Text(info['name']!, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                  trailing: IconButton(icon: const Icon(Icons.close, size: 16), onPressed: () => _removeUrl(index)),
                );
              },
            ),
          ),
          const SizedBox(height: 20),
        ],
        // Mode selector
        Row(children: [
          _ModeChip(label: 'Upload to Vault', value: 'upload', selected: _mode == 'upload', onSelected: () => setState(() => _mode = 'upload')),
          const SizedBox(width: 12),
          _ModeChip(label: 'Download to Disk', value: 'disk', selected: _mode == 'disk', onSelected: () => setState(() => _mode = 'disk')),
        ]),
        const SizedBox(height: 20),
        if (_mode == 'upload') ...[
          Autocomplete<String>(
            optionsBuilder: (textEditingValue) => widget.folders.where(
              (f) => f.toLowerCase().contains(textEditingValue.text.toLowerCase()),
            ),
            fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
              if (_folderController.text.isEmpty && controller.text.isNotEmpty) _folderController.text = controller.text;
              return TextField(
                controller: controller, focusNode: focusNode,
                decoration: const InputDecoration(labelText: 'Target Folder', hintText: 'e.g. Documents', prefixIcon: Icon(Icons.folder, size: 20)),
                onChanged: (v) => _folderController.text = v,
                onSubmitted: (_) => onSubmitted(),
              );
            },
          ),
          const SizedBox(height: 16),
          TextField(
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
          const SizedBox(height: 12),
          Row(children: [
            Switch(value: _encrypt, onChanged: (v) => setState(() => _encrypt = v), activeColor: AppColors.primary),
            const SizedBox(width: 8), const Text('Encrypt before uploading', style: TextStyle(fontSize: 14)),
          ]),
        ],
        const SizedBox(height: 24),
        SizedBox(
          width: 200, height: 48,
          child: ElevatedButton.icon(
            onPressed: _submit,
            icon: Icon(_mode == 'upload' ? Icons.cloud_upload : Icons.download, size: 20),
            label: Text(_mode == 'upload' ? 'Upload to Vault' : 'Download to Disk'),
          ),
        ),
      ]),
    );
  }
}

class UrlItem {
  final String url;
  final String provider;
  UrlItem({required this.url, required this.provider});
}

class _ModeChip extends StatelessWidget {
  final String label;
  final String value;
  final bool selected;
  final VoidCallback onSelected;
  const _ModeChip({required this.label, required this.value, required this.selected, required this.onSelected});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onSelected,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          color: selected ? AppColors.primary.withOpacity(0.15) : AppColors.cardBg,
          borderRadius: const BorderRadius.all(Radius.circular(8)),
          border: Border.all(color: selected ? AppColors.primary : AppColors.borderDefault),
        ),
        child: Text(label, style: TextStyle(
          fontSize: 14, fontWeight: FontWeight.w600,
          color: selected ? AppColors.primary : AppColors.textSecondary,
        )),
      ),
    );
  }
}