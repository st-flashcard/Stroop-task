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
MAX_PRACTICE = 4
MAX_TRIALS   = 10

def build_trial_sequence(condition, n_trials):
    if condition == "congruent":
        pool = [(w, w) for w in COLOR_NAMES]
    else:
        pool = [(w, c) for w in COLOR_NAMES for c in COLOR_NAMES if c != w]
    sequence = []
    while len(sequence) < n_trials:
        shuffled = pool[:]
        random.shuffle(shuffled)
        # 連続で同じ問題が出ないようにする処理
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ────────────────────────────────────────
# 修正ポイント①：無限ループバグの解消
# ────────────────────────────────────────
def ensure_sequence():
    phase = st.session_state.phase
    seq   = st.session_state.trial_sequence
    
    # セッションが消えた場合（len(seq) == 0）のみ復元するように変更（無限ループを防止）
    if phase in ("practice", "part1", "part2") and len(seq) == 0:
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

def go_practice():
    load_sequence("congruent", MAX_PRACTICE)
    st.session_state.phase = "practice"

def go_part1():
    load_sequence("congruent", MAX_TRIALS)
    st.session_state.phase = "part1"

def go_part2():
    # ここで "incongruent" (不一致) を指定してストループ問題を生成
    load_sequence("incongruent", MAX_TRIALS)
    st.session_state.phase = "part2"

def go_result():
    st.session_state.phase = "result"

def go_reset():
    st.session_state.clear()
    init_state()

def handle_click(selected_color):
    word, color = current_pair()
    if word is None:
        return
    reaction_time = time.time() - st.session_state.start_time
    is_correct    = (selected_color == color)
    phase         = st.session_state.phase

    if phase != "practice":
        label = {"part1": "一致", "part2": "不一致"}.get(phase, "")
        st.session_state.results.append({
            "条件":         label,
            "試行":         st.session_state.trial + 1,
            "表示文字":     word,
            "インク色":     color,
            "回答":         selected_color,
            "正誤":         "〇" if is_correct else "×",
            "反応時間(秒)": round(reaction_time, 3),
        })

    st.session_state.trial     += 1
    st.session_state.start_time = time.time()

def show_stimulus_and_buttons():
    word, color = current_pair()
    if word is None:
        st.error("⚠️ データが見つかりません。「最初からやり直す」を押してください。")
        st.button("最初からやり直す", on_click=go_reset, use_container_width=True)
        return

    color_code = COLORS[color]
    st.markdown(
        f"<div style='text-align:center; font-size:110px; font-weight:bold;"
        f"color:{color_code}; margin:30px 0;'>{word}</div>",
        unsafe_allow_html=True
    )

    # ────────────────────────────────────────
    # 修正ポイント②：ボタンの配置を固定し、視覚探索のノイズを排除
    # ────────────────────────────────────────
    cols  = st.columns(4)
    phase = st.session_state.phase
    trial = st.session_state.trial

    # ランダムシャッフルを廃止し、常に「あか」「あお」「きいろ」「みどり」の順に固定
    for i, cn in enumerate(COLOR_NAMES):
        with cols[i]:
            st.button(
                cn,
                key=f"btn_{phase}_{trial}_{i}",
                use_container_width=True,
                on_click=handle_click,
                args=(cn,),
            )

# ════════════════════════════════════════
# 画面描画
# ════════════════════════════════════════
st.title("🧠 ストループ課題（Stroop Task）")
phase = st.session_state.phase

