import streamlit as st
import pandas as pd
import sqlite3
import secrets
import base64
import json
import os
import urllib.request
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================================================================
# 🖼️ 閱讀測驗附件圖片安全載入器
# =========================================================================
def get_image_as_base64(file_path):
    """讀取本地圖片檔案並轉成 HTML/Streamlit 相容的 Base64 格式"""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode('utf-8')
        ext = file_path.split('.')[-1].lower()
        mime_type = "jpeg" if ext in ["jpg", "jpeg"] else "png"
        return f"data:image/{mime_type};base64,{encoded}"
    return None

def display_quiz_image(image_filename, alt_caption):
    """安全渲染圖片，若圖片存在則以完整 base64 顯示，避免路徑解析失敗"""
    img_b64 = get_image_as_base64(image_filename)
    if img_b64:
        st.image(img_b64, caption=alt_caption, use_container_width=True)
    else:
        st.error(f"⚠️ 找不到圖片檔案：`{image_filename}`！請確認該圖片是否已放置在與 `app.py` 同一個資料夾內，並已 Git Push 上傳。")
