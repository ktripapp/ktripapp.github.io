import streamlit as st
import random
import pandas as pd
import re

# --- 1. MBTI 데이터 및 질문 ---
MBTI_QUESTIONS = [
    # 라운드 1: E/I (외향성/내향성) - 15개 질문
    [
        {"question": "주말에 무엇을 하고 싶은가?", "E": "친구들과 활동적으로 시간을 보내기", "I": "혼자 조용히 휴식 취하기"},
        {"question": "새로운 사람을 만날 때 기분은?", "E": "설렘과 흥미로움", "I": "긴장하고 신중함"},
        {"question": "에너지를 어디서 얻는가?", "E": "사람과의 상호작용에서", "I": "혼자 있을 때"},
        {"question": "파티에서의 당신은?", "E": "많은 사람과 얘기하며 돌아다님", "I": "한두 사람과 깊은 대화"},
        {"question": "스트레스 해소 방법은?", "E": "외출해서 활동하기", "I": "집에서 휴식하기"},
        {"question": "휴일에 주로 무엇을 하는가?", "E": "외출해서 사람을 만남", "I": "집에서 여유 있게 지냄"},
        {"question": "그룹 활동에서 당신은?", "E": "주도적으로 나서서 리드함", "I": "필요할 때만 참여함"},
        {"question": "전화 통화를 좋아하는가?", "E": "다양한 사람들과 자주 통화함", "I": "필요한 경우에만 함"},
        {"question": "새로운 취미를 시작할 때는?", "E": "단체 활동으로 배우고 싶음", "I": "혼자 천천히 배우고 싶음"},
        {"question": "회사 행사에서의 당신은?", "E": "여러 사람과 네트워킹함", "I": "편한 사람들과만 어울림"},
        {"question": "낯선 활동에 참여할 때의 태도는?", "E": "직접 뛰어들어 경험해보는 편", "I": "먼저 관찰하고 판단함"},
        {"question": "회의 중 의견 제시 방식은?", "E": "즉석에서 활발히 말함", "I": "생각을 정리한 후 말함"},
        {"question": "혼자 있는 시간을 어떻게 쓰는가?", "E": "충전의 시간이 아닌 계획 세우는 시간", "I": "에너지를 회복하는 시간"},
        {"question": "사교 모임 초대가 왔을 때?", "E": "기분 좋게 참석함", "I": "가끔은 거절하고 싶음"},
        {"question": "작업할 때 집중 방식은?", "E": "주변 사람과 함께 있을 때 더 집중", "I": "조용한 환경에서 집중"}
    ],
    # 라운드 2: S/N (감각/직관) - 15개 질문
    [
        {"question": "결정할 때 중요한 것은?", "S": "구체적인 사실과 경험", "N": "가능성과 미래 비전"},
        {"question": "선호하는 일의 방식은?", "S": "검증된 방법으로 차근차근", "N": "창의적이고 새로운 방법으로"},
        {"question": "일을 배울 때 선호하는 방식은?", "S": "실무적이고 체계적으로", "N": "큰 그림을 먼저 이해하기"},
        {"question": "당신의 강점은?", "S": "세부사항 포착 및 실행력", "N": "패턴 인식 및 창의력"},
        {"question": "미래를 생각할 때는?", "S": "현실 기반으로", "N": "가능성 기반으로"},
        {"question": "새로운 프로젝트를 시작할 때는?", "S": "명확한 계획과 절차부터", "N": "전체적인 비전부터"},
        {"question": "문제 해결 방식은?", "S": "과거 경험과 사례로", "N": "새로운 이론과 가설로"},
        {"question": "독서할 때 선호하는 책은?", "S": "실용적이고 구체적인 책", "N": "철학적이고 추상적인 책"},
        {"question": "일상적인 작은 것들에 대해?", "S": "중요하고 주목할 가치 있음", "N": "흥미롭지만 큰 그림의 일부일 뿐"},
        {"question": "변화에 대한 태도는?", "S": "현재 상황을 개선하고 싶음", "N": "완전히 새로운 것을 시도하고 싶음"},
        {"question": "상세한 계획과 아이디어 중 무엇이 더 끌리는가?", "S": "구체적인 실행 계획", "N": "독창적인 아이디어와 컨셉"},
        {"question": "직장에서의 문제 해결은?", "S": "실용적 해결책을 찾음", "N": "근본 원인과 패턴을 분석함"},
        {"question": "사물을 볼 때 무엇에 더 주목하는가?", "S": "현재 상태의 사실들", "N": "가능성과 연결"},
        {"question": "계약서나 규정 보는 것을 선호하나?", "S": "자세히 읽어 확인하는 편", "N": "큰 틀을 이해하는 편"},
        {"question": "새로운 아이디어을 평가할 때?", "S": "실현 가능성 우선", "N": "창의성과 잠재력 우선"}
    ],
    # 라운드 3: T/F (사고/감정) - 15개 질문
    [
        {"question": "결정할 때 중시하는 것은?", "T": "논리와 객관적 분석", "F": "개인의 감정과 가치관"},
        {"question": "갈등 상황에서는?", "T": "문제를 논리적으로 해결", "F": "관계와 감정을 우선 고려"},
        {"question": "타인의 실수에 대해?", "T": "객관적으로 지적하고 개선", "F": "상황을 이해하고 위로"},
        {"question": "당신의 강점은?", "T": "분석력과 객관적 판단", "F": "공감능력과 따뜻함"},
        {"question": "중요한 것은?", "T": "효율성과 성과", "F": "조화와 사람과의 관계"},
        {"question": "비판을 받을 때는?", "T": "내용의 타당성을 검토함", "F": "상대의 의도를 고민함"},
        {"question": "업무에서 우선순위는?", "T": "결과와 성과", "F": "팀의 화합과 만족도"},
        {"question": "남의 고민을 들을 때는?", "T": "해결책을 제시하고 싶음", "F": "공감하고 위로하고 싶음"},
        {"question": "칭찬받을 때 기분은?", "T": "능력을 인정받아 뿌듯함", "F": "소중한 사람이 되어 감동함"},
        {"question": "직장에서 중요한 것은?", "T": "공정하고 명확한 규칙", "F": "따뜻한 인간관계"},
        {"question": "의사결정에서 사실과 감정을 어떻게 균형을 잡나?", "T": "사실을 우선시함", "F": "상대의 감정을 우선시함"},
        {"question": "프로젝트 평가 시 무엇을 더 보나?", "T": "성과와 수치", "F": "팀 분위기와 참여도"},
        {"question": "갈등 해결 시 당신의 첫 행동은?", "T": "문제 원인 분석", "F": "감정 정리와 공감"},
        {"question": "타인의 실수에 대해 공개적으로 말하는가?", "T": "개선의 목적으로 지적함", "F": "사생활을 존중함"},
        {"question": "팀에서 맡고 싶은 역할은?", "T": "분석과 계획 담당", "F": "조정과 사람 관리 담당"}
    ],
    # 라운드 4: J/P (판단/인식) - 15개 질문
    [
        {"question": "계획을 세울 때 당신은?", "J": "상세하게 미리 계획함", "P": "자유롭게 유동적으로"},
        {"question": "마감일이 있을 때는?", "J": "미리 완료하려 함", "P": "마지막에 빨리 하는 편"},
        {"question": "삶의 방식은?", "J": "구조화되고 조직적", "P": "자유롭고 개방적"},
        {"question": "선호하는 환경은?", "J": "명확한 목표와 규칙", "P": "선택의 폭과 유연성"},
        {"question": "당신의 강점은?", "J": "계획성과 책임감", "P": "적응력과 유연성"},
        {"question": "변경 사항이 생기면?", "J": "불안감을 느낌", "P": "새로운 기회로 봄"},
        {"question": "집 정리 상태는?", "J": "깔끔하고 체계적임", "P": "편하면 되는 스타일"},
        {"question": "업무 스타일은?", "J": "일정에 맞춰 진행", "P": "상황에 따라 유동적"},
        {"question": "결정을 내릴 때는?", "J": "신중하게 결정 후 실행", "P": "여러 옵션을 두고 유지"},
        {"question": "시간 약속에 대해?", "J": "정확히 지키려고 함", "P": "약간의 여유를 봄"},
        {"question": "일정을 변경해야 할 때 반응은?", "J": "불편하지만 조정함", "P": "새로운 기회로 받아들임"},
        {"question": "여행 계획을 세울 때 당신은?", "J": "일정을 꼼꼼히 짬", "P": "현장에서 즉흥적으로 결정"},
        {"question": "업무 마감 방식은?", "J": "체계적으로 단계별 완료", "P": "유동적으로 처리하면서 조정"},
        {"question": "장기 프로젝트를 다룰 때?", "J": "체계적 계획 수립", "P": "상황에 맞춰 유연하게 진행"},
        {"question": "예상치 못한 상황에서의 행동은?", "J": "빠르게 재계획함", "P": "상황을 보며 천천히 대처함"}
    ]
]

