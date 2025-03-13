import streamlit as st
import pandas as pd
import random

# 스트림릿 페이지 기본 설정
st.set_page_config(page_title="간호사 근무표 자동 생성기", layout="wide")

# 📌 한 달의 일수와 공휴일 설정 기능
st.sidebar.header("📅 달력 설정")
selected_year = st.sidebar.number_input("연도 선택", min_value=2020, max_value=2030, value=2025, step=1)
selected_month = st.sidebar.number_input("월 선택", min_value=1, max_value=12, value=3, step=1)

# 해당 월의 총 일수 계산
days_in_month = pd.Period(f"{selected_year}-{selected_month}").days_in_month
st.sidebar.write(f"📆 이번 달은 **{days_in_month}일**까지 있음.")

# 공휴일 설정 (수동 입력 가능)
manual_holidays = st.sidebar.text_area("📌 공휴일 입력 (쉼표로 구분)", "1, 3, 9")  # 예제: 1, 3, 9
holiday_list = [int(day.strip()) for day in manual_holidays.split(",") if day.strip().isdigit()]

# 📌 엑셀 업로드하여 간호사 목록 불러오기
st.sidebar.header("📂 간호사 정보 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=["xlsx"])

if uploaded_file:
    nurses_df = pd.read_excel(uploaded_file)
    st.session_state.nurses = nurses_df.to_dict(orient="records")
    st.sidebar.success("✅ 간호사 정보 불러오기 완료!")

# 📌 간호사 데이터 확인
st.write("📋 **현재 저장된 간호사 목록:**", st.session_state.get("nurses", []))

# 📌 근무 배정 규칙
def generate_schedule(nurses, days_in_month, holiday_list):
    schedule = pd.DataFrame(index=[n["이름"] for n in nurses], columns=[f"{day}일" for day in range(1, days_in_month+1)])
    
    # 🔥 N Keep 간호사 먼저 배정 (최대 3일 연속)
    n_keep_nurses = [n for n in nurses if n["근무 유형"] == "N Keep"]
    for nurse in n_keep_nurses:
        assigned_days = []
        for day in range(1, days_in_month+1, 4):  # N 근무 간격 조정
            if len(assigned_days) >= 3:
                break
            if day not in holiday_list:
                schedule.at[nurse["이름"], f"{day}일"] = "N (C)"
                assigned_days.append(day)

    # 🔥 D → E → N 순서로 근무 배정 (D 4명 / E 4명 / N 2명 필수 유지)
    other_nurses = [n for n in nurses if n["근무 유형"] != "N Keep"]
    for day in range(1, days_in_month+1):
        if day in holiday_list:
            continue
        
        daily_schedule = []
        charge_count, acting_count = 0, 0
        for nurse in other_nurses:
            if len(daily_schedule) >= 10:  # 하루 근무 제한 (D4 E4 N2)
                break
            
            # Acting/Charge 구분
            role = "A" if nurse["Charge_가능"] != "O" else "C"
            if role == "C" and charge_count < 2:
                duty = "Charge"
                charge_count += 1
            elif role == "A" and acting_count < 2:
                duty = "Acting"
                acting_count += 1
            else:
                continue

            # 팀 배정 (A/B 랜덤 배정)
            team = "A" if random.random() > 0.5 else "B"
            schedule.at[nurse["이름"], f"{day}일"] = f"{duty}({team})"
            daily_schedule.append(nurse["이름"])
    
    return schedule

# 📌 근무표 생성 버튼
if st.button("📅 근무표 생성"):
    if "nurses" in st.session_state:
        schedule_df = generate_schedule(st.session_state.nurses, days_in_month, holiday_list)
        st.session_state.schedule_df = schedule_df
        st.success("✅ 근무표가 성공적으로 생성되었습니다!")
    else:
        st.error("⚠ 간호사 정보를 먼저 업로드하세요!")

# 📌 근무표 확인
if "schedule_df" in st.session_state:
    st.subheader("📋 **자동 생성된 근무표**")
    st.dataframe(st.session_state.schedule_df)

    # 📂 엑셀 다운로드 기능 추가
    st.download_button("📥 근무표 엑셀 다운로드", st.session_state.schedule_df.to_csv(index=True).encode('utf-8-sig'), "nurse_schedule.csv", "text/csv")
