import random
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# 🔹 월별 공휴일 가져오기
def get_korean_holidays(year, month):
    holidays = {
        "2025-01": [1], "2025-02": [9, 10], "2025-03": [1],
        "2025-04": [10], "2025-05": [5, 15], "2025-06": [6],
        "2025-07": [], "2025-08": [15], "2025-09": [14, 15, 16],
        "2025-10": [3, 9], "2025-11": [], "2025-12": [25]
    }
    return holidays.get(f"{year}-{str(month).zfill(2)}", [])

# 🔹 근무표 생성 함수
def assign_shift(schedule_df, nurses_df, day, holidays):
    required_roles = {
        "D": {"Charge": 2, "Acting": 2},
        "E": {"Charge": 2, "Acting": 2},
        "N": {"Charge": 2}
    }
    assigned_nurses = {"D": [], "E": [], "N": []}

    # 🔹 해당 날짜에 오프인 간호사 제외
    available_nurses = nurses_df[~nurses_df["Wanted Off"].apply(lambda x: str(day) in str(x))]

    # 🔹 팀 A/B 배정
    available_nurses["팀"] = ["A" if i % 2 == 0 else "B" for i in range(len(available_nurses))]

    def assign_role(shift, role, num_needed):
        candidates = available_nurses.copy()
        
        # 🔹 나이트 근무 제한 적용
        if shift == "N":
            candidates = candidates[candidates["근무유형"].isin(["N Keep", "3교대 가능"])]

        # 🔹 연속근무 3일 제한 적용
        for name in assigned_nurses[shift]:
            if sum([schedule_df.at[name, f"{d}일"] == shift for d in range(max(1, day-3), day)]) >= 3:
                candidates = candidates[candidates["이름"] != name]

        # 🔹 차지 간호사 필터링
        if role == "Charge":
            candidates = candidates[candidates["Charge 가능"] == "O"]

        # 🔹 인원 배정
        selected = random.sample(list(candidates["이름"]), min(num_needed, len(candidates)))

        for name in selected:
            team = nurses_df[nurses_df["이름"] == name]["팀"].values[0]
            color = "🔵" if role == "Charge" else "⚪"
            schedule_df.at[name, f"{day}일"] = f"{color} {shift}({team})"
            assigned_nurses[shift].append(name)

    # 🔹 근무 배정 실행
    for shift, roles in required_roles.items():
        for role, num in roles.items():
            assign_role(shift, role, num)

    # 🔹 근무 인원이 부족할 경우 추가 배정
    for shift, roles in required_roles.items():
        if len(assigned_nurses[shift]) < sum(roles.values()):
            additional_needed = sum(roles.values()) - len(assigned_nurses[shift])
            assign_role(shift, "Acting", additional_needed)

    # 🔹 공휴일이 아니면 오프 자동 배정
    if day not in holidays:
        off_nurses = random.sample(list(available_nurses["이름"]), min(3, len(available_nurses)))
        for name in off_nurses:
            schedule_df.at[name, f"{day}일"] = "🟡 Off"

    return schedule_df

# 🔹 사용자 입력 처리
year, month = 2025, 3  # 예제 값
days_in_month = (datetime(year, month % 12 + 1, 1) - timedelta(days=1)).day
holidays = get_korean_holidays(year, month)

# 🔹 간호사 명단 엑셀 업로드
st.title("📅 간호사 근무표 자동 생성기")
uploaded_file = st.file_uploader("📂 간호사 명단 엑셀 업로드", type=["xlsx"])

if uploaded_file:
    nurses_df = pd.read_excel(uploaded_file)

    # 🔹 컬럼명 확인 후 변환 (대소문자 & 띄어쓰기 문제 해결)
    nurses_df.columns = nurses_df.columns.str.strip().str.replace(" ", "_")

    # 🔹 원티드 오프 날짜를 리스트로 변환
    nurses_df["Wanted_Off"] = nurses_df["Wanted_Off"].apply(lambda x: str(x).split(",") if pd.notna(x) else [])

    # 🔹 근무표 초기화
    schedule_df = pd.DataFrame(index=nurses_df["이름"], columns=[f"{day}일" for day in range(1, days_in_month + 1)])

    # 🔹 근무표 자동 생성
    for day in range(1, days_in_month + 1):
        schedule_df = assign_shift(schedule_df, nurses_df, day, holidays)

    # 🔹 결과 출력
    st.dataframe(schedule_df)
    st.download_button("📥 근무표 엑셀 다운로드", schedule_df.to_csv(index=True).encode("utf-8"), "nurse_schedule.csv", "text/csv")