# MBTI별 어울리는 MBTI와 추천 동물과 음식 (성별 구분)
MBTI_INFO = {
    "ISTJ": {"compatible": "ISFP, INFP", "male_animals": [{"name": "강아지 (Dog)", "image": "https://via.placeholder.com/180?text=Dog", "description": "충성스럽고 친근한 성향을 가진 동물입니다."}], "female_animals": [{"name": "고양이 (Cat)", "image": "https://via.placeholder.com/180?text=Cat", "description": "독립적이고 호기심 많은 성격을 지녔습니다."}], "foods": [{"name":"된장찌개","image":"https://via.placeholder.com/180?text=Doenjang","description":"따뜻하고 든든한 집밥 스타일"},{"name":"김치찌개","image":"https://via.placeholder.com/180?text=KimchiStew","description":"얼큰하고 푸근한 한 그릇"}]},
    "ISFJ": {"compatible": "ISFP, INFP", "male_animals": [{"name": "토끼 (Rabbit)", "image": "https://via.placeholder.com/180?text=Rabbit", "description": "온화하고 조용한 특성을 가졌습니다."}], "female_animals": [{"name": "사슴 (Deer)", "image": "https://via.placeholder.com/180?text=Deer", "description": "섬세하고 민감한 성향을 나타냅니다."}], "foods": [{"name":"삼계탕","image":"https://via.placeholder.com/180?text=Samgyetang","description":"정성스럽고 건강한 한 그릇"},{"name":"갈비탕","image":"https://via.placeholder.com/180?text=Galbitang","description":"깊고 진한 고기국물의 한 끼"}]},
    "INFJ": {"compatible": "ENFP, ENFJ", "male_animals": [{"name": "거북이 (Turtle)", "image": "https://via.placeholder.com/180?text=Turtle", "description": "차분하고 꾸준한 면모를 상징합니다."}], "female_animals": [{"name": "햄스터 (Hamster)", "image": "https://via.placeholder.com/180?text=Hamster", "description": "작고 귀여우며 호기심 많은 성향입니다."}], "foods": [{"name":"리조또","image":"https://via.placeholder.com/180?text=Risotto","description":"부드럽고 고소한 크리미 리조또"},{"name":"미역국","image":"https://via.placeholder.com/180?text=Miyeokguk","description":"담백하고 건강한 국물"}]},
    "INTJ": {"compatible": "ENFP, INTP", "male_animals": [{"name": "부엉이 (Owl)", "image": "https://via.placeholder.com/180?text=Owl", "description": "지혜롭고 사려 깊은 이미지입니다."}], "female_animals": [{"name": "여우 (Fox)", "image": "https://via.placeholder.com/180?text=Fox", "description": "영리하고 재치있는 성향을 갖습니다."}], "foods": [{"name":"한우 구이","image":"https://via.placeholder.com/180?text=KoreanBeef","description":"깊고 고급스러운 소고기 맛"},{"name":"미소라멘","image":"https://via.placeholder.com/180?text=MisoRamen","description":"담백하고 깊은 풍미의 미소 라멘"}]},
    "ISTP": {"compatible": "ESFJ, ISFJ", "male_animals": [{"name": "독수리 (Eagle)", "image": "https://via.placeholder.com/180?text=Eagle", "description": "결단력 있고 관찰력이 뛰어난 동물입니다."}], "female_animals": [{"name": "늑대 (Wolf)", "image": "https://via.placeholder.com/180?text=Wolf", "description": "강한 리더십과 협력성을 상징합니다."}], "foods": [{"name":"바베큐","image":"https://via.placeholder.com/180?text=BBQ","description":"활동적이고 실감나는 식사"},{"name":"순대","image":"https://via.placeholder.com/180?text=Sundae","description":"즉석에서 즐기는 한국식 순대"}]},
    "ISFP": {"compatible": "ISTJ, ISFJ", "male_animals": [{"name": "말 (Horse)", "image": "https://via.placeholder.com/180?text=Horse", "description": "자유롭고 활발한 에너지를 나타냅니다."}], "female_animals": [{"name": "매 (Hawk)", "image": "https://via.placeholder.com/180?text=Hawk", "description": "민첩하고 집중력이 높은 특성입니다."}], "foods": [{"name":"크림 파스타","image":"https://via.placeholder.com/180?text=CreamPasta","description":"부드럽고 풍부한 소스의"},{"name":"비빔밥","image":"https://via.placeholder.com/180?text=Bibimbap","description":"다채로운 재료가 어우러진 한국의 대표 한그릇"}]},
    "INFP": {"compatible": "ENTJ, ENFJ", "male_animals": [{"name": "펭귄 (Penguin)", "image": "https://via.placeholder.com/180?text=Penguin", "description": "친근하고 사교적인 이미지를 가집니다."}], "female_animals": [{"name": "사자 (Lion)", "image": "https://via.placeholder.com/180?text=Lion", "description": "용감하고 자신감 있는 성향을 상징합니다."}], "foods": [{"name":"마카롱","image":"https://via.placeholder.com/180?text=Macaron","description":"다채로운 맛의 프랑스식 디저트"},{"name":"초밥","image":"https://via.placeholder.com/180?text=Sushi","description":"신선한 생선과 밥이 조화로운"}]},
    "INTP": {"compatible": "ENFP, ENTJ", "male_animals": [{"name": "돌고래 (Dolphin)", "image": "https://via.placeholder.com/180?text=Dolphin", "description": "지능적이고 유쾌한 성향을 보입니다."}], "female_animals": [{"name": "원숭이 (Monkey)", "image": "https://via.placeholder.com/180?text=Monkey", "description": "호기심이 많고 창의적인 특성입니다."}], "foods": [{"name":"수제버거","image":"https://via.placeholder.com/180?text=Burger","description":"다채로운 토핑을 즐기는"},{"name":"라면","image":"https://via.placeholder.com/180?text=Ramen","description":"진한 국물과 쫄깃한 면발"}]},
    "ESTP": {"compatible": "ISFJ, ISTJ", "male_animals": [{"name": "코끼리 (Elephant)", "image": "https://via.placeholder.com/180?text=Elephant", "description": "책임감이 강하고 무게감 있는 이미지입니다."}], "female_animals": [{"name": "곰 (Bear)", "image": "https://via.placeholder.com/180?text=Bear", "description": "강인함과 안정감을 상징합니다."}], "foods": [{"name":"피자","image":"https://via.placeholder.com/180?text=Pizza","description":"즉흥적이고 활기찬 맛이 있는"},{"name":"불고기","image":"https://via.placeholder.com/180?text=Bulgogi","description":"달콤하고 풍미 있는 한국식 불고기"}]},
    "ESFP": {"compatible": "ISFJ, ISTJ", "male_animals": [{"name": "다람쥐 (Squirrel)", "image": "https://via.placeholder.com/180?text=Squirrel", "description": "활발하고 민첩한 성격을 닮았습니다."}], "female_animals": [{"name": "코알라 (Koala)", "image": "https://via.placeholder.com/180?text=Koala", "description": "느긋하고 안정적인 이미지를 줍니다."}], "foods": [{"name":"디저트 뷔페","image":"https://via.placeholder.com/180?text=DessertBuffet","description":"다양한 맛을 즐기기 좋은"},{"name":"삼겹살","image":"https://via.placeholder.com/180?text=PorkBelly","description":"구워서 나눠먹기 좋은 인기 메뉴"}]},
    "ENFP": {"compatible": "INTJ, INFJ", "male_animals": [{"name": "얼룩말 (Zebra)", "image": "https://via.placeholder.com/180?text=Zebra", "description": "개성 있고 사회적인 특성이 있습니다."}], "female_animals": [{"name": "기린 (Giraffe)", "image": "https://via.placeholder.com/180?text=Giraffe", "description": "우아하고 넓은 시야를 상징합니다."}], "foods": [{"name":"타이 그린 카레","image":"https://via.placeholder.com/180?text=GreenCurry","description":"향신료가 조화로운 동남아식 커리"},{"name":"초밥","image":"https://via.placeholder.com/180?text=Sushi","description":"신선한 생선과 밥이 조화로운"}]},
    "ENTP": {"compatible": "INFJ, INTJ", "male_animals": [{"name": "고래 (Whale)", "image": "https://via.placeholder.com/180?text=Whale", "description": "온화하고 깊이 있는 성향을 나타냅니다."}], "female_animals": [{"name": "문어 (Octopus)", "image": "https://via.placeholder.com/180?text=Octopus", "description": "유연하고 문제 해결 능력이 뛰어납니다."}], "foods": [{"name":"불고기 타코","image":"https://via.placeholder.com/180?text=BulgogiTaco","description":"한국식 불고기와 멕시코식 조합"},{"name":"김치볶음밥","image":"https://via.placeholder.com/180?text=KimchiFriedRice","description":"풍미 있는 김치와 밥이 조화로운"}]},
    "ESTJ": {"compatible": "ISFP, ISTP", "male_animals": [{"name": "물개 (Seal)", "image": "https://via.placeholder.com/180?text=Seal", "description": "적응력이 좋고 장난기 있는 성격입니다."}], "female_animals": [{"name": "너구리 (Raccoon)", "image": "https://via.placeholder.com/180?text=Raccoon", "description": "영리하고 호기심 많은 특성이 있습니다."}], "foods": [{"name":"김치전","image":"https://via.placeholder.com/180?text=KimchiJeon","description":"바삭하고 매콤한 맛이 있는"},{"name":"된장국","image":"https://via.placeholder.com/180?text=Doenjang","description":"온화하고 익숙한 맛"}]},
    "ESFJ": {"compatible": "ISFP, ISTP", "male_animals": [{"name": "호저 (Porcupine)", "image": "https://via.placeholder.com/180?text=Porcupine", "description": "자기 보호적이고 독립적인 면이 있습니다."}], "female_animals": [{"name": "고슴도치 (Hedgehog)", "image": "https://via.placeholder.com/180?text=Hedgehog", "description": "조심스럽고 친근한 이미지를 줍니다."}], "foods": [{"name":"제육볶음","image":"https://via.placeholder.com/180?text=JeyukSet","description":"정이 느껴지는 반찬 구성"},{"name":"순두부찌개","image":"https://via.placeholder.com/180?text=Sundubu","description":"부드럽고 얼큰한 순두부찌개"}]},
    "ENFJ": {"compatible": "INFP, ISFP", "male_animals": [{"name": "앵무새 (Parrot)", "image": "https://via.placeholder.com/180?text=Parrot", "description": "표현력이 풍부하고 사교적인 성향입니다."}], "female_animals": [{"name": "공작 (Peacock)", "image": "https://via.placeholder.com/180?text=Peacock", "description": "화려하고 자신감 있는 이미지를 가집니다."}], "foods": [{"name":"브런치 플래터","image":"https://via.placeholder.com/180?text=BrunchPlatter","description":"사교적이고 즐거운 경험을 선사하는"},{"name":"아보카도 토스트","image":"https://via.placeholder.com/180?text=AvocadoToast","description":"균형잡힌 세련된 맛"}]},
    "ENTJ": {"compatible": "ISFP, INFP", "male_animals": [{"name": "백조 (Swan)", "image": "https://via.placeholder.com/180?text=Swan", "description": "우아하고 품위 있는 성격을 상징합니다."}], "female_animals": [{"name": "매 (Falcon)", "image": "https://via.placeholder.com/180?text=Falcon", "description": "빠르고 정확한 판단력을 지녔습니다."}], "foods": [{"name":"트러플 리조또","image":"https://via.placeholder.com/180?text=TruffleRisotto","description":"풍미가 깊고 우아한 맛이 있는"},{"name":"돈까스","image":"https://via.placeholder.com/180?text=Donkatsu","description":"겉은 바삭하고 속은 촉촉한 돈까스"}]}
}

