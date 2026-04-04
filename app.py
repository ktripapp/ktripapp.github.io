import streamlit as st
import random
from datetime import datetime, timedelta, timezone
import os
import pandas as pd
import streamlit.components.v1 as components
from pymongo import MongoClient
import socket
try:
    from dotenv import load_dotenv
    # Load environment variables from .env if present (safe for GitHub workflows)
    load_dotenv()
except Exception:
    # python-dotenv is optional; if it's not installed we continue without failing.
    pass

# optional GA helper (falls back gracefully if not configured)
try:
    from ga4 import get_daily_users
except Exception:
    get_daily_users = None

# 페이지 설정
st.set_page_config(page_title="케이트립 갓생 플랫폼", layout="wide", initial_sidebar_state="expanded")

# Load AdSense script for page (inserted into page HTML)
st.markdown('''
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8900421212808751"
    crossorigin="anonymous"></script>
''', unsafe_allow_html=True)
# AdSense account meta (helps some verification flows)
st.markdown('''
<meta name="google-adsense-account" content="ca-pub-8900421212808751">
''', unsafe_allow_html=True)

# 커스텀 CSS 스타일
st.markdown("""
<style>
    /* 전체 배경 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 타이틀 스타일 */
    .title-container {
        text-align: center;
        padding: 15px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    .title-container h1 {
        color: white;
        font-size: 3.0em;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .title-container p {
        color: #e0e0ff;
        font-size: 1.2em;
        margin: 0px 0 0 0;
    }
    
    /* st.button을 카드처럼 보이도록 스타일링 */
    div.stButton > button {
        /* 김태립9784님의 .game-card 기본 스타일 적용 */
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 15px 0; /* 컬럼 배치 시 필요 */
        box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        
        width: 100%; /* 컬럼 내에서 가득 차도록 */
        height: auto; /* 내용에 맞춰 높이 자동 조절 */
        border: none; /* Streamlit 기본 버튼 테두리 제거 */
        cursor: pointer;
        text-align: left; /* 내부 콘텐츠 왼쪽 정렬 */
        color: inherit; /* 폰트 색상을 내부 요소에서 상속 */
        white-space: pre-wrap; /* 줄 바꿈 및 공백 유지 */
        font-family: "NanumGothic", sans-serif; /* 나눔고딕 폰트 적용 */
        display: flex; /* 내부 텍스트 및 아이콘 정렬을 위해 */
        flex-direction: column; /* 세로로 배치 */
        align-items: flex-start; /* 좌측 정렬 */
    }
    
    div.stButton > button:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px 0 rgba(0, 0, 0, 0.3);
    }

    /* 버튼 내부에 텍스트가 있을 때의 스타일 (st.button은 직접 HTML 요소를 포함하지 않으므로, 이 부분이 중요) */
    /* st.button의 텍스트 레이블 자체는 Span 태그 안에 들어갑니다. */
    div.stButton > button > div > p { /* Streamlit이 버튼 텍스트를 감싸는 구조 */
        font-size: 1.8em; /* 제목 폰트 크기 */
        font-weight: bold; /* 제목 굵기 */
        color: #333; /* 제목 색상 */
        margin: 0 0 10px 0; /* 제목 아래 여백 */
        line-height: 1.2;
    }
    
    div.stButton > button > div > p:nth-of-type(2) { /* 두 번째 p 태그, 즉 설명 */
        font-size: 1em; /* 설명 폰트 크기 */
        font-weight: normal;
        color: #555; /* 설명 텍스트 색상 */
        margin-bottom: 0;
        line-height: 1.6;
    }

    /* 아이콘 스타일 - st.button 텍스트 안에 이모지를 직접 넣는 방식 */
    /* 이모지 자체는 span 태그로 감싸지지 않고 텍스트로 인식됩니다. */
    
    /* 카테고리 헤더 */
    .category-header {
        font-size: 2em;
        font-weight: bold;
        color: #667eea;
        margin-top: 40px;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 3px solid #667eea;
    }
    
    /* 피처 섹션 */
    .feature-box {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        flex: 1;
        height: 100%; /* 일정한 높이 유지 */
    }
    
    .feature-icon {
        font-size: 3em;
        margin-bottom: 10px;
    }
    
    .feature-title {
        font-weight: bold;
        color: #667eea;
        font-size: 1.2em;
        margin-bottom: 5px;
    }
    
    .feature-text {
        color: #666;
        font-size: 0.95em;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀 섹션
st.markdown("""
<div class="title-container">
    <h1>🎮 게임 앱</h1>
    <p>누구나 쉽게 즐기는 게임!</p>
</div>
""", unsafe_allow_html=True)

# 피처 섹션
st.markdown("### ✨ 게임 앱 특징")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">다양한 게임</div>
        <div class="feature-text">숫자, 퀴즈, 오목 등 다양한 게임 즐기기</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🏆</div>
        <div class="feature-title">점수 기록</div>
        <div class="feature-text">각 게임의 성적을 기록하고 추적하기</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">빠른 플레이</div>
        <div class="feature-text">언제 어디서나 빠르게 게임 시작하기</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🎁</div>
        <div class="feature-title">재미있는 경험</div>
        <div class="feature-text">친구들과 함께 즐기는 게임 체험</div>
    </div>
    """, unsafe_allow_html=True)

