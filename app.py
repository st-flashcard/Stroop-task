import streamlit as st
import random
import time
import pandas as pd

st.set_page_config(layout="wide", page_title="Stroop Task Full")

COLORS = {
    "あか": "red",
    "あお": "blue",
    "きいろ": "#d4a017",
    "みどり": "green"
}
COLOR_NAMES = list(COLORS.keys())

# --- 設定 ---
MAX_PRACTICE = 4   # 練習問題（不一致・インクを答える）
MAX_TRIALS   = 12  # 各パートの問題数（4色×3回でバランスが良い！）

def build_trial_sequence(condition, n_trials):
    if condition == "congruent":
        pool = [(w, w) for w in COLOR_NAMES]
    else:
        pool = [(w, c) for w in COLOR_NAMES for c in COLOR_NAMES if c != w]
    
    sequence = []
    while len(sequence) < n_trials:
        shuffled = pool[:]
        random.shuffle(shuffled)
        # 連続で同じ問題が出ないように調整
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
def go_reset(): st.session_state.clear(); init_state()

def handle_click(selected_color):
    word, color = current_pair()
    if word is None:
        return
    reaction_time = time.time() - st.session_state.start_time
    phase         = st.session_state.phase

    # 🛑 ここがポイント！フェーズによって「正解」の判定基準を変える
    if phase in ("practice", "part1", "part2"):
        # インクの色を答えるのが正解
        correct_answer = color 
    else: # part3 (逆ストループ)
        # 文字の意味を答えるのが正解
        correct_answer = word  

    is_correct = (selected_color == correct_answer)

    if phase != "practice":
        labels = {"part1": "Part1(一致・色)", "part2": "Part2(不一致・色)", "part3": "Part3(不一致・文字)"}
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
# 画面描画
# ════════════════════════════════════════
st.title("🧠 3段階ストループ課題（Stroop & Reverse Stroop）")
phase = st.session_state.phase

if phase == "start":
    st.markdown("---")
    st.markdown(f"""
このアプリは、前頭葉の「抑制機能」と左半球の「言語の自動処理」を精密に評価する3段階テストです。

| フェーズ | 画面の文字 | 回答ルール | 難しさ・測るもの |
|---|---|---|---|
| Part 1 | 文字と色が**同じ** | インクの色 | ★☆☆（ベースの処理速度） |
| Part 2 | 文字と色が**違う** | インクの色 | ★★★（純粋な抑制機能） |
| Part 3 | 文字と色が**違う** | **文字を読む** | ★★☆（言語処理・切り替え） |
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
        
        # 各パートの平均反応時間を計算
        rt = {}
        acc = {}
        for p in ["Part1(一致・色)", "Part2(不一致・色)", "Part3(不一致・文字)"]:
            pdf = df[df["条件"] == p]
            rt[p]  = pdf["反応時間(秒)"].mean() if not pdf.empty else 0
            acc[p] = (pdf["正誤"] == "〇").mean() * 100 if not pdf.empty else 0

        # 指標の計算
        inhibition_cost = rt["Part2(不一致・色)"] - rt["Part1(一致・色)"]
        language_cost   = rt["Part3(不一致・文字)"] - rt["Part1(一致・色)"]

        c1, c2, c3 = st.columns(3)
        c1.metric("①ベース速度 (Part1)", f"{rt['Part1(一致・色)']:.2f} 秒", f"正答 {acc['Part1(一致・色)']:.0f}%")
        c2.metric("②ストループ (Part2)", f"{rt['Part2(不一致・色)']:.2f} 秒", f"正答 {acc['Part2(不一致・色)']:.0f}%")
        c3.metric("③逆ストループ (Part3)", f"{rt['Part3(不一致・文字)']:.2f} 秒", f"正答 {acc['Part3(不一致・文字)']:.0f}%")

        st.markdown("---")
        st.markdown("### 🔍 脳機能の解剖分析（タイム差の比較）")
        
        st.info(f"**🛑 前頭葉の純粋な抑制力：【 {inhibition_cost:+.2f} 秒 】の干渉** (Part2 - Part1)\n\n"
                "ルール変更の負荷がない状態で、文字の誘惑を我慢するのにかかった純粋なコストです。この数字が大きいほど、前頭葉の抑制機能が低下しています。")
        
        st.warning(f"**🗣️ 言語の自動化・切り替え力：【 {language_cost:+.2f} 秒 】の干渉** (Part3 - Part1)\n\n"
                 "健康であれば文字を読むのは一瞬（干渉ゼロに近い）はずです。ここで著しく遅くなっている場合、ルールの切り替え困難（セットの固執）か、軽度な言語・読字処理の低下が疑われます。")

        st.markdown("---")
        with st.expander("全試行の生データを見る"):
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSVダウンロード", csv, "stroop_full_result.csv", "text/csv")
        
        st.button("最初からやり直す", use_container_width=True, on_click=go_reset)
