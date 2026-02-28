import streamlit as st
import random

# --- 1. 게임 초기화 및 상태 관리 ---
BOARD_SIZE = 15

def initialize_omok():
    # 게임판 초기화 및 상태 변수 설정
    st.session_state.board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    st.session_state.current_player = "●"  # 플레이어는 파란 돌(●)
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.game_message = "파란 돌(●)의 차례입니다!"
    # 사용자 설정 기본값 설정
    if 'play_with_computer' not in st.session_state:
        st.session_state.play_with_computer = True
    if 'difficulty' not in st.session_state:
        st.session_state.difficulty = '중급'
    if 'who_starts' not in st.session_state:
        st.session_state.who_starts = '플레이어'

# --- 2. 승리 조건 검사 및 게임 로직 함수 ---
directions = [(0,1), (1,0), (1,1), (1,-1)]

def check_winner_omok(board):
    # 5목 연속 감지
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            stone = board[row][col]
            if stone == " ":
                continue
            for dr, dc in directions:
                count = 1
                r, c = row + dr, col + dc
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == stone:
                    count += 1
                    r += dr
                    c += dc
                r, c = row - dr, col - dc
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == stone:
                    count += 1
                    r -= dr
                    c -= dc
                if count >= 5:
                    return stone
    return None

def get_empty_cells(board):
    # 빈 칸 좌표 리스트 반환
    empties = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == " ":
                empties.append((r,c))
    return empties

def find_winning_move(board, player):
    # 해당 플레이어가 즉시 승리할 수 있는 위치 탐색
    for r, c in get_empty_cells(board):
        board[r][c] = player
        if check_winner_omok(board) == player:
            board[r][c] = " "
            return (r, c)
        board[r][c] = " "
    return None

def score_cell(board, r, c, player):
    # 휴리스틱 점수 계산 함수
    score = 0
    opp = '●' if player == '○' else '○'
    for dr, dc in directions:
        cnt = 0
        # 전방에 연속된 돌 개수 카운트
        rr, cc = r+dr, c+dc
        while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == player:
            cnt += 1
            rr += dr
            cc += dc
        rr, cc = r-dr, c-dc
        while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == player:
            cnt += 1
            rr -= dr
            cc -= dc
        score += (10 ** cnt)
        # 상대방 돌 차단 가능성 점수 추가
        bcnt = 0
        rr, cc = r+dr, c+dc
        while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == opp:
            bcnt += 1
            rr += dr
            cc += dc
        rr, cc = r-dr, c-dc
        while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == opp:
            bcnt += 1
            rr -= dr
            cc -= dc
        score += (5 ** bcnt)
    return score

def computer_move():
    # 컴퓨터 플레이 함수 (난이도에 따른 전략 포함)
    if st.session_state.game_over:
        return
    board = st.session_state.board
    comp = '○'
    player = '●'
    diff = st.session_state.difficulty

    # 1) 즉시 승리 수 찾기
    win = find_winning_move(board, comp)
    if win:
        r, c = win
        board[r][c] = comp
        st.session_state.current_player = player
        return

    # 2) 상대방 즉시 승리 차단
    block = find_winning_move(board, player)
    if block:
        r, c = block
        board[r][c] = comp
        st.session_state.current_player = player
        return

    empties = get_empty_cells(board)
    if not empties:
        return

    # 3) 난이도에 따른 수 선택
    if diff == '초급':
        r, c = random.choice(empties)
        board[r][c] = comp
        st.session_state.current_player = player
        return

    best = None
    best_score = -1
    for (r, c) in empties:
        s = score_cell(board, r, c, comp)
        if diff == '고급':
            s += score_cell(board, r, c, player)
        if s > best_score:
            best_score = s
            best = (r, c)

    if best:
        br, bc = best
        board[br][bc] = comp
    st.session_state.current_player = player

def handle_click_omok(row, col):
    # 사용자가 클릭 시 처리 함수
    if st.session_state.board[row][col] == " " and not st.session_state.game_over:
        st.session_state.board[row][col] = st.session_state.current_player
        winner = check_winner_omok(st.session_state.board)
        if winner:
            st.session_state.winner = winner
            st.session_state.game_over = True
            name = "파란 돌🔵" if winner == '●' else '핑크 돌🌸'
            st.session_state.game_message = f"🎉 {name} 승리! 🎉"
            st.rerun()
            return

        # 상대 차례로 변경
        st.session_state.current_player = '○' if st.session_state.current_player == '●' else '●'
        st.session_state.game_message = "컴퓨터의 차례입니다." if st.session_state.current_player == '○' else "플레이어의 차례입니다."

        # 컴퓨터 턴이면 자동으로 수 두기
        if st.session_state.play_with_computer and st.session_state.current_player == '○':
            computer_move()
            winner = check_winner_omok(st.session_state.board)
            if winner:
                st.session_state.winner = winner
                st.session_state.game_over = True
                name = "파란 돌🔵" if winner == '●' else '핑크 돌🌸'
                st.session_state.game_message = f"🎉 {name} 승리! 🎉"
                st.rerun()
                return
        st.rerun()

def reset_omok_game():
    initialize_omok()
    who = st.session_state.get('who_starts', '플레이어')
    if who == '플레이어':
        st.session_state.current_player = '●'
    elif who == '컴퓨터':
        st.session_state.current_player = '○'
    else:
        st.session_state.current_player = random.choice(['●', '○'])
    # 컴퓨터가 선공이라면 첫 수 둠
    if st.session_state.play_with_computer and st.session_state.current_player == '○':
        computer_move()
    st.rerun()

