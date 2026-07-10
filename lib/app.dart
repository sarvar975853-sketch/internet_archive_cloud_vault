import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/config.dart';
import 'core/credentials.dart';
import 'core/crypto.dart';
import 'core/storage.dart';
import 'core/queue_worker.dart';
import 'utils/logger.dart';
import 'theme/app_theme.dart';
import 'widgets/login_screen.dart';
import 'widgets/sidebar.dart';
import 'widgets/dashboard_screen.dart';
import 'widgets/upload_screen.dart';
import 'widgets/url_upload_screen.dart';
import 'widgets/explorer_screen.dart';
import 'widgets/files_screen.dart';
import 'widgets/omnifetch_screen.dart';
import 'widgets/settings_screen.dart';
import 'widgets/toast.dart';

class AegisVaultApp extends StatelessWidget {
  const AegisVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: MaterialApp(
        title: 'Aegis Vault',
        theme: AppTheme.darkTheme,
        debugShowCheckedModeBanner: false,
        home: const AegisVaultHome(),
      ),
    );
  }
}

class AppState extends ChangeNotifier {
  final AppConfig config = AppConfig();
  final CredentialManager credentialManager = CredentialManager();
  final CryptoEngine cryptoEngine = CryptoEngine();
  final AegisLogger aegisLogger = AegisLogger();

  IAStorageEngine? storageEngine;
  QueueWorker? queueWorker;

  bool isLoggedIn = false;
  bool isLoading = false;
  int currentTab = 0;
  String? currentFolder;
  List<String> folders = [];
  List<Map<String, dynamic>> encryptedFiles = [];
  List<Map<String, dynamic>> unencryptedFiles = [];
  Map<String, int> folderFileCounts = {};
  String totalStorage = '0 B';
  int totalFiles = 0;
  String? error;

  static const List<String> tabNames = [
    'Dashboard', 'Upload Queue', 'URL Upload', 'Explorer', 'Files',
  ];

  Future<void> init() async {
    await aegisLogger.init();
    aegisLogger.info('Aegis Vault starting...');
    final creds = await credentialManager.getCredentials();
    if (creds['access_key'] != null && creds['secret_key'] != null) {
      await startSession(creds['access_key']!, creds['secret_key']!);
    }
  }

  Future<void> startSession(String accessKey, String secretKey) async {
    isLoading = true;
    notifyListeners();

    try {
      storageEngine = IAStorageEngine(accessKey, secretKey);
      queueWorker = QueueWorker();
      folders = await storageEngine!.scanUserFolders();
      isLoggedIn = true;
      aegisLogger.info('Session started successfully');
      await _refreshDashboard();
    } catch (e) {
      error = 'Failed to start session: $e';
      aegisLogger.error('Session start failed', error: e);
    }

    isLoading = false;
    notifyListeners();
  }

  Future<void> _refreshDashboard() async {
    if (storageEngine == null) return;
    try {
      folderFileCounts = {};
      totalFiles = 0;
      for (final folder in folders) {
        final files = await storageEngine!.getFilesInBucket(folder);
        folderFileCounts[folder] = files.length;
        totalFiles += files.length;
      }
      totalStorage = '${(totalFiles * 5).toStringAsFixed(0)} MB'; // Estimate
    } catch (e) {
      aegisLogger.error('Dashboard refresh failed', error: e);
    }
  }

  Future<void> loadEncryptedFiles(String folder) async {
    if (storageEngine == null) return;
    isLoading = true;
    currentFolder = folder;
    notifyListeners();

    try {
      encryptedFiles = await storageEngine!.getFilesInBucket(folder);
    } catch (e) {
      error = 'Failed to load files: $e';
    }

    isLoading = false;
    notifyListeners();
  }

  Future<void> loadUnencryptedFiles(String folder) async {
    if (storageEngine == null) return;
    isLoading = true;
    currentFolder = folder;
    notifyListeners();

    try {
      unencryptedFiles = await storageEngine!.getFilesUnencrypted(folder);
    } catch (e) {
      error = 'Failed to load files: $e';
    }

    isLoading = false;
    notifyListeners();
  }

  void selectTab(int index) {
    currentTab = index;
    if (index == 0) _refreshDashboard();
    if (index == 3 && currentFolder != null) loadEncryptedFiles(currentFolder!);
    if (index == 4 && currentFolder != null) loadUnencryptedFiles(currentFolder!);
    notifyListeners();
  }

  void selectFolder(String folder) {
    currentFolder = folder;
    if (currentTab == 3) loadEncryptedFiles(folder);
    if (currentTab == 4) loadUnencryptedFiles(folder);
    notifyListeners();
  }

  Future<void> logout() async {
    await credentialManager.clearCredentials();
    queueWorker?.stop();
    storageEngine?.dispose();
    isLoggedIn = false;
    currentFolder = null;
    folders = [];
    encryptedFiles = [];
    unencryptedFiles = [];
    aegisLogger.info('Logged out');
    notifyListeners();
  }

