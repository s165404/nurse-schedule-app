import streamlit as st
import pandas as pd
import io
import random

st.title("🏥 간호사 근무표 자동 생성기")

st.sidebar.header("👩‍⚕️ 간호사 추가")
if "nurses" not in st.session_state:
    st.session_state.nurses = []

name = st.sidebar.text_input("이름")
staff_id = st.sidebar.text_input("직원ID")
shift_type = st.sidebar.selectbox("근무 유형", ["3교대 가능", "D Keep", "E Keep", "N Keep"])
charge = st.sidebar.checkbox("Charge Nurse 가능")
acting = st.sidebar.checkbox("Acting Nurse 가능")
n_keep = st.sidebar.checkbox("N Keep (야간 선호)")
wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)")
vacation = st.sidebar.text_input("휴가 (쉼표로 구분)")
priority = st.sidebar.number_input("우선순위 (낮을수록 우선 배정)", min_value=1, step=1)

if st.sidebar.button("간호사 추가"):
    st.session_state.nurses.append({
        "직원ID": staff_id,
        "이름": name,
        "근무 유형": shift_type,
        "Charge 가능": "O" if charge else "X",
        "Acting 가능": "O" if acting else "X",
        "N Keep": "O" if n_keep else "X",
        "Wanted Off": wanted_off,
        "휴가": vacation,
        "우선순위": priority
    })

if st.session_state.nurses:
    df_nurse_info = pd.DataFrame(st.session_state.nurses).sort_values(by="우선순위")
    st.write("### 🏥 간호사 목록")
    st.dataframe(df_nurse_info)

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

    for nurse in df_schedule.index:
        for i in range(1, len(df_schedule.columns)):
            prev_shift = df_schedule.at[nurse, df_schedule.columns[i-1]]
            current_shift = df_schedule.at[nurse, df_schedule.columns[i]]
            if prev_shift == "N" and current_shift in ["D", "E"]:
                df_schedule.at[nurse, df_schedule.columns[i]] = "OFF"

    st.write("### 📅 생성된 근무표")
    st.dataframe(df_schedule)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_nurse_info.to_excel(writer, sheet_name="간호사 정보", index=False)
        df_schedule.to_excel(writer, sheet_name="근무표", index=True)
    output.seek(0)

    st.download_button(label="📥 근무표 다운로드 (Excel)", data=output, file_name="nurse_schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.write("✅ 간호사 정보를 입력하고 '근무표 생성' 버튼을 눌러보세요!")
