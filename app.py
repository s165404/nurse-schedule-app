import streamlit as st
import pandas as pd
import io
import random

st.title("🏥 간호사 근무표 자동 생성기")

st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")

if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 직원 ID를 숫자로 변환하고 우선순위 자동 설정
def assign_priority(nurses):
    nurses.sort(key=lambda x: int(x["직원ID"]))  # 직원ID가 작은 순서대로 정렬
    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1  # 자동으로 우선순위 부여

# 기존 간호사 정보 표시 및 수정 기능 추가
selected_nurse = st.sidebar.selectbox("수정할 간호사 선택", ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses])

if selected_nurse == "새 간호사 추가":
    name = st.sidebar.text_input("이름", "")
    staff_id = st.sidebar.text_input("직원ID", "")
    shift_type = st.sidebar.selectbox("근무 유형", ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"])
    charge = st.sidebar.checkbox("Charge Nurse 가능")
    acting = st.sidebar.checkbox("Acting Nurse 가능")
    wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)", "")
    vacation = st.sidebar.text_input("휴가 (쉼표로 구분)", "")
else:
    nurse_data = next(n for n in st.session_state.nurses if n["이름"] == selected_nurse)
    name = st.sidebar.text_input("이름", nurse_data["이름"])
    staff_id = st.sidebar.text_input("직원ID", nurse_data["직원ID"])
    shift_type = st.sidebar.selectbox("근무 유형", ["3교대 가능", "D Keep", "E Keep", "N Keep"], index=["3교대 가능", "D Keep", "E Keep", "N Keep"].index(nurse_data["근무 유형"]))
    charge = st.sidebar.checkbox("Charge Nurse 가능", value=(nurse_data["Charge 가능"] == "O"))
    acting = st.sidebar.checkbox("Acting Nurse 가능", value=(nurse_data["Acting 가능"] == "O"))
    wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)", nurse_data["Wanted Off"])
    vacation = st.sidebar.text_input("휴가 (쉼표로 구분)", nurse_data["휴가"])

# 추가 및 수정 버튼
if st.sidebar.button("✅ 저장"):
    if selected_nurse == "새 간호사 추가":
        st.session_state.nurses.append({
            "직원ID": staff_id,
            "이름": name,
            "근무 유형": shift_type,
            "Charge 가능": "O" if charge else "X",
            "Acting 가능": "O" if acting else "X",
            "Wanted Off": wanted_off,
            "휴가": vacation,
        })
    else:
        for nurse in st.session_state.nurses:
            if nurse["이름"] == selected_nurse:
                nurse["직원ID"] = staff_id
                nurse["근무 유형"] = shift_type
                nurse["Charge 가능"] = "O" if charge else "X"
                nurse["Acting 가능"] = "O" if acting else "X"
                nurse["Wanted Off"] = wanted_off
                nurse["휴가"] = vacation

    # 우선순위 자동 설정
    assign_priority(st.session_state.nurses)

# 간호사 리스트 출력
if st.session_state.nurses:
    df_nurse_info = pd.DataFrame(st.session_state.nurses)
    st.write("### 🏥 간호사 목록 (우선순위 자동 적용)")
    st.dataframe(df_nurse_info)

# 근무표 자동 생성 버튼
if st.button("📅 근무표 생성"):
    dates = [str(i) + "일" for i in range(1, 31)]
    df_schedule = pd.DataFrame(index=df_nurse_info["이름"], columns=dates)
    df_schedule[:] = ""

    charge_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "O"]["이름"].tolist()
    acting_nurses = df_nurse_info[df_nurse_info["Acting 가능"] == "O"]["이름"].tolist()

    for date in df_schedule.columns:
        charge_assigned = 0
        for nurse in charge_nurses:
            if df_schedule.at[nurse, date] == "":
                df_schedule.at[nurse, date] = "Charge"
                charge_assigned += 1
            if charge_assigned >= 2:
                break

        acting_assigned = 0
        for nurse in acting_nurses:
            if df_schedule.at[nurse, date] == "":
                df_schedule.at[nurse, date] = "Acting"
                acting_assigned += 1
            if acting_assigned >= 2:
                break

    for date in df_schedule.columns:
        for _, row in df_nurse_info.iterrows():
            nurse = row["이름"]
            shift_type = row["근무 유형"]
            if df_schedule.at[nurse, date] in ["Charge", "Acting"]:
                continue

            if shift_type == "3교대 가능":
                df_schedule.at[nurse, date] = random.choice(["D", "E", "N"])
            elif shift_type == "D Keep":
                df_schedule.at[nurse, date] = "D"
            elif shift_type == "E Keep":
                df_schedule.at[nurse, date] = "E"
            elif shift_type == "N Keep":
                df_schedule.at[nurse, date] = "N"
            elif shift_type == "N 제외":
                df_schedule.at[nurse, date] = random.choice(["D", "E"]) # N을 배제
            
    for _, row in df_nurse_info.iterrows():
        nurse = row["이름"]
        if isinstance(row["Wanted Off"], str):
            for day in row["Wanted Off"].split(", "):
                if day in df_schedule.columns:
                    df_schedule.at[nurse, day] = "OFF"
        if isinstance(row["휴가"], str):
            for day in row["휴가"].split(", "):
                if day in df_schedule.columns:
                    df_schedule.at[nurse, day] = "OFF"

    st.write("### 📅 생성된 근무표")
    st.dataframe(df_schedule)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_nurse_info.to_excel(writer, sheet_name="간호사 정보", index=False)
        df_schedule.to_excel(writer, sheet_name="근무표", index=True)
    output.seek(0)

    st.download_button(label="📥 근무표 다운로드 (Excel)", data=output, file_name="nurse_schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.write("✅ 간호사 정보를 입력하고 '근무표 생성' 버튼을 눌러보세요!")
