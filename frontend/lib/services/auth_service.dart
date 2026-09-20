// lib/services/auth_service.dart
// import 'dart:convert';
// import 'package:http/http.dart' as http;

// class AuthService {
//   final String baseUrl = "http://127.0.0.1:8000";

//   Future login(String username, String password) async {
//     final url = Uri.parse(
//       '$baseUrl/api/v1/auth/login',
//     ); // ⚠️ تأكد أن هذا هو مسار تسجيل الدخول في خادمك (قد يكون /api/v1/auth/login)
    

//     try {
//       final response = await http.post(
//         url,
//         headers: {'Content-Type': 'application/x-www-form-urlencoded'},
//         // خادم FastAPI يتوقع البيانات كـ Form-Url-Encoded
//         body: {'username': username, 'password': password},
//       );

//       if (response.statusCode == 200) {
//         final data = jsonDecode(response.body);
//         print("RECEIVED TOKEN: ${data['access_token']}");// 🔴
//         return data['access_token']; // إرجاع التوكن الحقيقي والجديد
        
//       } else {
//         print(
//           "خطأ في تسجيل الدخول: \({response.statusCode} -\){response.body}",
//         );
//         return null; // فشل المصادقة
//       }
//     } catch (e) {
//       print("خطأ في الاتصال بالخادم: $e");
//       return null;
//     }
//   }
// }

import 'dart:convert';
import 'package:http/http.dart' as http;

class AuthService {
  final String baseUrl = "http://127.0.0.1:8000";

  Future<String?> login(String username, String password) async {
    final url = Uri.parse('$baseUrl/api/v1/auth/login');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {'username': username, 'password': password},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['access_token']; 
      } else {
        return null;
      }
    } catch (e) {
      return null;
    }
  }
}