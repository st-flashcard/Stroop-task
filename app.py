import streamlit as st
import random
import time
import pandas as pd

st.set_page_config(layout="wide", page_title="Stroop Task Full")

# ────────────────────────────────────────
# 【確実版】URLパラメータによるアクセス制限
# ────────────────────────────────────────
# セッション状態の初期化
if "is_access_allowed" not in st.session_state:
    st.session_state.is_access_allowed = False

# URLの末尾に ?from=tamasuke がついているかチェック
if st.query_params.get("from") == "tamasuke":
    st.session_state.is_access_allowed = True

# 許可されていない場合のブロック画面
if not st.session_state.is_access_allowed:
    st.error("⚠️ アクセスエラー")
    st.markdown("""
    **このアプリは、指定されたブログ記事からのみアクセスできます。**
    
    お手数ですが、ブログ記事（dementia-stroke-st.blogspot.com）に戻り、
    記事内の専用リンクから再度アクセスしてください。
    """)
    st.stop() # ここで処理を止め、アプリ画面を表示しない

# ────────────────────────────────────────
# アプリの本体コード（ここから下は変更なし）
# ────────────────────────────────────────

COLORS = {
    "あか": "red",
    "あお": "blue",
    "きいろ": "#d4a017",
    "みどり": "green"
}
COLOR_NAMES = list(COLORS.keys())

# ・・・（以下、先ほどのコードがそのまま続きます）・・・
