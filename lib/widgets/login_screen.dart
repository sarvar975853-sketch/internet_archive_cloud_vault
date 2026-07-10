import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../core/credentials.dart';

class LoginScreen extends StatefulWidget {
  final Function(String accessKey, String secretKey) onLogin;

  const LoginScreen({super.key, required this.onLogin});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _accessController = TextEditingController();
  final _secretController = TextEditingController();
  final _credentialManager = CredentialManager();
  bool _obscureSecret = true;
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSavedCredentials();
  }

  Future<void> _loadSavedCredentials() async {
    try {
      final creds = await _credentialManager.getCredentials();
      if (creds['access_key'] != null && creds['secret_key'] != null) {
        _accessController.text = creds['access_key']!;
        _secretController.text = creds['secret_key']!;
      }
    } catch (_) {}
  }

  Future<void> _handleLogin() async {
    final access = _accessController.text.trim();
    final secret = _secretController.text.trim();

    if (access.isEmpty || secret.isEmpty) {
      setState(() => _error = 'Please enter both Access Key and Secret Key');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      await _credentialManager.saveCredentials(access, secret);
      widget.onLogin(access, secret);
    } catch (e) {
      setState(() => _error = 'Failed to save credentials: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _accessController.dispose();
    _secretController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.mainBg,
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1000, maxHeight: 680),
          decoration: BoxDecoration(
            color: AppColors.cardBg,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: AppColors.borderDefault),
          ),
          child: Row(
            children: [
              // Left: Hero illustration area
              Expanded(
                flex: 5,
                child: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [AppColors.cardBg, AppColors.mainBg],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: const BorderRadius.horizontal(left: Radius.circular(24)),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Cloud icon
                      Icon(Icons.cloud, size: 120, color: AppColors.primary.withOpacity(0.15)),
                      const SizedBox(height: 24),
                      Text(
                        'Aegis Vault',
                        style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          fontSize: 42, fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Zero-Knowledge Encrypted Cloud Storage',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: AppColors.textSecondary, fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 48),
                      // Feature badges
                      Wrap(
                        spacing: 16, runSpacing: 12,
                        children: [
                          _FeatureBadge(icon: Icons.lock, label: 'AES-256-GCM Encryption'),
                          _FeatureBadge(icon: Icons.cloud_done, label: 'Internet Archive Backing'),
                          _FeatureBadge(icon: Icons.download, label: 'Multi-Threaded Downloads'),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              // Divider
              Container(width: 1, color: AppColors.borderDefault),
              // Right: Login form
              Expanded(
                flex: 4,
                child: Padding(
                  padding: const EdgeInsets.all(48),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Welcome Back',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Enter your Internet Archive S3 credentials',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 32),
                      // Access Key
                      TextField(
                        controller: _accessController,
                        decoration: const InputDecoration(
                          labelText: 'S3 Access Key',
                          hintText: 'Enter your IA S3 access key',
                          prefixIcon: Icon(Icons.vpn_key, size: 20),
                        ),
                      ),
                      const SizedBox(height: 16),
                      // Secret Key
                      TextField(
                        controller: _secretController,
                        obscureText: _obscureSecret,
                        decoration: InputDecoration(
                          labelText: 'S3 Secret Key',
                          hintText: 'Enter your IA S3 secret key',
                          prefixIcon: const Icon(Icons.lock, size: 20),
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscureSecret ? Icons.visibility_off : Icons.visibility,
                              size: 20,
                            ),
                            onPressed: () => setState(() => _obscureSecret = !_obscureSecret),
                          ),
                        ),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(_error!, style: const TextStyle(color: AppColors.error, fontSize: 13)),
                      ],
                      const SizedBox(height: 24),
                      // Login button
                      SizedBox(
                        height: 52,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _handleLogin,
                          child: _isLoading
                              ? const SizedBox(
                                  width: 24, height: 24,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                                )
                              : const Text('Unlock Vault'),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Your keys never leave this device.\nEncrypted at rest with AES-256.',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeatureBadge extends StatelessWidget {
  final IconData icon;
  final String label;
  const _FeatureBadge({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surfaceBg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderDefault),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 18, color: AppColors.primary),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}
