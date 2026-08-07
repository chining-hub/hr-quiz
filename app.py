import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime

# =========================================================================
# 📁 1. 資料庫 (CSV) 自動讀寫工具函式
# =========================================================================
TESTS_FILE = "tests_master.csv"
RESULTS_FILE = "results_master.csv"

def init_db():
    """初始化 CSV 資料表結構"""
    if not os.path.exists(TESTS_FILE):
        df_tests = pd.DataFrame(columns=[
            "test_id", "cand_id", "name", "dept", "exam_type", "created_time", "status"
        ])
        df_tests.to_csv(TESTS_FILE, index=False, encoding="utf-8-sig")
        
    if not os.path.exists(RESULTS_FILE):
        df_results = pd.DataFrame(columns=[
            "test_id", "cand_id", "name", "dept", "exam_type", "score", "submit_time", "details"
        ])
        df_results.to_csv(RESULTS_FILE, index=False, encoding="utf-8-sig")

def get_test_by_id(test_id):
    """根據 Token (test_id) 查詢應徵者資訊"""
    if os.path.exists(TESTS_FILE):
        df = pd.read_csv(TESTS_FILE, dtype=str)
        record = df[df["test_id"] == str(test_id)]
        if not record.empty:
            return record.iloc[0].to_dict()
    return None