# 게임 섹션
st.markdown('<div class="category-header">🎲 게임 시작하기</div>', unsafe_allow_html=True)

col_game1, col_game2 = st.columns(2)

with col_game1:
    if st.button("🎯 숫자 게임\n\n숫자를 맞혀보세요! 숫자 맞추기 게임으로 당신의 실력을 시험해보세요.", 
                 key="number_game_card_btn", use_container_width=True):
        st.switch_page("pages/1_Number Game.py")
        
with col_game2:
    if st.button("🧠 간단한 퀴즈 게임\n\n퀴즈를 풀어보세요! 간단한 퀴즈 게임으로 당신의 지식을 시험해보세요.", 
                 key="quiz_game_card_btn", use_container_width=True):
        st.switch_page("pages/2_Simple Quiz Game.py")

# iframe 배너 추가
st.markdown("""
<div style='text-align: center; margin: 20px 0;'>
    <iframe src="https://coupa.ng/clptOA" width="100%" height="44" frameborder="0" scrolling="no" referrerpolicy="unsafe-url" browsingtopics></iframe>
</div>
""", unsafe_allow_html=True)

# 쿠팡 파트너스 안내 문구 추가
st.markdown("<p style='text-align: center; font-size: 0.8em;'>※ 쿠팡 파트너스 활동을 통해 일정액의 수수료를 제공받을 수 있습니다.</p>", unsafe_allow_html=True)

# 사이드바에 iframe 배너 추가
st.sidebar.markdown("""
<div style='text-align: center; margin: 0px 0;'>
    <a href="https://link.coupang.com/a/dP9eTe" target="_blank" referrerpolicy="unsafe-url"><img src="https://ads-partners.coupang.com/banners/966772?subId=&traceId=V0-301-879dd1202e5c73b2-I966772&w=320&h=50" alt=""></a>
</div>
""", unsafe_allow_html=True)

# MongoDB 연결
# Client 객체는 리소스 캐시로 유지하고, 조회/집계는 `st.cache_data`로 분리합니다.
client = None
collection = None


@st.cache_resource
def init_connection():
    try:
        # 1) st.secrets['mongo']를 우선 확인 (문서 권장: dict 또는 uri 문자열)
        if hasattr(st, "secrets") and st.secrets.get("mongo") is not None:
            creds = st.secrets["mongo"]
            # dict 형태면 **로 전달
            if isinstance(creds, dict):
                if "uri" in creds:
                    return MongoClient(creds["uri"], serverSelectionTimeoutMS=5000)
                return MongoClient(**creds, serverSelectionTimeoutMS=5000)
            # 문자열이면 URI로 사용
            if isinstance(creds, str):
                return MongoClient(creds, serverSelectionTimeoutMS=5000)

        # 2) 이전 관습(환경변수 또는 secrets.MONGO_URI) 지원
        if hasattr(st, "secrets") and st.secrets.get("MONGO_URI"):
            uri = st.secrets.get("MONGO_URI")
            if isinstance(uri, str):
                return MongoClient(uri, serverSelectionTimeoutMS=5000)
    except Exception:
        pass

    # 3) 환경변수 폴백
    uri = os.getenv("MONGO_URI") or os.getenv("MONGO")
    if uri:
        return MongoClient(uri, serverSelectionTimeoutMS=5000)

    return None


client = init_connection()

collection = None
if client:
    try:
        client.admin.command("ping")
        # Determine DB name: prefer st.secrets['mongo']['db'], then env vars, fallback to 'ktrip'
        db_name = None
        try:
            if hasattr(st, "secrets") and st.secrets.get("mongo"):
                creds = st.secrets["mongo"]
                if isinstance(creds, dict) and creds.get("db"):
                    db_name = creds.get("db")
        except Exception:
            db_name = None

        if not db_name:
            db_name = os.getenv("MONGO_DB") or os.getenv("MONGO_DATABASE") or "ktrip"

        db = client.get_database(db_name)
        collection = db.get_collection("visitor")
    except Exception:
        collection = None
        st.sidebar.warning("MongoDB 통계 기능 비활성화")