# --- 3. 세션 상태 초기화 확인 ---
if 'board' not in st.session_state:
    initialize_omok()
    who = st.session_state.get('who_starts', '플레이어')
    if who == '플레이어':
        st.session_state.current_player = '●'
    elif who == '컴퓨터':
        st.session_state.current_player = '○'
    else:
        st.session_state.current_player = random.choice(['●', '○'])
    if st.session_state.play_with_computer and st.session_state.current_player == '○':
        computer_move()

# --- 4. 오목판 UI 스타일 ---
st.markdown("""
<style>
@media (max-width: 768px) {
    :root {
        --board-size: min(15vw, 150px);
        --cell-size: calc(var(--board-size) / 15);
    }

    .main .block-container {
        max-width: 100%;
        margin: 0 auto;
        padding-left: 4px;
        padding-right: 4px;
    }

    .omok-board-wrap {
        width: 100%;
        overflow: hidden;
        -webkit-overflow-scrolling: touch;
    }

    .omok-board {
        width: var(--board-size);
        max-width: var(--board-size);
    }

    .stHorizontalBlock {
        flex-wrap: nowrap !important;
        gap: 0 !important;
        row-gap: 0 !important;
        column-gap: 0 !important;
        width: var(--board-size);
        max-width: var(--board-size);
        margin: 0 !important;
        padding: 0 !important;
    }

    .stHorizontalBlock > div {
        margin: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .omok-board [data-testid="stColumn"] {
        flex: 0 0 var(--cell-size) !important;
        width: var(--cell-size) !important;
        max-width: var(--cell-size) !important;
        min-width: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
    }

    .stColumn {
        padding: 0 !important;
        margin: 0 !important;
    }

    .omok-board .stButton,
    .omok-board .stMarkdown,
    .omok-board .stMarkdown > div,
    .omok-board .stMarkdown > div > div {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 0 !important;
    }

    .omok-board * {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        line-height: 0 !important;
    }

    .omok-board [data-testid="element-container"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    .omok-board button {
        width: var(--cell-size) !important;
        height: var(--cell-size) !important;
        border-radius: 2px !important;
        border-width: 0.5px !important;
    }

    .omok-cell {
        margin: 0 !important;
    }

    .stone {
        width: 45%;
        height: 45%;
    }
}

.omok-cell {
    width: 100%;
    aspect-ratio: 1 / 1;
    background-color: transparent; /* 배경색을 투명하게 만듭니다 */
    border: none;                  /* 테두리를 완전히 제거합니다 */
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0;
}

button {
    width: 100% !important;
    height: auto !important;
    padding: 0 !important;
    min-height: 0 !important;
    aspect-ratio: 1 / 1 !important;
    background-color: transparent; /* 배경색을 투명하게 만듭니다 */
    border: 1px solid #999 !important;
    box-shadow: none !important;
    border-radius: 6px !important;
}

button:hover:not(:disabled) {
    background-color: #a0a0a0 !important;
}

button:disabled {
    opacity: 1 !important;
    cursor: not-allowed !important;
}

[data-testid="stSidebar"] button {
    width: auto !important;
    height: auto !important;
    min-height: unset !important;
    aspect-ratio: auto !important;
    padding: 0.35rem 0.75rem !important;
    border-radius: 6px !important;
}

.stone {
    width: 80%;
    height: 80%;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0;
    padding: 0;
}

.stone.blue {
    background-color: #d6ecff;
    border: 3px solid #0b3b5c;
}

.stone.pink {
    background-color: #ffd6e8;
    border: 3px solid #3b0b1a;
}
</style>
""", unsafe_allow_html=True)
# --- 4. 사이드바 설정 ---
with st.sidebar:
    st.header("설정")
    play = st.checkbox("컴퓨터와 플레이 (1인용)", value=st.session_state.play_with_computer)
    if play != st.session_state.play_with_computer:
        st.session_state.play_with_computer = play
    diff = st.selectbox("난이도", ['초급', '중급', '고급'], index=['초급', '중급', '고급'].index(st.session_state.difficulty))
    st.session_state.difficulty = diff
    who = st.selectbox("선공", ['플레이어', '컴퓨터', '주사위'], index=['플레이어', '컴퓨터', '주사위'].index(st.session_state.who_starts))
    st.session_state.who_starts = who
    if st.button("새 게임", key='new_game'):
        reset_omok_game()

# --- 5. 게임 제목 및 메시지 출력 ---
st.title("🔵 오목 & 빙고 🌸")

if st.session_state.game_over:
    st.header(st.session_state.game_message)
    if st.session_state.winner == '●':
        st.balloons()
else:
    if st.session_state.current_player == '●':
        st.info("🔵 **당신의 차례입니다!** (파란 돌)")
    else:
        st.warning("⏳ **컴퓨터 계산 중...**")

# --- 6. 게임 UI 그리기 ---
st.markdown('<div class="omok-board-wrap"><div class="omok-board">', unsafe_allow_html=True)
for i in range(BOARD_SIZE):
    cols = st.columns(BOARD_SIZE, gap="small")
    for j in range(BOARD_SIZE):
        with cols[j]:
            cell = st.session_state.board[i][j]
            disabled = cell != " " or st.session_state.game_over
            
            if cell == '●':
                st.markdown('<div class="omok-cell"><div class="stone blue"></div></div>', unsafe_allow_html=True)
            elif cell == '○':
                st.markdown('<div class="omok-cell"><div class="stone pink"></div></div>', unsafe_allow_html=True)
            else:
                if st.button("", key=f"cell_{i}_{j}", disabled=disabled, use_container_width=True):
                    handle_click_omok(i, j)
st.markdown('</div></div>', unsafe_allow_html=True)

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