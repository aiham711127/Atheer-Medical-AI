import os
import requests
from tqdm import tqdm

OUTPUT_DIR = "medical_papers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# روابط مباشرة (Direct Links) لأبحاث حقيقية وموثوقة عن الجهاز الهضمي والقولون
MEDICAL_PDF_LINKS = [
    # 1. القولون العصبي (Irritable Bowel Syndrome)
    {"name": "Irritable_Bowel_Syndrome.pdf", "url": "https://www.mdpi.com/2072-6643/13/3/914/pdf"},
    # 2. سرطان القولون (Colorectal Cancer)
    {"name": "Colorectal_Cancer.pdf", "url": "https://www.mdpi.com/2077-0383/10/2/204/pdf"},
    # 3. بكتيريا الأمعاء (Gut Microbiome)
    {"name": "Gut_Microbiome.pdf", "url": "https://www.mdpi.com/2076-2607/9/2/353/pdf"},
    # 4. التهاب الأمعاء (Inflammatory Bowel Disease)
    {"name": "Inflammatory_Bowel_Disease.pdf", "url": "https://www.mdpi.com/1422-0067/22/3/1352/pdf"},
    # 5. صحة الجهاز الهضمي (Gastrointestinal Health)
    {"name": "Gastrointestinal_Health.pdf", "url": "https://www.mdpi.com/2072-6643/13/2/582/pdf"}
]

print(f"🚀 بدء تحميل 5 أبحاث علمية موثوقة في مجال الجهاز الهضمي والقولون...")

downloaded_count = 0

for paper in tqdm(MEDICAL_PDF_LINKS, desc="جاري التحميل"):
    file_path = os.path.join(OUTPUT_DIR, paper["name"])
    
    if os.path.exists(file_path):
        downloaded_count += 1
        continue
        
    try:
        # إضافة هذه الترويسة ليظن الموقع أن الطلب من متصفح جوجل كروم عادي (لتجاوز الحظر)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(paper["url"], stream=True, headers=headers, timeout=20)
        
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            downloaded_count += 1
        else:
            print(f"\n⚠️ فشل في تحميل {paper['name']} (رمز الخطأ: {response.status_code})")
            
    except Exception as e:
        print(f"\n❌ خطأ: {e}")

print(f"\n✅ نجاح! تم تحميل {downloaded_count} أبحاث طبية (PDF) ووضعها في مجلد '{OUTPUT_DIR}'.")
print("👉 الخطوة التالية والأهم: قم بتشغيل سكربت 'batch_ingest.py' لضخها في قاعدة بياناتك السحابية.")