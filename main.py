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
                st.experimental_rerun()
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
        st.experimental_rerun()

    st.header("용돈 기록 입력")
    date = st.date_input("날짜")
    description = st.text_input("내용")
    amount = st.number_input("금액", step=100)

    if st.button("기록 저장"):
        record = {"날짜": str(date), "내용": description, "금액": amount}
        data = load_expenses(session.user)
        data.append(record)
        save_expenses(session.user, data)
        st.success("기록 저장 완료!")

    st.header("기록 보기")
    data = load_expenses(session.user)
    if data:
        st.table(data)
    else:
        st.info("아직 기록이 없습니다.")