  Future<void> uploadFiles(List<String> files, String folder, String password, bool encrypt) async {
    if (queueWorker == null || storageEngine == null) return;
    for (final filePath in files) {
      queueWorker!.submitTask(
        name: 'Upload $filePath',
        task: () async {
          if (encrypt) {
            final encPath = '$filePath.aegis_enc';
            cryptoEngine.encryptFile(filePath, password, encPath);
            await storageEngine!.uploadFile(encPath, filePath.split('/').last, folder);
          } else {
            await storageEngine!.uploadFileRaw(filePath, filePath.split('/').last, folder);
          }
          return null;
        },
      );
    }
  }

  void onTaskUpdate(String taskName, String status, dynamic result) {
    aegisLogger.info('Task $taskName: $status');
  }

  void dispose() {
    queueWorker?.stop();
    storageEngine?.dispose();
    aegisLogger.dispose();
    super.dispose();
  }
}

class AegisVaultHome extends StatefulWidget {
  const AegisVaultHome({super.key});

  @override
  State<AegisVaultHome> createState() => _AegisVaultHomeState();
}

class _AegisVaultHomeState extends State<AegisVaultHome> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().init();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(builder: (context, state, _) {
      if (!state.isLoggedIn) {
        return LoginScreen(
          onLogin: (access, secret) {
            state.startSession(access, secret);
          },
        );
      }
      return _buildWorkspace(state);
    });
  }

  Widget _buildWorkspace(AppState state) {
    return Scaffold(
      backgroundColor: AppColors.mainBg,
      body: Row(children: [
        // Sidebar
        Sidebar(
          folders: state.folders,
          currentFolder: state.currentFolder,
          onRefresh: () => state.selectFolder(state.currentFolder ?? ''),
          onCreateFolder: () => _showCreateFolderDialog(state),
          onFolderSelected: (folder) => state.selectFolder(folder),
          onManualFolder: (folder) => state.selectFolder(folder),
          onLogout: () => state.logout(),
        ),
        // Main content
        Expanded(
          child: Column(children: [
            // Top navigation
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: const BoxDecoration(
                border: Border(bottom: BorderSide(color: AppColors.borderDefault)),
              ),
              child: Row(children: [
                ...List.generate(AppState.tabNames.length, (i) => _NavPill(
                  label: AppState.tabNames[i],
                  isActive: state.currentTab == i,
                  onTap: () => state.selectTab(i),
                  shortcut: '${i + 1}',
                )),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.settings_outlined, size: 20),
                  onPressed: () => showDialog(
                    context: context,
                    builder: (context) => const SettingsScreen(),
                  ),
                  tooltip: 'Settings',
                ),
              ]),
            ),
            // Content area
            Expanded(child: _buildTabContent(state)),
          ]),
        ),
      ]),
    );
  }

  Widget _buildTabContent(AppState state) {
    switch (state.currentTab) {
      case 0:
        return DashboardScreen(
          folderFileCounts: state.folderFileCounts,
          totalStorage: state.totalStorage,
        );
      case 1:
        return UploadScreen(
          folders: state.folders,
          onUpload: (files, folder, password, encrypt) {
            state.uploadFiles(files, folder, password, encrypt);
          },
        );
      case 2:
        return UrlUploadScreen(
          folders: state.folders,
        );
      case 3:
        return ExplorerScreen(
          currentFolder: state.currentFolder,
          files: state.encryptedFiles,
          isLoading: state.isLoading,
        );
      case 4:
        return FilesScreen(
          currentFolder: state.currentFolder,
          files: state.unencryptedFiles,
          isLoading: state.isLoading,
        );
      default:
        return const SizedBox();
    }
  }

  void _showCreateFolderDialog(AppState state) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.cardBg,
        title: const Text('Create Folder'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Folder name',
            prefixIcon: Icon(Icons.folder),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              if (controller.text.isNotEmpty) {
                try {
                  await state.storageEngine?.createFolder(controller.text);
                  await state.startSession('', ''); // Refresh
                  if (context.mounted) Navigator.pop(context);
                  ToastManager.success(context, 'Folder created');
                } catch (e) {
                  ToastManager.error(context, 'Failed: $e');
                }
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }
}

class _NavPill extends StatelessWidget {
  final String label;
  final bool isActive;
  final VoidCallback onTap;
  final String shortcut;

  const _NavPill({
    required this.label,
    required this.isActive,
    required this.onTap,
    required this.shortcut,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: Material(
        color: isActive ? AppColors.primary.withOpacity(0.15) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Text(label, style: TextStyle(
                fontSize: 14,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
                color: isActive ? AppColors.primary : AppColors.textSecondary,
              )),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.surfaceBg,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(shortcut, style: TextStyle(fontSize: 10, color: AppColors.textMuted)),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
