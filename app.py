import streamlit as st
import pandas as pd
import random

# 간호사 정보 저장
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 간호사 정보 업로드 (엑셀 파일 불러오기)
st.sidebar.header("📂 간호사 정보 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)
    st.session_state.nurses = df_uploaded.to_dict(orient="records")
    st.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")

# 간호사 목록 표시
st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")
st.sidebar.write("📋 현재 저장된 간호사 목록:", st.session_state.nurses)

# 근무표 생성 함수
def generate_schedule(nurses, days):
    schedule = pd.DataFrame(index=[nurse["이름"] for nurse in nurses], columns=[f"{d+1}일" for d in range(days)])

    # A/B 팀 랜덤 배정 (이전 인터벌 유지)
    for nurse in nurses:
        nurse["팀"] = random.choice(["A", "B"]) if "팀" not in nurse else nurse["팀"]

    # 날짜별 근무 배정
    for day in range(days):
        day_column = f"{day+1}일"

        # 차지 가능한 사람 & 액팅 가능한 사람 필터링
        charge_nurses = [n for n in nurses if n["차지 가능"] == "O"]
        acting_nurses = [n for n in nurses if n["차지 가능"] != "O"]

        # 나이트 먼저 배정 (차지 2명 필수)
        night_shift = random.sample(charge_nurses, 2)
        for n in night_shift:
            schedule.at[n["이름"], day_column] = f"N (C) {n['팀']}"

        # 데이 & 이브닝 배정 (차지 2명 + 액팅 2명)
        for shift, shift_label in [("D", "데이"), ("E", "이브닝")]:
            assigned = []

            # 차지 2명 배정
            selected_charges = random.sample(charge_nurses, 2)
            assigned.extend(selected_charges)

            # 액팅 2명 배정
            selected_actings = random.sample(acting_nurses, 2)
            assigned.extend(selected_actings)

            for n in assigned:
                role = "C" if n in selected_charges else "A"
                schedule.at[n["이름"], day_column] = f"{shift} ({role}) {n['팀']}"

    return schedule

# 근무표 생성 버튼
if st.button("📅 근무표 생성"):
    if not st.session_state.nurses:
        st.error("❌ 간호사 정보가 없습니다. 엑셀 파일을 업로드하거나 직접 추가해주세요.")
    else:
        schedule_df = generate_schedule(st.session_state.nurses, 30)  # 30일 기준
        st.session_state["schedule_df"] = schedule_df
        st.success("✅ 근무표가 성공적으로 생성되었습니다!")

# 근무표 확인
if "schedule_df" in st.session_state:
    st.subheader("📄 자동 생성된 근무표")
    st.dataframe(st.session_state["schedule_df"])

# 엑셀 다운로드 기능 추가
if "schedule_df" in st.session_state:
    st.download_button("📥 근무표 엑셀 다운로드", st.session_state["schedule_df"].to_csv(index=True).encode("utf-8"), "schedule.csv", "text/csv")
