import streamlit as st
import pandas as pd
import sqlite3
import secrets
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================================================================
# 🗄️ 1. SQLite 資料庫自動建表與讀寫模組 (已移除 cand_id)
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
    
    # 建立派發測驗 Token 表
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
    
    # 建立應試者成績與行為日誌表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT,
            name TEXT,
            dept TEXT,
            exam_type TEXT,
            score INTEGER,
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

def mark_test_completed_and_save_result(test_id, name, dept, exam_type, score, duration_sec, details_str, cheat_logs):
    """更新測驗狀態並寫入成績庫"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 更新狀態為已完成
    cursor.execute("UPDATE tests SET status = '已完成' WHERE test_id = ?", (test_id,))
    
    # 2. 寫入詳細成績與行為日誌
    cursor.execute('''
        INSERT INTO results (test_id, name, dept, exam_type, score, submit_time, duration_seconds, details, cheat_logs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (test_id, name, dept, exam_type, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), duration_sec, details_str, cheat_logs))
    
    conn.commit()
    conn.close()

# 初始化 SQLite 資料庫
init_sqlite_db()

# =========================================================================
# 🛡️ 2. SVG 向量圖像化（終極 100% 防翻譯）與防右鍵/防複製模組
# =========================================================================
def text_to_svg(text: str, font_size: int = 18, height: int = 35) -> str:
    """
    將英文文字動態轉為 Base64 格式的 SVG 向量圖片
    Google 翻譯與外掛無法辨識圖片內的 HTML 節點，防翻譯成功率 100%！
    """
    width = max(int(len(text) * (font_size * 0.68)) + 20, 300)
    
    svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <text x="0" y="{font_size + 2}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="{font_size}px" font-weight="500" fill="#31333F">{text}</text>
    </svg>'''
    
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="vertical-align: middle; display: inline-block; margin: 2px 0;" />'

def inject_anti_cheat_script():
    """注入 JS：強制根目錄防翻譯、防選取與防右鍵"""
    st.markdown(
        """
        <script>
            // 1. 強制在最頂層 html 與 body 標籤加上防翻譯屬性
            document.documentElement.setAttribute('translate', 'no');
            document.documentElement.classList.add('notranslate');
            if (document.body) {
                document.body.setAttribute('translate', 'no');
                document.body.classList.add('notranslate');
            }

            // 2. 禁用右鍵選單 (阻斷右鍵選單中的「翻譯成中文」選項)
            document.addEventListener('contextmenu', event => event.preventDefault());
            
            // 3. 禁用複製、剪下與開發者工具
            document.addEventListener('copy', event => event.preventDefault());
            document.addEventListener('cut', event => event.preventDefault());
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && (e.key === 'c' || e.key === 'C' || e.key === 'x' || e.key === 'X' || 
                                  e.key === 'a' || e.key === 'A' || e.key === 'u' || e.key === 'U' || 
                                  e.key === 's' || e.key === 'S')) {
                    e.preventDefault();
                }
                if (e.keyCode === 123) e.preventDefault(); // F12 開發者工具
            });
        </script>
        <style>
            /* 全域禁止文字被選取與反白 */
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
        
        # 側邊欄身分鎖定 (已移除應徵編號)
        with st.sidebar:
            st.header("📋 應試者資訊 (已驗證)")
            st.text_input("姓名", value=cand_name, disabled=True)
            st.text_input("應徵部門", value=cand_dept, disabled=True)
            st.text_input("測驗科目", value=exam_type, disabled=True)
            st.success("✅ 身分鎖定成功")

        st.title(f"📝 {exam_type}")
        st.caption(f"歡迎應試者 **{cand_name}**（{cand_dept}），請仔細閱讀題目後作答。")
        st.divider()

        # 紀錄測驗開始時間
        start_key = f"start_time_{current_test_id}"
        if start_key not in st.session_state:
            st.session_state[start_key] = datetime.now()

        # ---------------- 防作弊機制 ----------------
        if exam_type == "英文測驗":
            inject_anti_cheat_script()

        # ---------------- 倒數計時器 (st_autorefresh) ----------------
        is_time_up = False
        if exam_type == "數學測驗":
            st_autorefresh(interval=1000, key="math_exam_timer")

            start_time = st.session_state[start_key]
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            total_limit_seconds = 50 * 60  # 50 分鐘
            remaining_seconds = max(0, int(total_limit_seconds - elapsed_seconds))

            mins, secs = divmod(remaining_seconds, 60)
            
            if remaining_seconds > 0:
                st.warning(f"⏳ **數學測驗限時 50 分鐘** ｜ 倒數計時：**{mins:02d} 分 {secs:02d} 秒**")
            else:
                is_time_up = True
                st.error("⏰ **測驗時間已到！** 系統已鎖定作答，請點擊下方按鈕進行強制交卷。")

        # ---------------- 測驗題目內容 ----------------
        if "submitted" not in st.session_state:
            st.session_state.submitted = False

        if not st.session_state.submitted:
            with st.form("exam_form"):
                score = 0
                ans_records = []
                
                if exam_type == "英文測驗":
                    st.markdown(text_to_svg("Q1. Choose the correct word:", font_size=20, height=40), unsafe_allow_html=True)
                    st.markdown(text_to_svg("The project was completed ____ schedule.", font_size=18, height=35), unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    * **A)** {text_to_svg("on")}
                    * **B)** {text_to_svg("in")}
                    * **C)** {text_to_svg("at")}
                    * **D)** {text_to_svg("to")}
                    """, unsafe_allow_html=True)
                    
                    q1 = st.radio("請選擇 Q1 正確答案：", ["A", "B", "C", "D"], key="q1_radio")
                    
                    if q1 == "A":
                        score += 50
                        ans_records.append("Q1:⭕ (選擇: A. on)")
                    else:
                        ans_records.append(f"Q1:❌ (選擇: {q1})")

                    st.divider()

                    st.markdown(text_to_svg("Q2. Reading Comprehension:", font_size=20, height=40), unsafe_allow_html=True)
                    st.markdown(text_to_svg("What does 'ATS' stand for in modern HR?", font_size=18, height=35), unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    * **A)** {text_to_svg("Applicant Tracking System")}
                    * **B)** {text_to_svg("Automated Testing Service")}
                    * **C)** {text_to_svg("Annual Team Strategy")}
                    """, unsafe_allow_html=True)
                    
                    q2 = st.radio("請選擇 Q2 正確答案：", ["A", "B", "C"], key="q2_radio")
                    
                    if q2 == "A":
                        score += 50
                        ans_records.append("Q2:⭕ (選擇: A. Applicant Tracking System)")
                    else:
                        ans_records.append(f"Q2:❌ (選擇: {q2})")

                elif exam_type == "數學測驗":
                    st.subheader("Q1. 邏輯運算：")
                    q1 = st.number_input("若 3x + 15 = 45，則 x = ?", step=1, disabled=is_time_up)
                    if q1 == 10:
                        score += 50
                        ans_records.append("Q1:⭕ (回答: 10)")
                    else:
                        ans_records.append(f"Q1:❌ (回答: {q1})")

                    st.subheader("Q2. 比例計算：")
                    q2 = st.radio("一件商品原價 2,000 元，打八折後是多少元？", [1400, 1600, 1800], disabled=is_time_up)
                    if q2 == 1600:
                        score += 50
                        ans_records.append("Q2:⭕ (選擇: 1600)")
                    else:
                        ans_records.append(f"Q2:❌ (選擇: {q2})")

                
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
                        score, duration_sec, details_str, cheat_logs
                    )
                    st.session_state.submitted = True
                    st.rerun()
        else:
            st.balloons()
            st.success("🎉 測驗已順利完成！您可以關閉此網頁。")

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
        
        # TAB 1: HR 派發測驗 (已移除應徵編號欄位)
        with tab1:
            st.subheader("產生應徵者隨機測驗連結")
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
                        st.info("💡 請直接複製上方連結寄發給應徵者，應徵者打開後將自動鎖定身分。")
                    else:
                        st.warning("⚠️ 請完整填寫應徵者姓名與部門！")

        # TAB 2: SQLite 成績與數據檢視
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
