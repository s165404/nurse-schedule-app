import streamlit as st
import pandas as pd

# 🚀 간호사 데이터 세션 저장 (세션 유지)
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 📌 엑셀 파일 업로드 기능 (우선순위 자동 반영)
st.sidebar.header("📤 간호사 정보 불러오기 (엑셀 업로드)")
uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드 (xlsx)", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)
    if "우선순위" in df_uploaded.columns:
        df_uploaded = df_uploaded.sort_values(by="우선순위")
    st.session_state.nurses = df_uploaded.to_dict(orient="records")
    st.sidebar.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")

# 📌 간호사 추가 및 수정 섹션
st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")
selected_nurse = st.sidebar.selectbox("수정할 간호사 선택", ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses])

if selected_nurse == "새 간호사 추가":
    name = st.sidebar.text_input("이름")
    nurse_id = st.sidebar.text_input("직원 ID (숫자 입력)")
    work_type = st.sidebar.selectbox("근무 유형 선택", ["D Keep", "E Keep", "N Keep", "3교대 가능", "N 제외"])
    can_charge = st.sidebar.checkbox("⚡ Charge Nurse 가능")
    can_acting = st.sidebar.checkbox("🩺 Acting Nurse 가능")
    night_charge_only = st.sidebar.checkbox("🌙 N 근무 시 Charge Nurse 가능")
    wanted_off = st.sidebar.text_area("Wanted Off (쉼표로 구분)")
    leave = st.sidebar.text_area("휴가 (쉼표로 구분)")
    public_holiday = st.sidebar.text_area("공가 (쉼표로 구분)")

    if st.sidebar.button("저장"):
        st.session_state.nurses.append({
            "이름": name, "직원ID": nurse_id, "근무 유형": work_type,
            "Charge 가능": "O" if can_charge else "",
            "Acting 가능": "O" if can_acting else "",
            "N 차지 전용": "O" if night_charge_only else "",
            "Wanted Off": wanted_off, "휴가": leave, "공가": public_holiday
        })
        st.sidebar.success(f"✅ {name} 간호사 정보가 저장되었습니다!")

# 📌 우선순위 조정 기능 (드래그)
st.write("📋 **현재 간호사 우선순위 목록 (순서를 조정하세요)**")
nurse_names = [n["이름"] for n in st.session_state.nurses]
new_order = st.experimental_data_editor(pd.DataFrame(nurse_names, columns=["이름"]))

if st.button("🔄 순서 업데이트"):
    new_nurses_ordered = []
    for new_name in new_order["이름"]:
        for nurse in st.session_state.nurses:
            if nurse["이름"] == new_name:
                new_nurses_ordered.append(nurse)
    st.session_state.nurses = new_nurses_ordered
    st.success("✅ 간호사 우선순위가 성공적으로 업데이트되었습니다!")

# 📌 근무표 자동 생성 로직
st.header("📅 간호사 근무표 자동 생성기")

if st.button("📊 근무표 생성"):
    nurses_df = pd.DataFrame(st.session_state.nurses)
    charge_nurses = nurses_df[nurses_df["Charge 가능"] == "O"]
    acting_nurses = nurses_df[nurses_df["Acting 가능"] == "O"]
    night_charge_only = nurses_df[nurses_df["N 차지 전용"] == "O"]

    num_days = 30  # 기본 한 달 30일 설정
    schedule_df = pd.DataFrame(index=nurses_df["이름"], columns=[f"{i+1}일" for i in range(num_days)])

    # 📌 Acting Nurse 배치 (각 팀당 1명씩)
    team_tracking = {}  # 인터벌 시 팀 유지 기능을 위한 딕셔너리
    for day in range(num_days):
        for nurse in acting_nurses.itertuples():
            if nurse.이름 in team_tracking:
                schedule_df.at[nurse.이름, f"{day+1}일"] = f"Acting({team_tracking[nurse.이름]})"
            else:
                assigned_team = "A" if day % 2 == 0 else "B"
                team_tracking[nurse.이름] = assigned_team
                schedule_df.at[nurse.이름, f"{day+1}일"] = f"Acting({assigned_team})"

    # 📌 Charge Nurse 배치 (매 근무 필수 2명)
    for day in range(num_days):
        charge_candidates = charge_nurses.sample(min(len(charge_nurses), 2))
        schedule_df.loc[charge_candidates["이름"], f"{day+1}일"] = "Charge"

    # 📌 N 근무 배치 (N 차지 전용 필드 활용)
    for day in range(num_days):
        night_candidates = night_charge_only.sample(min(len(night_charge_only), 2))
        schedule_df.loc[night_candidates["이름"], f"{day+1}일"] = "N (C)"

    # 📌 근무표 수정 기능 추가
    st.write("### 📝 근무표 수정 (클릭하여 변경)")
    edited_schedule = st.experimental_data_editor(schedule_df)

    # 📌 엑셀 다운로드 버튼 추가
    st.write("📥 **근무표 엑셀 다운로드**")
    output_file = "nurse_schedule.xlsx"
    edited_schedule.to_excel(output_file)
    st.download_button(label="📥 근무표 다운로드", data=open(output_file, "rb"), file_name="근무표.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 📌 최종 근무표 표시
    st.write("### 📋 자동 생성된 근무표")
    st.dataframe(edited_schedule)