def save_new_test(test_id, cand_id, name, dept, exam_type):
    """HR 建立新的測驗 Token"""
    df = pd.read_csv(TESTS_FILE, dtype=str)
    new_row = {
        "test_id": str(test_id),
        "cand_id": str(cand_id),
        "name": str(name),
        "dept": str(dept),
        "exam_type": str(exam_type),
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "未完成"
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(TESTS_FILE, index=False, encoding="utf-8-sig")

def mark_test_completed_and_save_result(test_id, cand_id, name, dept, exam_type, score, details_str):
    """更新測驗狀態為已完成，並記錄成績"""
    # 1. 更新 tests_master.csv 狀態
    df_tests = pd.read_csv(TESTS_FILE, dtype=str)
    df_tests.loc[df_tests["test_id"] == str(test_id), "status"] = "已完成"
    df_tests.to_csv(TESTS_FILE, index=False, encoding="utf-8-sig")
    
    # 2. 寫入 results_master.csv
    df_results = pd.read_csv(RESULTS_FILE, dtype=str)
    new_result = {
        "test_id": str(test_id),
        "cand_id": str(cand_id),
        "name": str(name),
        "dept": str(dept),
        "exam_type": str(exam_type),
        "score": str(score),
        "submit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": str(details_str)
    }
    df_results = pd.concat([df_results, pd.DataFrame([new_result])], ignore_index=True)
    df_results.to_csv(RESULTS_FILE, index=False, encoding="utf-8-sig")

# 初始化資料庫
init_db()

# =========================================================================
# ⚙️ 2. 頁面設定與路由判斷
# =========================================================================
st.set_page_config(page_title="UNITECH 線上測評系統", page_icon="📝", layout="centered")

query_params = st.query_params
current_test_id = query_params.get("test", None)

# -------------------------------------------------------------------------
# 🔀 情境 A：網址有 ?test=xxxx -> 進入【應試者測驗入口】
# -------------------------------------------------------------------------
if current_test_id:
    test_info = get_test_by_id(current_test_id)
    
    if not test_info:
        st.error("❌ 找不到此測驗連結，請確認網址是否完整，或聯繫 HR。")
    elif test_info["status"] == "已完成":
        st.warning("⚠️ 此測驗連結已經完成交卷，無法重複作答！")
    else:
        # 取得應徵者資訊
        cand_name = test_info["name"]
        cand_id = test_info["cand_id"]
        cand_dept = test_info["dept"]
        exam_type = test_info["exam_type"]
        
        # 側邊欄：顯示身份驗證（完全不顯示 HR 管理項目）
        with st.sidebar:
            st.header("📋 應試者資訊 (已驗證)")
            st.text_input("姓名", value=cand_name, disabled=True)
            st.text_input("應徵編號", value=cand_id, disabled=True)
            st.text_input("應徵部門", value=cand_dept, disabled=True)
            st.text_input("測驗科目", value=exam_type, disabled=True)
            st.success("✅ 身分鎖定成功")

        st.title(f"📝 UNITECH {exam_type}")
        st.caption(f"歡迎應試者 **{cand_name}**（{cand_dept}），請仔細閱讀題目後作答。")
        st.divider()

        # ---------- 測驗題目邏輯 (以英文與數學測驗為例) ----------
        if "submitted" not in st.session_state:
            st.session_state.submitted = False

        if not st.session_state.submitted:
            with st.form("exam_form"):
                score = 0
                ans_records = []
                
                if exam_type == "英文測驗":
                    st.subheader("Q1. Choose the correct word:")
                    q1 = st.radio("The project was completed ____ schedule.", ["on", "in", "at", "to"])
                    if q1 == "on":
                        score += 50
                        ans_records.append("Q1:⭕")
                    else:
                        ans_records.append("Q1:❌")

                    st.subheader("Q2. Reading Comprehension:")
                    q2 = st.radio("What does 'ATS' stand for in modern HR?", 
                                  ["Applicant Tracking System", "Automated Testing Service", "Annual Team Strategy"])
                    if q2 == "Applicant Tracking System":
                        score += 50
                        ans_records.append("Q2:⭕")
                    else:
                        ans_records.append("Q2:❌")

                elif exam_type == "數學測驗":
                    st.subheader("Q1. 邏輯運算：")
                    q1 = st.number_input("若 3x + 15 = 45，則 x = ?", step=1)
                    if q1 == 10:
                        score += 50
                        ans_records.append("Q1:⭕")
                    else:
                        ans_records.append("Q1:❌")

                    st.subheader("Q2. 比例計算：")
                    q2 = st.radio("一件商品原價 2,000 元，打八折後是多少元？", [1400, 1600, 1800])
                    if q2 == 1600:
                        score += 50
                        ans_records.append("Q2:⭕")
                    else:
                        ans_records.append("Q2:❌")

                btn_submit = st.form_submit_button("🚀 確認交卷", type="primary", use_container_width=True)
                
                if btn_submit:
                    details_str = " | ".join(ans_records)
                    # 儲存成績並把狀態設為已完成
                    mark_test_completed_and_save_result(
                        current_test_id, cand_id, cand_name, cand_dept, exam_type, score, details_str
                    )
                    st.session_state.submitted = True
                    st.rerun()
        else:
            st.balloons()
            st.success("🎉 測驗已順利完成！您的成績已自動送出，可以關閉此網頁。")

# -------------------------------------------------------------------------
# 🔀 情境 B：網址無參數 -> 進入【HR 人資管理後台】
# -------------------------------------------------------------------------
else:
    st.title("🏢 UNITECH 人資測評管理系統")
    st.caption("請輸入 HR 密碼以開啟管理功能")
    
    hr_password = st.text_input("HR 管理員密碼", type="password")
    
    if hr_password == "hr1234":  # 🔐 請依需求更改密碼
        st.success("身份驗證成功！")
        
        tab1, tab2 = st.tabs(["➕ 建立測驗連結", "📊 測驗紀錄與成績"])
        
        # TAB 1: HR 派發測驗
        with tab1:
            st.subheader("產生應徵者專屬測驗連結")
            with st.form("create_form"):
                col1, col2 = st.columns(2)
                c_name = col1.text_input("應徵者姓名", placeholder="例如：王小明")
                c_id = col2.text_input("應徵者編號", placeholder="例如：A001")
                
                col3, col4 = st.columns(2)
                c_dept = col3.text_input("應徵部門", placeholder="例如：財務部")
                c_exam = col4.selectbox("選擇測驗科目", ["英文測驗", "數學測驗"])
                
                btn_gen = st.form_submit_button("🎲 建立隨機測驗連結", type="primary", use_container_width=True)
                
                if btn_gen:
                    if c_name and c_id and c_dept:
                        # 1. 生成 8 位數隨機 Token
                        token = str(uuid.uuid4())[:8]
                        
                        # 2. 寫入資料庫
                        save_new_test(token, c_id, c_name, c_dept, c_exam)
                        
                        # 3. 組成專屬連結 (抓取目前網頁的主網址)
                        # 在 Cloudflare 或 Streamlit 上會自動帶入域名
                        base_url = "https://hr-quiz-6bya8ipfvrzg8c2zwfj2m2.streamlit.app"
                        quiz_url = f"{base_url}/?test={token}"
                        
                        st.subheader("📋 產生成功的測驗連結：")
                        st.code(quiz_url, language="text")
                        st.info("💡 請直接複製上方連結寄發給應徵者，應徵者打開後將自動鎖定身分。")
                    else:
                        st.warning("⚠️ 請完整填寫應徵者姓名、編號與部門！")

        # TAB 2: 成績與數據檢視
        with tab2:
            st.subheader("📜 測驗派發紀錄 (tests_master.csv)")
            if os.path.exists(TESTS_FILE):
                st.dataframe(pd.read_csv(TESTS_FILE, dtype=str), use_container_width=True)
                
            st.subheader("🏆 應試者成績總表 (results_master.csv)")
            if os.path.exists(RESULTS_FILE):
                st.dataframe(pd.read_csv(RESULTS_FILE, dtype=str), use_container_width=True)
                
    elif hr_password:
        st.error("密碼錯誤，請重新輸入！")
