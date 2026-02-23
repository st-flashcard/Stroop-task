import streamlit as st
import random
import time
import pandas as pd
from streamlit.components.v1 import html

# ────────────────────────────────────────
# 【重要】アクセス制限の設定
# ────────────────────────────────────────
# ↓ ここにご自身のブログのURL（ストループ記事のページ）を正確に入力してください！
# 例: "https://tamasuke-st-blog.com/entry/stroop-test-app"
ALLOWED_REFERER_URL = "https://あなたのブログのURL.com/記事のページ"

# アクセス制限のチェック関数
def check_referer():
    # JavaScriptを使って、アクセス元のURL（リファラー）を取得する
    # ※ Streamlitはサーバー側のPythonで動くため、ブラウザの情報を直接取るのが難しく、
    #    JSと連携するこの方法が、簡易的なチェックとしては一般的です。
    referer_check_html = f"""
        <script>
        const allowedUrl = "{ALLOWED_REFERER_URL}";
        const referrer = document.referrer;
        // リファラーが許可されたURLで始まっているかチェック
        if (!referrer.startsWith(allowedUrl)) {{
            // 許可されていない場合、Streamlit側に信号を送る（画面に警告を出す）
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: false
            }}, "*");
        }} else {{
            // 許可された場合
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: true
            }}, "*");
        }}
        </script>
    """
    # HTMLコンポーネントとしてJSを実行し、結果を受け取る
    is_allowed = html(referer_check_html, height=0)
    
    # ※注意：初回ロード時や環境によってはJSの結果がすぐに返ってこないため、
    # 完全にブロックするのは難しいですが、簡易的な「鍵」としては機能します。
    # より厳密な制限にはサーバー側の設定や認証システムが必要です。
    
    # 今回は簡易的に、セッションステートを使って初回アクセス時のフラグ管理をします
    if "is_access_allowed" not in st.session_state:
        # デフォルトはアクセス不可にしておき、JSからのOK信号を待つ
        st.session_state.is_access_allowed = False
    
    if is_allowed is True:
        st.session_state.is_access_allowed = True

# ────────────────────────────────────────
# アプリの本体コード
# ────────────────────────────────────────

st.set_page_config(layout="wide", page_title="Stroop Task Full")

COLORS = {
    "あか": "red",
    "あお": "blue",
    "きいろ": "#d4a017",
    "みどり": "green"
}
COLOR_NAMES = list(COLORS.keys())

MAX_PRACTICE = 4
MAX_TRIALS   = 12

def build_trial_sequence(condition, n_trials):
    if condition == "congruent":
        pool = [(w, w) for w in COLOR_NAMES]
    else:
        pool = [(w, c) for w in COLOR_NAMES for c in COLOR_NAMES if c != w]
    sequence = []
    while len(sequence) < n_trials:
        shuffled = pool[:]
        random.shuffle(shuffled)
        if sequence and shuffled[0] == sequence[-1]:
            swap_idx = random.randint(1, len(shuffled) - 1)
            shuffled[0], shuffled[swap_idx] = shuffled[swap_idx], shuffled[0]
        sequence.extend(shuffled)
    return sequence[:n_trials]

