import streamlit as st
import pandas as pd
import random

# 간호사 데이터 저장 (세션 유지)
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 📌 간호사 추가 및 수정 섹션
st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")
selected_nurse = st.sidebar.selectbox("수정할 간호사 선택", ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses])

if selected_nurse == "새 간호사 추가":
    name = st.sidebar.text_input("이름")
    nurse_id = st.sidebar.text_input("직원 ID (숫자 입력)")
    work_type = st.sidebar.selectbox("근무 유형 선택", ["D Keep", "E Keep", "N Keep", "3교대 가능", "N 제외"])
    can_charge = st.sidebar.checkbox("⚡ Charge Nurse 가능")
    can_acting = st.sidebar.checkbox("🩺 Acting Nurse 가능")
    night_charge_only = st.sidebar.checkbox("🌙 N 근무 시 Charge Nurse 가능")  # 📌 추가된 필드
    wanted_off = st.sidebar.text_area("Wanted Off (쉼표로 구분)")
    leave = st.sidebar.text_area("휴가 (쉼표로 구분)")
    public_holiday = st.sidebar.text_area("공가 (쉼표로 구분)")

    if st.sidebar.button("저장"):
        st.session_state.nurses.append({
            "이름": name, "직원ID": nurse_id, "근무 유형": work_type,
            "Charge 가능": "O" if can_charge else "",
            "Acting 가능": "O" if can_acting else "",
            "N 차지 전용": "O" if night_charge_only else "",  # 📌 추가된 필드
            "Wanted Off": wanted_off, "휴가": leave, "공가": public_holiday
        })
        st.sidebar.success(f"✅ {name} 간호사 정보가 저장되었습니다!")

# 📌 간호사 목록 확인용 (디버깅)
st.write("📋 현재 저장된 간호사 목록:", st.session_state.nurses)

# 📌 근무표 자동 생성 로직
st.header("📅 간호사 근무표 자동 생성기")

if st.button("📊 근무표 생성"):
    nurses_df = pd.DataFrame(st.session_state.nurses)

    # 📌 Charge Nurse와 Acting Nurse를 나눠서 처리
    charge_nurses = nurses_df[nurses_df["Charge 가능"] == "O"]
    acting_nurses = nurses_df[nurses_df["Acting 가능"] == "O"]
    night_charge_only = nurses_df[nurses_df["N 차지 전용"] == "O"]

    # 📌 근무표 기본 구조 설정 (이름 세로축, 날짜 가로축)
    num_days = 30  # 기본 한 달 30일 설정
    schedule_df = pd.DataFrame(index=nurses_df["이름"], columns=[f"{i+1}일" for i in range(num_days)])

    # 📌 Acting Nurse 배치 (각 팀당 1명씩)
    for day in range(num_days):
        acting_candidates = acting_nurses.sample(min(len(acting_nurses), 2))  # A팀, B팀 1명씩
        schedule_df.loc[acting_candidates["이름"], f"{day+1}일"] = "Acting"

    # 📌 Charge Nurse 배치 (매 근무 필수 2명)
    for day in range(num_days):
        charge_candidates = charge_nurses.sample(min(len(charge_nurses), 2))
        schedule_df.loc[charge_candidates["이름"], f"{day+1}일"] = "Charge"

    # 📌 N 근무 배치 (N 차지 전용 필드 활용)
    for day in range(num_days):
        night_candidates = night_charge_only.sample(min(len(night_charge_only), 2))
        schedule_df.loc[night_candidates["이름"], f"{day+1}일"] = "N (C)"

    # 📌 근무표 표시
    st.write("### 📋 자동 생성된 근무표")
    st.dataframe(schedule_df)
