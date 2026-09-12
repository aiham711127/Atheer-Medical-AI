import os
from pathlib import Path

# ==================== إعدادات الفلاتر ====================

# المجلدات التي يتم تجاهلها تمامًا في كل أنحاء المشروع
IGNORED_DIRS_GLOBAL = {
    '.git', '.vscode', '.idea', '__pycache__', 'venv', '.venv', 
    'env', '.env', 'node_modules', 'build', 'dist', '.dart_tool',
    '.flutter-plugins', '.flutter-plugins-dependencies', '.packages',
    '.metadata', 'android', 'ios', 'web', 'windows', 'macos', 'linux',
    'test', 'integration_test', 'coverage', 'docs'
}

# المجلدات التي يتم تجاهلها فقط داخل مشروع Flutter
FLUTTER_IGNORED_DIRS = {
    'android', 'ios', 'web', 'windows', 'macos', 'linux', 
    'test', 'integration_test', '.dart_tool', 'build'
}

# مجلدات Flutter المسموح دخولها (فقط lib + ملفات الجذر)
FLUTTER_ALLOWED_DIRS = {'lib'}

# الامتدادات المسموحة
ALLOWED_EXTENSIONS = {'.py', '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.sql', '.md', '.txt'}

# ==================== دوال المساعدة ====================

def is_flutter_project(path: Path) -> bool:
    """التحقق إذا كان المجلد هو مشروع Flutter (يحتوي على pubspec.yaml)"""
    return (path / "pubspec.yaml").exists()

def is_inside_flutter(path: Path, root: Path) -> bool:
    """التحقق إذا كان المسار داخل مشروع Flutter"""
    # نبحث عن pubspec.yaml في أي مستوى أعلى المسار الحالي
    try:
        for parent in path.relative_to(root).parents:
            check_path = root / parent
            if is_flutter_project(check_path):
                return True
        # نتحقق أيضًا من الجذر المباشر
        if is_flutter_project(path):
            return True
    except ValueError:
        pass
    return False

def should_ignore_dir(dir_name: str, current_path: Path, root: Path) -> bool:
    """تحديد ما إذا كان يجب تجاهل المجلد"""
    # تجاهل المجلدات المخفية والعامة
    if dir_name.startswith('.') or dir_name in IGNORED_DIRS_GLOBAL:
        return True
    
    # إذا كان داخل مشروع Flutter، نطبق قواعد Flutter
    if is_inside_flutter(current_path, root):
        # إذا كان المجلد الحالي هو جذر Flutter، نسمح فقط بـ lib
        if is_flutter_project(current_path):
            return dir_name not in FLUTTER_ALLOWED_DIRS
        # إذا كان داخل lib، نسمح بكل شيء (مع تجاهل العام)
        return False
    
    return False

def is_allowed_file(file_name: str) -> bool:
    """تحديد ما إذا كان الملف مسموحًا به"""
    ext = Path(file_name).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return True
    if file_name.lower() in {'dockerfile', 'makefile', 'requirements.txt', 'pipfile', 'pipfile.lock'}:
        return True
    return False

# ==================== منطق الاستخراج ====================

def extract_structure(root_path: str, output_file: str = "project_structure.txt"):
    root = Path(root_path).resolve()
    lines = []
    lines.append(f"📁 هيكل المشروع: {root.name}")
    lines.append(f"📍 المسار: {root}")
    lines.append("=" * 70)
    lines.append("")

    for dirpath, dirnames, filenames in os.walk(root):
        current_path = Path(dirpath)
        
        # فلترة المجلدات
        original_dirs = list(dirnames)
        dirnames[:] = []
        
        for d in original_dirs:
            if not should_ignore_dir(d, current_path, root):
                dirnames.append(d)
        
        rel_path = current_path.relative_to(root)
        depth = len(rel_path.parts)
        
        # تخطي إذا كان المجلد الحالي نفسه مجلد Flutter ولم نكن في lib
        if is_flutter_project(current_path) and depth > 0:
            # نعرض الجذر فقط
            pass
        
        indent = "    " * depth
        folder_name = current_path.name if depth > 0 else root.name
        
        lines.append(f"{indent}📂 {folder_name}/")
        
        # إضافة الملفات المسموحة
        file_indent = "    " * (depth + 1)
        allowed_files = [f for f in filenames if is_allowed_file(f)]
        
        for file in sorted(allowed_files):
            lines.append(f"{file_indent}📄 {file}")
        
        if not allowed_files and not dirnames and depth > 0:
            lines.append(f"{file_indent}(فارغ)")
    
    # حفظ الملف
    output_path = root / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ تم حفظ الهيكل في: {output_path}")
    print(f"📊 عدد الأسطر: {len(lines)}")
    return output_path

# ==================== التشغيل ====================

if __name__ == "__main__":
    project_path = input("أدخل مسار المشروع (اضغط Enter للمسار الحالي): ").strip()
    if not project_path:
        project_path = "."
    
    extract_structure(project_path)
    print("\n🎉 اكتمل الاستخراج بنجاح!")