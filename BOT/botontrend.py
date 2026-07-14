import os
import io
import re
import requests
from datetime import datetime
import telebot  # Thư viện pyTelegramBotAPI
import pypdf

# =====================================================================
# 1. CẤU HÌNH TOKEN BOT VÀ MAKE WEBHOOK
# =====================================================================
BOT_TOKEN = "7556338449:AAHsUQnvPH4hnRV7aST1IUYv8dp7DCBA4y4"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/a9f3573nlumba0ojwpgviwo6u34uw8hk"

bot = telebot.TeleBot(BOT_TOKEN)

print("⚡ Hệ thống Bot Nhóm Chat Phạm Quang Huy VPX đang chạy...")

# =====================================================================
# 2. HÀM XỬ LÝ LOGIC ĐƯỜNG LINK VÀ TÊN FILE
# =====================================================================
def get_download_info(user_message):
    clean_msg = user_message.upper().strip()
    
    # TRƯỜNG HỢP 1: Người dùng gõ lệnh liên quan đến VNINDEX
    if "VNINDEX" in clean_msg:
        date_match = re.search(r"\d{8}", clean_msg)
        if date_match:
            target_date_str = date_match.group(0)
        else:
            current_day = datetime.now()
            target_date_str = current_day.strftime("%Y%m%d")
            
        pdf_url = f"https://static.tcbs.com.vn/oneclick/{target_date_str}_BC_PTKT.pdf"
        
        try:
            formatted_date = datetime.strptime(target_date_str, "%Y%m%d").strftime("%d/%m/%Y")
        except:
            formatted_date = target_date_str
            
        display_name = f"Thị trường chung VNINDEX (Ngày {formatted_date})"
        ticker_label = f"VNINDEX_{target_date_str}"
        return pdf_url, display_name, ticker_label

    # TRƯỜNG HỢP 2: Người dùng gõ mã cổ phiếu thông thường (PVT, HSG, PDR...)
    else:
        pdf_url = f"https://static.tcbs.com.vn/oneclick/{clean_msg}.pdf"
        display_name = f"Cổ phiếu {clean_msg}"
        ticker_label = clean_msg
        return pdf_url, display_name, ticker_label

# =====================================================================
# 3. LẮNG NGHE VÀ XỬ LÝ TIN NHẮN TRONG NHÓM
# =====================================================================
# Bộ lọc thông minh: Chỉ xử lý nếu tin nhắn chứa "VNINDEX" hoặc là mã cổ phiếu 3 ký tự viết liền
def group_filter(message):
    if not message.text:
        return False
    clean_txt = message.text.strip().upper()
    # Thỏa mãn nếu chứa từ khóa VNINDEX HOẶC là một từ có đúng 3 chữ cái (Mã cổ phiếu)
    return "VNINDEX" in clean_txt or bool(re.match(r"^[A-Z]{3}$", clean_txt))

@bot.message_handler(func=group_filter)
def handle_group_messages(message):
    user_input = message.text.strip()
    chat_id = message.chat.id  # Đây sẽ là ID của Nhóm Chat
    
    pdf_url, display_name, ticker_label = get_download_info(user_input)
    
    # Trả lời trực tiếp bằng cách reply tin nhắn của người gọi lệnh trong nhóm
    bot.reply_to(message, f"🔍 Hệ thống đã ghi nhận yêu cầu từ thành viên.\n🚀 Đang tiến hành kiểm tra dữ liệu: *{display_name}*...", parse_mode="Markdown")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(pdf_url, headers=headers, timeout=15)
        
        if response.status_code == 404:
            bot.send_message(chat_id, f"❌ Không tìm thấy báo cáo kỹ thuật thích hợp cho từ khóa: *{user_input.upper()}* trên TCBS.", parse_mode="Markdown")
            return
        elif response.status_code != 200:
            return
            
        # Đọc dữ liệu text từ PDF
        pdf_file = io.BytesIO(response.content)
        reader = pypdf.PdfReader(pdf_file)
        
        raw_text = ""
        for index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                raw_text += f"\n--- TRANG {index + 1} ---\n" + page_text
                
        # Đóng gói dữ liệu chuyển sang Make Webhook
        payload = {
            "title": f"Báo cáo {display_name}",
            "ticker": ticker_label,
            "chat_id": str(chat_id),  # Gửi ID nhóm sang để Make gửi ảnh ngược lại vào đúng nhóm này
            "raw_pdf_text": raw_text.strip()
        }
        
        make_response = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=20)
        
        if make_response.status_code in [200, 201]:
            bot.send_message(chat_id, f"🎨 AI đang xử lý dữ liệu chiến lược cho *{ticker_label}*.\n📸 Ảnh Infographic sẽ sớm được gửi vào nhóm!", parse_mode="Markdown")
            
    except Exception as e:
        print(f"Lỗi: {str(e)}")

# Khởi chạy chế độ lắng nghe liên tục
bot.polling(none_stop=True)