else:
    st.sidebar.info("MongoDB 연결 정보가 없습니다. (secrets['mongo'] 또는 MONGO_URI 사용). Set MONGO_DB to choose DB (default 'ktrip').")


# 조회/집계용 함수는 `st.cache_data`로 분리하여 캐시합니다.
@st.cache_data(ttl=60)
def fetch_counts():
    if collection is None:
        return 0, 0
    try:
        total_count = collection.count_documents({})
    except Exception:
        total_count = 0

    # Compute "today" in Korea Standard Time (KST, UTC+9) and convert
    # the range to UTC for querying timestamps stored in UTC in MongoDB.
    try:
        kst = timezone(timedelta(hours=9))
        today_kst = datetime.now(kst).date()
        start_kst = datetime(today_kst.year, today_kst.month, today_kst.day, tzinfo=kst)
        end_kst = start_kst + timedelta(days=1)
        start_utc = start_kst.astimezone(timezone.utc)
        end_utc = end_kst.astimezone(timezone.utc)
        today_count = collection.count_documents({"timestamp": {"$gte": start_utc, "$lt": end_utc}})
    except Exception:
        today_count = 0

    return total_count, today_count

def log_visit():
    ip = None
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            ip = st.context.headers.get("X-Forwarded-For", None)
    except Exception:
        ip = None

    user_agent = "unknown"
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            user_agent = st.context.headers.get("User-Agent", "unknown")
    except Exception:
        user_agent = "unknown"

    # Try to detect a user id from session or headers (optional)
    user_id = None
    try:
        user_id = st.session_state.get("user_id") if "user_id" in st.session_state else None
    except Exception:
        user_id = None
    try:
        if user_id is None and hasattr(st, "context") and hasattr(st.context, "headers"):
            user_id = st.context.headers.get("X-User-Id") or st.context.headers.get("X-Auth-User")
    except Exception:
        pass

    # Prevent duplicate counting for the same ip or same user_id within the same KST "day".
    if collection is not None:
        try:
            kst = timezone(timedelta(hours=9))
            now_kst = datetime.now(timezone.utc).astimezone(kst)
            today_kst = now_kst.date()
            start_kst = datetime(today_kst.year, today_kst.month, today_kst.day, tzinfo=kst)
            end_kst = start_kst + timedelta(days=1)
            start_utc = start_kst.astimezone(timezone.utc)
            end_utc = end_kst.astimezone(timezone.utc)

            # Build query to find any existing visit today with same ip or same user_id
            query = {"timestamp": {"$gte": start_utc, "$lt": end_utc}}
            or_clauses = []
            if ip:
                or_clauses.append({"ip": ip})
            if user_id:
                or_clauses.append({"user_id": user_id})

            exists = False
            if or_clauses:
                query = {"$and": [query, {"$or": or_clauses}]}
                exists = collection.count_documents(query) > 0

            if exists:
                return

            visit_data = {
                "timestamp": datetime.now(timezone.utc),
                "ip": ip,
                "user_agent": user_agent,
                "user_id": user_id,
            }
            collection.insert_one(visit_data)
        except Exception:
            # fail silently to avoid breaking the app if DB errors occur
            pass

if "visited" not in st.session_state:
    log_visit()
    st.session_state.visited = True
if collection is not None:
    total_count, today_count = fetch_counts()

    col1, col2 = st.sidebar.columns(2)
    col1.markdown(
        f"<div style='width:100%;text-align:center;padding:6px 0;'>"
        f"<div style='font-size:16px;margin-bottom:4px'>오늘 방문자 수</div>"
        f"<div style='font-size:16px;font-weight:600'>{today_count}</div></div>",
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"<div style='width:100%;text-align:center;padding:6px 0;'>"
        f"<div style='font-size:16px;margin-bottom:4px'>총 방문자 수</div>"
        f"<div style='font-size:16px;font-weight:600'>{total_count}</div></div>",
        unsafe_allow_html=True,
    )
else:
    st.sidebar.info("데이터베이스 연결이 없어 통계 미표시")

# ads.txt 직접 반환
query_params = st.query_params
path = query_params.get("path", [""])[0] if query_params else ""

# Streamlit has no `requested_page` attribute. Some hosting platforms
# may pass a `path` query param when requesting a specific file
# (e.g. ?path=ads.txt). Fallback to checking `path` for ads.txt.
# Some older deployments or custom builds may set `st.requested_page`.
# Check it safely with getattr to avoid AttributeError on newer Streamlit.
requested_page = getattr(st, "requested_page", None)
if requested_page == "ads.txt" or path == "ads.txt":
    st.text("google.com, pub-8900421212808751, DIRECT, f08c47fec0942fa0")
    st.stop()

adsense_code = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8900421212808751"
     crossorigin="anonymous"></script>"""