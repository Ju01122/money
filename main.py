import streamlit as st
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

# ---------------------------
# 사용자별 데이터 파일 경로
# ---------------------------
def get_user_file(email):
    return f"{email}_ledger.json"

# ---------------------------
# 데이터 저장 함수 (JSON 안전 변환 포함)
# ---------------------------
def save_expenses(email, df):
    filepath = get_user_file(email)
    df_copy = df.copy()

    # 변환 함수 (JSON 직렬화 가능하도록 처리)
    def convert_value(v):
        if isinstance(v, (pd.Timestamp, datetime)):
            return v.strftime("%Y-%m-%d")
        elif isinstance(v, (np.integer,)):
            return int(v)
        elif isinstance(v, (np.floating,)):
            return float(v)
        elif pd.isna(v):
            return None
        else:
            return v

    # 전체 변환
    df_copy = df_copy.applymap(convert_value)

    # dict 변환 후 저장
    records = df_copy.to_dict(orient="records")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# ---------------------------
# 데이터 불러오기
# ---------------------------
def load_expenses(email):
    filepath = get_user_file(email)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)
        return pd.DataFrame(records)
    else:
        return pd.DataFrame(columns=["날짜", "분류", "금액", "비고", "타입"])

# ---------------------------
# 로그인 & 회원가입 관리
# ---------------------------
if "users" not in st.session_state:
    st.session_state.users = {}  # {email: password}

if "user" not in st.session_state:
    st.session_state.user = None

if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=["날짜", "분류", "금액", "비고", "타입"])

# ---------------------------
# 로그인 / 회원가입 화면
# ---------------------------
if not st.session_state.user:
    menu = st.sidebar.radio("메뉴", ["로그인", "회원가입"])

    if menu == "로그인":
        st.subheader("로그인")
        email = st.text_input("이메일")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if email in st.session_state.users and st.session_state.users[email] == pw:
                st.session_state.user = email
                st.session_state.ledger = load_expenses(email)
                st.success(f"{email}님 환영합니다!")
                st.experimental_rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

    elif menu == "회원가입":
        st.subheader("회원가입")
        email = st.text_input("이메일")
        pw = st.text_input("비밀번호", type="password")
        if st.button("가입하기"):
            if email in st.session_state.users:
                st.error("이미 존재하는 이메일입니다.")
            else:
                st.session_state.users[email] = pw
                st.success("회원가입 성공! 로그인 해주세요.")

# ---------------------------
# 메인 앱 (로그인 후)
# ---------------------------
else:
    st.sidebar.write(f"현재 사용자: {st.session_state.user}")
    if st.sidebar.button("로그아웃"):
        st.session_state.user = None
        st.experimental_rerun()

    st.title("💰 용돈 기입장")

    menu = st.radio("메뉴 선택", ["기록 추가", "전체 내역 보기"])

    # ---------------------------
    # 기록 추가
    # ---------------------------
    if menu == "기록 추가":
        with st.form("add_form"):
            date = st.date_input("날짜", datetime.today())
            category = st.text_input("분류")  # 사용자 직접 입력 가능
            amount = st.number_input("금액", min_value=0, step=100)
            note = st.text_input("비고")
            type_choice = st.radio("타입", ["수입", "지출"])
            submitted = st.form_submit_button("추가하기")

        if submitted:
            new_record = {
                "날짜": str(date),
                "분류": category,
                "금액": int(amount),
                "비고": note,
                "타입": type_choice
            }
            st.session_state.ledger = pd.concat(
                [st.session_state.ledger, pd.DataFrame([new_record])],
                ignore_index=True
            )
            save_expenses(st.session_state.user, st.session_state.ledger)
            st.success("기록이 추가되었습니다!")

    # ---------------------------
    # 전체 내역 보기 (수정/삭제 포함)
    # ---------------------------
    elif menu == "전체 내역 보기":
        st.subheader("전체 내역")

        df = st.session_state.ledger.copy()
        if not df.empty:
            # 금액 표시 (수입: +, 지출: -)
            df["표시금액"] = df.apply(
                lambda x: f"+{x['금액']:,}원" if x["타입"] == "수입" else f"-{x['금액']:,}원",
                axis=1
            )

            for i, row in df.iterrows():
                cols = st.columns([2, 2, 2, 3, 1, 1])
                cols[0].write(row["날짜"])
                cols[1].write(row["분류"])
                cols[2].write(row["표시금액"])
                cols[3].write(row["비고"])

                # 수정 버튼
                if cols[4].button("✏️", key=f"edit_{i}"):
                    st.session_state.edit_index = i
                    st.experimental_rerun()

                # 삭제 버튼
                if cols[5].button("🗑️", key=f"delete_{i}"):
                    st.session_state.ledger = st.session_state.ledger.drop(i).reset_index(drop=True)
                    save_expenses(st.session_state.user, st.session_state.ledger)
                    st.success("삭제되었습니다!")
                    st.experimental_rerun()

            # 수정 모드
            if "edit_index" in st.session_state and st.session_state.edit_index is not None:
                edit_i = st.session_state.edit_index
                st.subheader("✏️ 내역 수정")

                with st.form("edit_form"):
                    date = st.date_input("날짜", pd.to_datetime(st.session_state.ledger.loc[edit_i, "날짜"]))
                    category = st.text_input("분류", st.session_state.ledger.loc[edit_i, "분류"])
                    amount = st.number_input("금액", min_value=0, value=int(st.session_state.ledger.loc[edit_i, "금액"]))
                    note = st.text_input("비고", st.session_state.ledger.loc[edit_i, "비고"])
                    type_choice = st.radio("타입", ["수입", "지출"], index=0 if st.session_state.ledger.loc[edit_i, "타입"]=="수입" else 1)
                    updated = st.form_submit_button("저장하기")

                if updated:
                    st.session_state.ledger.loc[edit_i] = {
                        "날짜": str(date),
                        "분류": category,
                        "금액": int(amount),
                        "비고": note,
                        "타입": type_choice
                    }
                    save_expenses(st.session_state.user, st.session_state.ledger)
                    st.session_state.edit_index = None
                    st.success("수정되었습니다!")
                    st.experimental_rerun()
        else:
            st.info("아직 기록이 없습니다.")
