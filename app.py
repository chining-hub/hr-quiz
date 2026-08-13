import streamlit as st
import pandas as pd
import sqlite3
import secrets
import base64
import json
import urllib.request
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================================================================
# 🖼️ 閱讀測驗附件圖片 (Base64 編碼，免管理外部圖片檔)
# =========================================================================
# 附件一：Valentino's Corner 廣告圖
IMG_ATTACHMENT_1 = "data:image/png;base64,iVBORw0KGgoAAAANSU_PLACEHOLDER_FOR_ATTACHMENT_1" 
# 附件二：Yearly Consumption of Animal Products 圓餅圖
IMG_ATTACHMENT_2 = "data:image/png;base64,iVBORw0KGgoAAAANSU_PLACEHOLDER_FOR_ATTACHMENT_2"

# 若需要實體圖片，也可替換為 URL 或本地路徑
IMG_ATTACHMENT_1_URL = "https://i.imgur.com/example1.png" # 亦可更換為實際圖片網址
IMG_ATTACHMENT_2_URL = "https://i.imgur.com/example2.png"

# =========================================================================
# 📚 0. 英文 17 題完整多益題庫資料結構 (13題單字文法 + 4題閱讀測驗)
# =========================================================================
QUIZ_DATA = [
    # ------------------- Part 1: Vocabulary & Grammar (13題) -------------------
    {
        "id": "q1",
        "question": "1. Many problems with locks ------ by a simple repair or adjustment.",
        "options": {"A": "solved", "B": "could solve", "C": "can solve", "D": "can be solved"},
        "answer": "D"
    },
    {
        "id": "q2",
        "question": "2. A fine of $200 will be imposed upon any drivers ------ park illegally downtown during the holiday parade.",
        "options": {"A": "which", "B": "whose", "C": "whom", "D": "who"},
        "answer": "D"
    },
    {
        "id": "q3",
        "question": "3. The Eisenweg Foundation will soon ------ its funding of external scientific research into several new domains, including genetics and endangered languages.",
        "options": {"A": "exalt", "B": "exclaim", "C": "expel", "D": "expand"},
        "answer": "D"
    },
    {
        "id": "q4",
        "question": "4. Mobile phones have become ------ prevalent that telecommunications companies are establishing service in areas previously thought too remote.",
        "options": {"A": "only", "B": "such", "C": "so", "D": "still"},
        "answer": "C"
    },
    {
        "id": "q5",
        "question": "5. In recognition of Elaine Tang’s exceptional service to ------ company, the human resources director will honor her at tonight’s employee awards ceremony.",
        "options": {"A": "ours", "B": "our", "C": "us", "D": "we"},
        "answer": "B"
    },
    {
        "id": "q6",
        "question": "6. Our overseas branch office is ------ to open in Taipei next month.",
        "options": {"A": "scheduled", "B": "advanced", "C": "informed", "D": "maintained"},
        "answer": "A"
    },
    {
        "id": "q7",
        "question": "7. The afternoon flight from Tokyo has been canceled ------ a mechanical problem.",
        "options": {"A": "as much as", "B": "due to", "C": "because", "D": "in case"},
        "answer": "B"
    },
    {
        "id": "q8",
        "question": "8. Mr. Martin has decided to ------ the planning meeting because of a scheduling conflict.",
        "options": {"A": "evaluate", "B": "postpone", "C": "refer", "D": "identify"},
        "answer": "B"
    },
    {
        "id": "q9",
        "question": "9. Following her ------ to sales director, Ms. Lin assumed responsibility for the firm’s marketing activities.",
        "options": {"A": "development", "B": "delivery", "C": "promotion", "D": "acceptance"},
        "answer": "C"
    },
    {
        "id": "q10",
        "question": "10. In the Western world, second only to New Year’s Day, Christmas is perhaps the ------ holiday.",
        "options": {"A": "widely most celebrated", "B": "most widely celebrated", "C": "widely celebrated most", "D": "most celebrated widely"},
        "answer": "B"
    },
    {
        "id": "q11",
        "question": "11. Covering more than 9 million square kilometers in northern Africa, the Sahara Desert ------ from the Atlantic Ocean to the Red Sea.",
        "options": {"A": "contains", "B": "differs", "C": "extends", "D": "rises"},
        "answer": "C"
    },
    {
        "id": "q12",
        "question": "12. Payment of monthly parking vouchers can be made either by personal check ------ by automatic withdrawal from a bank account.",
        "options": {"A": "but", "B": "and", "C": "or", "D": "if"},
        "answer": "C"
    },
    {
        "id": "q13",
        "question": "13. To safeguard the factory from being further burglarized, it is decided that new detection equipment is to be -------.",
        "options": {"A": "founded", "B": "called", "C": "purchased", "D": "confiscated"},
        "answer": "C"
    },

    # ------------------- Part 2: Reading Comprehension (4題) -------------------
    # 附件一題組
    {
        "id": "q14",
        "attachment_type": "image",
        "image_key": "attachment1",
        "question": "14. What kind of business is Valentino’s Corner?",
        "options": {"A": "A restaurant", "B": "A bakery", "C": "A pottery shop", "D": "A courier service"},
        "answer": "A"
    },
    {
        "id": "q15",
        "attachment_type": "image",
        "image_key": "attachment1",
        "question": "15. What information does NOT appear in the advertisement?",
        "options": {
            "A": "The types of offerings available to the establishment’s customers",
            "B": "The hours during which the establishment is open",
            "C": "How much items cost at the establishment",
            "D": "How long the establishment has been in business"
        },
        "answer": "C"
    },

    # 附件二題組
    {
        "id": "q16",
        "attachment_type": "image",
        "image_key": "attachment2",
        "question": "16. Which product is consumed in the greatest amounts?",
        "options": {"A": "Pork", "B": "Beef", "C": "Chicken", "D": "Fish"},
        "answer": "B"
    },
    {
        "id": "q17",
        "attachment_type": "image",
        "image_key": "attachment2",
        "question": "17. Who would benefit from this particular graph?",
        "options": {"A": "A person on a diet", "B": "A produce farmer", "C": "A vegetarian", "D": "Cattle raisers"},
        "answer": "D"
    }
]

