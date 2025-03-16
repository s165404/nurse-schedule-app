import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="간호사 근무표 자동 생성기", layout="wide")

# 간호사 데이터 업로드
st.title("📅 간호사 근무표 자동 생성기")

uploaded_file = st.file_uploader("📂 간호사 엑셀 파일 업로드", type=["xlsx"])
if uploaded_file:
    nurses_df = pd.read_excel(uploaded_file)

    # 컬럼명 정리
    nurses_df.columns = nurses_df.columns.str.strip()
    
    # 오프 관련 데이터 처리
    for col in ["Wanted Off", "휴가", "공가"]:
        nurses_df[col] = nurses_df[col].apply(lambda x: str(x).split(",") if pd.notna(x) else [])

    # 근무 설정 값
    selected_year = st.selectbox("연도 선택", range(2024, 2031), index=0)
    selected_month = st.selectbox("월 선택", range(1, 13), index=datetime.now().month - 1)

    # 달의 마지막 날짜 계산
    _, last_day = divmod((datetime(selected_year, selected_month % 12 + 1, 1) - timedelta(days=1)).day, 32)
    days = list(range(1, last_day + 1))

    # 공휴일 설정
    holidays = [random.choice(days[:10]), random.choice(days[10:])]  # 임시 공휴일 설정

    # 근무표 생성
    schedule_df = pd.DataFrame(index=nurses_df["이름"], columns=[f"{day}일" for day in days])

    # A팀 / B팀 분배
    nurses_df["팀"] = ["A" if i % 2 == 0 else "B" for i in range(len(nurses_df))]

    # 근무 배정
    for day in days:
        # 하루 근무 필수 인원 설정
        required_roles = {
            "D": {"Charge": 2, "Acting": 2},
            "E": {"Charge": 2, "Acting": 2},
            "N": {"Charge": 2}
        }

        assigned_nurses = {"D": [], "E": [], "N": []}

        # 휴무자 제외
        available_nurses = nurses_df[~nurses_df["Wanted Off"].apply(lambda x: str(day) in x)]

        # 근무 배정 함수
       def assign_shift(schedule_df, nurses_df, day):
    """
    하루치 근무를 배정하는 함수
    - 필수 인원 (D: 차지2+액팅2 / E: 차지2+액팅2 / N: 2명)
    - 한 팀(A/B)으로 몰리지 않도록 배정
    - 연속 근무 최대 3일 제한
    - 12시간 휴식 보장 (D→E→N 순서 유지)
    - 차지 가능한 사람이 없으면 대체 인원 배정
    """

    required_roles = {
        "D": {"Charge": 2, "Acting": 2},
        "E": {"Charge": 2, "Acting": 2},
        "N": {"Charge": 2}
    }

    assigned_nurses = {"D": [], "E": [], "N": []}

    # 해당 날짜에 휴무(Wanted Off, 휴가, 공가)인 사람 제외
    available_nurses = nurses_df[~nurses_df["Wanted Off"].apply(lambda x: str(day) in x)]

    # 팀별 분배 고려
    available_nurses["팀"] = ["A" if i % 2 == 0 else "B" for i in range(len(available_nurses))]

    def assign_role(shift, role, num_needed):
        """
        특정 근무와 역할에 대해 인원을 배정하는 함수
        """
        candidates = available_nurses.copy()

        # N 제외 간호사 필터링
        if shift == "N":
            candidates = candidates[candidates["근무유형"].isin(["N Keep", "3교대 가능"])]

        # 연속근무 3일 제한 확인
        for name in assigned_nurses[shift]:
            if sum([schedule_df.at[name, f"{d}일"] == shift for d in range(day-3, day)]) >= 3:
                candidates = candidates[candidates["이름"] != name]

        # 차지 간호사 필터링
        if role == "Charge":
            candidates = candidates[candidates["Charge 가능"] == "O"]

        # 배정 인원 선별
        selected = random.sample(list(candidates["이름"]), min(num_needed, len(candidates)))

        for name in selected:
            team = nurses_df[nurses_df["이름"] == name]["팀"].values[0]
            schedule_df.at[name, f"{day}일"] = f"{shift}({team})"
            assigned_nurses[shift].append(name)

    # 근무 배정 실행
    for shift, roles in required_roles.items():
        for role, num in roles.items():
            assign_role(shift, role, num)

    # 근무 인원이 부족할 경우 추가 배정
    for shift, roles in required_roles.items():
        if len(assigned_nurses[shift]) < sum(roles.values()):
            additional_needed = sum(roles.values()) - len(assigned_nurses[shift])
            assign_role(shift, "Acting", additional_needed)  # 추가 인원은 액팅으로 배정

    return schedule_df

        # 근무 배정 실행
        for shift, roles in required_roles.items():
            for role, num in roles.items():
                assign_shift(shift, role, num)

        # 공휴일 반영
        if day in holidays:
            off_nurses = random.sample(list(available_nurses["이름"]), min(3, len(available_nurses)))
            for name in off_nurses:
                schedule_df.at[name, f"{day}일"] = "공(교)"

    # 가독성 개선을 위한 색상 적용
    def color_shift(val):
        if pd.isna(val):
            return ""
        if "D" in val:
            return "background-color: #D6EAF8;"  # 연파랑
        if "E" in val:
            return "background-color: #F9E79F;"  # 연노랑
        if "N" in val:
            return "background-color: #ABEBC6;"  # 연초록
        if "공" in val:
            return "background-color: #F5B7B1;"  # 연핑크
        return ""

    # 근무표 출력
    st.subheader("📋 자동 생성된 근무표")
    st.dataframe(schedule_df.style.applymap(color_shift))

    # 엑셀 다운로드 기능
    st.download_button("📥 근무표 엑셀 다운로드", schedule_df.to_csv(index=True).encode("utf-8"), "nurse_schedule.csv", "text/csv")
