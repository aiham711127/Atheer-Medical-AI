// lib/services/api_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatService {
  // الرابط الخاص بخادم FastAPI المحلي
  final String _baseUrl = 'http://127.0.0.1:8000/api/v1';

// --- 1. دالة الدردشة والبث المباشر (مع دعم الذاكرة) ---
  // أضفنا متغير history لاستقبال الذاكرة
  Stream<String> sendMessageStream(String message, {String role = "student", List<Map<String, String>> history = const []}) async* {
    final client = http.Client();
    final request = http.Request('POST', Uri.parse('$_baseUrl/chat'));
    
    request.headers['Content-Type'] = 'application/json';
    
    // تم إضافة الـ history إلى هيكل البيانات المرسلة
    request.body = jsonEncode({
      'query': message,
      'role': role,
      'history': history,
    });

    try {
      final response = await client.send(request);

      if (response.statusCode == 200) {
        await for (var chunk in response.stream.transform(utf8.decoder)) {
          yield chunk;
        }
      } else {
        yield "❌ خطأ من الخادم: كود ${response.statusCode}";
      }
    } catch (e) {
      yield "🔌 تعذر الاتصال بالخادم. تأكد من تشغيله في بيئة بايثون.";
    } finally {
      client.close();
    }
  }

  // --- 2. دالة رفع الملفات (التحديث الجديد) ---
  Future<String> uploadPdfFile(String filePath) async {
    try {
      // تجهيز رابط الرفع
      var uri = Uri.parse('$_baseUrl/upload');
      
      // استخدام MultipartRequest المخصص لرفع الملفات
      var request = http.MultipartRequest('POST', uri);

      // قراءة الملف من مساره وإضافته للطلب تحت اسم 'file' (كما يتوقع FastAPI)
      request.files.add(await http.MultipartFile.fromPath('file', filePath));

      // إرسال الطلب للخادم
      var streamedResponse = await request.send();
      
      // استقبال النتيجة وتحويلها لنص مقروء
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        // فك تشفير استجابة الخادم (JSON)
        var jsonResponse = jsonDecode(utf8.decode(response.bodyBytes));
        return jsonResponse['message'] ?? "تم الرفع بنجاح.";
      } else {
        // في حال رفض الخادم للملف (مثلاً صيغة غير مدعومة)
        return "❌ فشل رفع الملف. كود الخطأ: ${response.statusCode}";
      }
    } catch (e) {
      return "🔌 تعذر الاتصال بالخادم أثناء الرفع. تحقق من اتصال الشبكة.";
    }
  }
}