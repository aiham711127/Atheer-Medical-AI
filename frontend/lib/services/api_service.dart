// مسار الملف: lib/services/api_service.dart
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl = "http://127.0.0.1:8000"; 
  http.Client? _httpClient;

  Stream<Map<String, dynamic>> sendMessageStream(String message, String token) async* {
    _httpClient = http.Client();
    final request = http.Request('POST', Uri.parse('$baseUrl/api/v1/chat'));
    
    request.headers.addAll({
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    });

    // 🔴 تم إصلاح خطأ 422 هنا بتعديل المسميات وإضافة history
    request.body = jsonEncode({
      "query": message,
      "history": [], 
    });

    try {
      final response = await _httpClient!.send(request);

      if (response.statusCode != 200) {
        yield {"type": "error", "message": "فشل الاتصال بالخادم. الرمز: ${response.statusCode}"};
        return;
      }

      final stream = response.stream.transform(utf8.decoder).transform(const LineSplitter());
      String currentEvent = "";
      
      await for (final line in stream) {
        if (line.isEmpty) {
          currentEvent = "";
          continue;
        }

        if (line.startsWith("event:")) {
          currentEvent = line.substring(6).trim();
        } else if (line.startsWith("data:")) {
          final dataString = line.substring(5).trim();
          try {
            final dynamic decoded = jsonDecode(dataString);
            if (decoded is Map) {
              final Map<String, dynamic> dataJson = Map<String, dynamic>.from(decoded);
              if (currentEvent.isNotEmpty) {
                dataJson['event_type'] = currentEvent; 
              }
              yield dataJson;
            }
          } catch (e) {
            print("JSON Error: $e");
          }
        }
      }
    } catch (e) {
      yield {"type": "error", "message": "تم إنهاء الاتصال أو حدث خطأ في الشبكة."};
    } finally {
      cancelRequest();
    }
  }

  void cancelRequest() {
    if (_httpClient != null) {
      _httpClient!.close();
      _httpClient = null;
    }
  }
}