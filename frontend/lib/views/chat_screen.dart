import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // ضروري لخاصية النسخ (Clipboard)
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:file_selector/file_selector.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ChatService _chatService = ChatService();
  final List<ChatMessage> _messages = []; // هذه قائمة واجهة المستخدم
  // === [إضافة جديدة]: قائمة الذاكرة التي سنرسلها للخادم ===
  final List<Map<String, String>> _apiHistory = [];

  bool _isLoading = false;
  String _selectedRole = 'student';

  void _sendMessage() async {
    if (_controller.text.trim().isEmpty) return;

    String userText = _controller.text;

    // نأخذ نسخة من الذاكرة الحالية (قبل إضافة السؤال الجديد) لنرسلها للخادم
    List<Map<String, String>> historyToSend = List.from(_apiHistory);

    setState(() {
      _messages.add(ChatMessage(text: userText, isUser: true));
      _messages.add(ChatMessage(text: "", isUser: false));
      _isLoading = true;
    });

    _controller.clear();
    _scrollToBottom();

    // إضافة سؤال المستخدم لمتغير الذاكرة للمرات القادمة
    _apiHistory.add({"role": "user", "content": userText});

    String fullAiResponse = ""; // متغير لتجميع إجابة الذكاء الاصطناعي بالكامل

    // نمرر الذاكرة (historyToSend) في الاستدعاء
    await for (String chunk in _chatService.sendMessageStream(
      userText,
      role: _selectedRole,
      history: historyToSend,
    )) {
      setState(() {
        _messages.last.text += chunk;
        fullAiResponse += chunk;
      });
      _scrollToBottom();
    }

    // بعد انتهاء البث، نحفظ إجابة "أثير" في الذاكرة
    if (fullAiResponse.isNotEmpty &&
        !fullAiResponse.startsWith("❌") &&
        !fullAiResponse.startsWith("🔌")) {
      _apiHistory.add({"role": "assistant", "content": fullAiResponse});
    }

    setState(() {
      _isLoading = false;
    });
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 50), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 100),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'تم نسخ النص بنجاح!',
          style: TextStyle(fontFamily: 'Cairo'),
        ),
        backgroundColor: Colors.teal,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  // --- دالة رفع الملف ---
  void _showUploadDialog() {
    // (نفس الكود السابق للنافذة المنبثقة)
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (BuildContext context) {
        return Container(
          padding: const EdgeInsets.all(24),
          height: 200,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "إضافة بحث طبي جديد",
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.teal,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                "قم برفع ملف PDF ليقوم 'أثير' بقراءته وإضافته لقاعدة المعرفة.",
                style: TextStyle(color: Colors.grey),
              ),
              const Spacer(),
              Center(
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    _pickAndUploadFile();
                  },
                  icon: const Icon(Icons.upload_file, color: Colors.white),
                  label: const Text(
                    "اختيار ورفع ملف PDF",
                    style: TextStyle(fontSize: 16, color: Colors.white),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 40,
                      vertical: 15,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _pickAndUploadFile() async {
    // (نفس كود الرفع السابق)
    try {
      const XTypeGroup typeGroup = XTypeGroup(
        label: 'PDF Documents',
        extensions: <String>['pdf'],
      );
      final XFile? file = await openFile(
        acceptedTypeGroups: <XTypeGroup>[typeGroup],
      );
      if (file != null) {
        setState(() {
          _messages.add(
            ChatMessage(
              text: "جاري تحليل البحث: '${file.name}' ⏳...",
              isUser: true,
            ),
          );
          _isLoading = true;
        });
        _scrollToBottom();
        String uploadResponse = await _chatService.uploadPdfFile(file.path);
        setState(() {
          _messages.add(ChatMessage(text: "✅ $uploadResponse", isUser: false));
          _isLoading = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      setState(
        () => _messages.add(ChatMessage(text: "❌ حدث خطأ: $e", isUser: false)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      // لون خلفية عصري فاتح جداً
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const UserAccountsDrawerHeader(
              accountName: Text(
                "م. أيهم البخيتي",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
              accountEmail: Text("aiham711127@gmail.com"),
              currentAccountPicture: CircleAvatar(
                backgroundColor: Colors.white,
                child: Icon(Icons.person, size: 40, color: Colors.teal),
              ),
              decoration: BoxDecoration(color: Colors.teal),
            ),
            ListTile(
              leading: const Icon(Icons.history, color: Colors.teal),
              title: const Text('سجل المحادثات'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.settings, color: Colors.teal),
              title: const Text('إعدادات التطبيق'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.privacy_tip, color: Colors.teal),
              title: const Text('الخصوصية والأمان'),
              onTap: () => Navigator.pop(context),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.redAccent),
              title: const Text(
                'تسجيل الخروج',
                style: TextStyle(color: Colors.redAccent),
              ),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
      appBar: AppBar(
        title: const Text(
          "أثير الطبي",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                dropdownColor: Colors.teal[800],
                value: _selectedRole,
                icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
                items: const [
                  DropdownMenuItem(value: 'student', child: Text('👨‍🎓 طالب')),
                  DropdownMenuItem(value: 'doctor', child: Text('👨‍⚕️ طبيب')),
                ],
                onChanged: (value) {
                  if (value != null) setState(() => _selectedRole = value);
                },
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(
                horizontal: 16.0,
                vertical: 20.0,
              ),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];

                // تصميم فقاعة الدردشة الاحترافية
                return Container(
                  margin: const EdgeInsets.only(bottom: 24.0),
                  child: Row(
                    mainAxisAlignment: msg.isUser
                        ? MainAxisAlignment.end
                        : MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // أيقونة الذكاء الاصطناعي (أثير)
                      if (!msg.isUser)
                        Container(
                          margin: const EdgeInsets.only(
                            left: 12.0,
                          ), // مسافة من اليسار لدعم LTR/RTL
                          child: const CircleAvatar(
                            backgroundColor: Colors.teal,
                            radius: 18,
                            child: Icon(
                              Icons.health_and_safety,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                        ),

                      // مربع النص
                      Flexible(
                        child: Container(
                          padding: const EdgeInsets.all(18.0),
                          decoration: BoxDecoration(
                            color: msg.isUser ? Colors.teal[600] : Colors.white,
                            borderRadius: BorderRadius.circular(16.0).copyWith(
                              topRight: msg.isUser
                                  ? const Radius.circular(0)
                                  : const Radius.circular(16.0),
                              topLeft: !msg.isUser
                                  ? const Radius.circular(0)
                                  : const Radius.circular(16.0),
                            ),
                            boxShadow: msg.isUser
                                ? []
                                : [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.03),
                                      blurRadius: 10,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                            border: msg.isUser
                                ? null
                                : Border.all(color: Colors.grey.shade200),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              MarkdownBody(
                                data: msg.text,
                                selectable: true, // يتيح تحديد النص بالماوس
                                styleSheet: MarkdownStyleSheet(
                                  h3: TextStyle(
                                    color: msg.isUser
                                        ? Colors.white
                                        : Colors.teal[800],
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  p: TextStyle(
                                    fontSize: 15,
                                    color: msg.isUser
                                        ? Colors.white
                                        : const Color(0xFF2C3E50),
                                    height: 1.6,
                                  ),
                                  strong: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: msg.isUser
                                        ? Colors.white
                                        : Colors.teal[900],
                                  ),
                                  horizontalRuleDecoration: BoxDecoration(
                                    border: Border(
                                      top: BorderSide(
                                        width: 1.0,
                                        color: Colors.grey.shade300,
                                      ),
                                    ),
                                  ),
                                ),
                              ),

                              // زر النسخ أسفل رد الذكاء الاصطناعي فقط
                              if (!msg.isUser && msg.text.isNotEmpty) ...[
                                const SizedBox(height: 10),
                                Divider(color: Colors.grey.shade200),
                                Align(
                                  alignment: Alignment.centerLeft,
                                  child: IconButton(
                                    icon: const Icon(
                                      Icons.copy_rounded,
                                      size: 20,
                                      color: Colors.grey,
                                    ),
                                    tooltip: 'نسخ الإجابة',
                                    onPressed: () => _copyToClipboard(msg.text),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),

                      // أيقونة المستخدم
                      if (msg.isUser)
                        Container(
                          margin: const EdgeInsets.only(right: 12.0),
                          child: CircleAvatar(
                            backgroundColor: Colors.teal[100],
                            radius: 18,
                            child: const Icon(
                              Icons.person,
                              color: Colors.teal,
                              size: 20,
                            ),
                          ),
                        ),
                    ],
                  ),
                );
              },
            ),
          ),

          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 5),
              child: LinearProgressIndicator(
                color: Colors.teal,
                backgroundColor: Colors.white,
              ),
            ),

          // منطقة إدخال النص الأنيقة
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 12.0,
            ),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 15,
                  offset: const Offset(0, -5),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  decoration: BoxDecoration(
                    color: Colors.teal[50],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.add, color: Colors.teal),
                    onPressed: _showUploadDialog,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _controller,
                    style: const TextStyle(fontSize: 15),
                    decoration: InputDecoration(
                      hintText: "اسأل أثير عن أي حالة طبية...",
                      hintStyle: TextStyle(color: Colors.grey.shade400),
                      filled: true,
                      fillColor: const Color(0xFFF4F6F8),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20.0),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 14,
                      ),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 12),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.teal,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.send_rounded, color: Colors.white),
                    onPressed: _sendMessage,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
