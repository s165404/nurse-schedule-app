import streamlit as st
import pandas as pd
import random

# ⚡ Streamlit 설정
st.set_page_config(page_title="간호사 근무표 자동 생성기", layout="wide")

# ✅ 간호사 정보 저장 (세션 상태)
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# ✅ 엑셀 업로드 기능
st.sidebar.header("📂 엑셀 파일 업로드")
uploaded_file = st.sidebar.file_uploader("간호사 정보 엑셀 업로드", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)
    st.session_state.nurses = df_uploaded.to_dict(orient="records")
    st.sidebar.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")

# 📌 간호사 추가 함수
def add_nurse(name, id, work_type, charge, wanted_off, leave, public_holiday):
    st.session_state.nurses.append({
        "직원ID": id,
        "이름": name,
        "근무 유형": work_type,
        "Charge_가능": charge,
        "Wanted_Off": wanted_off,
        "휴가": leave,
        "공가": public_holiday
    })

# 📌 간호사 정보 입력
st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")
selected_nurse = st.sidebar.selectbox("수정할 간호사 선택", ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses])

if selected_nurse == "새 간호사 추가":
    name = st.sidebar.text_input("이름")
    id = st.sidebar.text_input("직원ID (숫자 입력)")
    work_type = st.sidebar.selectbox("근무 유형 선택", ["3교대 가능", "D Keep", "E Keep", "N Keep"])
    charge = st.sidebar.checkbox("⚡ Charge Nurse 가능")
    wanted_off = st.sidebar.text_area("Wanted Off (쉼표로 구분)")
    leave = st.sidebar.text_area("휴가 (쉼표로 구분)")
    public_holiday = st.sidebar.text_area("공가 (쉼표로 구분)")
    if st.sidebar.button("✅ 저장"):
        add_nurse(name, id, work_type, charge, wanted_off, leave, public_holiday)
        st.sidebar.success(f"{name} 간호사 정보가 저장되었습니다.")

# ✅ 간호사 정보 확인 (디버깅용)
st.write("📋 **현재 저장된 간호사 정보:**", st.session_state.nurses)

# ✅ 근무표 생성 버튼
st.title("📅 간호사 근무표 자동 생성기")
if st.button("📊 근무표 생성"):
    num_days = 30  # 기본 한 달 (조정 가능)
    schedule_df = pd.DataFrame(columns=["이름"] + [f"{i+1}일" for i in range(num_days)])

    # 간호사 정보 데이터프레임 변환
    nurses_df = pd.DataFrame(st.session_state.nurses)

    # ✅ 간호사 데이터 확인
    st.write("📝 **간호사 데이터 확인:**", nurses_df)

    if nurses_df.empty:
        st.error("⚠ 간호사 데이터가 없습니다! 간호사 정보를 추가해주세요.")
    else:
        # 🔥 Night 근무자 우선 배정
        night_nurses = nurses_df[nurses_df["근무 유형"] == "N Keep"]
        other_nurses = nurses_df[nurses_df["근무 유형"] != "N Keep"]
        
        for nurse in night_nurses.itertuples():
            for day in range(0, num_days, 3):  # 3일 간격 배정
                schedule_df.at[nurse.이름, f"{day+1}일"] = "N (C)"

        # 🔥 나머지 D/E 근무 배정
        for nurse in other_nurses.itertuples():
            work_days = random.sample(range(num_days), 10)  # 랜덤 근무 배정
            for day in work_days:
                shift = random.choice(["D", "E"])
                team = random.choice(["A", "B"])  # A팀 / B팀 랜덤 배정
                if nurse.Charge_가능:
                    schedule_df.at[nurse.이름, f"{day+1}일"] = f"{shift} (C)"
                else:
                    schedule_df.at[nurse.이름, f"{day+1}일"] = f"{shift} (A)"

        # ⚠ 연속 근무 초과 표시
        for nurse in nurses_df.itertuples():
            consecutive_days = 0
            for day in range(num_days):
                if pd.notna(schedule_df.at[nurse.이름, f"{day+1}일"]) and schedule_df.at[nurse.이름, f"{day+1}일"] != "🔴 OFF":
                    consecutive_days += 1
                    if consecutive_days > 3:
                        schedule_df.at[nurse.이름, f"{day+1}일"] += " ⚠"  # 3일 초과 시 경고 표시
                    if consecutive_days > 5:
                        schedule_df.at[nurse.이름, f"{day+1}일"] += " ⚠⚠"  # 5일 초과 시 강한 경고
                else:
                    consecutive_days = 0

        # 📌 가독성 개선을 위한 컬러 표시
        st.write("✏ **근무표 수정 (클릭하여 변경 가능)**")
        edited_schedule = st.experimental_data_editor(schedule_df)

        # 📥 **엑셀 다운로드 기능**
        st.download_button("📥 근무표 엑셀 다운로드", edited_schedule.to_csv(index=False).encode("utf-8"), "nurse_schedule.csv")

# 📌 자동 생성된 근무표 출력
st.subheader("📜 자동 생성된 근무표")
st.dataframe(schedule_df)