def init_state():
    defaults = {
        "phase":          "start",
        "trial":          0,
        "results":        [],
        "start_time":     0.0,
        "seq_condition":  "",
        "seq_length":     0,
        "trial_sequence": [],
        # アクセス許可フラグ（初期化時は保持）
        # "is_access_allowed" はここでは初期化しない
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
# アクセスチェックを実行（ページを開くたびに確認）
check_referer()

def ensure_sequence():
    phase = st.session_state.phase
    seq   = st.session_state.trial_sequence
    if phase in ("practice", "part1", "part2", "part3") and len(seq) == 0:
        cond = st.session_state.get("seq_condition")
        n    = st.session_state.get("seq_length")
        if cond and n > 0:
            st.session_state.trial_sequence = build_trial_sequence(cond, n)
            st.session_state.trial          = 0
            st.session_state.start_time     = time.time()
        else:
            st.session_state.phase = "start"

ensure_sequence()

def load_sequence(condition, n):
    st.session_state.seq_condition  = condition
    st.session_state.seq_length     = n
    st.session_state.trial_sequence = build_trial_sequence(condition, n)
    st.session_state.trial          = 0
    st.session_state.start_time     = time.time()

def current_pair():
    idx = st.session_state.trial
    seq = st.session_state.trial_sequence
    if not seq or idx >= len(seq):
        return None, None
    return seq[idx]

def go_practice(): load_sequence("incongruent", MAX_PRACTICE); st.session_state.phase = "practice"
def go_part1(): load_sequence("congruent", MAX_TRIALS); st.session_state.phase = "part1"
def go_part2(): load_sequence("incongruent", MAX_TRIALS); st.session_state.phase = "part2"
def go_part3(): load_sequence("incongruent", MAX_TRIALS); st.session_state.phase = "part3"
def go_result(): st.session_state.phase = "result"
def go_reset(): 
    # アクセス許可フラグだけ残してクリア
    allowed = st.session_state.get("is_access_allowed", False)
    st.session_state.clear()
    st.session_state["is_access_allowed"] = allowed
    init_state()

def handle_click(selected_color):
    word, color = current_pair()
    if word is None: return
    reaction_time = time.time() - st.session_state.start_time
    phase         = st.session_state.phase

    if phase in ("practice", "part1", "part2"):
        correct_answer = color
    else: # part3
        correct_answer = word

    is_correct = (selected_color == correct_answer)

    if phase != "practice":
        # ラベルから「言語」「文字」を削除し、「ルール切り替え」に変更
        labels = {"part1": "Part1(一致)", "part2": "Part2(不一致・抑制)", "part3": "Part3(不一致・切替)"}
        st.session_state.results.append({
            "条件":         labels.get(phase, ""),
            "試行":         st.session_state.trial + 1,
            "表示文字":     word,
            "インク色":     color,
            "正答ターゲット": correct_answer,
            "回答":         selected_color,
            "正誤":         "〇" if is_correct else "×",
            "反応時間(秒)": round(reaction_time, 3),
        })

    st.session_state.trial     += 1
    st.session_state.start_time = time.time()

def show_stimulus_and_buttons():
    word, color = current_pair()
    if word is None:
        st.error("⚠️ エラー：最初からやり直してください。")
        return
    color_code = COLORS[color]
    st.markdown(
        f"<div style='text-align:center; font-size:110px; font-weight:bold;"
        f"color:{color_code}; margin:30px 0;'>{word}</div>",
        unsafe_allow_html=True
    )
    cols  = st.columns(4)
    phase = st.session_state.phase
    trial = st.session_state.trial
    for i, cn in enumerate(COLOR_NAMES):
        with cols[i]:
            st.button(cn, key=f"btn_{phase}_{trial}_{i}", use_container_width=True, on_click=handle_click, args=(cn,))

# ════════════════════════════════════════
# アクセス制限の判定と画面描画
# ════════════════════════════════════════

# ★ アクセスが許可されていない場合（ブログから来ていない場合）の表示 ★
if not st.session_state.get("is_access_allowed", False):
    st.error("⚠️ アクセスエラー")
    st.markdown("""
    **このアプリは、指定されたブログ記事からのみアクセスできます。**
    
    お手数ですが、ブラウザの「戻る」ボタンでブログ記事に戻り、
    記事内のリンクから再度アクセスしてください。
    
    (※もしブログからアクセスしているのにこの画面が出る場合は、
    ブラウザのセキュリティ設定でリファラーが無効になっている可能性があります)
    """)
    st.stop() # ここで処理を止め、アプリ画面を表示しない

# ★ アクセス許可された場合のアプリ画面（ここから下は修正前と同じ） ★
st.title("🧠 3段階ストループ課題（Stroop & Reverse Stroop）")
phase = st.session_state.phase

if phase == "start":
    st.markdown("---")
    # 説明文から「言語処理」の文言を削除し、より臨床的な表現へ
    st.markdown(f"""
このアプリは、前頭葉の「抑制機能（我慢する力）」と「ルールの切り替え力（柔軟性）」を精密に評価する3段階テストです。

| フェーズ | 画面の文字 | 回答ルール | 難しさ・測るもの |
|---|---|---|---|
| Part 1 | 文字と色が**同じ** | **インクの色** | ★☆☆（ベースの処理速度） |
| Part 2 | 文字と色が**違う** | **インクの色** | ★★★（純粋な抑制機能） |
| Part 3 | 文字と色が**違う** | **文字を読む** | ★★☆（**ルールの切り替え力**） |
""")
    st.info("練習では、一番難しい「文字と色が違う画像で、インクの色を答える」練習をします。", icon="💡")
    st.button("練習をはじめる", type="primary", use_container_width=True, on_click=go_practice)

elif phase == "practice":
    if st.session_state.trial < MAX_PRACTICE:
        st.warning("【練習】ルール：文字の意味ではなく、**インクの色**を押してください。")
        show_stimulus_and_buttons()
    else:
        st.success("練習終了！次は本番です。")
        st.markdown("まずは **文字とインクが同じ** 簡単な問題です。ルールは変わらず「インクの色」を押してください。")
        st.button("Part 1 をスタート", type="primary", use_container_width=True, on_click=go_part1)

elif phase == "part1":
    if st.session_state.trial < MAX_TRIALS:
        st.info(f"【Part 1: 一致】 ルール：**インクの色**を押してください。 ({st.session_state.trial + 1}/{MAX_TRIALS})")
        show_stimulus_and_buttons()
    else:
        st.warning("Part 1 終了！次は文字とインクが **違います**。")
        st.markdown("ルールは同じです。文字の誘惑に負けず、**インクの色**を押してください。")
        st.button("Part 2 をスタート", type="primary", use_container_width=True, on_click=go_part2)

elif phase == "part2":
    if st.session_state.trial < MAX_TRIALS:
        st.error(f"【Part 2: ストループ】 ルール：**インクの色**を押してください。 ({st.session_state.trial + 1}/{MAX_TRIALS})")
        show_stimulus_and_buttons()
    else:
        st.success("Part 2 終了！ここで【ルール変更】です！！")
        st.markdown("### ⚠️ ルールが変わります ⚠️\n次はインクの色を無視して、**「文字が何と書いてあるか（文字の意味）」**を押してください。")
        st.button("Part 3 をスタート", type="primary", use_container_width=True, on_click=go_part3)

elif phase == "part3":
    if st.session_state.trial < MAX_TRIALS:
        st.success(f"【Part 3: 逆ストループ】 ⚠️ルール：**文字の意味**を押してください！ ({st.session_state.trial + 1}/{MAX_TRIALS})")
        show_stimulus_and_buttons()
    else:
        st.success("すべてのテストが終了しました！お疲れ様でした。")
        st.button("結果を見る", type="primary", use_container_width=True, on_click=go_result)

elif phase == "result":
    st.markdown("## 📊 臨床評価レポート")
    results = st.session_state.results
    if not results:
        st.button("最初からやり直す", on_click=go_reset)
    else:
        df = pd.DataFrame(results)
        rt = {}
        acc = {}
        # ラベル名を変更したため、集計キーも修正
        for p in ["Part1(一致)", "Part2(不一致・抑制)", "Part3(不一致・切替)"]:
            pdf = df[df["条件"] == p]
            rt[p]  = pdf["反応時間(秒)"].mean() if not pdf.empty else 0
            acc[p] = (pdf["正誤"] == "〇").mean() * 100 if not pdf.empty else 0

        inhibition_cost = rt["Part2(不一致・抑制)"] - rt["Part1(一致)"]
        switching_cost   = rt["Part3(不一致・切替)"] - rt["Part1(一致)"]

        c1, c2, c3 = st.columns(3)
        c1.metric("①ベース速度 (Part1)", f"{rt['Part1(一致)']:.2f} 秒", f"正答 {acc['Part1(一致)']:.0f}%")
        c2.metric("②抑制課題 (Part2)", f"{rt['Part2(不一致・抑制)']:.2f} 秒", f"正答 {acc['Part2(不一致・抑制)']:.0f}%")
        c3.metric("③切り替え課題 (Part3)", f"{rt['Part3(不一致・切替)']:.2f} 秒", f"正答 {acc['Part3(不一致・切替)']:.0f}%")

        st.markdown("---")
        st.markdown("### 🔍 脳機能の解剖分析（タイム差の比較）")
        
        st.info(f"**🛑 純粋な抑制力（我慢する力）：【 {inhibition_cost:+.2f} 秒 】の干渉** (Part2 - Part1)\n\n"
                "ルール変更の負荷がない状態で、文字の誘惑を我慢するのにかかったコストです。この数字が大きいほど、前頭葉の抑制機能が低下しています。")
        
        # 解説文から「言語」を削除し、たますけさんの臨床視点に変更
        st.warning(f"**🔄 ルールの切り替え力（セット転換）：【 {switching_cost:+.2f} 秒 】の干渉** (Part3 - Part1)\n\n"
                 "健康であれば一瞬で終わるはずの「文字読み」に時間がかかっています。直前のルール（インクの色）からの切り替えが難しく、セットの固執（保続傾向）が生じている可能性があります。")

        st.markdown("---")
        with st.expander("全試行の生データを見る"):
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSVダウンロード", csv, "stroop_full_result.csv", "text/csv")
        
        st.button("最初からやり直す", use_container_width=True, on_click=go_reset)
