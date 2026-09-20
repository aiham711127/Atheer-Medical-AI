// المسار: lib/main.dart

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'views/login_screen.dart';

void main() {
  runApp(const AtheerApp());
}

class AtheerApp extends StatelessWidget {
  const AtheerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'أثير الطبي',
      debugShowCheckedModeBanner: false,
      // ضبط الاتجاه ليكون من اليمين لليسار (عربي)
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('ar', 'AE'), // دعم اللغة العربية
      ],
      theme: ThemeData(
        primarySwatch: Colors.teal,
        primaryColor: Colors.teal.shade700,
        fontFamily: 'Tajawal', // يُفضل إضافة خط عربي جميل في pubspec.yaml
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.teal.shade700,
            foregroundColor: Colors.white,
          ),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.teal.shade700,
          foregroundColor: Colors.white,
        ),
      ),
      home: const LoginScreen(), 
    );
  }
}