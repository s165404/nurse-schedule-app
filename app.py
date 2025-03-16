import streamlit as st
import pandas as pd
import random

# 🌟 세션 상태 초기화
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 🌟 간호사 정보 업로드 (엑셀 파일)
st.sidebar.header("📂 간호사 정보 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)
    st.session_state.nurses = df_uploaded.to_dict(orient="records")
    st.sidebar.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")

# 🌟 간호사 수동 추가 및 수정
st.sidebar.header("🩺 간호사 추가 및 수정")
nurse_selection = st.sidebar.selectbox("수정할 간호사 선택", ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses])

nurse_data = {"이름": "", "직원ID": "", "근무 유형": "3교대 가능", "Charge 가능": "X", "Wanted Off": "", "휴가": "", "공가": ""}

if nurse_selection != "새 간호사 추가":
    for nurse in st.session_state.nurses:
        if nurse["이름"] == nurse_selection:
            nurse_data = nurse.copy()

nurse_data["이름"] = st.sidebar.text_input("이름", nurse_data["이름"])
nurse_data["직원ID"] = st.sidebar.text_input("직원ID (숫자 입력)", nurse_data["직원ID"])
nurse_data["근무 유형"] = st.sidebar.selectbox("근무 유형 선택", ["3교대 가능", "D Keep", "N Keep", "N 제외"], index=["3교대 가능", "D Keep", "N Keep", "N 제외"].index(nurse_data["근무 유형"]))
nurse_data["Charge 가능"] = st.sidebar.checkbox("⚡ Charge Nurse 가능", value=(nurse_data["Charge 가능"] == "O"))

nurse_data["Wanted Off"] = st.sidebar.text_input("Wanted Off (쉼표로 구분)", nurse_data["Wanted Off"])
nurse_data["휴가"] = st.sidebar.text_input("휴가 (쉼표로 구분)", nurse_data["휴가"])
nurse_data["공가"] = st.sidebar.text_input("공가 (쉼표로 구분)", nurse_data["공가"])

if st.sidebar.button("저장"):
    if nurse_selection == "새 간호사 추가":
        st.session_state.nurses.append(nurse_data)
    else:
        for i, nurse in enumerate(st.session_state.nurses):
            if nurse["이름"] == nurse_selection:
                st.session_state.nurses[i] = nurse_data
    st.sidebar.success("✅ 간호사 정보가 저장되었습니다!")

# 🌟 간호사 정보 확인
st.write("📋 현재 저장된 간호사 정보:")
st.write(st.session_state.nurses)

# 🌟 근무표 생성 로직
if st.button("📅 근무표 생성"):
    if not st.session_state.nurses:
        st.warning("⚠ 간호사 정보를 먼저 입력하세요!")
    else:
        df_nurses = pd.DataFrame(st.session_state.nurses)
        df_nurses["직원ID"] = pd.to_numeric(df_nurses["직원ID"], errors="coerce").fillna(9999).astype(int)
        df_nurses = df_nurses.sort_values(by="직원ID")

        days_in_month = 30  # 월별 일 수 (나중에 설정 가능)
        off_days = {}

        for nurse in df_nurses.itertuples():
            wanted_off = str(getattr(nurse, "Wanted_Off", "")).split(",") if pd.notna(getattr(nurse, "Wanted_Off", "")) else []
            vacation = str(getattr(nurse, "휴가", "")).split(",") if pd.notna(getattr(nurse, "휴가", "")) else []
            official_off = str(getattr(nurse, "공가", "")).split(",") if pd.notna(getattr(nurse, "공가", "")) else []
            off_days[nurse.이름] = set(wanted_off + vacation + official_off)

        schedule_df = pd.DataFrame(index=df_nurses["이름"], columns=[f"{i+1}일" for i in range(days_in_month)])

        for day in range(days_in_month):
            d_count, e_count, n_count = 0, 0, 0
            d_charge, e_charge, n_charge = 0, 0, 0

            for nurse in df_nurses.itertuples():
                if f"{day+1}" in off_days[nurse.이름]:
                    schedule_df.at[nurse.이름, f"{day+1}일"] = "OFF"
                    continue

                if n_count < 2 and nurse.근무유형 in ["N Keep", "3교대 가능"]:
                    shift = "N"
                    n_count += 1
                    if nurse.Charge_가능 == "O":
                        shift += " (C)"
                        n_charge += 1
                elif d_count < 4:
                    shift = "D"
                    d_count += 1
                    if nurse.Charge_가능 == "O" and d_charge < 2:
                        shift += " (C)"
                        d_charge += 1
                elif e_count < 4:
                    shift = "E"
                    e_count += 1
                    if nurse.Charge_가능 == "O" and e_charge < 2:
                        shift += " (C)"
                        e_charge += 1
                else:
                    shift = "OFF"

                schedule_df.at[nurse.이름, f"{day+1}일"] = shift

        st.write("📋 자동 생성된 근무표:")
        st.dataframe(schedule_df)

        # 🌟 근무표 엑셀 다운로드 기능
        st.download_button("📥 근무표 엑셀 다운로드", schedule_df.to_csv(index=True).encode("utf-8"), file_name="근무표.csv", mime="text/csv")
