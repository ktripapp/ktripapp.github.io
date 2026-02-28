import streamlit as st

# 세션 상태 초기화
if 'show_map' not in st.session_state:
    st.session_state.show_map = True  # 기본적으로 지도 화면 표시

# 지도 기능
if st.session_state.show_map:
    st.markdown("""
    <div style="text-align: center;">
        <iframe 
            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3168.123456789012!2d126.978388!3d37.566610!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca1b2c3d4e5f7%3A0x1234567890abcdef!2z7J207Iuc7J2A!5e0!3m2!1sko!2skr!4v1234567890123"
            width="100%" 
            height="450" 
            style="border:0; max-width: 900px;" 
            allowfullscreen="" 
            loading="lazy">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

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