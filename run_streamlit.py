# run_streamlit.py 내용 (예시)
import subprocess
import sys
import os

# Streamlit 앱 파일 경로
streamlit_app_path = os.path.join(os.path.dirname(__file__), "app.py")

# Streamlit 실행 명령어
command = [
    sys.executable, "-m", "streamlit", "run", streamlit_app_path,
    "--server.runOnSave=true"
]

# 서브프로세스로 Streamlit 앱 실행
try:
    subprocess.run(command, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error running Streamlit: {e}")
    sys.exit(1)