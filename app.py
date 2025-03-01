import streamlit as st
import pandas as pd
import io
import random
import pickle  # 데이터 저장용 라이브러리

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

st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")

# 🔄 우선순위 부여 함수
def assign_priority(nurses):
    for nurse in nurses:
        if not nurse["직원ID"].isdigit():  # 직원ID가 숫자가 아니면 기본값 "9999" 설정
            nurse["직원ID"] = "9999"

    nurses.sort(key=lambda x: int(x["직원ID"]))  # 직원ID 기준으로 정렬
    
    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1  # 정렬된 순서대로 "우선순위" 추가

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

st.sidebar.button("🔄 세션 초기화", on_click=lambda: [st.session_state.clear(), load_data()])

# 📅 근무표 생성 버튼
if st.button("📅 근무표 생성"):
    if not st.session_state.nurses:
        st.warning("간호사가 없습니다. 먼저 간호사를 추가해주세요.")
        st.stop()

    df_nurse_info = pd.DataFrame(st.session_state.nurses)

    # 🛠 "우선순위" 컬럼이 없으면 자동 생성
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

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_nurse_info.to_excel(writer, sheet_name="간호사 정보", index=False)
        df_schedule.to_excel(writer, sheet_name="근무표", index=True)
    output.seek(0)

    st.download_button("📥 근무표 다운로드", data=output, file_name="nurse_schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
