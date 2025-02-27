import streamlit as st
import pandas as pd
import io
import random

st.title("🏥 간호사 근무표 자동 생성기")

st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")

if "nurses" not in st.session_state:
    st.session_state.nurses = []

def assign_priority(nurses):
    for nurse in nurses:
        if not nurse["직원ID"].isdigit():  # 직원ID가 숫자가 아니거나 빈 값이면 기본값 설정
            nurse["직원ID"] = "9999"  # 임시로 가장 낮은 우선순위 부여

    nurses.sort(key=lambda x: int(x["직원ID"]))  # 이제 변환 가능
    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1

selected_nurse = st.sidebar.selectbox(
    "수정할 간호사 선택",
    ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses]
)

if selected_nurse == "새 간호사 추가":
    name = st.sidebar.text_input("이름", "")
    staff_id = st.sidebar.text_input("직원ID", "")
    shift_type = st.sidebar.selectbox("근무 유형", ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"])
    charge = st.sidebar.checkbox("Charge Nurse 가능")  # Acting Nurse 제거
    wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)", "")
    vacation = st.sidebar.text_input("휴가 (쉼표로 구분)", "")
    public_leave = st.sidebar.text_input("공가 (쉼표로 구분)", "")
else:
    nurse_data = next(n for n in st.session_state.nurses if n["이름"] == selected_nurse)
    name = st.sidebar.text_input("이름", nurse_data["이름"])
    staff_id = st.sidebar.text_input("직원ID", nurse_data["직원ID"])
    shift_type = st.sidebar.selectbox("근무 유형", ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"], index=["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"].index(nurse_data["근무 유형"]))
    charge = st.sidebar.checkbox("Charge Nurse 가능", value=(nurse_data["Charge 가능"] == "O"))
    wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)", nurse_data.get("Wanted Off", ""))
    vacation = st.sidebar.text_input("휴가 (쉼표로 구분)", nurse_data.get("휴가", ""))
    public_leave = st.sidebar.text_input("공가 (쉼표로 구분)", nurse_data.get("공가", ""))

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

if st.button("📅 근무표 생성"):
    if not st.session_state.nurses:
        st.warning("간호사가 없습니다. 먼저 간호사를 추가해주세요.")
        st.stop()

    df_nurse_info = pd.DataFrame(st.session_state.nurses).sort_values(by="우선순위")
    dates = [str(i) + "일" for i in range(1, 31)]
    df_schedule = pd.DataFrame(index=df_nurse_info["이름"], columns=dates)
    df_schedule[:] = ""

    charge_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "O"]["이름"].tolist()

    if len(charge_nurses) < 2:
        st.error("⚠️ Charge Nurse 인원이 부족합니다! 최소 2명 이상 필요합니다.")
        st.stop()

    for date in df_schedule.columns:
        charge_assigned = 0
        for nurse in charge_nurses:
            if df_schedule.at[nurse, date] == "":
                df_schedule.at[nurse, date] = f"{random.choice(['D', 'E', 'N'])} (C)"
                charge_assigned += 1
            if charge_assigned >= 2:
                break

        if charge_assigned < 2:
            st.error(f"⚠️ {date}에 Charge Nurse가 2명 이하로 배정되었습니다. Charge Nurse를 추가해주세요!")
            st.stop()

    for date in df_schedule.columns:
        for _, row in df_nurse_info.iterrows():
            nurse = row["이름"]
            if df_schedule.at[nurse, date]:
                continue
            shift_type = row["근무 유형"]
            if shift_type == "3교대 가능":
                df_schedule.at[nurse, date] = random.choice(["D", "E", "N"])
            elif shift_type == "D Keep":
                df_schedule.at[nurse, date] = "D"
            elif shift_type == "E Keep":
                df_schedule.at[nurse, date] = "E"
            elif shift_type == "N Keep":
                df_schedule.at[nurse, date] = "N"
            elif shift_type == "N 제외":
                df_schedule.at[nurse, date] = random.choice(["D", "E"])

    st.write("### 📅 생성된 근무표")
    st.dataframe(df_schedule)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_nurse_info.to_excel(writer, sheet_name="간호사 정보", index=False)
        df_schedule.to_excel(writer, sheet_name="근무표", index=True)
    output.seek(0)

    st.download_button("📥 근무표 다운로드 (Excel)", data=output, file_name="nurse_schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
