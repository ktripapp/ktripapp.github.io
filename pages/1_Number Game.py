import streamlit as st
import random

# --- 1. 게임 초기화 및 상태 관리 ---
# st.session_state를 사용해서 게임 상태를 저장해요.
# Streamlit 앱은 사용자 인터랙션이 발생할 때마다 코드를 처음부터 다시 실행하기 때문에,
# 게임의 진행 상황(예: 정답 숫자, 시도 횟수, 메시지)을 저장하기 위해 필요합니다.

def initialize_game():
    st.session_state.secret_number = random.randint(1, 100) # 1부터 100 사이의 비밀 숫자 생성
    st.session_state.attempts = 0 # 시도 횟수 초기화
    st.session_state.game_message = "1에서 100 사이의 숫자를 맞춰보세요!" # 초기 메시지
    st.session_state.game_over = False # 게임 종료 여부

# 게임이 처음 실행될 때 또는 '새 게임' 버튼을 눌렀을 때 초기화
if 'secret_number' not in st.session_state:
    initialize_game()

# --- 2. 게임 화면 구성 ---
st.title("🎯 숫자 맞추기")

st.write(st.session_state.game_message) # 현재 게임 메시지 표시
st.write(f"현재 시도 횟수: {st.session_state.attempts}회") # 시도 횟수 표시

# 게임이 끝나지 않았을 때만 입력 필드와 버튼을 보여줍니다.
if not st.session_state.game_over:
    # 사용자 입력 받기
    guess = st.number_input("당신의 숫자는?", min_value=1, max_value=100, step=1, key="guess_input")

    # '확인' 버튼
    if st.button("확인"):
        # 입력된 값이 있고, 게임이 아직 끝나지 않았다면
        if guess is not None:
            st.session_state.attempts += 1 # 시도 횟수 증가

            if guess < st.session_state.secret_number:
                st.session_state.game_message = "더 높은 숫자를 맞춰보세요!"
            elif guess > st.session_state.secret_number:
                st.session_state.game_message = "더 낮은 숫자를 맞춰보세요!"
            else:
                st.session_state.game_message = f"정답입니다! {st.session_state.attempts}회 만에 맞추셨어요!"
                st.session_state.game_over = True # 게임 종료

            # 메시지를 업데이트했으니 화면을 다시 그리기 위해 한 번 더 갱신합니다.
            st.rerun()

# 게임이 끝났을 때 '새 게임' 버튼을 보여줍니다.
if st.session_state.game_over:
    st.balloons() # 축하 풍선 표시
    
    # 시도 횟수에 따른 등급 결정
    attempts = st.session_state.attempts
    if attempts <= 5:
        grade = "🏆 완벽합니다!"
        color = "green"
    elif attempts <= 10:
        grade = "⭐ 훌륭합니다!"
        color = "blue"
    elif attempts <= 15:
        grade = "👍 좋습니다!"
        color = "orange"
    else:
        grade = "📚 계속 도전하세요!"
        color = "red"
    
    # 결과 표시
    st.success(f"정답입니다! 정답은 {st.session_state.secret_number}입니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("시도 횟수", f"{attempts}회")
    with col2:
        st.info(grade)
    
    if st.button("새 게임 시작"):
        initialize_game() # 게임 초기화
        st.rerun() # 화면을 다시 그려 새 게임 시작

# --- 3. 힌트 (디버깅용, 실제 게임에서는 숨기거나 삭제) ---
# st.sidebar.write(f"힌트: 비밀 숫자 = {st.session_state.secret_number}")

# 배너 추가
st.markdown("""
<div style='text-align: center; margin: 20px 0;'>
    <a href="https://link.coupang.com/a/dP9eTe" target="_blank" referrerpolicy="unsafe-url"><img src="https://ads-partners.coupang.com/banners/966772?subId=&traceId=V0-301-879dd1202e5c73b2-I966772&w=320&h=50" alt=""></a>
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