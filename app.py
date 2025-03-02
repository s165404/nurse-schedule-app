import streamlit as st
import pandas as pd
import io
import calendar
from datetime import datetime

# 🔄 우선순위 부여 함수 (직원ID 기준 정렬)
def assign_priority(nurses):
    for nurse in nurses:
        if "직원ID" not in nurse or nurse["직원ID"] is None or pd.isna(nurse["직원ID"]):
            nurse["직원ID"] = "9999"
        elif isinstance(nurse["직원ID"], str) and not nurse["직원ID"].isdigit():
            nurse["직원ID"] = "9999"
        else:
            nurse["직원ID"] = str(nurse["직원ID"])  

    nurses.sort(key=lambda x: int(x["직원ID"]))  

    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1  

# 📂 간호사 정보 불러오기 (엑셀 파일 업로드 기능 추가)
st.sidebar.subheader("📂 간호사 정보 불러오기")
uploaded_file = st.sidebar.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)

    df_uploaded = df_uploaded.fillna("").astype(str)  

    required_columns = ["직원ID", "이름", "근무 유형", "Charge 가능", "Wanted Off", "휴가", "공가"]
    
    if all(col in df_uploaded.columns for col in required_columns):
        st.session_state.nurses = df_uploaded.to_dict(orient="records")  

        st.write("📋 현재 저장된 간호사 목록:", st.session_state.nurses)

        if st.session_state.nurses:
            assign_priority(st.session_state.nurses)  
            st.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")
        else:
            st.warning("📢 업로드된 간호사 데이터가 없습니다. 엑셀 파일을 확인하세요.")
    else:
        st.error("⚠️ 엑셀 파일의 형식이 올바르지 않습니다. 올바른 컬럼을 포함하고 있는지 확인하세요.")

# 📌 **사용자가 연도와 월을 선택할 수 있도록 UI 추가**
st.sidebar.subheader("📅 근무표 연도 및 월 선택")
selected_year = st.sidebar.number_input("연도 선택", min_value=2024, max_value=2030, value=datetime.now().year)
selected_month = st.sidebar.number_input("월 선택", min_value=1, max_value=12, value=datetime.now().month)

# 해당 월의 일수 가져오기
days_in_month = calendar.monthrange(selected_year, selected_month)[1]

# 🔹 **월별 근무표 생성 함수**
def generate_monthly_schedule(nurses, days=30):
    # N Keep 간호사를 아래로 정렬
    n_keep_nurses = [n for n in nurses if n["근무 유형"] == "N Keep"]
    other_nurses = [n for n in nurses if n["근무 유형"] != "N Keep"]
    nurses_sorted = sorted(other_nurses, key=lambda x: int(x["직원ID"])) + sorted(n_keep_nurses, key=lambda x: int(x["직원ID"]))

    schedule_dict = {f"{n['이름']} ({n['근무 유형']})": [""] * days for n in nurses_sorted}  # 초기 빈 근무표
    shift_order = ["D", "E", "N", "OFF"]
    night_count = {n["이름"]: 0 for n in nurses_sorted}  # 나이트 연속 근무 확인용

    for day in range(days):
        charge_nurses = [n for n in nurses_sorted if n["Charge 가능"] == "O"]

        for i, nurse in enumerate(nurses_sorted):
            # 📌 나이트 3연속 제한 (이전 3일간 나이트였으면 강제 OFF)
            if night_count[nurse["이름"]] >= 3:
                assigned_shift = "OFF"
                night_count[nurse["이름"]] = 0  # 연속 카운트 초기화
            else:
                if nurse["근무 유형"] == "D Keep":
                    assigned_shift = "D"
                elif nurse["근무 유형"] == "E Keep":
                    assigned_shift = "E"
                elif nurse["근무 유형"] == "N Keep":
                    assigned_shift = "N"
                    night_count[nurse["이름"]] += 1  # 나이트 근무 카운트 증가
                else:
                    assigned_shift = shift_order[(i + day) % len(shift_order)]  # 한 달 순환

            # 📌 Wanted Off 적용
            if "Wanted Off" in nurse and str(day + 1) in nurse["Wanted Off"].split(", "):
                assigned_shift = "OFF"

            # 📌 Charge Nurse 배치 (2명 유지)
            is_charge = False
            if assigned_shift == "N":
                # 🔹 나이트 근무 시 "3교대 가능"인 사람은 자동으로 차지 가능
                if nurse["근무 유형"] == "3교대 가능":
                    is_charge = True
            else:
                # 🔹 일반 근무 시에는 "Charge 가능"이 O인 사람만 차지 가능
                if len([n for n in schedule_dict.keys() if schedule_dict[n][day] == f"{assigned_shift} (C)"]) < 2:
                    if nurse in charge_nurses:
                        is_charge = True

            # 🔹 OFF에는 차지 표시 ❌
            schedule_dict[f"{nurse['이름']} ({nurse['근무 유형']})"][day] = f"{assigned_shift} {'(C)' if is_charge and assigned_shift != 'OFF' else ''}"

    # 📌 pandas DataFrame으로 변환하여 가로로 날짜, 세로로 직원 배치
    schedule_df = pd.DataFrame(schedule_dict).T
    schedule_df.columns = [f"{selected_month}월 {d+1}일" for d in range(days)]
    schedule_df.insert(0, "이름", schedule_df.index)  # 직원명 컬럼 추가
    schedule_df.reset_index(drop=True, inplace=True)  # 인덱스 초기화

    return schedule_df

# 📅 근무표 생성 버튼 추가
st.header(f"📅 {selected_year}년 {selected_month}월 간호사 근무표 자동 생성기")
if st.button("📌 근무표 생성"):
    if "nurses" in st.session_state and st.session_state.nurses:
        schedule_df = generate_monthly_schedule(st.session_state.nurses, days_in_month)

        st.write(f"📌 **{selected_year}년 {selected_month}월 생성된 근무표 (가독성 개선)**")
        st.dataframe(schedule_df)  

        # 📥 생성된 근무표 다운로드 기능 추가
        output_schedule = io.BytesIO()
        with pd.ExcelWriter(output_schedule, engine="xlsxwriter") as writer:
            schedule_df.to_excel(writer, index=False, sheet_name=f"{selected_month}월 근무표")
        output_schedule.seek(0)

        st.download_button(
            label="📥 근무표 다운로드",
            data=output_schedule,
            file_name=f"nurse_schedule_{selected_year}_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ 간호사 정보를 먼저 업로드하세요!")
