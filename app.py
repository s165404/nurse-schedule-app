import streamlit as st
import pandas as pd
import random

# 🚀 간호사 데이터 세션 저장
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 📌 **엑셀 파일 업로드**
st.sidebar.header("📤 간호사 정보 불러오기 (엑셀 업로드)")
uploaded_file = st.sidebar.file_uploader("📂 엑셀 파일 업로드 (xlsx)", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)

    # 📌 **필수 컬럼 확인 후 자동 생성**
    required_columns = ["이름", "직원ID", "근무 유형", "Charge 가능", "Acting 가능", "N 차지 전용", "Wanted Off", "휴가", "공가"]
    for col in required_columns:
        if col not in df_uploaded.columns:
            df_uploaded[col] = ""

    st.session_state.nurses = df_uploaded.to_dict(orient="records")
    st.sidebar.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")

# 📌 **근무시간 정의**
WORK_HOURS = {
    "D": (6.5, 15.5),  # 06:30 ~ 15:30
    "E": (13, 22),     # 13:00 ~ 22:00
    "N": (21, 8)       # 21:00 ~ 익일 08:00
}

# 📌 **근무표 생성**
st.header("📅 간호사 근무표 자동 생성기")

if st.button("📊 근무표 생성"):
    nurses_df = pd.DataFrame(st.session_state.nurses)

    # ✅ **컬럼 자동 생성 (누락 방지)**
    required_columns = ["Charge 가능", "Acting 가능", "N 차지 전용", "Wanted Off", "휴가", "공가"]
    for col in required_columns:
        if col not in nurses_df.columns:
            nurses_df[col] = ""

    charge_nurses = nurses_df[nurses_df["Charge 가능"] == "O"]
    acting_nurses = nurses_df[nurses_df["Acting 가능"] == "O"]
    night_charge_only = nurses_df[nurses_df["N 차지 전용"] == "O"]

    num_days = 30  # 기본 한 달 30일 설정
    schedule_df = pd.DataFrame(index=nurses_df["이름"], columns=[f"{i+1}일" for i in range(num_days)])

    # 📌 **오프 반영 (Wanted Off → 휴가 → 공가 순)**
    for nurse in nurses_df.itertuples():
        off_days = str(nurse.Wanted_Off).split(",") + str(nurse.휴가).split(",") + str(nurse.공가).split(",")
        for day in off_days:
            try:
                day = int(day.strip()) - 1
                schedule_df.at[nurse.이름, f"{day+1}일"] = "🔴 OFF"
            except:
                continue

    # 📌 **Acting Nurse 배치 (A/B 팀 구분)**
    team_tracking = {}
    for day in range(num_days):
        for nurse in acting_nurses.itertuples():
            if nurse.이름 in team_tracking:
                schedule_df.at[nurse.이름, f"{day+1}일"] = f"🟢 Acting({team_tracking[nurse.이름]})"
            else:
                assigned_team = "A" if day % 2 == 0 else "B"
                team_tracking[nurse.이름] = assigned_team
                schedule_df.at[nurse.이름, f"{day+1}일"] = f"🟢 Acting({assigned_team})"

    # 📌 **Charge Nurse 배치 (매 근무 필수 2명)**
    for day in range(num_days):
        charge_candidates = charge_nurses.sample(min(len(charge_nurses), 2))
        schedule_df.loc[charge_candidates["이름"], f"{day+1}일"] = "🔵 Charge"

    # 📌 **N 근무 배치 (N 차지 전용 필드 활용)**
    for day in range(num_days):
        night_candidates = night_charge_only.sample(min(len(night_charge_only), 2))
        schedule_df.loc[night_candidates["이름"], f"{day+1}일"] = "🔵 N (C)"

    # 📌 **연속 근무 제한 (최대 3일, 인원 부족 시 5일까지 허용)**
    for nurse in nurses_df.itertuples():
        consecutive_days = 0
        for day in range(num_days):
            current_shift = schedule_df.at[nurse.이름, f"{day+1}일"]
            if current_shift not in ["🔴 OFF", None]:
                consecutive_days += 1
                if consecutive_days > 3:
                    schedule_df.at[nurse.이름, f"{day+1}일"] += " ⚠"  # 3일 초과 시 경고 표시
            else:
                consecutive_days = 0

    # 📌 **미오프 수당 표시 (필수 오프 못 채운 경우)**
    required_off = 8  # 예제: 한 달 최소 8개 OFF 필요
    for nurse in nurses_df.itertuples():
        off_count = sum([1 for day in range(num_days) if schedule_df.at[nurse.이름, f"{day+1}일"] == "🔴 OFF"])
        if off_count < required_off:
            missing_offs = required_off - off_count
            schedule_df.at[nurse.이름, "미오프"] = f"⚠ 미오프 {missing_offs}일"

    # 📌 **근무표 수정 가능 UI**
    st.write("### 📝 근무표 수정 (클릭하여 변경 가능)")
    edited_schedule = st.data_editor(schedule_df)

    # 📌 **엑셀 다운로드 기능 추가**
    st.write("📥 **근무표 엑셀 다운로드**")
    output_file = "nurse_schedule.xlsx"
    edited_schedule.to_excel(output_file)
    st.download_button(label="📥 근무표 다운로드", data=open(output_file, "rb"), file_name="근무표.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 📌 **최종 근무표 표시**
    st.write("### 📋 자동 생성된 근무표")
    st.dataframe(edited_schedule)
