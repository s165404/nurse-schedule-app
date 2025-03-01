import streamlit as st
import pandas as pd
import io
import random
import pickle  # 데이터 저장용 라이브러리

# 🔄 우선순위 부여 함수
def assign_priority(nurses):
    for nurse in nurses:
        if not nurse["직원ID"].isdigit():  # 직원ID가 숫자가 아니면 기본값 "9999" 설정
            nurse["직원ID"] = "9999"

    nurses.sort(key=lambda x: int(x["직원ID"]))  # 직원ID 기준으로 정렬
    
    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1  # 정렬된 순서대로 "우선순위" 추가

st.set_page_config(page_title="🏥 간호사 근무표 자동 생성기", layout="wide")

DATA_FILE = "nurse_data.pkl"  # 간호사 정보 저장 파일

# 🔄 데이터 저장 함수 (세션 유지용)
def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(st.session_state.nurses, f)

# 🔄 데이터 불러오기 함수
def load_data():
    try:
        with open(DATA_FILE, "rb") as f:
            st.session_state.nurses = pickle.load(f)
    except FileNotFoundError:
        st.session_state.nurses = []

# 📌 앱 시작 시 기존 데이터 불러오기
if "nurses" not in st.session_state:
    load_data()

st.title("🏥 간호사 근무표 자동 생성기")

# 📂 간호사 정보 불러오기 (엑셀 파일 업로드 기능 추가)
st.sidebar.subheader("📂 간호사 정보 불러오기")
uploaded_file = st.sidebar.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)

    # 엑셀 파일에서 필요한 컬럼만 추출
    required_columns = ["직원ID", "이름", "근무 유형", "Charge 가능", "Wanted Off", "휴가", "공가"]
    
    if all(col in df_uploaded.columns for col in required_columns):
        st.session_state.nurses = df_uploaded.to_dict(orient="records")  # 엑셀 데이터를 세션에 저장

        # 🔹 현재 세션에 저장된 간호사 목록을 확인하는 디버깅 코드 추가 
        st.write("📋 현재 저장된 간호사 목록:", st.session_state.nurses)

        # 🔹 데이터가 존재할 때만 우선순위 정렬 및 저장 수행
        if st.session_state.nurses:  
            assign_priority(st.session_state.nurses)
            save_data()
            st.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")
        else:
            st. warning("📢 업로드된 간호사 데이터가 없습니다. 엑셀 파일을 확인하세요.")
    else:
        st.error("⚠️ 엑셀 파일의 형식이 올바르지 않습니다. 올바른 컬럼을 포함하고 있는지 확인하세요.")

# 📥 엑셀 양식 다운로드 기능 추가
sample_data = pd.DataFrame({
    "직원ID": [101, 102, 103, 104],
    "이름": ["홍길동", "이영희", "박철수", "김민지"],
    "근무 유형": ["3교대 가능", "D Keep", "E Keep", "N Keep"],
    "Charge 가능": ["O", "X", "O", "O"],
    "Wanted Off": ["5, 10, 15", "3, 7, 21", "6, 11", "4, 19, 23"],
    "휴가": ["8, 9", "14, 15", "-", "25"],
    "공가": ["12", "-", "20", "-"]
})

output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    sample_data.to_excel(writer, index=False, sheet_name="간호사 정보 양식")
output.seek(0)

st.sidebar.download_button(
    label="📥 엑셀 양식 다운로드",
    data=output,
    file_name="nurse_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")

selected_nurse = st.sidebar.selectbox(
    "수정할 간호사 선택",
    ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses]
)

st.sidebar.subheader("📝 간호사 정보 입력")
name = st.sidebar.text_input("📛 이름", "" if selected_nurse == "새 간호사 추가" else next(n["이름"] for n in st.session_state.nurses if n["이름"] == selected_nurse))
staff_id = st.sidebar.text_input("👤 직원ID (숫자 입력)", "" if selected_nurse == "새 간호사 추가" else next(n["직원ID"] for n in st.session_state.nurses if n["이름"] == selected_nurse))

shift_type = st.sidebar.selectbox(
    "🔄 근무 유형 선택",
    ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"],
    index=0 if selected_nurse == "새 간호사 추가" else ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"].index(next(n["근무 유형"] for n in st.session_state.nurses if n["이름"] == selected_nurse))
)

