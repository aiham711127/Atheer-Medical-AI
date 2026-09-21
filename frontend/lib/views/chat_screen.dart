// مسار الملف: lib/views/chat_screen.dart
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';
import 'login_screen.dart';
// import 'package:file_picker/file_picker.dart'; // مكتبة رفع الملفات
import 'package:file_selector/file_selector.dart';

class ChatScreen extends StatefulWidget {
  final String userToken;
  const ChatScreen({Key? key, required this.userToken}) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late final String userToken;
  final ApiService _apiService = ApiService();
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessage> _messages = [];
  StreamSubscription? _streamSubscription;

  bool _isGenerating = false;
  String _currentStatus = "";

  // متغير لحفظ الملف الذي تم اختياره
  XFile? _selectedFile;
  // PlatformFile? _selectedFile;

  @override
  void initState() {
    super.initState();
    userToken = widget.userToken;
  }

  @override
  void dispose() {
    _streamSubscription?.cancel();
    _apiService.cancelRequest();
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  // دالة اختيار الملف (PDF وغيره)
Future<void> _pickFile() async {
    try {
      // تحديد الصيغ المسموحة
      const XTypeGroup typeGroup = XTypeGroup(
        label: 'documents',
        extensions: <String>['pdf', 'doc', 'docx', 'txt'],
      );
      
      // فتح نافذة اختيار الملفات الرسمية
      final XFile? file = await openFile(
        acceptedTypeGroups: <XTypeGroup>[typeGroup],
      );

      if (file != null) {
        setState(() {
          _selectedFile = file;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('حدث خطأ أثناء اختيار الملف')),
      );
    }
  }

  // دالة إزالة الملف المختار
  void _removeSelectedFile() {
    setState(() {
      _selectedFile = null;
    });
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    // يجب أن يكون هناك نص أو ملف للإرسال
    if ((text.isEmpty && _selectedFile == null) || _isGenerating) return;

    setState(() {
      // إذا كان هناك ملف، نضيف اسمه للمحادثة ليعرف المستخدم أنه تم إرساله
      String displayMessage = text;
      if (_selectedFile != null) {
        displayMessage += displayMessage.isEmpty
            ? "📁 مرفق: ${_selectedFile!.name}"
            : "\n\n📁 مرفق: ${_selectedFile!.name}";
      }

      _messages.add(ChatMessage(text: displayMessage, isUser: true));
      _messages.add(ChatMessage(text: "", isUser: false));
      _isGenerating = true;
      _currentStatus = "جاري معالجة البيانات...";
    });

    // تفريغ الحقول بعد الإرسال
    _messageController.clear();
    // حفظ الملف في متغير مؤقت للإرسال عبر الـ API ثم تفريغ الواجهة
    // ignore: unused_local_variable
    final fileToSend = _selectedFile;
    _removeSelectedFile();
    _scrollToBottom();

    /* 
     ملاحظة هامة للباك إند: 
     حالياً الدالة sendMessageStream ترسل النص فقط (JSON).
     إذا كان الباك إند الخاص بك يدعم استقبال ملفات (Multipart Form Data)، 
     يجب تعديل ApiService لتقوم بإرسال `fileToSend.bytes` أو مساره.
    */

    _streamSubscription = _apiService
        .sendMessageStream(text, userToken)
        .listen(
          (data) {
            setState(() {
              final eventType = data['event_type'];

              if (eventType == 'status') {
                _currentStatus = data['text'] ?? "";
              } else if (eventType == 'message') {
                _currentStatus = "";
                final currentText = _messages.last.text;
                final newChunk = data['text'] ?? "";
                _messages[_messages.length - 1] = ChatMessage(
                  text: currentText + newChunk,
                  isUser: false,
                );
              } else if (eventType == 'refusal') {
                _currentStatus = "";
                _messages[_messages.length - 1] = ChatMessage(
                  text: data['text'] ?? "تم رفض الطلب بدواعي السلامة الطبية.",
                  isUser: false,
                  isWarning: true,
                );
                _isGenerating = false;
              } else if (eventType == 'error') {
                _currentStatus = "";
                _messages[_messages.length - 1] = ChatMessage(
                  text: "⚠️ ${data['message'] ?? 'حدث خطأ في الاتصال'}",
                  isUser: false,
                  isWarning: true,
                );
                _isGenerating = false;
              }
            });
            _scrollToBottom();
          },
          onDone: () {
            setState(() {
              _isGenerating = false;
              _currentStatus = "";
            });
          },
          onError: (error) {
            setState(() {
              _isGenerating = false;
              _currentStatus = "";
              _messages[_messages.length - 1] = ChatMessage(
                text: "⚠️ انقطع الاتصال بالخادم.",
                isUser: false,
                isWarning: true,
              );
            });
          },
        );
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('تم نسخ النص بنجاح'),
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _logout() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text(
          "المساعد الطبي أثير",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        elevation: 0,
      ),
      drawer: Drawer(
        child: Column(
          children: [
            UserAccountsDrawerHeader(
              decoration: BoxDecoration(color: Theme.of(context).primaryColor),
              accountName: const Text(
                "م. أيهم البخيتي",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              accountEmail: const Text("aiham123@gmail.com"),
              currentAccountPicture: const CircleAvatar(
                backgroundColor: Colors.white,
                child: Icon(Icons.person, size: 40, color: Colors.teal),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.history),
              title: const Text('سجل المحادثات'),
              onTap: () {},
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.red),
              title: const Text(
                'تسجيل الخروج',
                style: TextStyle(color: Colors.red),
              ),
              onTap: _logout,
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _buildChatBubble(msg);
              },
            ),
          ),
          if (_isGenerating && _currentStatus.isNotEmpty)
            _buildTypingIndicator(),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildChatBubble(ChatMessage msg) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16.0),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.85,
        ),
        decoration: BoxDecoration(
          color: msg.isWarning
              ? Colors.red.shade50
              : (msg.isUser ? Theme.of(context).primaryColor : Colors.white),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(msg.isUser ? 16 : 0),
            bottomRight: Radius.circular(msg.isUser ? 0 : 16),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
          border: msg.isWarning ? Border.all(color: Colors.red.shade300) : null,
        ),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SelectableText(
                msg.text,
                style: TextStyle(
                  fontSize: 15.5,
                  height: 1.5,
                  color: msg.isWarning
                      ? Colors.red.shade900
                      : (msg.isUser ? Colors.white : Colors.black87),
                ),
              ),
              if (!msg.isUser && msg.text.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      InkWell(
                        onTap: () => _copyToClipboard(msg.text),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.copy,
                              size: 16,
                              color: Colors.grey.shade600,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              "نسخ",
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
      child: Row(
        children: [
          const SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 12),
          Text(
            _currentStatus,
            style: TextStyle(
              color: Colors.grey.shade600,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(12.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            offset: const Offset(0, -2),
            blurRadius: 10,
          ),
        ],
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // عرض الملف المختار فوق حقل النص
            if (_selectedFile != null)
              Container(
                margin: const EdgeInsets.only(bottom: 8.0),
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.teal.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.teal.shade200),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.picture_as_pdf,
                      color: Colors.redAccent,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        _selectedFile!.name,
                        style: TextStyle(
                          color: Colors.teal.shade900,
                          fontWeight: FontWeight.bold,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 8),
                    InkWell(
                      onTap: _removeSelectedFile,
                      child: const Icon(
                        Icons.close,
                        size: 20,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),

            // حقل النص وأزرار الإرسال والرفع
            Row(
              children: [
                // زر رفع الملفات مع تلميح (Tooltip)
                Tooltip(
                  message: "رفع ملف",
                  child: IconButton(
                    icon: Icon(Icons.attach_file, color: Colors.grey.shade700),
                    onPressed: _isGenerating ? null : _pickFile,
                  ),
                ),
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    maxLines: 4,
                    minLines: 1,
                    decoration: InputDecoration(
                      hintText: "اسأل أثير أو ارفع ملفاً...",
                      filled: true,
                      fillColor: Colors.grey.shade100,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  decoration: BoxDecoration(
                    color: _isGenerating
                        ? Colors.grey
                        : Theme.of(context).primaryColor,
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.arrow_upward, color: Colors.white),
                    onPressed: _isGenerating ? null : _sendMessage,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}


