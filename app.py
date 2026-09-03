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
        "question": "1. 2，2，4，12，    ，240",
        "options": {" A": "24", "B": "84", "C": "32", "D": "48", "E": "120"},
        "answer": "D"
    },
    {
        "id": "mq2",
        "question": "2. 27，9，18，6，12，    ，8",
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
        "question": "24. (題組24-25) 在九宮格中，任何直的三位數字相加等於橫的三位數字相加，也等於斜的三位數字相加。\n已知矩陣為：\n[ 18,  X,  Y  ]\n[  M, 15,  N ]\n[  Z, 19, 12  ]\n請問 X = ？",
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
        "question": "1. 2，2，4，12，    ，240",
        "options": {" A": "24", "B": "84", "C": "32", "D": "48", "E": "120"},
        "answer": "D"
    },
    {
        "id": "mq2",
        "question": "2. 27，9，18，6，12，    ，8",
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
        "question": "24. (題組24-25) 在九宮格中，任何直的三位數字相加等於橫的三位數字相加，也等於斜的三位數字相加。\n已知矩陣為：\n[ 18,  X,  Y  ]\n[  M, 15,  N ]\n[  Z, 19, 12  ]\n請問 X = ？",
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
            lines.append(current_line)
            
    # 計算排版所需的 SVG 尺寸
    line_height = font_size * 1.5
    svg_height = int(len(lines) * line_height + 15)
    
    # 動態計算所需的最寬寬度，避免文字被裁切
    max_line_width = 0
    for line in lines:
        line_capacity = sum(2 if ord(c) > 127 else 1 for c in line)
        w = line_capacity * (font_size * 0.55)
        if w > max_line_width:
            max_line_width = w
            
    # 確保寬度至少 720，如果內容很長會自動擴展
    svg_width = int(max(720, max_line_width + 40)) 
    
    tspan_elements = ""
    for idx, line in enumerate(lines):
        y_pos = int((idx + 1) * line_height)
        # 過濾特殊字元避免破壞 XML 結構
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tspan_elements += f'<tspan x="0" y="{y_pos}">{safe_line}</tspan>'
        
    svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">
        <text font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="{font_size}px" font-weight="600" fill="#111827">
            {tspan_elements}
        </text>
    </svg>'''
    
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="vertical-align: middle; display: block; margin: 8px 0; max-width: 100%; height: auto;" />'

def option_to_svg(text: str, font_size: int = 20) -> str:
    # 修復：將中文字元考慮為2單位，動態調整寬度避免右方截斷
    text_capacity = sum(2 if ord(c) > 127 else 1 for c in text)
    width = int(max(text_capacity * (font_size * 0.6) + 30, 320))
    height = int(font_size * 1.6)
    
    safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <text x="5" y="{font_size * 1.1}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="{font_size}px" font-weight="500" fill="#374151">{safe_text}</text>
    </svg>'''
    
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="vertical-align: middle; display: inline-block; margin: 2px 0;" />'

def inject_anti_cheat_script():
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
                
                # ------------------- 英文測驗 -------------------
                if exam_type == "英文測驗":
                    st.markdown(text_to_multiline_svg("PART 1. Vocabulary & Grammar Test (Q1-Q13)", font_size=24, max_chars_per_line=60), unsafe_allow_html=True)
                    st.divider()

                    last_rendered_attachment = None

                    for idx, q_item in enumerate(ENGLISH_QUIZ_DATA):
                        q_id = q_item["id"]
                        q_text = q_item["question"]
                        opts = q_item["options"]
                        corr_ans = q_item["answer"]

                        if idx == 13:
                            st.markdown(text_to_multiline_svg("PART 2. Reading Comprehension Test (Q14-Q17)", font_size=24, max_chars_per_line=60), unsafe_allow_html=True)
                            st.divider()

                        if "image_key" in q_item:
                            img_key = q_item["image_key"]
                            if img_key != last_rendered_attachment:
                                st.info("📌 請根據下方文章/圖表內容回答問題：")
                                if img_key == "attachment1":
                                    display_quiz_image("題目1.png", "[附件一] Valentino's Corner 廣告")
                                elif img_key == "attachment2":
                                    display_quiz_image("題目2.png", "[附件二] Yearly Consumption of Animal Products")
                                last_rendered_attachment = img_key

                        st.markdown(text_to_multiline_svg(q_text, font_size=22, max_chars_per_line=50), unsafe_allow_html=True)
                        
                        opts_html = "".join([f"* **{k})** {option_to_svg(v, font_size=20)}<br/>" for k, v in opts.items()])
                        st.markdown(opts_html, unsafe_allow_html=True)
                        
                        user_ans = st.radio("請選擇正確答案：", list(opts.keys()), key=f"radio_{q_id}")
                        
                        if user_ans == corr_ans:
                            score += (100.0 / len(ENGLISH_QUIZ_DATA))
                            ans_records.append(f"Q{idx+1}:⭕ ({user_ans})")
                        else:
                            ans_records.append(f"Q{idx+1}:❌ ({user_ans})")
                        
                        st.divider()

                # ------------------- 數學測驗 (1-27題) -------------------
                elif exam_type == "數學測驗":
                    st.markdown(text_to_multiline_svg("數學邏輯能力測驗（共 27 題，每題 2.5 分）", font_size=24, max_chars_per_line=60), unsafe_allow_html=True)
                    st.divider()

                    for idx, q_item in enumerate(MATH_QUIZ_DATA):
                        q_id = q_item["id"]
                        q_text = q_item["question"]
                        opts = q_item["options"]
                        corr_ans = q_item["answer"]

                        st.markdown(text_to_multiline_svg(q_text, font_size=20, max_chars_per_line=45), unsafe_allow_html=True)
                        
                        opts_html = "".join([f"* **({k})** {option_to_svg(v, font_size=18)}<br/>" for k, v in opts.items()])
                        st.markdown(opts_html, unsafe_allow_html=True)
                        
                        user_ans = st.radio("請選擇正確答案：", list(opts.keys()), key=f"m_radio_{q_id}", disabled=is_time_up)
                        
                        if user_ans == corr_ans:
                            score += 2.5  # 每題 2.5 分
                            ans_records.append(f"Q{idx+1}:⭕ ({user_ans})")
                        else:
                            ans_records.append(f"Q{idx+1}:❌ ({user_ans})")
                        
                        st.divider()

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
# 🔀 情境 B：HR 管理後台
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
                        st.info("💡 請複製上方連結寄發給應徵者。")
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
        st.error("密碼錯誤，請重新輸入！")5
