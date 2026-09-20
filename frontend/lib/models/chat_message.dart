// مسار الملف: lib/models/chat_message.dart

// class ChatMessage {
//   String text;
//   final bool isUser;
//   final bool isWarning; // 🔴 الإضافة الجديدة لتمييز رسائل الرفض الطبي

//   ChatMessage({
//     required this.text,
//     required this.isUser,
//     this.isWarning = false, // القيمة الافتراضية: رسالة عادية (ليست تحذيراً)
//   });
// }
class ChatMessage {
  final String text;
  final bool isUser;
  final bool isWarning;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.isWarning = false,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}
