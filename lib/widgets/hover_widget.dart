import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class HoverButton extends StatefulWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final double borderWidth;
  final Color? borderColor;
  final Color? hoverBorderColor;
  final BorderRadius borderRadius;

  const HoverButton({
    super.key,
    required this.child,
    this.onPressed,
    this.borderWidth = 1,
    this.borderColor,
    this.hoverBorderColor,
    this.borderRadius = const BorderRadius.all(Radius.circular(8)),
  });

  @override
  State<HoverButton> createState() => _HoverButtonState();
}

class _HoverButtonState extends State<HoverButton> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final borderColor = _isHovered
        ? (widget.hoverBorderColor ?? AppColors.primary)
        : (widget.borderColor ?? Colors.transparent);

    return MouseRegion(
      onEnter: (_) => widget.onPressed != null ? setState(() => _isHovered = true) : null,
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          borderRadius: widget.borderRadius,
          border: Border.all(color: borderColor, width: widget.borderWidth),
          boxShadow: _isHovered
              ? [BoxShadow(color: AppColors.primary.withOpacity(0.15), blurRadius: 12, spreadRadius: 1)]
              : [],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: widget.borderRadius,
            onTap: widget.onPressed,
            child: widget.child,
          ),
        ),
      ),
    );
  }
}

class HoverWrapper extends StatefulWidget {
  final Widget child;
  final VoidCallback? onPressed;

  const HoverWrapper({super.key, required this.child, this.onPressed});

  @override
  State<HoverWrapper> createState() => _HoverWrapperState();
}

class _HoverWrapperState extends State<HoverWrapper> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          borderRadius: const BorderRadius.all(Radius.circular(8)),
          color: _isHovered ? AppColors.sidebarItemHover : Colors.transparent,
        ),
        child: widget.child,
      ),
    );
  }
}
