import 'package:flutter/material.dart';

class AppColors {
  // Primary
  static const Color primary = Color(0xFFF59E0B); // Amber
  static const Color primaryLight = Color(0xFFFBBF24);
  static const Color primaryDark = Color(0xFFD97706);

  // Backgrounds
  static const Color mainBg = Color(0xFF121010);
  static const Color cardBg = Color(0xFF1C1917);
  static const Color surfaceBg = Color(0xFF252220);
  static const Color inputBg = Color(0xFF1A1817);

  // Text
  static const Color textPrimary = Color(0xFFF5F0EB);
  static const Color textSecondary = Color(0xFFA8A29E);
  static const Color textMuted = Color(0xFF787571);

  // Borders
  static const Color borderDefault = Color(0xFF3A3735);
  static const Color borderFocus = Color(0xFFF59E0B);

  // Status
  static const Color success = Color(0xFF22C55E);
  static const Color error = Color(0xFFEF4444);
  static const Color warning = Color(0xFFF59E0B);
  static const Color info = Color(0xFF3B82F6);

  // Sidebar
  static const Color sidebarBg = Color(0xFF171514);
  static const Color sidebarItem = Color(0xFF252220);
  static const Color sidebarItemHover = Color(0xFF2F2C2A);
  static const Color sidebarItemActive = Color(0xFF3A3735);

  // Button variants
  static const Color buttonPrimary = Color(0xFFF59E0B);
  static const Color buttonPrimaryHover = Color(0xFFD97706);
  static const Color buttonSecondary = Color(0xFF3A3735);
  static const Color buttonSecondaryHover = Color(0xFF4A4745);
  static const Color buttonDanger = Color(0xFFDC2626);
  static const Color buttonDangerHover = Color(0xFFB91C1C);

  // Progress
  static const Color progressBg = Color(0xFF3A3735);
  static const Color progressFill = Color(0xFFF59E0B);
}

class AppTheme {
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: AppColors.primary,
      scaffoldBackgroundColor: AppColors.mainBg,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.primary,
        secondary: AppColors.primaryLight,
        surface: AppColors.cardBg,
        error: AppColors.error,
      ),
      cardColor: AppColors.cardBg,
      dividerColor: AppColors.borderDefault,
      fontFamily: 'SF Pro Display, Helvetica Neue, Arial, sans-serif',
      
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.mainBg,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
      ),

      textTheme: const TextTheme(
        headlineLarge: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w700),
        headlineMedium: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600),
        titleLarge: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600),
        titleMedium: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w500),
        bodyLarge: TextStyle(color: AppColors.textPrimary),
        bodyMedium: TextStyle(color: AppColors.textSecondary),
        bodySmall: TextStyle(color: AppColors.textMuted),
        labelLarge: TextStyle(color: AppColors.textPrimary),
        labelMedium: TextStyle(color: AppColors.textSecondary),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.inputBg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.borderDefault),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.borderDefault),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.borderFocus, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.error),
        ),
        labelStyle: const TextStyle(color: AppColors.textSecondary),
        hintStyle: const TextStyle(color: AppColors.textMuted),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.buttonPrimary,
          foregroundColor: AppColors.mainBg,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.textPrimary,
          side: const BorderSide(color: AppColors.borderDefault),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primary,
        ),
      ),

      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: AppColors.progressFill,
        backgroundColor: AppColors.progressBg,
      ),

      dialogTheme: DialogTheme(
        backgroundColor: AppColors.cardBg,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.surfaceBg,
        contentTextStyle: const TextStyle(color: AppColors.textPrimary),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
