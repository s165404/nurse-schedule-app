import streamlit as st
import pandas as pd
import io
import random

st.set_page_config(page_title="🏥 간호사 근무표 자동 생성기", layout="wide")

# 🌟 스타일 설정 (버튼, 테이블, 제목 스타일링)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #008CBA;
        color: white;
        width: 100%;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
    }
    div.stDownloadButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        width: 100%;
        height: 40px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 간호사 근무표 자동 생성기")

# 🏥 사이드바: 간호사 추가 및 수정
st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")

if "nurses" not in st.session_state:
    st.session_state.nurses = []

def assign_priority(nurses):
    for nurse in nurses:
        if not nurse["직원ID"].isdigit():
            nurse["직원ID"] = "9999"
    nurses.sort(key=lambda x: int(x["직원ID"]))
    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1

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

if selected_nurse != "새 간호사 추가":
    if st.sidebar.button("❌ 간호사 삭제"):
        st.session_state.nurses = [n for n in st.session_state.nurses if n["이름"] != selected_nurse]
        st.success(f"간호사 '{selected_nurse}' 정보를 삭제했습니다.")
        st.stop()

# 🔄 세션 초기화 버튼
st.sidebar.button("🔄 세션 초기화", on_click=lambda: st.session_state.clear())

# 🏥 현재 간호사 목록 표시 (엑셀 스타일)
st.write("### 🏥 현재 간호사 목록")

if st.session_state.nurses:
    df_nurse_info = pd.DataFrame(st.session_state.nurses).sort_values(by="우선순위")
    st.data_editor(
        df_nurse_info,
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("현재 추가된 간호사가 없습니다.")

# 📅 근무표 생성 버튼
if st.button("📅 근무표 생성"):
    if not st.session_state.nurses:
        st.warning("간호사가 없습니다. 먼저 간호사를 추가해주세요.")
        st.stop()

    df_nurse_info = pd.DataFrame(st.session_state.nurses).sort_values(by="우선순위")
    dates = [str(i) + "일" for i in range(1, 31)]
    df_schedule = pd.DataFrame(index=df_nurse_info["이름"], columns=dates)
    df_schedule[:] = ""

    # Charge Nurse (차지 가능자는 엑팅도 가능) / Acting Nurse (엑팅만 가능)
    charge_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "O"]["이름"].tolist()
    acting_only_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "X"]["이름"].tolist()
    night_only_charge = df_nurse_info[df_nurse_info["Night 차지 전용"] == "O"]["이름"].tolist()

    if len(charge_nurses) < 2:
        st.error("⚠️ Charge Nurse 인원이 부족합니다! 최소 2명 이상 필요합니다.")
        st.stop()

    for date in df_schedule.columns:
        # 🌙 나이트 근무 - 차지(Charge) 2명 필수 (엑팅 없음)
        night_charge = []
        if len(night_only_charge) >= 2:
            night_charge = random.sample(night_only_charge, 2)
        else:
            night_charge = random.sample(charge_nurses, 2)

        for nurse in night_charge:
            df_schedule.at[nurse, date] = "N (C)"

        # ☀️ 주간(D) & 저녁(E) 근무 - 차지 2명 + 엑팅 2명 배정
        day_evening_charge = random.sample(charge_nurses, 2)
        day_evening_acting = random.sample(acting_only_nurses, 2)

        for nurse in day_evening_charge:
            df_schedule.at[nurse, date] = random.choice(["D (C)", "E (C)"])

        for nurse in day_evening_acting:
            df_schedule.at[nurse, date] = random.choice(["D (A)", "E (A)"])

    # 🚀 최종 근무표 출력
    st.write("### 📅 생성된 근무표")
    st.data_editor(df_schedule, use_container_width=True)

    # 📥 엑셀 다운로드
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_nurse_info.to_excel(writer, sheet_name="간호사 정보", index=False)
        df_schedule.to_excel(writer, sheet_name="근무표", index=True)
    output.seek(0)

    st.download_button("📥 근무표 다운로드", data=output, file_name="nurse_schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
