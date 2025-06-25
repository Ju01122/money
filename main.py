import streamlit as st
import bcrypt
import json
import os

USER_DB = "users.json"
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def signup(email, password):
    users = load_users()
    if email in users:
        return False
    users[email] = hash_password(password)
    save_users(users)
    return True

def login(email, password):
    users = load_users()
    if email in users and verify_password(password, users[email]):
        return True
    return False

def load_expenses(email):
    filepath = os.path.join(DATA_DIR, f"{email}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

def save_expenses(email, data):
    filepath = os.path.join(DATA_DIR, f"{email}.json")
    with open(filepath, "w") as f:
        json.dump(data, f)

st.title("용돈 기입장")

menu = st.sidebar.selectbox("메뉴 선택", ["로그인", "회원가입"])
session = st.session_state

if "logged_in" not in session:
    session.logged_in = False
    session.user = None

if not session.logged_in:
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")

    if menu == "로그인":
        if st.button("로그인"):
            if login(email, password):
                session.logged_in = True
                session.user = email
                st.success(f"{email}님 환영합니다!")
                st.rerun()
            else:
                st.error("로그인 실패")

    elif menu == "회원가입":
        if st.button("회원가입"):
            if signup(email, password):
                st.success("회원가입 성공! 로그인 해주세요.")
            else:
                st.warning("이미 존재하는 이메일입니다.")

else:
    st.sidebar.success(f"{session.user}님 로그인 중")
    if st.sidebar.button("로그아웃"):
        session.logged_in = False
        session.user = None
        st.rerun()

    import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="용돈기입장", page_icon="💸", layout="centered")

# 세션 상태로 임시 데이터 저장
if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=["날짜", "분류", "내용", "금액", "수입/지출"])

st.title("💸 용돈기입장")

# 탭으로 기능 분리
tab1, tab2, tab3 = st.tabs(["➕ 입력하기", "📋 전체 내역", "📊 통계 보기"])

with tab1:
    st.subheader("➕ 새 내역 입력")

    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("날짜", value=datetime.today())
            category = st.selectbox("분류", ["식비", "교통", "문화", "쇼핑", "기타"])
        with col2:
            amount = st.number_input("금액", min_value=0, step=100)
            type_ = st.radio("수입/지출", ["수입", "지출"], horizontal=True)
        
        description = st.text_input("내용", placeholder="예: 편의점 간식")

        submitted = st.form_submit_button("저장")
        if submitted:
            new_data = {
                "날짜": pd.to_datetime(date).strftime("%Y-%m-%d"),
                "분류": category,
                "내용": description,
                "금액": amount,
                "수입/지출": type_
            }
            st.session_state.ledger = pd.concat(
                [st.session_state.ledger, pd.DataFrame([new_data])],
                ignore_index=True
            )
            st.success("저장되었습니다!")

with tab2:
    st.subheader("📋 전체 내역 보기")
    if st.session_state.ledger.empty:
        st.info("아직 입력된 내역이 없습니다.")
    else:
        df = st.session_state.ledger.copy()
        st.dataframe(df.sort_values("날짜", ascending=False), use_container_width=True)

with tab3:
    st.subheader("📊 통계 보기")
    df = st.session_state.ledger
    if df.empty:
        st.info("데이터가 없어요. 먼저 입력해 주세요!")
    else:
        col1, col2 = st.columns(2)
        income = df[df["수입/지출"] == "수입"]["금액"].sum()
        expense = df[df["수입/지출"] == "지출"]["금액"].sum()
        balance = income - expense

        with col1:
            st.metric("총 수입", f"{income:,.0f} 원")
            st.metric("총 지출", f"{expense:,.0f} 원")
        with col2:
            st.metric("잔액", f"{balance:,.0f} 원", delta=f"{income - expense:,.0f} 원")

        st.divider()

        # 카테고리별 지출 합계
        exp_by_cat = (
            df[df["수입/지출"] == "지출"]
            .groupby("분류")["금액"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(exp_by_cat)
