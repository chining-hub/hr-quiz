我的程式碼為:import streamlit as st
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

# =========================================================================
# 📚 題庫資料結構 (英文 17 題 / 數學 27 題)
# =========================================================================
ENGLISH_QUIZ_DATA = [
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
    {
        "id": "q14",
        "image_key": "attachment1",
        "question": "14. What kind of business is Valentino’s Corner?",
        "options": {"A": "A restaurant", "B": "A bakery", "C": "A pottery shop", "D": "A courier service"},
        "answer": "A"
    },
    {
        "id": "q15",
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
    {
        "id": "q16",
        "image_key": "attachment2",
        "question": "16. Which product is consumed in the greatest amounts?",
        "options": {"A": "Pork", "B": "Beef", "C": "Chicken", "D": "Fish"},
        "answer": "B"
    },
    {
        "id": "q17",
        "image_key": "attachment2",
        "question": "17. Who would benefit from this particular graph?",
        "options": {"A": "A person on a diet", "B": "A produce farmer", "C": "A vegetarian", "D": "Cattle raisers"},
        "answer": "D"
    }
]

MATH_QUIZ_DATA = [
    {
        "id": "mq1",
        "question": "1. 2，2，4，12，    ，240",
        "options": {" A": "24", "B": "84", "C": "32", "D": "48", "E": "120"},
        "answer": "D"
    },
    {
        "id": "mq2",
        "question": "2. 27，9，18，6，12，    ，8",
        "options": {" A": "3", "B": "6", "C": "4", "D": "12", "E": "8"},
        "answer": "C"
    },
    {
        "id": "mq3",
        "question": "3. 某次數學測驗中，試題共有50題，答對一題給2分，答錯一題倒扣1分，沒有做答的不給分，某生答對42題，答錯4題，有4題未答，則此生得多少分？",
        "options": {" A": "76", "B": "78", "C": "80", "D": "82", "E": "84"},
        "answer": "C"
    },
    {
        "id": "mq4",
        "question": "4. 某一牧場共有牛、羊、馬共1300隻，已知牛的數量恰為馬的數量75%，而羊的數量為牛的數量2倍，則請問牛有多少隻？",
        "options": {" A": "200", "B": "300", "C": "400", "D": "600", "E": "800"},
        "answer": "B"
    },
    {
        "id": "mq5",
        "question": "5. 在一條路的兩旁種樹，每隔4公尺種樹一棵，共種200棵，請問此條路長多少公尺？",
        "options": {" A": "800", "B": "792", "C": "400", "D": "396", "E": "404"},
        "answer": "D"
    },
    {
        "id": "mq6",
        "question": "6. 已知某個水池，每秒鐘流出8公升的水，每秒鐘流入10公升的水；1分半鐘以後，池中有水200公升，池中原來有水多少公升？",
        "options": {" A": "20", "B": "40", "C": "60", "D": "80", "E": "100"},
        "answer": "A"
    },
    {
        "id": "mq7",
        "question": "7. 甲乙兩杯糖水，甲杯濃度為18%，乙杯為14%；若在現要調配出16%的糖水，則甲乙兩杯糖水取用的比例為多少？",
        "options": {" A": "1:1", "B": "1:2", "C": "1:3", "D": "2:3", "E": "1:4"},
        "answer": "A"
    },
    {
        "id": "mq8",
        "question": "8. 某家便利商店推出特賣商品，每賣出一件可獲利60元。已知其成本為特價的7折，則請問特價為多少元？",
        "options": {" A": "100", "B": "140", "C": "150", "D": "180", "E": "200"},
        "answer": "E"
    },
    {
        "id": "mq9",
        "question": "9. 若正方形各邊長減少10%時，則其面積減少多少？",
        "options": {" A": "1%", "B": "10%", "C": "15%", "D": "19%", "E": "20%"},
        "answer": "D"
    },
    {
        "id": "mq10",
        "question": "10. 同樣的物品，甲店的定價為1,300，乙店為1,350元，丙店為1,600元，但甲店打9折，乙店打75折，丙店打雙8折，則賣價最低的是那一家？",
        "options": {" A": "甲", "B": "乙", "C": "丙", "D": "甲乙一樣低", "E": "三家一樣低"},
        "answer": "B"
    },
    {
        "id": "mq11",
        "question": "11. 甲乙丙三個兄弟，每個兄弟各有三個妹妺，請問這家共有幾個兄弟姐妹？",
        "options": {" A": "3", "B": "4", "C": "6", "D": "9", "E": "12"},
        "answer": "C"
    },
    {
        "id": "mq12",
        "question": "12. 一邊長各為6公分的正方體，六面皆塗上顏料後，再將各邊長三等分，切成長寬高各為2公分的小立方體，請問這些小立方體中，六面皆未塗上顏料的有幾個？",
        "options": {" A": "1", "B": "2", "C": "3", "D": "4", "E": "5"},
        "answer": "A"
    },
    {
        "id": "mq13",
        "question": "13. 屋內有一群男女生，男生眼中所見「男3倍於女」，女生眼中所見「男5倍於女」，請問男生有幾人？",
        "options": {" A": "3", "B": "5", "C": "9", "D": "10", "E": "12"},
        "answer": "C"
    },
    {
        "id": "mq14",
        "question": "14. 某布店繪製一張圓形圖，表明銷售各種布料之比例；其中卡其布的銷售佔總銷售量的5%，請問在圓形圖上應佔多少度的面積？",
        "options": {" A": "5", "B": "9", "C": "15", "D": "18", "E": "36"},
        "answer": "D"
    },
    {
        "id": "mq15",
        "question": "15. 有一列火車全長90公尺，時速為90km/hr，現在要通過一座橋，橋長60公尺，則請問當火車剛通過橋頭，到火車尾離開橋尾，總共需花費多少分鐘？",
        "options": {" A": "0.1", "B": "0.5", "C": "1", "D": "1.5", "E": "2"},
        "answer": "A"
    },
    {
        "id": "mq16",
        "question": "16. 一件工作，甲獨做24日完成，乙獨做36日完成，丙獨作18日完成，則三人合作要幾天才能完成？",
        "options": {" A": "7", "B": "8", "C": "9", "D": "12", "E": "18"},
        "answer": "B"
    },
    {
        "id": "mq17",
        "question": "17. 已知小美年齡與老公大華的年齡比為3：4，且小美年紀比大華小9歲，則請問2人明年的年齡和為多少歲？",
        "options": {" A": "55", "B": "57", "C": "63", "D": "65", "E": "67"},
        "answer": "D"
    },
    {
        "id": "mq18",
        "question": "18. 有一個二位數，已知個位數字和十位數字和為11，若將個位數數字和十位數數字交換，可得一個新的二位數，此新二位數為原來的二位數之2倍多7；請問此新二位數為多少？",
        "options": {" A": "38", "B": "83", "C": "56", "D": "65", "E": "74"},
        "answer": "B"
    },
    {
        "id": "mq19",
        "question": "19. 一群獵人在小屋裡開會，身旁皆會跟著自己帶來的獵狗；已知屋內共有28個頭，96條腿，請問屋內共有幾隻獵狗？",
        "options": {" A": "8", "B": "12", "C": "16", "D": "20", "E": "24"},
        "answer": "D"
    },
    {
        "id": "mq20",
        "question": "20. (題組20-21) 有甲、乙、丙共3位月薪資不同之員工，已知：(1) 甲的75%等於乙的57% (2) 甲的75%等於丙的45%。請問誰的月薪最高？",
        "options": {" A": "甲", "B": "乙", "C": "丙"},
        "answer": "C"
    },
    {
        "id": "mq21",
        "question": "21. (題組20-21) 承上題，請問誰的月薪最低？",
        "options": {" A": "甲", "B": "乙", "C": "丙"},
        "answer": "B"
    },
    {
        "id": "mq22",
        "question": "22. (題組22-23) 小明有一個哥哥、一個弟弟和一個妹妺，已知：(1)3年前哥哥的年紀是弟弟年紀的3倍 (2)2年後哥哥的年紀是弟弟年紀的2倍 (3)弟弟和妹妹年紀相差1歲 (4)2年前小明的年紀是弟弟的2倍 (5)明年小明的年紀是妹妹的2倍少1歲。請問小明今年幾歲？",
        "options": {" A": "8", "B": "10", "C": "12", "D": "14", "E": "16"},
        "answer": "C"
    },
    {
        "id": "mq23",
        "question": "23. (題組22-23) 承上題，請問幾年後，哥哥年紀是妹妺的2倍？",
        "options": {" A": "2", "B": "3", "C": "4", "D": "5", "E": "6"},
        "answer": "D"
    },
    {
        "id": "mq24",
        "question": "24. (題組24-25) 在九宮格中，任何直的三位數字相加等於橫的三位數字相加，也等於斜的三位數字相加。\n已知矩陣為：\n[ 18,  X,  Y  ]\n[  M, 15,  N ]\n[  Z, 19, 12  ]\n請問 X = ？",
        "options": {" A": "16", "B": "18", "C": "14", "D": "12", "E": "11"},
        "answer": "E"
    },
    {
        "id": "mq25",
        "question": "25. (題組24-25) 承上題，請問 N = ？",
        "options": {" A": "14", "B": "15", "C": "16", "D": "17", "E": "18"},
        "answer": "D"
    },
    {
        "id": "mq26",
        "question": "26. (題組26-27) 某次小考，老師出了2題數學題目，班上同學一共40人，第一題答對者有10人，第二題答對者有26人，但零分者有6人。請問考滿分100分者，有幾個人？",
        "options": {" A": "0", "B": "2", "C": "3", "D": "4", "E": "6"},
        "answer": "B"
    },
    {
        "id": "mq27",
        "question": "27. (題組26-27) 承上題，請問只答對一題者，有幾個人？",
        "options": {" A": "26", "B": "28", "C": "30", "D": "32", "E": "36"},
        "answer": "D"
    }
]

# =========================================================================
# 🗄️ 1. SQLite 資料庫自動建表與讀寫模組
# =========================================================================
DB_NAME = "quiz_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tests WHERE test_id = ?", (test_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_new_test(test_id, name, dept, exam_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tests (test_id, name, dept, exam_type, created_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (test_id, name, dept, exam_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "未完成"))
    conn.commit()
    conn.close()

def sync_to_google_sheets(data_dict):
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
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception as e:
        print(f"Google Sheets 同步失敗: {e}")

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

# =========================================================================
# 📚 題庫資料結構 (英文 17 題 / 數學 27 題)
# =========================================================================
ENGLISH_QUIZ_DATA = [
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
    {
        "id": "q14",
        "image_key": "attachment1",
        "question": "14. What kind of business is Valentino’s Corner?",
        "options": {"A": "A restaurant", "B": "A bakery", "C": "A pottery shop", "D": "A courier service"},
        "answer": "A"
    },
    {
        "id": "q15",
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
    {
        "id": "q16",
        "image_key": "attachment2",
        "question": "16. Which product is consumed in the greatest amounts?",
        "options": {"A": "Pork", "B": "Beef", "C": "Chicken", "D": "Fish"},
        "answer": "B"
    },
    {
        "id": "q17",
        "image_key": "attachment2",
        "question": "17. Who would benefit from this particular graph?",
        "options": {"A": "A person on a diet", "B": "A produce farmer", "C": "A vegetarian", "D": "Cattle raisers"},
        "answer": "D"
    }
]

MATH_QUIZ_DATA = [
    {
        "id": "mq1",
        "question": "1. 2，2，4，12，    ，240",
        "options": {" A": "24", "B": "84", "C": "32", "D": "48", "E": "120"},
        "answer": "D"
    },
    {
        "id": "mq2",
        "question": "2. 27，9，18，6，12，    ，8",
        "options": {" A": "3", "B": "6", "C": "4", "D": "12", "E": "8"},
        "answer": "C"
    },
    {
        "id": "mq3",
        "question": "3. 某次數學測驗中，試題共有50題，答對一題給2分，答錯一題倒扣1分，沒有做答的不給分，某生答對42題，答錯4題，有4題未答，則此生得多少分？",
        "options": {" A": "76", "B": "78", "C": "80", "D": "82", "E": "84"},
        "answer": "C"
    },
    {
        "id": "mq4",
        "question": "4. 某一牧場共有牛、羊、馬共1300隻，已知牛的數量恰為馬的數量75%，而羊的數量為牛的數量2倍，則請問牛有多少隻？",
        "options": {" A": "200", "B": "300", "C": "400", "D": "600", "E": "800"},
        "answer": "B"
    },
    {
        "id": "mq5",
        "question": "5. 在一條路的兩旁種樹，每隔4公尺種樹一棵，共種200棵，請問此條路長多少公尺？",
        "options": {" A": "800", "B": "792", "C": "400", "D": "396", "E": "404"},
        "answer": "D"
    },
    {
        "id": "mq6",
        "question": "6. 已知某個水池，每秒鐘流出8公升的水，每秒鐘流入10公升的水；1分半鐘以後，池中有水200公升，池中原來有水多少公升？",
        "options": {" A": "20", "B": "40", "C": "60", "D": "80", "E": "100"},
        "answer": "A"
    },
    {
        "id": "mq7",
        "question": "7. 甲乙兩杯糖水，甲杯濃度為18%，乙杯為14%；若在現要調配出16%的糖水，則甲乙兩杯糖水取用的比例為多少？",
        "options": {" A": "1:1", "B": "1:2", "C": "1:3", "D": "2:3", "E": "1:4"},
        "answer": "A"
    },
    {
        "id": "mq8",
        "question": "8. 某家便利商店推出特賣商品，每賣出一件可獲利60元。已知其成本為特價的7折，則請問特價為多少元？",
        "options": {" A": "100", "B": "140", "C": "150", "D": "180", "E": "200"},
        "answer": "E"
    },
    {
        "id": "mq9",
        "question": "9. 若正方形各邊長減少10%時，則其面積減少多少？",
        "options": {" A": "1%", "B": "10%", "C": "15%", "D": "19%", "E": "20%"},
        "answer": "D"
    },
    {
        "id": "mq10",
        "question": "10. 同樣的物品，甲店的定價為1,300，乙店為1,350元，丙店為1,600元，但甲店打9折，乙店打75折，丙店打雙8折，則賣價最低的是那一家？",
        "options": {" A": "甲", "B": "乙", "C": "丙", "D": "甲乙一樣低", "E": "三家一樣低"},
        "answer": "B"
    },
    {
        "id": "mq11",
        "question": "11. 甲乙丙三個兄弟，每個兄弟各有三個妹妺，請問這家共有幾個兄弟姐妹？",
        "options": {" A": "3", "B": "4", "C": "6", "D": "9", "E": "12"},
        "answer": "C"
    },
    {
        "id": "mq12",
        "question": "12. 一邊長各為6公分的正方體，六面皆塗上顏料後，再將各邊長三等分，切成長寬高各為2公分的小立方體，請問這些小立方體中，六面皆未塗上顏料的有幾個？",
        "options": {" A": "1", "B": "2", "C": "3", "D": "4", "E": "5"},
        "answer": "A"
    },
    {
        "id": "mq13",
        "question": "13. 屋內有一群男女生，男生眼中所見「男3倍於女」，女生眼中所見「男5倍於女」，請問男生有幾人？",
        "options": {" A": "3", "B": "5", "C": "9", "D": "10", "E": "12"},
        "answer": "C"
    },
    {
        "id": "mq14",
        "question": "14. 某布店繪製一張圓形圖，表明銷售各種布料之比例；其中卡其布的銷售佔總銷售量的5%，請問在圓形圖上應佔多少度的面積？",
        "options": {" A": "5", "B": "9", "C": "15", "D": "18", "E": "36"},
        "answer": "D"
    },
    {
        "id": "mq15",
        "question": "15. 有一列火車全長90公尺，時速為90km/hr，現在要通過一座橋，橋長60公尺，則請問當火車剛通過橋頭，到火車尾離開橋尾，總共需花費多少分鐘？",
        "options": {" A": "0.1", "B": "0.5", "C": "1", "D": "1.5", "E": "2"},
        "answer": "A"
    },
    {
        "id": "mq16",
        "question": "16. 一件工作，甲獨做24日完成，乙獨做36日完成，丙獨作18日完成，則三人合作要幾天才能完成？",
        "options": {" A": "7", "B": "8", "C": "9", "D": "12", "E": "18"},
        "answer": "B"
    },
    {
        "id": "mq17",
        "question": "17. 已知小美年齡與老公大華的年齡比為3：4，且小美年紀比大華小9歲，則請問2人明年的年齡和為多少歲？",
        "options": {" A": "55", "B": "57", "C": "63", "D": "65", "E": "67"},
        "answer": "D"
    },
    {
        "id": "mq18",
        "question": "18. 有一個二位數，已知個位數字和十位數字和為11，若將個位數數字和十位數數字交換，可得一個新的二位數，此新二位數為原來的二位數之2倍多7；請問此新二位數為多少？",
        "options": {" A": "38", "B": "83", "C": "56", "D": "65", "E": "74"},
        "answer": "B"
    },
    {
        "id": "mq19",
        "question": "19. 一群獵人在小屋裡開會，身旁皆會跟著自己帶來的獵狗；已知屋內共有28個頭，96條腿，請問屋內共有幾隻獵狗？",
        "options": {" A": "8", "B": "12", "C": "16", "D": "20", "E": "24"},
        "answer": "D"
    },
    {
        "id": "mq20",
        "question": "20. (題組20-21) 有甲、乙、丙共3位月薪資不同之員工，已知：(1) 甲的75%等於乙的57% (2) 甲的75%等於丙的45%。請問誰的月薪最高？",
        "options": {" A": "甲", "B": "乙", "C": "丙"},
        "answer": "C"
    },
    {
        "id": "mq21",
        "question": "21. (題組20-21) 承上題，請問誰的月薪最低？",
        "options": {" A": "甲", "B": "乙", "C": "丙"},
        "answer": "B"
    },
    {
        "id": "mq22",
        "question": "22. (題組22-23) 小明有一個哥哥、一個弟弟和一個妹妺，已知：(1)3年前哥哥的年紀是弟弟年紀的3倍 (2)2年後哥哥的年紀是弟弟年紀的2倍 (3)弟弟和妹妹年紀相差1歲 (4)2年前小明的年紀是弟弟的2倍 (5)明年小明的年紀是妹妹的2倍少1歲。請問小明今年幾歲？",
        "options": {" A": "8", "B": "10", "C": "12", "D": "14", "E": "16"},
        "answer": "C"
    },
    {
        "id": "mq23",
        "question": "23. (題組22-23) 承上題，請問幾年後，哥哥年紀是妹妺的2倍？",
        "options": {" A": "2", "B": "3", "C": "4", "D": "5", "E": "6"},
        "answer": "D"
    },
    {
        "id": "mq24",
        "question": "24. (題組24-25) 在九宮格中，任何直的三位數字相加等於橫的三位數字相加，也等於斜的三位數字相加。\n已知矩陣為：\n[ 18,  X,  Y  ]\n[  M, 15,  N ]\n[  Z, 19, 12  ]\n請問 X = ？",
        "options": {" A": "16", "B": "18", "C": "14", "D": "12", "E": "11"},
        "answer": "E"
    },
    {
        "id": "mq25",
        "question": "25. (題組24-25) 承上題，請問 N = ？",
        "options": {" A": "14", "B": "15", "C": "16", "D": "17", "E": "18"},
        "answer": "D"
    },
    {
        "id": "mq26",
        "question": "26. (題組26-27) 某次小考，老師出了2題數學題目，班上同學一共40人，第一題答對者有10人，第二題答對者有26人，但零分者有6人。請問考滿分100分者，有幾個人？",
        "options": {" A": "0", "B": "2", "C": "3", "D": "4", "E": "6"},
        "answer": "B"
    },
    {
        "id": "mq27",
        "question": "27. (題組26-27) 承上題，請問只答對一題者，有幾個人？",
        "options": {" A": "26", "B": "28", "C": "30", "D": "32", "E": "36"},
        "answer": "D"
    }
]

# =========================================================================
# 🗄️ 1. SQLite 資料庫自動建表與讀寫模組
# =========================================================================
DB_NAME = "quiz_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tests WHERE test_id = ?", (test_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_new_test(test_id, name, dept, exam_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tests (test_id, name, dept, exam_type, created_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (test_id, name, dept, exam_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "未完成"))
    conn.commit()
    conn.close()

def sync_to_google_sheets(data_dict):
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    submit_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("UPDATE tests SET status = '已完成' WHERE test_id = ?", (test_id,))
    cursor.execute('''
        INSERT INTO results (test_id, name, dept, exam_type, score, submit_time, duration_seconds, details, cheat_logs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (test_id, name, dept, exam_type, score, submit_time_str, duration_sec, details_str, cheat_logs))
    
    conn.commit()
    conn.close()

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

init_sqlite_db()

# =========================================================================
# 🛡️ 2. SVG 向量圖像化與防偷看腳本 (已修復中文切字問題)
# =========================================================================
def text_to_multiline_svg(text: str, font_size: int = 22, max_chars_per_line: int = 50) -> str:
    """將文字轉換為 SVG，支援中英混排與自動安全換行"""
    lines_input = text.split("\n")
    lines = []
    
    # 建立一個容量基準：中文字元/全形算 2 單位，英文字元算 1 單位
    # 假設原始 max_chars_per_line 是針對英文字的長度，則總容量為 max_chars_per_line * 2
    max_capacity = max_chars_per_line * 2 
    
    for paragraph in lines_input:
        words = paragraph.split(" ")
        current_line = ""
        current_capacity = 0
        
        for word in words:
            # 計算該單詞的單位長度（中文字 > 127，視為 2）
            word_capacity = sum(2 if ord(c) > 127 else 1 for c in word)
            space_capacity = 1 if current_line else 0
            
            if current_capacity + space_capacity + word_capacity <= max_capacity:
                # 若能塞得下，直接合併
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
                current_capacity += space_capacity + word_capacity
            else:
                # 如果單字本身超越了單行最大容量 (例如: 整句無空白的中文)
                if word_capacity > max_capacity:
                    if current_line:
                        lines.append(current_line)
                        current_line = ""
                        current_capacity = 0
                        
                    # 強制逐字切分
                    for char in word:
                        char_capacity = 2 if ord(char) > 127 else 1
                        if current_capacity + char_capacity > max_capacity:
                            lines.append(current_line)
                            current_line = char
                            current_capacity = char_capacity
                        else:
                            current_line += char
                            current_capacity += char_capacity
                else:
                    # 只是這行滿了，將單字移到下一行
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                    current_capacity = word_capacity

        if current_line:
            lines.append(current_lin
