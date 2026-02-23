import streamlit as st
import random
import time
import pandas as pd

st.set_page_config(layout="wide", page_title="Stroop Task")

COLORS = {
    "あか": "red",
    "あお": "blue",
    "きいろ": "#d4a017",
    "みどり": "green"
}
COLOR_NAMES = list(COLORS.keys())

# ────────────────────────────────────────
# 【修正②】乱数の偏り対策
# ────────────────────────────────────────
# 全組み合わせをあらかじめリストアップしてシャッフル → 均等に出現させる
# 不一致条件：文字≠色の全16通りのうち12通りを使う
# 一致条件：文字＝色の4通りをN回分シャッフル

def build_trial_sequence(condition, n_trials):
    """
    condition: "congruent" | "incongruent"
    偏りがなく連続同一組み合わせも出にくいシーケンスを生成する
    """
    if condition == "congruent":
        pool = [(w, w) for w in COLOR_NAMES]          # 4通り
    else:
        pool = [(w, c) for w in COLOR_NAMES
                       for c in COLOR_NAMES if c != w]  # 12通り

    # n_trials分になるまでpoolを繰り返してシャッフル
    sequence = []
    while len(sequence) < n_trials:
        shuffled = pool[:]
        random.shuffle(shuffled)
        # 連続同一ペアを避ける：直前の末尾と先頭が被ったら1枚ずらす
        if sequence and shuffled[0] == sequence[-1]:
            # 先頭以外からランダムに入れ替え
            swap_idx = random.randint(1, len(shuffled) - 1)
            shuffled[0], shuffled[swap_idx] = shuffled[swap_idx], shuffled[0]
        sequence.extend(shuffled)

    return sequence[:n_trials]

