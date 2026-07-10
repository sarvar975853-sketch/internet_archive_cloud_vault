import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

enum ToastType { info, success, error, warning }

class ToastWidget extends StatelessWidget {
  final String message;
  final ToastType type;
  final VoidCallback? onDismiss;

  const ToastWidget({
    super.key,
    required this.message,
    this.type = ToastType.info,
    this.onDismiss,
  });

  Color get _color {
    switch (type) {
      case ToastType.success: return AppColors.success;
      case ToastType.error: return AppColors.error;
      case ToastType.warning: return AppColors.warning;
      case ToastType.info: return AppColors.info;
    }
  }

  IconData get _icon {
    switch (type) {
      case ToastType.success: return Icons.check_circle;
      case ToastType.error: return Icons.error;
      case ToastType.warning: return Icons.warning;
      case ToastType.info: return Icons.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.surfaceBg,
          borderRadius: const BorderRadius.all(Radius.circular(12)),
          border: Border.all(color: _color.withOpacity(0.5)),
          boxShadow: [
            BoxShadow(
              color: _color.withOpacity(0.15),
              blurRadius: 20,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(_icon, color: _color, size: 20),
            const SizedBox(width: 12),
            Flexible(
              child: Text(message, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
            ),
            if (onDismiss != null) ...[
              const SizedBox(width: 12),
              GestureDetector(
                onTap: onDismiss,
                child: const Icon(Icons.close, size: 16, color: AppColors.textMuted),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class ToastManager {
  static OverlayEntry? _show({
    required BuildContext context,
    required String message,
    required ToastType type,
    Duration duration = const Duration(seconds: 3),
  }) {
    final overlay = Overlay.of(context);
    late OverlayEntry entry;

    entry = OverlayEntry(
      builder: (context) => Positioned(
        bottom: 24,
        left: 0,
        right: 0,
        child: Material(
          color: Colors.transparent,
          child: _ToastDismiss(
            child: ToastWidget(
              message: message,
              type: type,
              onDismiss: () => entry.remove(),
            ),
            onDismiss: () => entry.remove(),
          ),
        ),
      ),
    );

    overlay.insert(entry);
    Future.delayed(duration, () {
      if (entry.mounted) entry.remove();
    });
    return entry;
  }

  static void info(BuildContext context, String message) =>
      _show(context: context, message: message, type: ToastType.info);
  static void success(BuildContext context, String message) =>
      _show(context: context, message: message, type: ToastType.success);
  static void error(BuildContext context, String message) =>
      _show(context: context, message: message, type: ToastType.error);
  static void warning(BuildContext context, String message) =>
      _show(context: context, message: message, type: ToastType.warning);
}

class _ToastDismiss extends StatefulWidget {
  final Widget child;
  final VoidCallback onDismiss;
  const _ToastDismiss({required this.child, required this.onDismiss});

  @override
  State<_ToastDismiss> createState() => _ToastDismissState();
}

class _ToastDismissState extends State<_ToastDismiss>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _fadeAnim = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.5),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnim,
      child: SlideTransition(
        position: _slideAnim,
        child: widget.child,
      ),
    );
  }
}
