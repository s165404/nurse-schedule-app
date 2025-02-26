import streamlit as st
import pandas as pd
import io
import random

st.title("🏥 간호사 근무표 자동 생성기")

st.sidebar.header("👩‍⚕️ 간호사 추가 및 수정")

# 세션 상태에 간호사 정보 저장
if "nurses" not in st.session_state:
    st.session_state.nurses = []

# 직원ID가 작은 순서대로 우선순위를 자동 부여하는 함수
def assign_priority(nurses):
    # 직원ID를 숫자로 변환하여 정렬 (ID가 작은 순 -> 우선순위 높음)
    nurses.sort(key=lambda x: int(x["직원ID"]))
    # 정렬된 순서대로 우선순위 부여 (1부터 시작)
    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1

# 사이드바에서 "새 간호사 추가" 또는 기존 간호사 중 선택
selected_nurse = st.sidebar.selectbox(
    "수정할 간호사 선택",
    ["새 간호사 추가"] + [n["이름"] for n in st.session_state.nurses]
)

# 선택된 간호사의 정보를 가져오거나, 새 간호사 정보를 입력받기
if selected_nurse == "새 간호사 추가":
    name = st.sidebar.text_input("이름", "")
    staff_id = st.sidebar.text_input("직원ID", "")
    # 근무 유형: N Keep, N 제외, D/E Keep, 3교대 가능 등
    shift_type = st.sidebar.selectbox("근무 유형", ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"])
    charge = st.sidebar.checkbox("Charge Nurse 가능")
    acting = st.sidebar.checkbox("Acting Nurse 가능")
    wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)", "")
    vacation = st.sidebar.text_input("휴가 (쉼표로 구분)", "")
    public_leave = st.sidebar.text_input("공가 (쉼표로 구분)", "")
else:
    # 기존 간호사 정보 불러오기
    nurse_data = next(n for n in st.session_state.nurses if n["이름"] == selected_nurse)
    name = st.sidebar.text_input("이름", nurse_data["이름"])
    staff_id = st.sidebar.text_input("직원ID", nurse_data["직원ID"])
    shift_type_list = ["3교대 가능", "D Keep", "E Keep", "N Keep", "N 제외"]
    shift_type = st.sidebar.selectbox("근무 유형", shift_type_list, index=shift_type_list.index(nurse_data["근무 유형"]))
    charge = st.sidebar.checkbox("Charge Nurse 가능", value=(nurse_data["Charge 가능"] == "O"))
    acting = st.sidebar.checkbox("Acting Nurse 가능", value=(nurse_data["Acting 가능"] == "O"))
    wanted_off = st.sidebar.text_input("Wanted Off (쉼표로 구분)", nurse_data.get("Wanted Off", ""))
    vacation = st.sidebar.text_input("휴가 (쉼표로 구분)", nurse_data.get("휴가", ""))
    public_leave = st.sidebar.text_input("공가 (쉼표로 구분)", nurse_data.get("공가", ""))

# "✅ 저장" 버튼: 새 간호사 추가 or 기존 간호사 수정
if st.sidebar.button("✅ 저장"):
    if selected_nurse == "새 간호사 추가":
        # 새 간호사 정보 추가
        st.session_state.nurses.append({
            "직원ID": staff_id,
            "이름": name,
            "근무 유형": shift_type,
            "Charge 가능": "O" if charge else "X",
            "Acting 가능": "O" if acting else "X",
            "Wanted Off": wanted_off,
            "휴가": vacation,
            "공가": public_leave,
        })
    else:
        # 기존 간호사 정보 수정
        for nurse in st.session_state.nurses:
            if nurse["이름"] == selected_nurse:
                nurse["직원ID"] = staff_id
                nurse["근무 유형"] = shift_type
                nurse["Charge 가능"] = "O" if charge else "X"
                nurse["Acting 가능"] = "O" if acting else "X"
                nurse["Wanted Off"] = wanted_off
                nurse["휴가"] = vacation
                nurse["공가"] = public_leave

    # 직원ID 기준으로 우선순위 자동 설정
    assign_priority(st.session_state.nurses)