# ────────────────────────────────────────
# セッション初期化
# ────────────────────────────────────────
def init_state():
    defaults = {
        "phase": "start",       # start / practice / part1 / part2 / result
        "trial": 0,
        "results": [],
        "start_time": 0.0,
        "trial_sequence": [],   # 事前生成したシーケンス
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

MAX_PRACTICE = 4
MAX_TRIALS   = 10   # Part1・Part2それぞれの試行数

def load_sequence(condition, n):
    st.session_state.trial_sequence = build_trial_sequence(condition, n)
    st.session_state.trial = 0

def current_pair():
    idx = st.session_state.trial
    return st.session_state.trial_sequence[idx]

def advance_start_time():
    st.session_state.start_time = time.time()

# ────────────────────────────────────────
# ボタン押下処理
# ────────────────────────────────────────
def handle_click(selected_color):
    reaction_time = time.time() - st.session_state.start_time
    word, color = current_pair()
    is_correct = (selected_color == color)

    phase = st.session_state.phase
    condition_label = {"practice": "練習", "part1": "一致", "part2": "不一致"}.get(phase, "")

    if phase != "practice":
        st.session_state.results.append({
            "条件":         condition_label,
            "試行":         st.session_state.trial + 1,
            "表示文字":     word,
            "インク色":     color,
            "回答":         selected_color,
            "正誤":         "〇" if is_correct else "×",
            "反応時間(秒)": round(reaction_time, 3)
        })

    st.session_state.trial += 1

# ────────────────────────────────────────
# 刺激表示ブロック
# ────────────────────────────────────────
def show_stimulus_and_buttons():
    word, color = current_pair()
    color_code = COLORS[color]
    st.markdown(
        f"<div style='text-align:center; font-size:110px; font-weight:bold;"
        f"color:{color_code}; margin:30px 0;'>{word}</div>",
        unsafe_allow_html=True
    )
    # ボタン順をランダム（固定順だと位置で覚えるのを防ぐ）
    shuffled_names = COLOR_NAMES[:]
    random.shuffle(shuffled_names)
    cols = st.columns(4)
    for i, cn in enumerate(shuffled_names):
        btn_color = COLORS[cn]
        with cols[i]:
            # ボタン自体に色をつける
            st.markdown(
                f"<style>div[data-testid='stButton']:nth-of-type({i+1}) button"
                f"{{background-color:{btn_color}; color:white;"
                f"font-size:1.3rem; font-weight:bold; height:70px;"
                f"border:none; border-radius:10px;}}</style>",
                unsafe_allow_html=True
            )
            st.button(
                cn,
                key=f"btn_{st.session_state.phase}_{st.session_state.trial}_{i}",
                use_container_width=True,
                on_click=handle_click,
                args=(cn,)
            )

# ────────────────────────────────────────
# 画面描画
# ────────────────────────────────────────
st.title("🧠 ストループ課題（Stroop Task）")

# ════════════════════════════════════════
# 【修正①】スタート・説明画面
# ════════════════════════════════════════
if st.session_state.phase == "start":
    st.markdown("---")

    # ストループ課題の正しい説明
    st.markdown("""
    ## ストループ課題とは？

    色の名前（あか・あお など）が、**その意味とは違う色のインク**で書かれているとき、
    「文字が何と書いてあるか」より「どんな色で書かれているか」を答える方が**ずっと難しい**
    ことがわかっています。これを **ストループ効果** と呼びます。

    ---

    ## このアプリの流れ

    | フェーズ | 内容 | 難しさ |
    |---|---|---|
    | 練習 | 文字と色が同じ（あか → <span style='color:red'>**あか**</span>） | ★☆☆ |
    | Part 1 | 文字と色が **一致** する問題（{n}回） | ★☆☆ |
    | Part 2 | 文字と色が **一致しない** 問題（{n}回） | ★★★ |

    """.replace("{n}", str(MAX_TRIALS)), unsafe_allow_html=True)

    st.info("""
    **📌 答え方のルール（重要！）**

    画面に大きく文字が表示されます。
    「文字が何と書いてあるか（意味）」ではなく、
    **「文字がどんな色で書かれているか（インクの色）」のボタンを押してください。**

    例：　<span style='color:blue; font-size:1.5rem; font-weight:bold;'>あか</span>
    　→ 「あか」と書いてあるが、青いインクで書かれているので **「あお」** を押す
    """, icon="💡")

    st.markdown("---")
    if st.button("まず練習をはじめる（4回）", type="primary", use_container_width=True):
        load_sequence("congruent", MAX_PRACTICE)
        st.session_state.phase = "practice"
        advance_start_time()
        st.rerun()

# ════════════════════════════════════════
# 練習フェーズ（一致条件で慣れる）
# ════════════════════════════════════════
elif st.session_state.phase == "practice":
    if st.session_state.trial < MAX_PRACTICE:
        st.markdown(f"### 練習中 （{st.session_state.trial + 1} / {MAX_PRACTICE}）")
        st.caption("文字と色は同じです。インクの色のボタンを押してください。")
        show_stimulus_and_buttons()
        # ボタン押下後に次の問題の開始時刻をセット
        if st.session_state.trial > 0:
            advance_start_time()
    else:
        st.success("練習終了！いよいよ本番です。")
        st.markdown("""
        **Part 1** は引き続き「文字と色が一致」する問題です。
        できるだけ **速く・正確に** 答えてください。
        """)
        if st.button("Part 1 をスタート", type="primary", use_container_width=True):
            load_sequence("congruent", MAX_TRIALS)
            st.session_state.phase = "part1"
            advance_start_time()
            st.rerun()

# ════════════════════════════════════════
# Part 1 / Part 2 テスト画面
# ════════════════════════════════════════
elif st.session_state.phase in ["part1", "part2"]:
    is_part1 = st.session_state.phase == "part1"
    label = "Part 1（一致条件）" if is_part1 else "Part 2（不一致条件）"
    trial_num = st.session_state.trial

    if trial_num < MAX_TRIALS:
        progress = trial_num / MAX_TRIALS
        st.markdown(f"### {label}　{trial_num + 1} / {MAX_TRIALS} 問")
        st.progress(progress)
        show_stimulus_and_buttons()
        if trial_num > 0:
            advance_start_time()

    else:
        # フェーズ終了
        if is_part1:
            st.warning("Part 1 終了！次は文字と色が **一致しない** 難しい問題です。")
            st.markdown("""
            **ストループ干渉**：色名と色が食い違うと、脳は「意味」と「知覚」の間で葛藤を起こします。
            さっきより難しく感じても大丈夫です。引き続きインクの色のボタンを押してください。
            """)
            if st.button("Part 2 をスタート", type="primary", use_container_width=True):
                load_sequence("incongruent", MAX_TRIALS)
                st.session_state.phase = "part2"
                advance_start_time()
                st.rerun()
        else:
            st.success("全テスト終了！")
            if st.button("結果を見る", type="primary", use_container_width=True):
                st.session_state.phase = "result"
                st.rerun()

# ════════════════════════════════════════
# 結果画面
# ════════════════════════════════════════
elif st.session_state.phase == "result":
    st.markdown("## 📊 評価結果")
    df = pd.DataFrame(st.session_state.results)

    p1 = df[df["条件"] == "一致"]
    p2 = df[df["条件"] == "不一致"]

    rt1   = p1["反応時間(秒)"].mean() if not p1.empty else 0
    rt2   = p2["反応時間(秒)"].mean() if not p2.empty else 0
    acc1  = (p1["正誤"] == "〇").mean() * 100 if not p1.empty else 0
    acc2  = (p2["正誤"] == "〇").mean() * 100 if not p2.empty else 0
    interference = rt2 - rt1

    col1, col2, col3 = st.columns(3)
    col1.metric("Part1 平均反応時間", f"{rt1:.3f} 秒", help="一致条件")
    col2.metric("Part2 平均反応時間", f"{rt2:.3f} 秒", help="不一致条件")
    col3.metric("ストループ干渉時間", f"{interference:+.3f} 秒",
                delta_color="inverse",
                help="Part2 - Part1。プラスが大きいほど干渉効果が強い")

    col4, col5 = st.columns(2)
    col4.metric("Part1 正答率", f"{acc1:.1f}%")
    col5.metric("Part2 正答率", f"{acc2:.1f}%")

    st.markdown(f"""
    ### 🔍 解釈のポイント

    - **干渉時間が {interference:.3f} 秒**：
      {"干渉効果が明確に見られます。" if interference > 0.1 else "干渉効果は小さめです。"}
    - 一般的に不一致条件は一致条件より **0.1〜0.3 秒** 遅くなると言われています。
    - 干渉時間が大きいほど、**認知的な柔軟性・抑制機能**に負荷がかかっている可能性があります。
    """)

    st.markdown("---")
    st.markdown("### 全試行ログ")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 CSVダウンロード", csv, "stroop_result.csv", "text/csv")

    if st.button("最初からやり直す", use_container_width=True):
        st.session_state.clear()
        st.rerun()