charge = st.sidebar.toggle("⚡ Charge Nurse 가능", value=False if selected_nurse == "새 간호사 추가" else next(n["Charge 가능"] == "O" for n in st.session_state.nurses if n["이름"] == selected_nurse))

wanted_off = st.sidebar.text_area("🏖️ Wanted Off (쉼표로 구분)", "" if selected_nurse == "새 간호사 추가" else next(n["Wanted Off"] for n in st.session_state.nurses if n["이름"] == selected_nurse))
vacation = st.sidebar.text_area("🛫 휴가 (쉼표로 구분)", "" if selected_nurse == "새 간호사 추가" else next(n["휴가"] for n in st.session_state.nurses if n["이름"] == selected_nurse))
public_leave = st.sidebar.text_area("🏥 공가 (쉼표로 구분)", "" if selected_nurse == "새 간호사 추가" else next(n["공가"] for n in st.session_state.nurses if n["이름"] == selected_nurse))

if st.sidebar.button("✅ 저장"):
    if selected_nurse == "새 간호사 추가":
        st.session_state.nurses.append({
            "직원ID": staff_id,
            "이름": name,
            "근무 유형": shift_type,
            "Charge 가능": "O" if charge else "X",
            "Wanted Off": wanted_off,
            "휴가": vacation,
            "공가": public_leave,
        })
    else:
        for nurse in st.session_state.nurses:
            if nurse["이름"] == selected_nurse:
                nurse.update({
                    "직원ID": staff_id,
                    "근무 유형": shift_type,
                    "Charge 가능": "O" if charge else "X",
                    "Wanted Off": wanted_off,
                    "휴가": vacation,
                    "공가": public_leave,
                })
    assign_priority(st.session_state.nurses)
    save_data()

if selected_nurse != "새 간호사 추가":
    if st.sidebar.button("❌ 간호사 삭제"):
        st.session_state.nurses = [n for n in st.session_state.nurses if n["이름"] != selected_nurse]
        save_data()
        st.success(f"간호사 '{selected_nurse}' 정보를 삭제했습니다.")
        st.stop()

st.sidebar.button("🔄 세션 초기화", on_click=lambda: [save_data(), load_data()])

# 📌 오른쪽 화면: 간호사 목록 표시 (자동 업데이트)
st.write("### 🏥 현재 간호사 목록")
if st.session_state.nurses:
    df_nurse_info = pd.DataFrame(st.session_state.nurses).sort_values(by="우선순위")
    st.data_editor(df_nurse_info, hide_index=True, use_container_width=True)
else:
    st.info("현재 추가된 간호사가 없습니다.")

# 📅 근무표 생성 버튼
if st.button("📅 근무표 생성"):
    if not st.session_state.nurses:
        st.warning("간호사가 없습니다. 먼저 간호사를 추가해주세요.")
        st.stop()

    df_nurse_info = pd.DataFrame(st.session_state.nurses)

    if "우선순위" not in df_nurse_info.columns:
        df_nurse_info["우선순위"] = range(1, len(df_nurse_info) + 1)

    df_nurse_info = df_nurse_info.sort_values(by="우선순위")

    charge_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "O"]["이름"].tolist()
    acting_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "X"]["이름"].tolist()

    if len(charge_nurses) < 2:
        st.error("⚠️ Charge Nurse 인원이 부족합니다! 최소 2명 이상 필요합니다.")
        st.stop()

    dates = [str(i) + "일" for i in range(1, 31)]
    df_schedule = pd.DataFrame(index=df_nurse_info["이름"], columns=dates)
    df_schedule[:] = ""

    for date in df_schedule.columns:
        night_charge = random.sample(charge_nurses, 2)
        for nurse in night_charge:
            df_schedule.at[nurse, date] = "N (C)"

        day_evening_charge = random.sample(charge_nurses, 2)
        day_evening_acting = random.sample(acting_nurses, 2)

        for nurse in day_evening_charge:
            df_schedule.at[nurse, date] = random.choice(["D (C)", "E (C)"])

        for nurse in day_evening_acting:
            df_schedule.at[nurse, date] = random.choice(["D (A)", "E (A)"])

    st.write("### 📅 생성된 근무표")
    st.data_editor(df_schedule, use_container_width=True)
