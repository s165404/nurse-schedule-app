import streamlit as st
import pandas as pd
import io

# 🔄 우선순위 부여 함수 (직원ID 기준 정렬)
def assign_priority(nurses):
    for nurse in nurses:
        # 직원ID가 None이거나 NaN이면 기본값 설정
        if "직원ID" not in nurse or nurse["직원ID"] is None or pd.isna(nurse["직원ID"]):
            nurse["직원ID"] = "9999"
        elif isinstance(nurse["직원ID"], str) and not nurse["직원ID"].isdigit():
            nurse["직원ID"] = "9999"
        else:
            nurse["직원ID"] = str(nurse["직원ID"])  # 숫자로 변환 가능하면 문자열로 유지

    nurses.sort(key=lambda x: int(x["직원ID"]))  # 직원ID 기준으로 정렬

    for i, nurse in enumerate(nurses):
        nurse["우선순위"] = i + 1  # 정렬된 순서대로 "우선순위" 추가

# 📂 간호사 정보 불러오기 (엑셀 파일 업로드 기능 추가)
st.sidebar.subheader("📂 간호사 정보 불러오기")
uploaded_file = st.sidebar.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file:
    df_uploaded = pd.read_excel(uploaded_file)

    # 🔹 NaN 값을 빈 문자열("")로 변환하여 오류 방지
    df_uploaded = df_uploaded.fillna("").astype(str)  # 모든 값을 문자열로 변환하여 NaN 제거

    required_columns = ["직원ID", "이름", "근무 유형", "Charge 가능", "Wanted Off", "휴가", "공가"]
    
    if all(col in df_uploaded.columns for col in required_columns):
        st.session_state.nurses = df_uploaded.to_dict(orient="records")  # NaN이 제거된 데이터를 세션에 저장

        # 🔹 현재 세션에 저장된 간호사 목록을 확인하는 디버깅 코드 추가
        st.write("📋 현재 저장된 간호사 목록:", st.session_state.nurses)

        # 🔹 데이터가 존재할 때만 실행 (빈 데이터일 경우 실행 안 함)
        if st.session_state.nurses:
            assign_priority(st.session_state.nurses)  # ✅ NaN이 제거된 데이터 사용
            st.success("✅ 간호사 정보가 성공적으로 불러와졌습니다!")
        else:
            st.warning("📢 업로드된 간호사 데이터가 없습니다. 엑셀 파일을 확인하세요.")
    else:
        st.error("⚠️ 엑셀 파일의 형식이 올바르지 않습니다. 올바른 컬럼을 포함하고 있는지 확인하세요.")

# 📥 엑셀 양식 다운로드 기능 추가
sample_data = pd.DataFrame({
    "직원ID": [101, 102, 103, 104],
    "이름": ["홍길동", "이영희", "박철수", "김민지"],
    "근무 유형": ["3교대 가능", "D Keep", "E Keep", "N Keep"],
    "Charge 가능": ["O", "X", "O", "O"],
    "Wanted Off": ["5, 10, 15", "3, 7, 21", "6, 11", "4, 19, 23"],
    "휴가": ["8, 9", "14, 15", "-", "25"],
    "공가": ["12", "-", "20", "-"]
})

output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    sample_data.to_excel(writer, index=False, sheet_name="간호사 정보 양식")
output.seek(0)

st.sidebar.download_button(
    label="📥 엑셀 양식 다운로드",
    data=output,
    file_name="nurse_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