# =========================================================================
# 🗄️ 1. SQLite 資料庫自動建表與讀寫模組
# =========================================================================
DB_NAME = "quiz_database.db"

def get_db_connection():
    """建立 SQLite 連線"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    """初始化 SQLite 資料表結構"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            test_id TEXT PRIMARY KEY,
            name TEXT,
            dept TEXT,
            exam_type TEXT,
            created_time TEXT,
            status TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT,
            name TEXT,
            dept TEXT,
            exam_type TEXT,
            score REAL,
            submit_time TEXT,
            duration_seconds INTEGER,
            details TEXT,
            cheat_logs TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_test_by_id(test_id):
    """查詢 Token 資料"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tests WHERE test_id = ?", (test_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_new_test(test_id, name, dept, exam_type):
    """新增測驗派發紀錄"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tests (test_id, name, dept, exam_type, created_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (test_id, name, dept, exam_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "未完成"))
    conn.commit()
    conn.close()

def sync_to_google_sheets(data_dict):
    """自動備份成績至 Google Sheets (經由 Google Apps Script Web App)"""
    url = st.secrets.get("GSHEET_WEBAPP_URL", "")
    if not url:
        return
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data_dict).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Google Sheets 同步失敗: {e}")

def mark_test_completed_and_save_result(test_id, name, dept, exam_type, score, duration_sec, details_str, cheat_logs):
    """更新測驗狀態、寫入 SQLite 並同步至 Google Sheets"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    submit_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 更新狀態為已完成
    cursor.execute("UPDATE tests SET status = '已完成' WHERE test_id = ?", (test_id,))
    
    # 2. 寫入 SQLite
    cursor.execute('''
        INSERT INTO results (test_id, name, dept, exam_type, score, submit_time, duration_seconds, details, cheat_logs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (test_id, name, dept, exam_type, score, submit_time_str, duration_sec, details_str, cheat_logs))
    
    conn.commit()
    conn.close()

    # 3. 背景自動同步至 Google Sheets
    sync_data = {
        "test_id": test_id,
        "name": name,
        "dept": dept,
        "exam_type": exam_type,
        "score": score,
        "submit_time": submit_time_str,
        "duration_seconds": duration_sec,
        "details": details_str,
        "cheat_logs": cheat_logs
    }
    sync_to_google_sheets(sync_data)

# 初始化 SQLite 資料庫
init_sqlite_db()

# =========================================================================
# 🛡️ 2. SVG 向量圖像化（支援多行自動折行 + 大字體）
# =========================================================================
def text_to_multiline_svg(text: str, font_size: int = 22, max_chars_per_line: int = 50) -> str:
    """將題目自動折行為多行，生成不會被等比例縮小的清晰大字 SVG"""
    words = text.split(" ")
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if sum(len(w) for w in current_line) + len(current_line) - 1 >= max_chars_per_line:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))
        
    line_height = font_size * 1.45
    svg_height = int(len(lines) * line_height + 15)
    svg_width = 720  
    
    tspan_elements = ""
    for idx, line in enumerate(lines):
        y_pos = int((idx + 1) * line_height)
        tspan_elements += f'<tspan x="0" y="{y_pos}">{line}</tspan>'
        
    svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">
        <text font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="{font_size}px" font-weight="600" fill="#111827">
            {tspan_elements}
        </text>
    </svg>'''
    
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="vertical-align: middle; display: block; margin: 8px 0; max-width: 100%; height: auto;" />'

def option_to_svg(text: str, font_size: int = 20) -> str:
    """單行選項專用大字體 SVG"""
    width = max(int(len(text) * (font_size * 0.7)) + 20, 320)
    height = int(font_size * 1.6)
    
    svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <text x="0" y="{font_size}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="{font_size}px" font-weight="500" fill="#374151">{text}</text>
    </svg>'''
    
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="vertical-align: middle; display: inline-block; margin: 2px 0;" />'

def inject_anti_cheat_script():
    """注入 JS：強制根目錄防翻譯、防選取與防右鍵"""
    st.markdown(
        """
        <script>
            document.documentElement.setAttribute('translate', 'no');
            document.documentElement.classList.add('notranslate');
            if (document.body) {
                document.body.setAttribute('translate', 'no');
                document.body.classList.add('notranslate');
            }

            document.addEventListener('contextmenu', event => event.preventDefault());
            document.addEventListener('copy', event => event.preventDefault());
            document.addEventListener('cut', event => event.preventDefault());
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && (e.key === 'c' || e.key === 'C' || e.key === 'x' || e.key === 'X' || 
                                  e.key === 'a' || e.key === 'A' || e.key === 'u' || e.key === 'U' || 
                                  e.key === 's' || e.key === 'S')) {
                    e.preventDefault();
                }
                if (e.keyCode === 123) e.preventDefault();
            });
        </script>
        <style>
            * {
                -webkit-user-select: none !important;
                -moz-user-select: none !important;
                -ms-user-select: none !important;
                user-select: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

# =========================================================================
# ⚙️ 3. 頁面設定與路由判斷
# =========================================================================
st.set_page_config(page_title="線上測評系統", page_icon="📝", layout="centered")

query_params = st.query_params
current_test_id = query_params.get("test", None)

# -------------------------------------------------------------------------
# 🔀 情境 A：網址有 ?test=xxxx -> 進入【應試者測驗入口】
# -------------------------------------------------------------------------
if current_test_id:
    test_info = get_test_by_id(current_test_id)
    
    if not test_info:
        st.error("❌ 找不到此測驗連結，請確認網址是否完整或聯繫 HR。")
    elif test_info["status"] == "已完成":
        st.warning("⚠️ 此測驗連結已經交卷完成，無法重複作答！")
    else:
        cand_name = test_info["name"]
        cand_dept = test_info["dept"]
        exam_type = test_info["exam_type"]
        
        with st.sidebar:
            st.header("📋 應試者資訊 (已驗證)")
            st.text_input("姓名", value=cand_name, disabled=True)
            st.text_input("應徵部門", value=cand_dept, disabled=True)
            st.text_input("測驗科目", value=exam_type, disabled=True)
            st.success("✅ 身分鎖定成功")

        st.title(f"📝 {exam_type}")
        st.caption(f"歡迎應試者 **{cand_name}**（{cand_dept}），請仔細閱讀題目後作答。")
        st.divider()

        start_key = f"start_time_{current_test_id}"
        if start_key not in st.session_state:
            st.session_state[start_key] = datetime.now()

        if exam_type == "英文測驗":
            inject_anti_cheat_script()

        is_time_up = False
        if exam_type == "數學測驗":
            st_autorefresh(interval=1000, key="math_exam_timer")

            start_time = st.session_state[start_key]
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            total_limit_seconds = 50 * 60
            remaining_seconds = max(0, int(total_limit_seconds - elapsed_seconds))

            mins, secs = divmod(remaining_seconds, 60)
            
            if remaining_seconds > 0:
                st.warning(f"⏳ **數學測驗限時 50 分鐘** ｜ 倒數計時：**{mins:02d} 分 {secs:02d} 秒**")
            else:
                is_time_up = True
                st.error("⏰ **測驗時間已到！** 系統已鎖定作答，請點擊下方按鈕進行強制交卷。")

        if "submitted" not in st.session_state:
            st.session_state.submitted = False

        if not st.session_state.submitted:
            with st.form("exam_form"):
                score = 0.0
                ans_records = []
                
                # ------------------- 英文測驗（含單字語法 + 閱讀圖表）-------------------
                if exam_type == "英文測驗":
                    st.markdown(text_to_multiline_svg("PART 1. Vocabulary & Grammar Test (Q1-Q13)", font_size=24, max_chars_per_line=60), unsafe_allow_html=True)
                    st.divider()

                    last_rendered_attachment = None

                    for idx, q_item in enumerate(QUIZ_DATA):
                        q_id = q_item["id"]
                        q_text = q_item["question"]
                        opts = q_item["options"]
                        corr_ans = q_item["answer"]

                        # 進入 Part 2 閱讀測驗標頭
                        if idx == 13:
                            st.markdown(text_to_multiline_svg("PART 2. Reading Comprehension Test (Q14-Q17)", font_size=24, max_chars_per_line=60), unsafe_allow_html=True)
                            st.divider()

                        # 判斷是否需要渲染附件圖片
                        if "image_key" in q_item:
                            img_key = q_item["image_key"]
                            if img_key != last_rendered_attachment:
                                st.info("📌 請根據下方文章/圖表內容回答問題：")
                                if img_key == "attachment1":
                                    # 可替換為圖片 Base64 或上傳檔路徑
                                    st.image("題目1.png", caption="[附件一] Valentino's Corner 廣告", use_column_width=True)
                                elif img_key == "attachment2":
                                    st.image("題目2.png", caption="[附件二] Yearly Consumption of Animal Products", use_column_width=True)
                                last_rendered_attachment = img_key

                        # 題目採用多行自動折行 SVG，字體 22px 加粗清晰
                        st.markdown(text_to_multiline_svg(q_text, font_size=22, max_chars_per_line=50), unsafe_allow_html=True)
                        
                        # 選項採用單行 20px SVG
                        opts_html = f"""
                        * **A)** {option_to_svg(opts['A'], font_size=20)}
                        * **B)** {option_to_svg(opts['B'], font_size=20)}
                        * **C)** {option_to_svg(opts['C'], font_size=20)}
                        * **D)** {option_to_svg(opts['D'], font_size=20)}
                        """
                        st.markdown(opts_html, unsafe_allow_html=True)
                        
                        # 選擇單選鈕
                        user_ans = st.radio("請選擇正確答案：", ["A", "B", "C", "D"], key=f"radio_{q_id}")
                        
                        # 判斷得分與記錄 (配分：每題 5.88 分，共 100 分)
                        if user_ans == corr_ans:
                            score += (100.0 / len(QUIZ_DATA))
                            ans_records.append(f"Q{idx+1}:⭕ ({user_ans})")
                        else:
                            ans_records.append(f"Q{idx+1}:❌ ({user_ans})")
                        
                        st.divider()

                # ------------------- 數學測驗 -------------------
                elif exam_type == "數學測驗":
                    st.subheader("Q1. 比例計算：")
                    q_math1 = st.radio("一件商品原價 2,000 元，打八折後是多少元？", [1400, 1600, 1800], disabled=is_time_up, key="qm1_radio")
                    if q_math1 == 1600:
                        score += 100.0
                        ans_records.append("Q1:⭕ (選擇: 1600)")
                    else:
                        ans_records.append(f"Q1:❌ (選擇: {q_math1})")

                btn_label = "🚨 時間已到，強制交卷" if is_time_up else "🚀 確認交卷"
                btn_submit = st.form_submit_button(btn_label, type="primary", use_container_width=True)
                
                if btn_submit:
                    end_time = datetime.now()
                    duration_sec = int((end_time - st.session_state[start_key]).total_seconds())
                    
                    details_str = " | ".join(ans_records)
                    if is_time_up:
                        details_str += " [系統備註: 逾時強制交卷]"

                    cheat_logs = f"總花費時間: {duration_sec} 秒"
                    
                    mark_test_completed_and_save_result(
                        current_test_id, cand_name, cand_dept, exam_type, 
                        round(score, 1), duration_sec, details_str, cheat_logs
                    )
                    st.session_state.submitted = True
                    st.rerun()
        else:
            st.balloons()
            st.success("🎉 測驗已順利完成！")

# -------------------------------------------------------------------------
# 🔀 情境 B：網址無參數 -> 進入【HR 人資管理後台】
# -------------------------------------------------------------------------
else:
    st.title("🏢 人資測評管理系統")
    st.caption("請輸入 HR 密碼以開啟管理功能")
    
    CORRECT_PASSWORD = st.secrets.get("HR_PASSWORD", "hr1234")
    hr_password = st.text_input("HR 管理員密碼", type="password")
    
    if hr_password == CORRECT_PASSWORD:
        st.success("身份驗證成功！")
        
        tab1, tab2 = st.tabs(["➕ 建立測驗連結", "📊 測驗紀錄與數據分析"])
        
        with tab1:
            st.subheader("產生應徵者專屬加密測驗連結")
            with st.form("create_form"):
                col1, col2, col3 = st.columns(3)
                c_name = col1.text_input("應徵者姓名", placeholder="例如：王小明")
                c_dept = col2.text_input("應徵部門", placeholder="例如：財務部")
                c_exam = col3.selectbox("選擇測驗科目", ["英文測驗", "數學測驗"])
                
                btn_gen = st.form_submit_button("🎲 建立隨機測驗連結", type="primary", use_container_width=True)
                
                if btn_gen:
                    if c_name and c_dept:
                        token_32 = secrets.token_hex(16)
                        save_new_test(token_32, c_name, c_dept, c_exam)
                        
                        base_url = "https://hr-quiz-6bya8ipfvrzg8c2zwfj2m2.streamlit.app"
                        quiz_url = f"{base_url}/?test={token_32}"
                        
                        st.subheader("📋 隨機測驗連結：")
                        st.code(quiz_url, language="text")
                        st.info("💡 請直接複製上方連結寄發給應徵者，應徵者開啟後將自動鎖定身分。")
                    else:
                        st.warning("⚠️ 請完整填寫應徵者姓名與部門！")

        with tab2:
            conn = get_db_connection()
            
            st.subheader("📜 測驗派發紀錄表 (SQLite: tests)")
            df_tests = pd.read_sql_query("SELECT * FROM tests ORDER BY created_time DESC", conn)
            st.dataframe(df_tests, use_container_width=True)
                
            st.subheader("🏆 應試者成績與行為日誌表 (SQLite: results)")
            df_results = pd.read_sql_query("SELECT * FROM results ORDER BY submit_time DESC", conn)
            st.dataframe(df_results, use_container_width=True)
            
            conn.close()
                
    elif hr_password:
        st.error("密碼錯誤，請重新輸入！")
        st.error("密碼錯誤，請重新輸入！")
    elif hr_password:
        st.error("密碼錯誤，請重新輸入！")
