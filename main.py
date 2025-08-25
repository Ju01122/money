import streamlit as st
import bcrypt
import json
import os
import pandas as pd
from datetime import datetime

# ------------------------
# 사용자 데이터 저장 경로
# ------------------------
USER_DB = "users.json"
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------
# 회원 관리 함수
# ------------------------
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

# ------------------------
# 데이터 저장 / 불러오기
# ------------------------
def get_user_file(email):
    return os.path.join(DATA_DIR, f"{email}.json")

def load_expenses(email):
    filepath = get_user_file(email)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return pd.DataFrame(json.load(f))
    return pd.DataFrame(columns=["날짜", "분류", "내용", "금액", "수입/지출"])

def save_expenses(email, df):
    filepath = get_user_file(email)
    with open(filepath, "w") as f:
        json.dump(df.to_dict(orient="records"), f)

# ------------------------
# 앱 설정
# ------------------------
st.set_page_config(page_title="💸 용돈기입장", page_icon="💸", layout="centered")
st.title("💸 용돈기입장")

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=["날짜", "분류", "내용", "금액", "수입/지출"])

# ------------------------
# 로그인 & 회원가입
# ------------------------
if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("메뉴 선택", ["로그인", "회원가입"])
    email = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")

    if menu == "로그인":
        if st.button("로그인"):
            if login(email, password):
                st.session_state.logged_in = True
                st.session_state.user = email
                st.session_state.ledger = load_expenses(email)
                st.success(f"{email}님 환영합니다!")
                st.rerun()
            else:
                st.error("로그인 실패")

    elif menu == "회원가입":
        if st.button("회원가입"):
            if signup(email, password):
                st.success("회원가입 성공! 로그인 해주세요.")
            else:
                st.warning("이미 존재하는 아이디입니다.")

# ------------------------
# 메인 기능
# ------------------------
else:
    st.sidebar.success(f"{st.session_state.user}님 로그인 중")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.ledger = pd.DataFrame(columns=["날짜", "분류", "내용", "금액", "수입/지출"])
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["➕ 입력하기", "📋 전체 내역", "📊 통계 보기"])

    # ------------------------
    # 입력하기
    # ------------------------
    with tab1:
        st.subheader("➕ 새 내역 입력")

        with st.form("entry_form"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("날짜", value=datetime.today())
                categories = ["식비", "교통", "용돈", "기타"]
                category_input = st.selectbox("분류", categories)

            with col2:
                amount = st.number_input("금액", min_value=0, step=100)
                type_ = st.radio("수입/지출", ["수입", "지출"], horizontal=True)

            description = st.text_input("내용", placeholder="예: 편의점 간식")

            submitted = st.form_submit_button("저장")
            if submitted:
                new_data = {
                    "날짜": pd.to_datetime(date).strftime("%Y-%m-%d"),
                    "분류": category_input,
                    "내용": description,
                    "금액": amount,
                    "수입/지출": type_
                }
                st.session_state.ledger = pd.concat(
                    [st.session_state.ledger, pd.DataFrame([new_data])],
                    ignore_index=True
                )
                save_expenses(st.session_state.user, st.session_state.ledger)
                st.success("저장되었습니다!")

    # ------------------------
    # 전체 내역 (수정 / 삭제 가능)
    # ------------------------
    with tab2:
        st.subheader("📋 전체 내역 보기")
        df = st.session_state.ledger.copy()
        if df.empty:
            st.info("아직 입력된 내역이 없습니다.")
        else:
            df["날짜"] = pd.to_datetime(df["날짜"])
            df = df.sort_values(by="날짜", ascending=False).reset_index(drop=True)

            for i, row in df.iterrows():
                cols = st.columns(6)
                cols[0].write(row["날짜"].strftime("%Y-%m-%d"))
                cols[1].write(row["분류"])
                cols[2].write(row["내용"])

            amount_sign = "+" if row["수입/지출"] == "수입" else "-"
            color = "green" if amount_sign == "+" else "red"
            formatted_amount = f"{amount_sign}{row['금액']:,}원"
            cols[3].markdown(f"<span style='color:{color}'>{formatted_amount}</span>", unsafe_allow_html=True)

            if cols[4].button("✏️ 수정", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.session_state.edit_df = df
                st.rerun()

            if cols[5].button("🗑 삭제", key=f"delete_{i}"):
                df.drop(i, inplace=True)
                df.reset_index(drop=True, inplace=True)
                st.session_state.ledger = df
                save_expenses(st.session_state.user, df)
                st.success("삭제되었습니다!")
                st.rerun()

        # ✏️ 수정 폼
        if st.session_state.edit_index is not None:
            edit_row = df.loc[st.session_state.edit_index]
            st.subheader("✏️ 내역 수정")

            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_date = st.date_input("날짜", value=pd.to_datetime(edit_row["날짜"]))
                    categories = ["식비", "교통", "용돈", "기타"]
                    new_category = st.selectbox(
                        "분류",
                        categories,
                        index=categories.index(edit_row["분류"]) if edit_row["분류"] in categories else 0
                    )
                with col2:
                    new_amount = st.number_input(
                        "금액", min_value=0, step=100, value=int(edit_row["금액"])
                    )
                    new_type = st.radio(
                        "수입/지출",
                        ["수입", "지출"],
                        index=0 if edit_row["수입/지출"] == "수입" else 1
                    )

                new_description = st.text_input("내용", value=edit_row["내용"])

                if st.form_submit_button("수정 저장"):
                    df.loc[st.session_state.edit_index] = {
                        "날짜": pd.to_datetime(new_date).strftime("%Y-%m-%d"),
                        "분류": new_category,
                        "내용": new_description,
                        "금액": new_amount,
                        "수입/지출": new_type
                    }
                    st.session_state.ledger = df
                    save_expenses(st.session_state.user, df)
                    st.session_state.edit_index = None
                    st.success("수정되었습니다!")
                    st.rerun()

    # ------------------------
    # 통계 보기
    # ------------------------
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
