import plotly.graph_objects as go
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).with_name("companies.db")

st.set_page_config(
    page_title="企業分析アプリ",
    page_icon="📊",
    layout="wide"
)

def format_number(value):
    try:
        number = float(str(value).replace(",", ""))
        return f"{number:,.15g}"
    except ValueError:
        return str(value)
def connect():
    return sqlite3.connect(DB)


def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS financials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                year INTEGER NOT NULL,
                revenue REAL NOT NULL,
                operating_profit REAL NOT NULL,
                net_profit REAL NOT NULL,
                total_assets REAL NOT NULL,
                equity REAL NOT NULL,
                debt REAL NOT NULL,
                cash REAL NOT NULL,
                interest_expense REAL NOT NULL,
                interest_income REAL NOT NULL,
                dividend_income REAL NOT NULL,
                tax_rate REAL NOT NULL,
                UNIQUE(company, year)
            )
        """)

        existing_columns = {
            row[1] for row in con.execute("PRAGMA table_info(financials)")
        }

        cf_columns = [
            "operating_cf",
            "investing_cf",
            "financing_cf"
        ]

        for column in cf_columns:
            if column not in existing_columns:
                con.execute(
                    f"ALTER TABLE financials ADD COLUMN {column} REAL"
                )
def load_data(company=None):
    with connect() as con:
        if company:
            df = pd.read_sql_query(
                "SELECT * FROM financials WHERE company=? "
                "ORDER BY year",
                con, params=(company,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM financials ORDER BY company, year",
                con
            )
    return df


def calculate(df):
    df = df.sort_values("year").copy()

    # 前年度末の資産・自己資本を使って平均値を計算
    df["avg_assets"] = (
        df["total_assets"].shift(1) + df["total_assets"]
    ) / 2
    df["avg_equity"] = (
        df["equity"].shift(1) + df["equity"]
    ) / 2

    # 初年度は期末残高で代用
    df["avg_assets"] = df["avg_assets"].fillna(
        df["total_assets"]
    )
    df["avg_equity"] = df["avg_equity"].fillna(
        df["equity"]
    )

    df["ROE (%)"] = (
        df["net_profit"] / df["avg_equity"].where(
            df["avg_equity"] > 0
        ) * 100
    )
    df["ROA (%)"] = (
        df["net_profit"] / df["avg_assets"].where(
            df["avg_assets"] > 0
        ) * 100
    )
    df["営業利益率 (%)"] = (
        df["operating_profit"] / df["revenue"].where(
            df["revenue"] != 0
        ) * 100
    )

    # ROIC = 税引後営業利益 / 投下資本
    invested = df["equity"] + df["debt"] - df["cash"]
    nopat = df["operating_profit"] * (1 - df["tax_rate"])
    df["ROIC (%)"] = (
        nopat / invested.where(invested > 0) * 100
    )

    # 一般的なICR（営業利益 / 支払利息）
    df["ICR (倍)"] = (
        df["operating_profit"] /
        df["interest_expense"].where(
            df["interest_expense"] > 0
        )
    )

    df["自己資本比率 (%)"] = (
        df["equity"] / df["total_assets"].where(
            df["total_assets"] > 0
        ) * 100
    )
    df["財務レバレッジ (倍)"] = (
        df["total_assets"] / df["equity"].where(
            df["equity"] > 0
        )
    )

    # 前年度比st.metric(
    for col in ["revenue", "operating_profit", "net_profit"]:
        df[f"{col}_前年比 (%)"] = (
            df[col].pct_change() * 100
        )
    # フリーキャッシュフロー（営業CF ＋ 投資CF）
    df["フリーCF"] = df["operating_cf"] + df["investing_cf"]
    return df


init_db()

st.title("企業IR")
st.info("🎓 IR分析は就活の企業研究に役立ちます。企業の業績や成長戦略を数字で把握することで、企業比較・志望動機の作成・面接での質問準備に活用できます。")
with st.expander("🎓 IR情報を就活に活かす4つの方法"):
    st.markdown("""
    **① 企業研究**
    - 売上高や利益から企業の収益力を理解する
    - 中期経営計画から今後の成長戦略を把握する

    **② 企業比較**
    - ROE・ROA・営業利益率などを同業他社と比較する
    - 各企業の強みや特徴を発見する

    **③ 志望動機の作成**
    - 企業の成長戦略と自分の経験を結びつける
    - 数字を根拠に企業への理解を伝える

    **④ 面接対策**
    - 決算説明資料から企業の課題を調べる
    - 事業戦略に関する具体的な逆質問を考える
    """)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 データ入力",
    "📊 企業分析",
    "📈 年度比較",
    "🔮 将来予測",
    "🦍 ゴリラ相談室"
])

with tab1:
    st.subheader("決算データを登録")
    if "revenue_input" in st.session_state:
        st.session_state["revenue_input"] = format_number(
            st.session_state["revenue_input"]
        )

    if "op_input" in st.session_state:
        st.session_state["op_input"] = format_number(
            st.session_state["op_input"]
        )
    if "net_input" in st.session_state:
        st.session_state["net_input"] = format_number(
            st.session_state["net_input"]
        )
    if "assets_input" in st.session_state:
        st.session_state["assets_input"] = format_number(
            st.session_state["assets_input"]
        )
    if "equity_input" in st.session_state:
        st.session_state["equity_input"] = format_number(
            st.session_state["equity_input"]
        )
    if "debt_input" in st.session_state:
        st.session_state["debt_input"] = format_number(
            st.session_state["debt_input"]
        )
    if "cash_input" in st.session_state:
        st.session_state["cash_input"] = format_number(
            st.session_state["cash_input"]
        )
    if "interest_input" in st.session_state:
        st.session_state["interest_input"] = format_number(
            st.session_state["interest_input"]
        )    
    if "interest_income_input" in st.session_state:
        st.session_state["interest_income_input"] = format_number(
            st.session_state["interest_income_input"]
        )
    if "dividends_input" in st.session_state:
        st.session_state["dividends_input"] = format_number(
            st.session_state["dividends_input"]
        )
    with st.form("financial_form"):
        company = st.text_input("企業名", placeholder="例：株式会社〇〇")
        year = st.number_input(
            "決算年度", min_value=1900, max_value=2200,
            value=2025, step=1
        )

        st.caption("金額の単位を統一してください（例：百万円）")
        c1, c2 = st.columns(2, border=True)

        with c1:
            st.markdown("#### 📊 財務データ①")
            revenue_text = st.text_input(
    "売上高",
    value="0",
    placeholder="例：1,000,000",
    key="revenue_input"
)

           
            try:
                revenue = float(revenue_text.replace(",", ""))
            except ValueError:
                st.error("売上高には数字を入力してください。")
                st.stop()
            op_text = st.text_input(
                "営業利益",
                value="0",
                placeholder="例：1,000,000",
                help="企業が本業の事業活動によって稼いだ利益です。",
                key="op_input"
            )

            try:
                op = float(op_text.replace(",", ""))
            except ValueError:
                st.error("営業利益には数字を入力してください。")
                st.stop()
            net_text = st.text_input(
            "純利益",
            value="0",
            placeholder="例：1,000,000",
            help="企業が税金などを差し引いた後に残る最終的な利益です。ROEやROAの計算に使用します。",
            key="net_input"
        )

            try:
                net = float(net_text.replace(",", ""))
            except ValueError:
                st.error("純利益には数字を入力してください。")
                st.stop()
            assets_text = st.text_input(
                "総資産",
                value="0",
                placeholder="例：1,000,000",
                help="企業が保有する現金・売掛金・建物・設備など、すべての資産の合計です。ROAや自己資本比率の計算に使用します。",
                key="assets_input"
            )

            try:
                assets = float(assets_text.replace(",", ""))
            except ValueError:
                st.error("総資産には数字を入力してください。")
                st.stop()
            equity_text = st.text_input(
            "自己資本",
            value="0",
            placeholder="例：1,000,000",
            help="企業の総資産から負債などを差し引いた、株主に帰属する資本です。ROEや自己資本比率の計算に使用します。純資産とは必ずしも一致しません。",
            key="equity_input"
        )

            try:
                equity = float(equity_text.replace(",", ""))
            except ValueError:
                st.error("自己資本には数字を入力してください。")
                st.stop()

        with c2:
            st.markdown("#### 💰 財務データ②")
            debt_text = st.text_input(
                "有利子負債",
                value="0",
                placeholder="例：1,000,000",
                key="debt_input"
            )

            try:
                debt = float(debt_text.replace(",", ""))
                if debt < 0:
                    st.error("有利子負債には0以上の数字を入力してください。")
                    st.stop()
            except ValueError:
                st.error("有利子負債には数字を入力してください。")
                st.stop()          
            cash_text = st.text_input(
                "現金・現金同等物",
                value="0",
                placeholder="例：1,000,000",
                key="cash_input"
            )

            try:
                cash = float(cash_text.replace(",", ""))
                if cash < 0:
                    st.error("現金・現金同等物には0以上の数字を入力してください。")
                    st.stop()
            except ValueError:
                st.error("現金・現金同等物には数字を入力してください。")
                st.stop()
            interest_text = st.text_input(
                "支払利息",
                value="0",
                placeholder="例：1,000,000",
                key="interest_input"
            )

            try:
                interest = float(interest_text.replace(",", ""))
                if interest < 0:
                    st.error("支払利息には0以上の数字を入力してください。")
                    st.stop()
            except ValueError:
                st.error("支払利息には数字を入力してください。")
                st.stop()
            
            interest_income_text = st.text_input(
                "受取利息",
                value="0",
                placeholder="例：1,000,000",
                key="interest_income_input"
            )

            try:
                interest_income = float(interest_income_text.replace(",", ""))
                if interest_income < 0:
                    st.error("受取利息には0以上の数字を入力してください。")
                    st.stop()
            except ValueError:
                st.error("受取利息には数字を入力してください。")
                st.stop()
            dividends_text = st.text_input(
                "受取配当金",
                value="0",
                placeholder="例：1,000,000",
                key="dividends_input"
            )

            try:
                dividends = float(dividends_text.replace(",", ""))
                if dividends < 0:
                    st.error("受取配当金には0以上の数字を入力してください。")
                    st.stop()
            except ValueError:
                st.error("受取配当金には数字を入力してください。")
                st.stop()
            tax = st.number_input(
                "実効税率（%）",
                min_value=0.0,
                max_value=100.0,
                value=30.0
            )
        st.markdown("#### 💰 キャッシュフロー")

        operating_cf_text = st.text_input(
            "営業キャッシュフロー",
            value="",
            placeholder="例：1,000,000 または -500,000",
            help="本業の営業活動による現金の増減です。マイナスの場合もあります。",
            key="operating_cf_input"
        )
        investing_cf_text = st.text_input(
            "投資キャッシュフロー",
            value="",
            placeholder="例：-1,000,000",
            help="設備投資や有価証券の売買など、投資活動による現金の増減です。",
            key="investing_cf_input"
        )
        financing_cf_text = st.text_input(
            "財務キャッシュフロー",
            value="",
            placeholder="例：-500,000",
            help="借入金の調達・返済や配当金の支払いなど、財務活動による現金の増減です。",
            key="financing_cf_input"
        )
        try:
            operating_cf = (
                float(operating_cf_text.replace(",", ""))
                if operating_cf_text.strip() else None
            )
            investing_cf = (
                float(investing_cf_text.replace(",", ""))
                if investing_cf_text.strip() else None
            )
            financing_cf = (
                float(financing_cf_text.replace(",", ""))
                if financing_cf_text.strip() else None
            )
        except ValueError:
            st.error(
                "キャッシュフローには数字を入力してください。"
                "例：1,000,000 または -500,000"
            )
            st.stop()
        submitted = st.form_submit_button("データを保存")

        if submitted:
            if not company.strip():
                st.error("企業名を入力してください。")
            elif equity <= 0 or assets <= 0:
                st.error("総資産と自己資本は0より大きい値にしてください。")
            else:
                try:
                    with connect() as con:
                        con.execute("""
                            INSERT INTO financials (
                                company, year, revenue, operating_profit,
                                net_profit, total_assets, equity, debt,
                                cash, interest_expense, interest_income,
                                dividend_income, tax_rate,
                                operating_cf, investing_cf, financing_cf
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(company, year) DO UPDATE SET
                                revenue=excluded.revenue,
                                operating_profit=excluded.operating_profit,
                                net_profit=excluded.net_profit,
                                total_assets=excluded.total_assets,
                                equity=excluded.equity,
                                debt=excluded.debt,
                                cash=excluded.cash,
                                interest_expense=excluded.interest_expense,
                                interest_income=excluded.interest_income,
                                dividend_income=excluded.dividend_income,
                                tax_rate=excluded.tax_rate,
                                operating_cf=excluded.operating_cf,
                                investing_cf=excluded.investing_cf,
                                financing_cf=excluded.financing_cf
                        """, (
                            company.strip(), int(year), revenue, op,
                            net, assets, equity, debt, cash, interest,
                            interest_income, dividends, tax / 100,
                            operating_cf, investing_cf, financing_cf
                        ))
                    st.success("データを保存しました。")
                except sqlite3.Error as e:
                    st.error(f"保存エラー: {e}")

with tab2:
    st.subheader("企業分析")
    with st.expander("📘 財務指標の読み方ガイド"):

        st.markdown("""
    ### 📈 ROE（自己資本利益率）
    **株主のお金を使って、どれだけ効率よく利益を出しているかを示す指標。**

    例えば、自己資本100億円で純利益20億円ならROEは20％です。

    - 高い場合：少ない自己資本で効率よく利益を生み出している
    - 注意点：借入金が多いことでROEが高くなる場合もある
    - 就活での活用：企業の収益力を確認し、同業他社と比較する

    ---

    ### 🏢 ROA（総資産利益率）
    **会社が持っている資産全体を使って、どれだけ利益を出しているかを示す指標。**

    例えば、総資産200億円で純利益10億円ならROAは5％です。

    - 高い場合：資産を効率よく活用して利益を生み出している
    - 注意点：設備投資が多い業種では低くなりやすい
    - 就活での活用：企業が資産を有効活用できているか確認する

    ---

    ### 💰 ROIC（投下資本利益率）
    **事業に投じた資本から、どれだけ効率よく利益を生み出しているかを示す指標。**

    例えば、投下資本100億円に対して税引後営業利益が15億円ならROICは15％です。

    - 高い場合：事業への投資が効率よく利益につながっている
    - 注意点：投下資本の計算方法は企業によって異なる場合がある
    - 就活での活用：企業の事業運営や投資効率を比較する

    ---

    ### 📊 営業利益率
    **売上高のうち、本業の利益としてどれだけ残ったかを示す指標。**

    例えば、売上高100億円で営業利益20億円なら営業利益率は20％です。

    - 高い場合：本業で利益を生み出す力が強い
    - 注意点：IT業界でもSaaSやSIerなど、事業形態によって水準が異なる
    - 就活での活用：企業の競争力やビジネスモデルの違いを考える

    ---

    ### 🛡️ ICR（インタレスト・カバレッジ・レシオ）
    **会社が借入金の利息を支払う余裕を示す指標。**

    例えば、営業利益10億円で支払利息1億円なら、簡易計算のICRは10倍です。

    - 高い場合：利益に対して利息の負担が小さい
    - 低い場合：借入金の利息が経営の負担になっている可能性がある
    - 就活での活用：企業の財務面の安定性を確認する
    """)
    all_data = load_data()
    companies = sorted(all_data["company"].unique()) if not all_data.empty else []

    if companies:
        selected = st.selectbox("分析する企業", companies, key="analysis_company")
        raw = load_data(selected)
        result = calculate(raw)
        latest = result.iloc[-1]

    metric_help = {
        "ROE (%)": "自己資本利益率。株主のお金（自己資本）を使って、どれだけ効率よく利益を出したかを示す指標です。",
        "ROA (%)": "総資産利益率。会社が持つ資産全体を使って、どれだけ利益を生み出したかを示す指標です。",
        "ROIC (%)": "投下資本利益率。事業に投じた資本から、どれだけ効率よく利益を生み出したかを示す指標です。",
        "営業利益率 (%)": "売上高に対して営業利益がどれくらいあるかを示す指標です。本業の収益力を見るのに使います。",
        "ICR (倍)": "インタレスト・カバレッジ・レシオ。営業利益が支払利息の何倍あるかを示し、利息の支払い余力を見る指標です。",
        "自己資本比率 (%)": "総資産に対して自己資本がどれくらいあるかを示す指標です。財務の安定性を見るのに使います。",
        "財務レバレッジ (倍)": "総資産が自己資本の何倍あるかを示す指標です。負債をどの程度活用しているかを見ることができます。"
    }

    cols = st.columns(4, border=True)
    for col, label in zip(
        cols,
        ["ROE (%)", "ROA (%)", "ROIC (%)", "営業利益率 (%)"]
    ):
        value = latest[label]
        col.metric(
            label,
            "--" if pd.isna(value) else f"{value:.2f}%",
            help=metric_help.get(label, "")
        )

    cols = st.columns(3, border=True)
    for col, label in zip(
        cols,
        ["ICR (倍)", "自己資本比率 (%)", "財務レバレッジ (倍)"]
    ):
        value = latest[label]
        suffix = "倍" if "倍" in label else "%"
        col.metric(
            label,
            "--" if pd.isna(value) else f"{value:.2f}{suffix}",
            help=metric_help.get(label, "")
        )
    st.subheader("💰 キャッシュフロー分析")
    cf_cols = st.columns(4, border=True)

    cf_items = [
        ("営業CF", "operating_cf"),
        ("投資CF", "investing_cf"),
        ("財務CF", "financing_cf"),
        ("フリーCF", "フリーCF"),
    ]

    for col, (label, key) in zip(cf_cols, cf_items):
        value = latest[key]
        col.metric(
            label,
            "未入力" if pd.isna(value) else f"{value:,.0f} 円"
        )
    st.markdown("#### 📈 キャッシュフローの推移")

    cf_chart_data = result[
        ["year", "operating_cf", "investing_cf", "financing_cf", "フリーCF"]
    ].copy()

    cf_chart_data = cf_chart_data.rename(columns={
        "operating_cf": "営業CF",
        "investing_cf": "投資CF",
        "financing_cf": "財務CF",
        "フリーCF": "フリーCF",
    })

    if cf_chart_data[["営業CF", "投資CF", "財務CF", "フリーCF"]].notna().any().any():
        st.line_chart(
            cf_chart_data.set_index("year"),
            y=["営業CF", "投資CF", "財務CF", "フリーCF"]
        )
    else:
        st.info("キャッシュフローのデータがまだ登録されていません。")
        st.markdown("#### 📝 キャッシュフローの自動分析")

    operating_cf_value = latest["operating_cf"]

if pd.isna(operating_cf_value):
    st.info("営業CFのデータが未入力です。")
elif operating_cf_value > 0:
    st.success(
        "営業CFがプラスです。本業の活動によって現金を生み出しています。"
    )
elif operating_cf_value < 0:
    st.warning(
        "営業CFがマイナスです。本業の活動による現金の支出が収入を上回っています。"
    )
else:
    st.info("営業CFは0円です。")
free_cf_value = latest["フリーCF"]

if pd.isna(free_cf_value):
    st.info("フリーCFは未計算です。営業CFと投資CFを入力してください。")
elif free_cf_value > 0:
    st.success(
        "フリーCFはプラスです。営業CFから投資CFを反映した後も、現金が残っています。"
    )
elif free_cf_value < 0:
    st.warning(
        "フリーCFはマイナスです。投資活動を含めると現金の支出が収入を上回っています。投資の内容や複数年度の推移を確認しましょう。"
    )
else:
    st.info("フリーCFは0円です。")
        # 投資キャッシュフローの分析
investing_cf_value = latest["investing_cf"]

if pd.isna(investing_cf_value):
    st.info("投資CFのデータが未入力です。")
elif investing_cf_value < 0:
    st.info(
        "投資CFはマイナスです。設備投資や資産の購入などによる支出が考えられます。投資内容を確認しましょう。"
    )
elif investing_cf_value > 0:
    st.info(
        "投資CFはプラスです。資産の売却や投資の回収などによる収入が考えられます。内訳を確認しましょう。"
    )
else:
    st.info("投資CFは0円です。")
        # 財務キャッシュフローの分析
financing_cf_value = latest["financing_cf"]

if pd.isna(financing_cf_value):
    st.info("財務CFのデータが未入力です。")
elif financing_cf_value < 0:
    st.info(
        "財務CFはマイナスです。借入金の返済や配当金の支払いなどが考えられます。内訳を確認しましょう。"
    )
elif financing_cf_value > 0:
    st.info(
        "財務CFはプラスです。借入金の調達や増資などによる資金流入が考えられます。内訳を確認しましょう。"
    )
else:
    st.info("財務CFは0円です。")
    st.subheader("📊 企業財務レーダーチャート")

    radar_labels = [
        "ROE", "ROA", "ROIC",
        "営業利益率", "自己資本比率"
    ]

    radar_columns = [
        "ROE (%)", "ROA (%)", "ROIC (%)",
        "営業利益率 (%)", "自己資本比率 (%)"
    ]

    radar_scores = []
    for column in radar_columns:
        value = latest[column]
        score = 0 if pd.isna(value) else max(0, min(float(value), 100))
        radar_scores.append(score)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=radar_scores + [radar_scores[0]],
        theta=radar_labels + [radar_labels[0]],
        fill="toself",
        name=selected
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "※ 仮表示です。各指標を0〜100の範囲に収めたもので、"
        "企業の優劣を示す評価スコアではありません。"
    )
    st.subheader("🧠 企業財務分析レポート")
    roe = latest["ROE (%)"]

    st.markdown("#### 📈 収益性の分析")

    if pd.isna(roe):
        st.info("ROEを計算できるデータがありません。")
    elif roe >= 15:
        st.success(
            f"ROEは{roe:.2f}%です。自己資本に対する利益創出力が"
            "高い水準にあります。ただし、負債の活用によって"
            "ROEが高くなっている可能性もあるため、"
            "ROAや財務レバレッジとの比較が重要です。"
        )
    elif roe >= 8:
        st.info(
            f"ROEは{roe:.2f}%です。一定の利益創出力が認められます。"
            "同業他社のROEや過去の推移と比較することで、"
            "収益性をより正確に評価できます。"
        )
    else:
        st.warning(
            f"ROEは{roe:.2f}%です。自己資本に対する利益創出力を"
            "確認する必要があります。利益率の低下や"
            "自己資本の増加など、背景を調べることが重要です。"
        )
        st.markdown("#### 🔍 収益性の詳細分析")

        roa = latest["ROA (%)"]
        roic = latest["ROIC (%)"]
        margin = latest["営業利益率 (%)"]

        if pd.notna(roa):
            st.write(
                f"**ROA：{roa:.2f}%** — "
                "総資産を使ってどれだけ効率よく利益を生み出しているかを示します。"
                "過去の推移や同業他社との比較が重要です。"
            )
        else:
            st.info("ROAを計算できません。")

        if pd.notna(roic):
            st.write(
                f"**ROIC：{roic:.2f}%** — "
                "事業に投じた資本から得られる税引後営業利益の割合です。"
                "資本コストとの比較が重要です。"
            )
        else:
            st.info("ROICを計算できません。")

        if pd.notna(margin):
            st.write(
                f"**営業利益率：{margin:.2f}%** — "
                "売上高に対する本業の利益の割合です。"
                "利益率の変化から収益構造を分析できます。"
            )
        else:
            st.info("営業利益率を計算できません。")
    st.markdown("#### 🛡️ 財務安全性の分析")

    equity_ratio = latest["自己資本比率 (%)"]
    icr = latest["ICR (倍)"]
    leverage = latest["財務レバレッジ (倍)"]

    if pd.notna(equity_ratio):
        st.write(
            f"**自己資本比率：{equity_ratio:.2f}%** — "
            "総資産のうち自己資本が占める割合です。"
            "負債への依存度や財務の安定性を確認する指標です。"
        )

    if pd.notna(icr):
        st.write(
            f"**ICR：{icr:.2f}倍** — "
            "営業利益が支払利息の何倍あるかを示します。"
            "利息の支払い余力を確認できます。"
        )
    else:
        st.info("ICRを計算できません。支払利息が0の場合などが考えられます。")

    if pd.notna(leverage):
        st.write(
            f"**財務レバレッジ：{leverage:.2f}倍** — "
            "総資産が自己資本の何倍あるかを示します。"
            "ROEの高さに財務構造が影響していないか確認できます。"
        )

    if pd.notna(equity_ratio) and pd.notna(icr):
        if equity_ratio < 30 and icr < 3:
            st.warning(
                "【要確認】自己資本比率と利息支払余力の両面で、"
                "財務安全性に注意が必要な可能性があります。"
                "同業他社や過去の推移も確認しましょう。"
            )
        elif equity_ratio >= 50 and icr >= 5:
            st.success(
                "【注目ポイント】自己資本の割合が比較的高く、"
                "営業利益による利息支払余力も確認できます。"
                "財務安全性が強みとなる可能性があります。"
            )
        else:
            st.info(
                "【総合コメント】財務安全性を判断するには、"
                "自己資本比率・ICRに加えて、"
                "負債構成やキャッシュフローの確認が重要です。"
            )
    st.markdown("#### 📈 成長性の分析")

    growth_items = [
        ("売上高", "revenue"),
        ("営業利益", "operating_profit"),
        ("純利益", "net_profit")
    ]

    if len(result) < 2:
        st.info(
            "成長性を分析するには、異なる年度の"
            "決算データが2年分以上必要です。"
        )
    else:
        current = result.sort_values("year").iloc[-1]
        previous = result.sort_values("year").iloc[-2]

        if int(current["year"]) - int(previous["year"]) != 1:
            st.info(
                "直前年度のデータがないため、"
                "前年比の分析はできません。"
            )
        else:
            for name, column in growth_items:
                current_value = current[column]
                previous_value = previous[column]

                if (
                    pd.isna(current_value)
                    or pd.isna(previous_value)
                    or previous_value <= 0
                ):
                    st.info(
                        f"{name}の成長率は比較条件を"
                        "満たさないため算出できません。"
                    )
                    continue

                growth = (
                    (current_value - previous_value)
                    / previous_value * 100
                )

                if growth > 0:
                    st.write(
                        f"📈 **{name}：前年比 +{growth:.2f}%**"
                        " — 前年度から増加しています。"
                    )
                elif growth < 0:
                    st.write(
                        f"📉 **{name}：前年比 {growth:.2f}%**"
                        " — 前年度から減少しています。"
                    )
                else:
                    st.write(
                        f"➡️ **{name}：前年比 0.00%**"
                        " — 前年度と同水準です。"
                    )
    st.markdown("#### 🧠 企業の総合財務分析")
    # IT業界向けの暫定評価基準
    IT_BENCHMARKS = {
        "roe": {"strong": 15, "caution": 5},
        "roa": {"strong": 8, "caution": 3},
        "roic": {"strong": 10, "caution": 5},
        "margin": {"strong": 15, "caution": 5},
        "equity_ratio": {"strong": 50, "caution": 30},
        "icr": {"strong": 10, "caution": 3},
    }
    strengths = []
    cautions = []
    margin = latest["営業利益率 (%)"]
    roa = latest["ROA (%)"]
    roic = latest["ROIC (%)"]
    if pd.notna(roe) and pd.notna(margin):
        if roe >= IT_BENCHMARKS["roe"]["strong"] and margin >= IT_BENCHMARKS["margin"]["strong"]:
            strengths.append(
                "ROEと営業利益率がともに高めです。"
                "本業の収益性が強みとなる可能性があります。"
            )
    if pd.notna(margin) and margin >= IT_BENCHMARKS["margin"]["strong"]:
        strengths.append(
            f"営業利益率は{margin:.2f}%です。"
            "売上高に対する本業の利益の割合が比較的高く、"
            "収益性が強みとなる可能性があります。"
            "同業他社との比較も重要です。"
        )
    if pd.notna(roa) and roa >= IT_BENCHMARKS["roa"]["strong"]:
        strengths.append(
            f"ROAは{roa:.2f}%です。"
            "総資産に対する利益創出力が高い可能性があります。"
            "資産効率が強みかどうか、同業他社と比較して確認しましょう。"
        )

    if pd.notna(roic) and roic >= IT_BENCHMARKS["roic"]["strong"]:
        strengths.append(
            f"ROICは{roic:.2f}%です。"
            "投下資本に対して一定の利益を生み出しています。"
            "資本コストを上回っているか確認することが重要です。"
        )
    if pd.notna(equity_ratio) and equity_ratio >= IT_BENCHMARKS["equity_ratio"]["strong"]:
        strengths.append(
            f"自己資本比率は{equity_ratio:.2f}%です。"
            "自己資本による資産の裏付けが比較的大きく、"
            "財務安全性が強みとなる可能性があります。"
            "同業他社との比較やキャッシュフローの確認も重要です。"
        )
    if pd.notna(equity_ratio):
        if equity_ratio < IT_BENCHMARKS["equity_ratio"]["caution"]:
            cautions.append(
                "自己資本比率が30%未満です。"
                "負債構成や財務安全性の確認が必要です。"
            )
    if pd.notna(icr) and icr >= IT_BENCHMARKS["icr"]["strong"]:
        strengths.append(
            f"ICRは{icr:.2f}倍です。"
            "営業利益に対する支払利息の負担が比較的小さく、"
            "利息支払余力に注目できます。"
            "ただし、借入金の残高や返済期限、"
            "キャッシュフローも確認する必要があります。"
        )
    if pd.notna(icr):
        if icr < IT_BENCHMARKS["icr"]["caution"]:
            cautions.append(
                "ICRが3倍未満です。"
                "利息の支払い余力について確認が必要です。"
            )

    st.markdown("**✅ 注目できる強み**")
    if strengths:
        for comment in strengths:
            st.write("・" + comment)
    else:
        st.write("現在の簡易判定では、明確な強みを特定できません。")

    st.markdown("**🔍 注意・確認すべき点**")
    if cautions:
        for comment in cautions:
            st.write("・" + comment)
    else:
        st.write("現在の簡易判定では、特に該当する注意項目はありません。")

    st.caption(
        "※ この分析は試験的な目安に基づいています。"
        "実際の企業評価には業界比較や複数年度の分析が必要です。"
    )
    st.caption(f"最新年度：{int(latest['year'])}年度")

    st.dataframe(
        result[[
            "year", "revenue", "operating_profit", "net_profit",
            "ROE (%)", "ROA (%)", "ROIC (%)", "ICR (倍)",
            "営業利益率 (%)", "自己資本比率 (%)"
        ]],
        use_container_width=True,
        hide_index=True
    )

    if not companies:
        st.info("「データ入力」タブから企業の決算数値を登録してください。")
with tab3:
    st.subheader("年度比較")
    all_data = load_data()
    companies = sorted(all_data["company"].unique()) if not all_data.empty else []

    if companies:
        selected = st.selectbox("比較する企業", companies, key="compare_company")
        result = calculate(load_data(selected)).sort_values("year")
        metrics = [
            "revenue", "operating_profit", "net_profit",
            "ROE (%)", "ROA (%)", "ROIC (%)",
            "営業利益率 (%)", "ICR (倍)"
        ]
        st.markdown("**売上高・営業利益の推移**")
        st.line_chart(result.set_index("year")[["revenue", "operating_profit"]])
        st.markdown("**年度別の指標一覧**")
        st.dataframe(result[["year"] + metrics], use_container_width=True, hide_index=True)

        if len(result) >= 2:
            years = result["year"].astype(int).tolist()
            target_year = st.selectbox("比較する年度", years[1:], index=len(years)-2)
            current = result.loc[result["year"] == target_year].iloc[0]
            previous_rows = result.loc[result["year"] == target_year - 1]
            if previous_rows.empty:
                st.info("選択年度の前年データがありません。前年の決算データを登録してください。")
            else:
                previous = previous_rows.iloc[0]
                st.markdown(f"**{target_year - 1}年度 → {target_year}年度の比較**")
                labels = {
                    "revenue": "売上高", "operating_profit": "営業利益",
                    "net_profit": "当期純利益", "ROE (%)": "ROE",
                    "ROA (%)": "ROA", "ROIC (%)": "ROIC",
                    "営業利益率 (%)": "営業利益率", "ICR (倍)": "ICR"
                }
                rows = []
                for key, label in labels.items():
                    old, new = previous[key], current[key]
                    if key in ("revenue", "operating_profit", "net_profit"):
                        change = f"{(new / old - 1) * 100:+.2f}%" if old > 0 else "算出不可（前年が0以下）"
                    elif key == "ICR (倍)":
                        change = f"{new - old:+.2f}倍" if pd.notna(new) and pd.notna(old) else "算出不可"
                    else:
                        change = f"{new - old:+.2f}ポイント" if pd.notna(new) and pd.notna(old) else "算出不可"
                    rows.append({"指標": label, "前年": old, "当年": new, "増減": change})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.caption("利益率などの変化はパーセントポイントで表示。前年比成長率は前年が正のときのみ算出します。")
        else:
            st.info("前年比較には同じ企業の2年度分のデータが必要です。")
    else:
        st.info("比較するデータがまだありません。")

with tab4:
    st.subheader("5年間の将来予測")
    all_data = load_data()
    companies = sorted(all_data["company"].unique()) if not all_data.empty else []

    if companies:
        selected = st.selectbox("予測する企業", companies, key="forecast_company")
        history = load_data(selected).sort_values("year")
        latest = history.iloc[-1]

        st.caption(
            f"基準年度：{int(latest['year'])}年度"
            "。一定の成長率を仮定した試算です。"
        )

        growth = st.slider("年間売上成長率（%）", -20, 30, 5)
        margin = st.slider("予測営業利益率（%）", -10, 30, 10)
        net_margin = st.slider(
        "予測純利益率（%）",
        0.0,
        30.0,
        10.0,
        0.5
    )
        equity_growth = st.slider(
        "年間自己資本成長率（%）",
        -20.0,
        30.0,
        5.0,
       0.5
    )
     
        forecast = []
        for n in range(1, 6):
            sales = latest["revenue"] * (1 + growth / 100) ** n
            profit = sales * margin / 100
            net_profit = sales * net_margin / 100
            future_equity = latest["equity"] * (1 + equity_growth / 100) ** n
            forecast_roe = net_profit / future_equity * 100 if future_equity > 0 else 0
            forecast.append({
                        "年度": int(latest["year"]) + n,
                        "予測売上高": sales,
                        "予測営業利益": profit,
                        "予測当期純利益": net_profit,
                        "予測営業利益率 (%)": margin,
                        
                        "予測ROE (%)": round(forecast_roe, 2)
                    })

        forecast_df = pd.DataFrame(forecast)
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)
        st.line_chart(forecast_df.set_index("年度")[[
                    "予測売上高", "予測営業利益"
                ]])
        st.warning(
                "これは仮定に基づく試算です。将来のROE・ROA・ROICや"
                "資金繰りを予測するには、将来の資産・負債・利益などの"
                "前提も追加する必要があります。"
            )
   

st.divider()
st.caption(
    "注意：入力データの正確性、会計基準、各指標の定義を確認してください。"
    "本アプリの数値は投資判断や業績予想を保証するものではありません。"
)

st.subheader("📊 企業比較")
df_compare = load_data()
companies = sorted(df_compare["company"].dropna().unique().tolist())
selected_companies = st.multiselect(
    "比較したい企業を選択してください",
    companies
)
if selected_companies:
    compare_data = df_compare[
        df_compare["company"].isin(selected_companies)
    ].copy()
    st.dataframe(compare_data, use_container_width=True)
    
    latest_data = (
        compare_data.groupby("company", group_keys=False)
        .apply(lambda df: calculate(df.assign(company=df.name)).tail(1), include_groups=False)
        .reset_index(drop=True)
    )
    columns = [
       "company",
       "year",
       "ROE (%)",
       "ROA (%)",
       "ROIC (%)",
       "営業利益率 (%)",
       "ICR (倍)"
    ]
    comparison_table = latest_data[columns].copy()
    comparison_table = comparison_table.set_index("company").T
    st.dataframe(comparison_table, use_container_width=True)
    st.subheader("📊 最新年度の財務指標比較")
    st.dataframe(latest_data, use_container_width=True)
    st.subheader("📊 企業別ROE比較")
    indicator = st.selectbox(
            "比較する財務指標を選択",
            [
                "ROE (%)",
                "ROA (%)",
                "ROIC (%)",
                "営業利益率 (%)",
                "ICR (倍)"
            ]
        )
    st.bar_chart(
            latest_data.set_index("company")[indicator]
        )
    st.subheader("📊 財務指標比較ダッシュボード")

    metrics = [
            "ROE (%)",
            "ROA (%)",
            "ROIC (%)",
            "営業利益率 (%)",
            "ICR (倍)"
        ]

    st.dataframe(
            latest_data.set_index("company")[metrics].T,
            use_container_width=True
        )
    st.subheader("📊 5つの財務指標をグラフで比較")

    col1, col2 = st.columns(2)

    for i, metric in enumerate(metrics):
            with [col1, col2][i % 2]:
                st.write(f"### {metric}")
                st.bar_chart(
                    latest_data.set_index("company")[[metric]],
                    color="#2563EB"
                )
                st.subheader("🏆 財務指標別ランキング")
    sort_order = st.radio(
    "ランキングの並び順",
    ["高い順", "低い順"],
    horizontal=True
)
    for metric in metrics:
            ranking = latest_data[
                ["company", metric]
            ].dropna().sort_values(
               by=metric, ascending=(sort_order == "低い順")
            )

            if not ranking.empty:
                st.write(f"### {metric}")

            ranking_table = ranking.copy()
                
               # IT企業向けの参考評価基準
            if metric.startswith("ROE"):
                a, b, c = 15, 10, 5
            elif metric.startswith("ROA"):
                a, b, c = 15, 10, 5
            elif metric.startswith("ROIC"):
                a, b, c = 15, 10, 5
            elif metric.startswith("営業利益率"):
                a, b, c = 20, 10, 5
            elif metric.startswith("ICR"):
                a, b, c = 10, 5, 2
            else:
                a, b, c = None, None, None

            if a is not None:
                ranking_table["評価"] = ranking_table[metric].apply(
                    lambda x: "優秀" if x >= a else "良好" if x >= b else "標準" if x >= c else "改善余地あり"
                )
                
            ranking_table.insert(
                    0, "順位", range(1, len(ranking_table) + 1)
                )

            ranking_table = ranking_table.rename(
                    columns={
                        "company": "企業名",
                        metric: "数値"
                    }
                )
            ranking_table = ranking_table.rename(
                    columns={
                        "company": "企業名",
                        metric: "数値"
                    }
                )    

            st.dataframe(
                ranking_table.style.format({"数値": "{:.2f}"}),
                hide_index=True,
                use_container_width=True
            )
with tab5:
    st.header("🦍 ゴリラ相談室 🍌")
    st.markdown(
        "<div style='text-align:center; font-size:120px;'>🦍</div>",
        unsafe_allow_html=True
    )

    st.info("🍌 何でも聞いてくれウホ！")

    question = st.text_area(
        "ゴリラへの質問",
        placeholder="ここに質問を入力してね！",
        height=120
    )

    if st.button("🦍 質問する"):
        st.markdown(
        """
        <div style="
            background-color: #FFF3C4;
            border: 3px solid #E9B949;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
        ">
            <div style="font-size: 22px; color: #795600;">
                🦍 ゴリラからの回答
            </div>
            <div style="font-size: 36px; font-weight: bold; color: #6B4C00;">
                🍌 What The Fuck！ 🍌
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )