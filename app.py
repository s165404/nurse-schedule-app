import streamlit as st
import pandas as pd
import io
import calendar
import requests
from datetime import datetime

# 📌 공휴일 API 호출 함수
def get_korean_holidays(year, month):
    API_KEY = "uUphF3Bca10axnyQuJxIvmJvJmK%2FhEm%2BHscgxCBiUFTL0GIYDsAtRT7aBgDxX7N66Ps76L4Y3ZgwQjbRXzmsEQ%3D%3D"  # 🔹 공공데이터포털에서 발급받은 API 키 입력
    url = f"https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?solYear={year}&solMonth={str(month).zfill(2)}&ServiceKey={API_KEY}&_type=json"

    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        try:
            holidays = [int(item['locdate']) % 100 for item in data['response']['body']['items']['item']]
            return holidays
        except KeyError:
            return []
    else:
        return []

# 📌 우선순위 부여 함수
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

# 📂 간호사 정보 불러오기
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
            st.warning("📢 업로드된 간호사 데이터가 없습니다.")
    else:
        st.error("⚠️ 엑셀 파일의 형식이 올바르지 않습니다.")

# 📌 연도 및 월 선택 UI 추가
st.sidebar.subheader("📅 근무표 연도 및 월 선택")
selected_year = st.sidebar.number_input("연도 선택", min_value=2024, max_value=2030, value=datetime.now().year)
selected_month = st.sidebar.number_input("월 선택", min_value=1, max_value=12, value=datetime.now().month)

# 📌 공휴일 자동 조회
holiday_list = get_korean_holidays(selected_year, selected_month)
days_in_month = calendar.monthrange(selected_year, selected_month)[1]
num_weekends = sum(1 for d in range(days_in_month) if calendar.weekday(selected_year, selected_month, d+1) in [5, 6])
required_offs = num_weekends + len(holiday_list)  # 필수 OFF 수 계산

# 🔹 **월별 근무표 생성 함수**
def generate_monthly_schedule(nurses, days=30):
    n_keep_nurses = [n for n in nurses if n["근무 유형"] == "N Keep"]
    other_nurses = [n for n in nurses if n["근무 유형"] != "N Keep"]
    nurses_sorted = sorted(other_nurses, key=lambda x: int(x["직원ID"])) + sorted(n_keep_nurses, key=lambda x: int(x["직원ID"]))

    schedule_dict = {f"{n['이름']} ({n['근무 유형']})": [""] * days for n in nurses_sorted}  
    shift_order = ["D", "E", "N", "OFF"]
    night_count = {n["이름"]: 0 for n in nurses_sorted}  

    for day in range(days):
        is_holiday = (day + 1) in holiday_list  
        weekday = calendar.weekday(selected_year, selected_month, day + 1)  
        charge_nurses = [n for n in nurses_sorted if n["Charge 가능"] == "O"]

        for i, nurse in enumerate(nurses_sorted):
            if night_count[nurse["이름"]] >= 3:
                assigned_shift = "OFF"
                night_count[nurse["이름"]] = 0  
            else:
                if nurse["근무 유형"] == "D Keep":
                    assigned_shift = "D"
                elif nurse["근무 유형"] == "E Keep":
                    assigned_shift = "E"
                elif nurse["근무 유형"] == "N Keep":
                    assigned_shift = "N"
                    night_count[nurse["이름"]] += 1
                else:
                    assigned_shift = shift_order[(i + day) % len(shift_order)]

            if nurse["근무 유형"] == "N 제외" and assigned_shift == "N":
                assigned_shift = "D"  # ❌ N 제외 선생님들은 N 근무 X

            if is_holiday or weekday in [5, 6]:
                assigned_shift = shift_order[(i + day) % len(shift_order)]  

            is_charge = False
            if assigned_shift in ["D", "E", "N"] and nurse in charge_nurses:
                is_charge = True

            if assigned_shift == "OFF":
                schedule_dict[f"{nurse['이름']} ({nurse['근무 유형']})"][day] = "OFF"
            else:
                schedule_dict[f"{nurse['이름']} ({nurse['근무 유형']})"][day] = f"{assigned_shift} {'(C)' if is_charge else ''}"

    schedule_df = pd.DataFrame(schedule_dict).T
    schedule_df.columns = [f"{selected_month}월 {d+1}일" for d in range(days)]
    schedule_df.insert(0, "이름", schedule_df.index)  
    schedule_df.reset_index(drop=True, inplace=True)  

    return schedule_df

# 📅 근무표 생성 버튼 추가
st.header(f"📅 {selected_year}년 {selected_month}월 간호사 근무표 자동 생성기")
if st.button("📌 근무표 생성"):
    if "nurses" in st.session_state and st.session_state.nurses:
        schedule_df = generate_monthly_schedule(st.session_state.nurses, days_in_month)
        st.write(f"📌 **{selected_year}년 {selected_month}월 생성된 근무표 (가독성 개선)**")
        st.dataframe(schedule_df)
    else:
        st.error("❌ 간호사 정보를 먼저 업로드하세요!")
