
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

    # 前年度比
    for col in ["revenue", "operating_profit", "net_profit"]:
        df[f"{col}_前年比 (%)"] = (
            df[col].pct_change() * 100
        )

    return df


init_db()

st.title("📊 企業分析アプリ")
st.caption("財務データの保存・指標計算・年度比較・将来予測")

tab1, tab2, tab3, tab4 = st.tabs([
    "データ入力", "企業分析", "年度比較", "将来予測"
])

with tab1:
    st.subheader("決算データを登録")
    with st.form("financial_form"):
        company = st.text_input("企業名", placeholder="例：株式会社〇〇")
        year = st.number_input(
            "決算年度", min_value=1900, max_value=2200,
            value=2025, step=1
        )

        st.caption("金額の単位を統一してください（例：百万円）")
        c1, c2 = st.columns(2)

        with c1:
            revenue = st.number_input("売上高", min_value=0.0)
            op = st.number_input("営業利益", value=0.0)
            net = st.number_input("純利益", value=0.0)
            assets = st.number_input("総資産", min_value=0.0)
            equity = st.number_input("自己資本", min_value=0.0)

        with c2:
            debt = st.number_input("有利子負債", min_value=0.0)
            cash = st.number_input("現金・現金同等物", min_value=0.0)
            interest = st.number_input("支払利息", min_value=0.0)
            interest_income = st.number_input("受取利息", min_value=0.0)
            dividends = st.number_input("受取配当金", min_value=0.0)
            tax = st.number_input(
                "実効税率（%）", min_value=0.0,
                max_value=100.0, value=30.0
            )

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
                                dividend_income, tax_rate
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                                tax_rate=excluded.tax_rate
                        """, (
                            company.strip(), int(year), revenue, op,
                            net, assets, equity, debt, cash, interest,
                            interest_income, dividends, tax / 100
                        ))
                    st.success("データを保存しました。")
                except sqlite3.Error as e:
                    st.error(f"保存エラー: {e}")

with tab2:
    st.subheader("企業分析")
    all_data = load_data()
    companies = sorted(all_data["company"].unique()) if not all_data.empty else []

    if companies:
        selected = st.selectbox("分析する企業", companies, key="analysis_company")
        raw = load_data(selected)
        result = calculate(raw)
        latest = result.iloc[-1]

        cols = st.columns(4)
        for col, label in zip(
            cols,
            ["ROE (%)", "ROA (%)", "ROIC (%)", "営業利益率 (%)"]
        ):
            value = latest[label]
            col.metric(label, "—" if pd.isna(value) else f"{value:.2f}%")

        cols = st.columns(3)
        for col, label in zip(
            cols,
            ["ICR (倍)", "自己資本比率 (%)", "財務レバレッジ (倍)"]
        ):
            value = latest[label]
            suffix = "倍" if "倍" in label else "%"
            col.metric(label, "—" if pd.isna(value) else f"{value:.2f}{suffix}")

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
    else:
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