# 간호사 목록 표시
if st.session_state.nurses:
    df_nurse_info = pd.DataFrame(st.session_state.nurses)
    st.write("### 🏥 간호사 목록 (직원ID 작은 순으로 우선순위)")
    st.dataframe(df_nurse_info)

# 근무표 생성 버튼
if st.button("📅 근무표 생성"):
    # 우선순위대로 정렬 (이미 assign_priority 했으므로, 우선순위 순 정렬)
    df_nurse_info = df_nurse_info.sort_values(by="우선순위")

    # 날짜 컬럼 생성 (1일 ~ 30일 예시)
    dates = [str(i) + "일" for i in range(1, 31)]
    # 근무표 데이터프레임 (행=간호사 이름, 열=날짜)
    df_schedule = pd.DataFrame(index=df_nurse_info["이름"], columns=dates)
    df_schedule[:] = ""

    # 1) Charge & Acting 먼저 배정
    charge_nurses = df_nurse_info[df_nurse_info["Charge 가능"] == "O"]["이름"].tolist()
    acting_nurses = df_nurse_info[df_nurse_info["Acting 가능"] == "O"]["이름"].tolist()

    for date in df_schedule.columns:
        # 하루에 Charge 2명
        charge_assigned = 0
        for nurse in charge_nurses:
            if df_schedule.at[nurse, date] == "":
                df_schedule.at[nurse, date] = "Charge"
                charge_assigned += 1
            if charge_assigned >= 2:
                break

        # 하루에 Acting 2명
        acting_assigned = 0
        for nurse in acting_nurses:
            if df_schedule.at[nurse, date] == "":
                df_schedule.at[nurse, date] = "Acting"
                acting_assigned += 1
            if acting_assigned >= 2:
                break

    # 2) 근무 유형(D/E/N) 배정
    for date in df_schedule.columns:
        for _, row in df_nurse_info.iterrows():
            nurse = row["이름"]
            if df_schedule.at[nurse, date] in ["Charge", "Acting"]:
                continue  # 이미 배정됨

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
                df_schedule.at[nurse, date] = random.choice(["D", "E"])  # N 배제

    # 3) Wanted Off / 휴가 / 공가를 OFF로 처리
    for _, row in df_nurse_info.iterrows():
        nurse = row["이름"]
        # Wanted Off
        if isinstance(row.get("Wanted Off"), str):
            for day in row["Wanted Off"].split(", "):
                if day in df_schedule.columns:
                    df_schedule.at[nurse, day] = "OFF"

        # 휴가
        if isinstance(row.get("휴가"), str):
            for day in row["휴가"].split(", "):
                if day in df_schedule.columns:
                    df_schedule.at[nurse, day] = "OFF"

        # 공가
        if isinstance(row.get("공가"), str):
            for day in row["공가"].split(", "):
                if day in df_schedule.columns:
                    df_schedule.at[nurse, day] = "OFF"

    # 4) N 후 D/E 금지 시 OFF
    for nurse in df_schedule.index:
        for i in range(1, len(df_schedule.columns)):
            prev_shift = df_schedule.at[nurse, df_schedule.columns[i-1]]
            current_shift = df_schedule.at[nurse, df_schedule.columns[i]]
            if prev_shift == "N" and current_shift in ["D", "E"]:
                df_schedule.at[nurse, df_schedule.columns[i]] = "OFF"

    # 최종 근무표 출력
    st.write("### 📅 생성된 근무표")
    st.dataframe(df_schedule)

    # 엑셀 다운로드 기능
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_nurse_info.to_excel(writer, sheet_name="간호사 정보", index=False)
        df_schedule.to_excel(writer, sheet_name="근무표", index=True)
    output.seek(0)

    st.download_button(
        label="📥 근무표 다운로드 (Excel)",
        data=output,
        file_name="nurse_schedule.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.write("✅ 간호사 정보를 입력하고 '근무표 생성' 버튼을 눌러보세요!")
