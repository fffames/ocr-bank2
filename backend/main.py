from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from groq import Groq
import uvicorn
import io
import os
import json
from PIL import Image
import numpy as np

app = FastAPI()

# เพิ่ม CORS เพื่อให้ Next.js (Step 2) สามารถเรียกใช้งาน API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # ในโปรดักชันควรระบุ Domain ที่แน่นอน
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Initialize PaddleOCR (รองรับภาษาไทยและอังกฤษ)
# ครั้งแรกที่รันจะมีการดาวน์โหลดโมเดลอัตโนมัติ
ocr = PaddleOCR(use_angle_cls=True, lang='th') 

# 2. Initialize Groq Client
# ดึง API Key จาก Environment Variable เพื่อความปลอดภัย
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def process_with_groq(raw_text: str):
    """ส่ง Raw Text ไปให้ Groq จัดระเบียบเป็น JSON"""
    
    # ตรวจสอบว่ามีข้อความเพียงพอให้ประมวลผลหรือไม่
    if len(raw_text.strip()) < 10:
        return {
            "error": "Insufficient text extracted from OCR",
            "date": None, "time": None, "sender": None, "receiver": None, "amount": 0, "note": None
        }

    prompt = f"""
    You are an intelligent data extraction system.
    From raw text obtained via OCR of a transfer slip or receipt, extract the information into JSON format only, with the following fields:
        - date: Date in format YYYY-MM-DD using BUDDHIST ERA (BE) year - DO NOT convert to Gregorian/CE.
                - If the year is 4 digits starting with 25 (e.g., 2569), use it directly as-is.
                - If the year is 2 digits (e.g., 69), prepend "25" to make it 4-digit BE (e.g., 69 → 2569).
                - Examples: "17 เม.ย. 2569" → "2569-04-17", "30 เม.ย. 69" → "2569-04-30"
        - time: Time (format HH:mm)
        - sender: Name of sender - If keywords "จาก" (from) exist, use the name after it. Otherwise, the FIRST person's name found is the sender.
        - receiver: Name of receiver - If keywords "ไปยัง" or "ถึง" (to) exist, use the name after them. Otherwise, the SECOND person's name found is the receiver.
        - amount: Amount (numbers only)
        - note: Memo (if any; if none, put null)

    Raw Text:
    {raw_text}


    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON format. If text is gibberish, return null values."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"LLM Processing failed: {str(e)}"}

@app.post("/process-slip")
async def process_slip(file: UploadFile = File(...)):
    try:
        # อ่านไฟล์รูปภาพ
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # ปรับขนาดภาพเบื้องต้นถ้าภาพใหญ่หรือเล็กเกินไป (Optional Preprocessing)
        # image = image.resize((width, height)) 
        
        image_np = np.array(image)

        # 3. รัน PaddleOCR
        # เปลี่ยนลำดับสีจาก RGB เป็น BGR เพื่อให้แม่นยำขึ้นสำหรับ Paddle
        image_bgr = image_np[:, :, ::-1].copy()
        result = ocr.predict(image_bgr)
        
        # ตรวจสอบว่าพบข้อความหรือไม่
        if not result or len(result) == 0 or not result[0]:
            return {
                "status": "warning",
                "message": "No text detected in image",
                "raw_text": "",
                "structured_data": None
            }

        # รวม Text ที่สแกนได้ทั้งหมด
        raw_texts = []

        # Extract text from the new PaddleOCR result structure
        if isinstance(result[0], dict):
            # New format: dictionary with rec_texts and rec_scores
            rec_texts = result[0].get('rec_texts', [])
            rec_scores = result[0].get('rec_scores', [])

            for text, confidence in zip(rec_texts, rec_scores):
                if confidence > 0.5:  # กรองเอาเฉพาะที่มั่นใจ
                    raw_texts.append(text)
        else:
            # Old format: list of [coordinates, (text, confidence)]
            for line in result[0]:
                try:
                    if line and len(line) >= 2:
                        text_info = line[1]
                        if text_info and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = text_info[1]
                            if confidence > 0.5:
                                raw_texts.append(text)
                except (IndexError, TypeError):
                    continue
        
        full_text = " ".join(raw_texts)

        # 4. ส่งไปให้ Groq ประมวลผล
        structured_data = process_with_groq(full_text)
        
        return {
            "status": "success",
            "raw_text": full_text,
            "structured_data": structured_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)