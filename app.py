import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# 📌 공휴일 자동 반영 함수
def get_holidays(year, month):
    holidays = {
        (2025, 1): [1],  # 예시: 1월 1일
        (2025, 2): [10, 11],  # 예시: 2월 10일, 11일
        (2025, 3): [1],  # 예시: 3월 1일
    }
    return holidays.get((year, month), [])

# 📌 Streamlit UI
st.title("📅 간호사 근무표 자동 생성기")

# 📌 사용자로부터 월 선택받기
selected_year = st.selectbox("연도 선택", [2025])
selected_month = st.selectbox("월 선택", list(range(1, 13)))

# 📌 공휴일 자동 반영
holidays = get_holidays(selected_year, selected_month)
st.write(f"📌 {selected_year}년 {selected_month}월 공휴일: {holidays}")

# 📌 엑셀 파일 업로드 기능 추가
uploaded_file = st.file_uploader("간호사 명단 엑셀 업로드", type=["xlsx"])

if uploaded_file:
    nurses_df = pd.read_excel(uploaded_file)
    
    # ✅ 데이터 전처리
    nurses_df.fillna("", inplace=True)  # 빈값 채우기
    nurses_df["Wanted_Off"] = nurses_df["Wanted_Off"].apply(lambda x: str(x).split(",") if x else [])

    st.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")

    # 📌 근무표 생성 로직
    days_in_month = (datetime(selected_year, selected_month + 1, 1) - timedelta(days=1)).day
    schedule = {nurse: [""] * days_in_month for nurse in nurses_df["이름"]}

    # ✅ 근무 배정 기준
    shifts_per_day = {"D": 4, "E": 4, "N": 2}
    
    for day in range(days_in_month):
        available_nurses = nurses_df.sample(frac=1).to_dict(orient="records")  # 랜덤 배정

        # ✅ 하루 근무 배정
        assigned_shifts = {"D": [], "E": [], "N": []}
        for nurse in available_nurses:
            for shift in ["D", "E", "N"]:
                if len(assigned_shifts[shift]) < shifts_per_day[shift]:
                    if shift not in nurse["Wanted_Off"] and shift not in schedule[nurse["이름"]][max(0, day-1)]:
                        schedule[nurse["이름"]][day] = f"{shift} (A)" if "Acting 가능" in nurse else f"{shift} (C)"
                        assigned_shifts[shift].append(nurse["이름"])
                        break

    # 📌 DataFrame 변환
    schedule_df = pd.DataFrame.from_dict(schedule, orient="index", columns=[f"{i+1}일" for i in range(days_in_month)])
    schedule_df.index.name = "이름"

    # 📌 근무표 화면에 출력
    st.subheader("📜 자동 생성된 근무표:")
    st.dataframe(schedule_df)

    # 📌 엑셀 다운로드 기능
    st.download_button("📥 근무표 엑셀 다운로드", schedule_df.to_csv(index=True).encode(), "nurse_schedule.csv", "text/csv")