# Normalize any literal placeholder image URLs in MBTI_INFO to the repository raw URLs
def _normalize_mbti_info_images():
    prefix = 'https://via.placeholder.com/180?text='
    # Use raw.githubusercontent so images are directly accessible
    new_prefix = 'https://raw.githubusercontent.com/ktripapp/image/main/'

    def _has_image_ext(s: str) -> bool:
        return any(s.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'))

    def _replace(obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if k == 'image' and isinstance(v, str) and v.startswith(prefix):
                    new_url = v.replace(prefix, new_prefix)
                    if not _has_image_ext(new_url):
                        new_url = new_url + '.png'
                    obj[k] = new_url
                else:
                    _replace(v)
        elif isinstance(obj, list):
            for item in obj:
                _replace(item)

    _replace(MBTI_INFO)

# run normalization once at import/load time
_normalize_mbti_info_images()

# --- 2. 게임 초기화 및 상태 관리 ---
if 'gender' not in st.session_state:
    st.session_state.gender = None
    st.session_state.round_index = 0
    st.session_state.question_index = 0
    st.session_state.mbti_scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    st.session_state.result_mbti = None
    st.session_state.game_over = False

# --- 3. 게임 로직 함수 ---
def calculate_mbti():
    E_I = "E" if st.session_state.mbti_scores["E"] > st.session_state.mbti_scores["I"] else "I"
    S_N = "S" if st.session_state.mbti_scores["S"] > st.session_state.mbti_scores["N"] else "N"
    T_F = "T" if st.session_state.mbti_scores["T"] > st.session_state.mbti_scores["F"] else "F"
    J_P = "J" if st.session_state.mbti_scores["J"] > st.session_state.mbti_scores["P"] else "P"
    
    st.session_state.result_mbti = E_I + S_N + T_F + J_P
    st.session_state.game_over = True

def _korean_subject_particle(text: str) -> str:
    """텍스트 끝 글자에 따라 한국어 주격조사 '이' 또는 '가'를 반환합니다.
    비한글 문자는 기본으로 '가'를 반환합니다.
    """
    if not text:
        return '이'
    s = text.strip()
    # 끝 문장부호 제거
    while s and s[-1] in '.?!,。、 ':
        s = s[:-1].strip()
    if not s:
        return '이'
    last = s[-1]
    code = ord(last)
    # 한글 음절 범위
    if 0xAC00 <= code <= 0xD7A3:
        jong = (code - 0xAC00) % 28
        return '이' if jong != 0 else '가'
    # 기본: 모음으로 끝나는 외래어 등은 '가'
    return '가'

def select_answer(mbti_type):
    if mbti_type == "E":
        st.session_state.mbti_scores["E"] += 1
    elif mbti_type == "I":
        st.session_state.mbti_scores["I"] += 1
    elif mbti_type == "S":
        st.session_state.mbti_scores["S"] += 1
    elif mbti_type == "N":
        st.session_state.mbti_scores["N"] += 1
    elif mbti_type == "T":
        st.session_state.mbti_scores["T"] += 1
    elif mbti_type == "F":
        st.session_state.mbti_scores["F"] += 1
    elif mbti_type == "J":
        st.session_state.mbti_scores["J"] += 1
    elif mbti_type == "P":
        st.session_state.mbti_scores["P"] += 1
    
    st.session_state.question_index += 1

    if st.session_state.question_index >= 5:
        st.session_state.question_index = 0
        st.session_state.round_index += 1

        if st.session_state.round_index >= 4:
            calculate_mbti()
    
    st.rerun()

def reset_game():
    st.session_state.gender = None
    st.session_state.round_index = 0
    st.session_state.question_index = 0
    st.session_state.mbti_scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    st.session_state.result_mbti = None
    st.session_state.game_over = False
    st.session_state.selected_questions = None
    st.rerun()

def initialize_selected_questions():
    """각 라운드별로 15개 문항 중 랜덤으로 5개를 선택하여 라운드의 문제로 사용"""
    if "selected_questions" not in st.session_state or st.session_state.selected_questions is None:
        st.session_state.selected_questions = []
        for round_idx in range(4):
            # 각 라운드의 15개 질문 중 5개를 랜덤 선택
            selected = random.sample(MBTI_QUESTIONS[round_idx], 5)
            st.session_state.selected_questions.append(selected)

# --- 4. 게임 화면 구성 ---
st.title("💫 MBTI 게임")

# 성별 선택 화면
if st.session_state.gender is None:
    st.write("먼저 성별을 선택해주세요!")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👨 남성", use_container_width=True, key="male"):
            st.session_state.gender = "male"
            st.rerun()
    
    with col2:
        if st.button("👩 여성", use_container_width=True, key="female"):
            st.session_state.gender = "female"
            st.rerun()

# 게임 진행 중
elif not st.session_state.game_over:
    # 선택된 질문 초기화
    initialize_selected_questions()
    
    # 진행도 표시
    current_question = st.session_state.question_index + 1
    current_round = st.session_state.round_index + 1
    st.progress((st.session_state.round_index * 5 + st.session_state.question_index) / 20)
    st.write(f"🎯 {current_round}번째 라운드 - {current_question}/5 질문")
    
    # 현재 질문 표시
    current_q = st.session_state.selected_questions[st.session_state.round_index][st.session_state.question_index]
    st.subheader(current_q["question"])
    
    # 라운드별 선택지 표시
    round_types = [["E", "I"], ["S", "N"], ["T", "F"], ["J", "P"]]
    type_a, type_b = round_types[st.session_state.round_index]

    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"← {current_q[type_a]}", use_container_width=True, key="answer_a"):
            select_answer(type_a)
    
    with col2:
        if st.button(f"→ {current_q[type_b]}", use_container_width=True, key="answer_b"):
            select_answer(type_b)

# 결과 화면
else:
    st.balloons()
    mbti_result = st.session_state.result_mbti
    mbti_data = MBTI_INFO[mbti_result]
    
    # MBTI 설명
    st.write("### 🧠 당신의 MBTI 유형 설명")
    
    # MBTI 결과와 설명을 한 번에 표시
    phrases = {
        "E": "외향적이고 활동적인",
        "I": "내향적이고 신중한",
        "S": "현실적이고 구체적인",
        "N": "직관적이고 창의적인",
        "T": "논리적이고 객관적인",
        "F": "감정적이고 따뜻한",
        "J": "계획적이고 조직적인",
        "P": "유연하고 개방적인"
    }

    emoji_map = {"E": "🗣️", "I": "🤫", "S": "🔎", "N": "✨", "T": "🧠", "F": "💖", "J": "📅", "P": "🎈"}

    # MBTI 설명을 한 문장으로 합쳐서 표시
    a, b, c, d = mbti_result[0], mbti_result[1], mbti_result[2], mbti_result[3]
    ea, eb, ec, ed = emoji_map.get(a, ''), emoji_map.get(b, ''), emoji_map.get(c, ''), emoji_map.get(d, '')
    # 자연스러운 한 문장으로 조합 — 문장 앞뒤에 하트 이모지 추가
    sentence = (
        f"당신은 {phrases[a]}이자 {phrases[b]} 성향을 동시에 지니고, "
        f"{phrases[c]}이면서 {phrases[d]} 기질을 보여 상황에 따라 잘 적응하는 편이에요."
    )
    desc_html = f"💖 {sentence} 💖"
    comp_html = f"<div style='margin-top:12px;font-size:16px;color:#073b2b;'>💑 당신과 어울리는 MBTI는 <strong>{mbti_data.get('compatible','')}</strong>예요.</div>"
    st.markdown(
        (
            f"<div style='background:#e9f7ef;padding:16px;border-radius:10px;'>"
            f"<div style='font-size:22px;font-weight:700;color:#114b22;'>당신의 MBTI는 "
            f"<span style='font-size:28px;color:#0b3b1f;'>{mbti_result}</span> 입니다! 🎉</div>"
            f"<div style='margin-top:10px;font-size:16px;color:#0b2b18;'>{desc_html}</div>"
            f"{comp_html}"
            f"</div>"
        ),
        unsafe_allow_html=True,
    )

    # MBTI에 따라 어울리는 동물 하나만 표시
    animals = []
    animals.extend(mbti_data.get('male_animals', []))
    animals.extend(mbti_data.get('female_animals', []))
    # 한 가지만 보여주기 (첫 항목 사용)
    animals = animals[:1]
    animal_label = "🐾 추천 동물"

    col1, col2 = st.columns(2)

    # 왼쪽 열: 추천 동물 (첫 항목)
    with col1:
        st.subheader(f"{animal_label}")
        if animals:
            animal = animals[0]
            img_url = animal.get('image', '')
            if isinstance(img_url, str) and img_url.startswith('https://via.placeholder.com/180?text='):
                img_url = img_url.replace('https://via.placeholder.com/180?text=', 'https://raw.githubusercontent.com/ktripapp/image/main/')
                if not any(img_url.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                    img_url += '.png'
            if not img_url:
                img_url = 'https://raw.githubusercontent.com/ktripapp/image/main/Food.png'
            st.image(img_url, caption=animal['name'], use_container_width=True)
            # 동물 이모지 결정
            name_kr = animal['name'].split(' (')[0]
            name_l = name_kr.lower()
            animal_emoji = '🐾'
            if any(k in name_l for k in ('강아지','개','dog')):
                animal_emoji = '🐶'
            elif any(k in name_l for k in ('고양이','cat')):
                animal_emoji = '🐱'
            elif any(k in name_l for k in ('토끼','rabbit')):
                animal_emoji = '🐰'
            elif '펭귄' in name_l:
                animal_emoji = '🐧'
            elif any(k in name_l for k in ('사자','lion')):
                animal_emoji = '🦁'
            elif any(k in name_l for k in ('거북','turtle')):
                animal_emoji = '🐢'
            elif any(k in name_l for k in ('부엉','올빼미','owl')):
                animal_emoji = '🦉'
            elif '여우' in name_l:
                animal_emoji = '🦊'
            elif any(k in name_l for k in ('돌고래','dolphin')):
                animal_emoji = '🐬'
            elif any(k in name_l for k in ('원숭이','monkey')):
                animal_emoji = '🐒'
            elif any(k in name_l for k in ('독수리','eagle')):
                animal_emoji = '🦅'
            elif '늑대' in name_l:
                animal_emoji = '🐺'
            elif '코끼리' in name_l:
                animal_emoji = '🐘'
            elif '곰' in name_l:
                animal_emoji = '🐻'
            elif any(k in name_l for k in ('다람쥐','squirrel')):
                animal_emoji = '🐿️'
            elif '코알라' in name_l:
                animal_emoji = '🐨'
            elif '얼룩말' in name_l:
                animal_emoji = '🦓'
            elif '기린' in name_l:
                animal_emoji = '🦒'
            elif '고래' in name_l:
                animal_emoji = '🐋'
            elif '문어' in name_l:
                animal_emoji = '🐙'
            elif '물개' in name_l:
                animal_emoji = '🦭'
            elif any(k in name_l for k in ('너구리','raccoon')):
                animal_emoji = '🦝'
            elif any(k in name_l for k in ('고슴도치','호저','hedgehog')):
                animal_emoji = '🦔'
            elif any(k in name_l for k in ('앵무','parrot')):
                animal_emoji = '🦜'
            elif '공작' in name_l:
                animal_emoji = '🦚'
            elif '백조' in name_l:
                animal_emoji = '🦢'
            elif any(k in name_l for k in ('말','horse')):
                animal_emoji = '🐎'
            # 캡션 문구 처리
            if 'description' in animal:
                desc_raw = animal['description'].strip().rstrip('.')
                # 문장형 어미를 제거하여 서술형 -> 관형형으로 변환하려는 간단한 후처리
                desc_core = re.sub(r'(입니다|습니다|있습니다|가집니다|지녔습니다|지니고 있습니다)$', '', desc_raw).strip()
                # 끝에 '동물' 단어가 있으면 중복되니 제거
                desc_core = re.sub(r'동물$', '', desc_core).strip()
                # 추가 정리: '이미지', '성향', '성격' 등 명사형 래퍼나 목적격 조사(을/를) 제거
                desc_core = re.sub(r'(이미지(를|인)?|성향(을|이)?|특성(을|이)?|성격(을|이)?|특징(을|이)?)$', '', desc_core).strip()
                desc_core = re.sub(r'(을|를|의|로|으로|에게|에|에서)$', '', desc_core).strip()
                # 공백 정리
                desc_core = re.sub(r'\s+', ' ', desc_core).strip()
                # 'X을 가진' 형태를 'X이 있는'으로 변환하여 관형형 처리
                desc_core = re.sub(r'(.+?)을\s*가진인$', r"\1이 있는", desc_core)
                desc_core = re.sub(r'(.+?)을\s*가진$', r"\1이 있는", desc_core)
                desc_core = re.sub(r'성향을\s*가진', '성향이 있는', desc_core)
                # 특정 어색한 중복 어미 정리: '가진인' -> '가진', '가졌인' -> '가진'
                desc_core = re.sub(r'가졌?인$', '가진', desc_core)
                # '뛰어난인' -> '뛰어난'
                desc_core = re.sub(r'뛰어난인$', '뛰어난', desc_core)
                # '닮았인' -> '닮은'
                desc_core = re.sub(r'닮았인$', '닮은', desc_core)
                # 서술형 표현을 자연스러운 관형형으로 변환
                desc_core = re.sub(r'상징합니다인$|상징합니다$', '상징하고 있는', desc_core)
                desc_core = re.sub(r'나타냅니다인$|나타냅니다$', '나타내고 있는', desc_core)
                desc_core = re.sub(r'나타냅니다인은$|나타냅니다인$', '나타내고 있는', desc_core)
                desc_core = re.sub(r'보입니다인$|보입니다$|보인인$|보인$', '보이는', desc_core)
                # '면이' 형태는 '성향이 있는'으로 정리
                desc_core = re.sub(r'면이인$|면이$', '성향이 있는', desc_core)
                # 중복 '인' 제거 (예: '성향이 있는인' -> '성향이 있는')
                desc_core = re.sub(r'(성향이 있는)인$', r'\1', desc_core)
                particle = _korean_subject_particle(name_kr)
                if desc_core:
                    # desc_core가 이미 관형형(예: '친근한', '사교적인', '있는' 등)인 경우 '인'을 추가하지 않음
                    if re.search(r"(인|은|한|있는|적인|스러운|적|는|가진|지닌|보이는|나타내는)$", desc_core):
                        st.caption(f"{desc_core} {name_kr}{particle} 당신과 어울려요. {animal_emoji}")
                    else:
                        st.caption(f"{desc_core}인 {name_kr}{particle} 당신과 어울려요. {animal_emoji}")
                else:
                    st.caption(f"{name_kr}{particle} 당신과 어울려요. {animal_emoji}")
            else:
                particle = _korean_subject_particle(name_kr)
                st.caption(f"{name_kr}{particle} 당신과 어울려요. {animal_emoji}")

    # 오른쪽 열: 추천 음식 (첫 항목)
    with col2:
        st.subheader("🍽️ 추천 음식")
        foods = mbti_data.get('foods', [])[:1]
        if foods:
            f = foods[0]
            img = f.get('image', 'https://raw.githubusercontent.com/ktripapp/image/main/Food.png')
            if isinstance(img, str) and img.startswith('https://via.placeholder.com/180?text='):
                img = img.replace('https://via.placeholder.com/180?text=', 'https://raw.githubusercontent.com/ktripapp/image/main/')
                if not any(img.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                    img += '.png'
            st.image(img, caption=f['name'], use_container_width=True)
            if 'description' in f:
                desc = f['description'].strip().rstrip('.')
                # normalize common descriptor patterns early
                desc = re.sub(r'실험적\s*토핑', '다채로운 토핑', desc)
                desc = re.sub(r'(.+?)\s*의\s*조화', r"\1이 조화로운", desc)
                desc = re.sub(r'즐기기\s*좋음의', '즐기기 좋은', desc)
                desc = re.sub(r'즐기기\s*좋음', '즐기기 좋은', desc)
                desc = re.sub(r'선호의', '선사하는', desc)
                desc = re.sub(r'선호$', '선사하는', desc)
                desc = re.sub(r'선택의$', '맛이 있는', desc)
                desc = re.sub(r'선택$', '맛이 있는', desc)
                desc = re.sub(r'좋음의', '좋은', desc)
                # '간식' 단어는 중복될 수 있으니 제거하여 문장이 자연스럽게 이어지도록 함
                desc_clean = re.sub(r'\b간식\b', '', desc).strip()
                desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
                name_kr = f.get('name', '').split(' (')[0]
                particle = _korean_subject_particle(name_kr)
                name_l = name_kr.lower()
                emoji = '🍽️'
                if any(k in name_l for k in ('한우','한우 구이','한우구이','스테이크','steak')):
                    emoji = '🥩'
                elif any(k in name_l for k in ('피자','pizza')):
                    emoji = '🍕'
                elif any(k in name_l for k in ('초밥','sushi')):
                    emoji = '🍣'
                elif any(k in name_l for k in ('비빔밥','bibimbap')):
                    emoji = '🍚'
                elif any(k in name_l for k in ('삼겹살','돼지','pork','pork belly')):
                    emoji = '🥓'
                elif any(k in name_l for k in ('김치찌개','된장찌개','순두부찌개','갈비탕','미역국','찌개','국','수프','soup')):
                    emoji = '🍲'
                elif any(k in name_l for k in ('짜장','짜장면','짬뽕','마파두부','탕수육','중화','중식')):
                    emoji = '🥡'
                elif any(k in name_l for k in ('라멘','라면','면','noodle')):
                    emoji = '🍜'
                elif any(k in name_l for k in ('리조또','risotto','리조토')):
                    emoji = '🍛'
                elif any(k in name_l for k in ('파스타','pasta','스파게티')):
                    emoji = '🍝'
                elif any(k in name_l for k in ('버거','burger')):
                    emoji = '🍔'
                elif any(k in name_l for k in ('맥주','beer')):
                    emoji = '🍺'
                elif any(k in name_l for k in ('디저트','dessert','베이커리','마카롱')):
                    emoji = '🍰'
                elif any(k in name_l for k in ('과일','fruit','cocktail','과일칵테일')):
                    emoji = '🍓'
                elif any(k in name_l for k in ('샐러드','salad')):
                    emoji = '🥗'
                elif any(k in name_l for k in ('피클','pickles')):
                    emoji = '🥒'
                # 친근 톤으로 일관된 문장 생성
                if desc_clean:
                    # If description already mentions the food name, show as 'name — desc'
                    if re.search(re.escape(name_kr), desc_clean, flags=re.IGNORECASE):
                        pattern = ''.join(re.escape(ch) + r'\s*' for ch in name_kr)
                        desc_no_name = re.sub(pattern, '', desc_clean, flags=re.IGNORECASE).strip()
                        desc_no_name = re.sub(r'\b한\s?그릇\b|\b한\s?끼\b|\b한\s?그릇의\b|\b한\s?끼의\b', '', desc_no_name).strip()
                        desc_no_name = re.sub(r'\s+', ' ', desc_no_name).strip().rstrip('.')
                        desc_no_name = re.sub(r'실험적\s*토핑', '다채로운 토핑', desc_no_name)
                        desc_no_name = re.sub(r'(.+?)\s*의\s*조화$', r"\1이 조화로운", desc_no_name)
                        desc_no_name = re.sub(r'즐기기\s*좋음의$', '즐기기 좋은', desc_no_name)
                        desc_no_name = re.sub(r'즐기기\s*좋음$', '즐기기 좋은', desc_no_name)
                        desc_no_name = re.sub(r'선호의$', '선사하는', desc_no_name)
                        desc_no_name = re.sub(r'선호$', '선사하는', desc_no_name)
                        desc_no_name = re.sub(r'선택의$', '맛이 있는', desc_no_name)
                        desc_no_name = re.sub(r'선택$', '맛이 있는', desc_no_name)
                        desc_no_name = re.sub(r'좋음의', '좋은', desc_no_name)
                        last_word = name_kr.split()[-1]
                        if desc_no_name.endswith(last_word):
                            base = desc_no_name[: -len(last_word)].strip()
                            if base.endswith('의'):
                                desc_no_name = base
                            elif base:
                                desc_no_name = f"{base} 맛=이 있는".replace('=','')
                            else:
                                desc_no_name = ''
                        particle = _korean_subject_particle(name_kr)
                        if desc_no_name:
                            # avoid adding '의' when descriptor already attributive
                            if re.search(r'(조화로운|맛이 있는|즐기기 좋은|선사하는|있는|로운|한|적|스러운|는)$', desc_no_name):
                                st.caption(f"{desc_no_name} {name_kr}{particle} 당신과 어울려요. {emoji}")
                            else:
                                st.caption(f"{desc_no_name}의 {name_kr}{particle} 당신과 어울려요. {emoji}")
                        else:
                            st.caption(f"당신과 잘 어울리는 음식은 {name_kr}이에요. {emoji}")
                    else:
                        # remove name from description to avoid duplication
                        desc_no_name = re.sub(re.escape(name_kr), '', desc_clean, flags=re.IGNORECASE).strip()
                        desc_no_name = re.sub(r'[，,\s]+', ' ', desc_no_name).strip()
                        # If description already contains a genitive/measure phrase, prefer 'name — desc'
                        if '의' in desc_clean or re.search(r'(한\s?그릇|한\s?끼|한\s?그릇의|한\s?끼의)$', desc_clean):
                            desc_proc = re.sub(r'\b한\s?그릇\b|\b한\s?끼\b', '', desc_clean).strip().rstrip('.')
                            particle = _korean_subject_particle(name_kr)
                            st.caption(f"{desc_proc} {name_kr}{particle} 당신과 어울려요. {emoji}")
                        elif desc_no_name:
                            # remove trailing '의' if present
                            desc_no_name = re.sub(r'의$', '', desc_no_name).strip()
                            particle = _korean_subject_particle(name_kr)
                            st.caption(f"{desc_no_name}의 {name_kr}{particle} 당신과 어울려요. {emoji}")
                        else:
                            st.caption(f"당신과 잘 어울리는 음식은 {name_kr}이에요. {emoji}")
                else:
                    st.caption(f"당신과 잘 어울리는 음식은 {name_kr}이에요. {emoji}")
    
    if st.button("다시 하기", use_container_width=True):
        reset_game()

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