if phase == "start":
    st.markdown("---")
    st.markdown(f"""
## ストループ課題とは？

色の名前（あか・あお など）が、**その意味とは違う色のインク**で書かれているとき、
「文字が何と書いてあるか」より「どんな色で書かれているか」を答える方が**ずっと難しい**
ことがわかっています。これを **ストループ効果** と呼びます。

---

## このアプリの流れ

| フェーズ | 内容 | 難しさ |
|---|---|---|
| 練習（{MAX_PRACTICE}回） | 文字と色が同じ | ★☆☆ |
| Part 1（{MAX_TRIALS}回） | 文字と色が **一致** | ★☆☆ |
| Part 2（{MAX_TRIALS}回） | 文字と色が **不一致** | ★★★ |
""")
    st.info("""
**📌 答え方のルール**

画面に大きく文字が表示されます。
「文字が何と書いてあるか（意味）」ではなく、
**「文字がどんな色で書かれているか（インクの色）」のボタンを押してください。**

例：<span style='color:blue; font-size:1.4rem; font-weight:bold;'>あか</span>
→「あか」と書いてあるが青いインクなので **「あお」** を押す
""", icon="💡")
    st.markdown("---")
    st.button("まず練習をはじめる（4回）", type="primary",
              use_container_width=True, on_click=go_practice)

elif phase == "practice":
    if st.session_state.trial < MAX_PRACTICE:
        st.markdown(f"### 練習中　{st.session_state.trial + 1} / {MAX_PRACTICE}")
        st.caption("文字と色は同じです。インクの色のボタンを押してください。")
        show_stimulus_and_buttons()
    else:
        st.success("練習終了！いよいよ本番です。")
        st.markdown("**Part 1** は文字と色が一致する問題です。できるだけ速く・正確に答えてください。")
        st.button("Part 1 をスタート", type="primary",
                  use_container_width=True, on_click=go_part1)

elif phase in ("part1", "part2"):
    is_part1  = (phase == "part1")
    label     = "Part 1（一致条件）" if is_part1 else "Part 2（不一致条件）"
    trial_num = st.session_state.trial

    if trial_num < MAX_TRIALS:
        st.markdown(f"### {label}　{trial_num + 1} / {MAX_TRIALS} 問")
        st.progress(trial_num / MAX_TRIALS)
        show_stimulus_and_buttons()
    else:
        if is_part1:
            st.warning("Part 1 終了！次は文字と色が **一致しない** 難しい問題です。")
            st.markdown("色名と色が食い違うと、脳は「意味」と「知覚」の間で葛藤を起こします。インクの色のボタンを押してください。")
            st.button("Part 2 をスタート", type="primary",
                      use_container_width=True, on_click=go_part2)
        else:
            st.success("全テスト終了！")
            st.button("結果を見る", type="primary",
                      use_container_width=True, on_click=go_result)

elif phase == "result":
    st.markdown("## 📊 評価結果")
    results = st.session_state.results
    if not results:
        st.warning("記録されたデータがありません。")
        st.button("最初からやり直す", on_click=go_reset, use_container_width=True)
    else:
        df   = pd.DataFrame(results)
        p1   = df[df["条件"] == "一致"]
        p2   = df[df["条件"] == "不一致"]
        rt1  = p1["反応時間(秒)"].mean() if not p1.empty else 0
        rt2  = p2["反応時間(秒)"].mean() if not p2.empty else 0
        acc1 = (p1["正誤"] == "〇").mean() * 100 if not p1.empty else 0
        acc2 = (p2["正誤"] == "〇").mean() * 100 if not p2.empty else 0
        diff = rt2 - rt1

        c1, c2, c3 = st.columns(3)
        c1.metric("Part1 平均反応時間", f"{rt1:.3f} 秒")
        c2.metric("Part2 平均反応時間", f"{rt2:.3f} 秒")
        c3.metric("ストループ干渉時間", f"{diff:+.3f} 秒", delta_color="inverse")
        c4, c5 = st.columns(2)
        c4.metric("Part1 正答率", f"{acc1:.1f}%")
        c5.metric("Part2 正答率", f"{acc2:.1f}%")

        comment = "干渉効果が明確に見られます。" if diff > 0.1 else "干渉効果は小さめです。"
        st.info(f"**解釈**：ストループ干渉時間は {diff:.3f} 秒です。{comment} 干渉時間が大きいほど認知的柔軟性・抑制機能に負荷がかかっている可能性があります。")

        st.markdown("---")
        st.markdown("### 全試行ログ")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("📥 CSVダウンロード", csv, "stroop_result.csv", "text/csv")
        st.markdown("---")
        st.button("最初からやり直す", use_container_width=True, on_click=go_reset)
