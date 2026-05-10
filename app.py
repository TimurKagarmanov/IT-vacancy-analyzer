from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

CSV = "vacancies_merged.csv"
BAR = "#818cf8"
BAR_LINE = "#c4b5fd"
PLOT_BG = "#1a1f2e"
GRID = "rgba(148,163,184,0.28)"


def find_csv() -> Path:
    base = Path(__file__).resolve().parent
    for d in (base / "storage", base):
        p = d / CSV
        if p.is_file():
            return p
    return base / "storage" / CSV


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["salary_mid"] = pd.to_numeric(df.get("salary_mid"), errors="coerce")
    na = df["salary_mid"].isna()
    if na.any():
        sm = pd.to_numeric(df.loc[na, "salary_min"], errors="coerce")
        sx = pd.to_numeric(df.loc[na, "salary_max"], errors="coerce")
        mid = pd.Series(pd.NA, index=df.index, dtype="Float64")
        ok = sm.notna() & sx.notna() & (sm > 0) & (sx > 0)
        mid.loc[na & ok] = (sm[ok] + sx[ok]) / 2
        mid.loc[na & ~ok & sm.notna() & (sm > 0)] = sm
        mid.loc[na & ~ok & sx.notna() & (sx > 0)] = sx
        df.loc[na, "salary_mid"] = mid[na]
    if "specialty" not in df.columns:
        df["specialty"] = "Unknown"
    else:
        s = df["specialty"].fillna("").astype(str).str.strip()
        df["specialty"] = s.mask(s.eq("") | s.str.lower().eq("nan"), "Unknown")
    loc = df.get("location", pd.Series("", index=df.index)).fillna("").astype(str).str.strip()
    df["location"] = loc.mask(loc.str.lower().isin({"", "nan", "none"}), "Unknown")
    if "skills" not in df.columns:
        df["skills"] = ""
    return df[df["salary_mid"].notna()].copy()


def tokens(s: str) -> list[str]:
    if not isinstance(s, str) or not s.strip():
        return []
    bad = {"not specified", "nan", "remote", "experience", "years", "engineer"}
    out = []
    for part in re.split(r"[,;|/\n]+", s.lower()):
        t = re.sub(r"\s+", " ", part.strip())
        if 2 < len(t) < 40 and t not in bad:
            out.append(t)
    return out


def apply_base_layout(fig, title: str, h: int) -> None:
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, font=dict(color="#f8fafc", size=15)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        height=h,
        margin=dict(l=12, r=12, t=48, b=12),
        font=dict(color="#e2e8f0", size=13),
        xaxis=dict(
            gridcolor=GRID,
            tickfont=dict(color="#f1f5f9", size=12),
            title_font=dict(color="#e2e8f0"),
        ),
        yaxis=dict(
            gridcolor=GRID,
            tickfont=dict(color="#f1f5f9", size=12),
            title_font=dict(color="#e2e8f0"),
        ),
        showlegend=False,
    )


def bar_h(frame: pd.DataFrame, x: str, y: str, title: str, h: int = 300) -> object:
    fig = px.bar(frame, x=x, y=y, orientation="h", title=title)
    apply_base_layout(fig, title, h)
    fig.update_traces(marker_color=BAR, marker_line=dict(color=BAR_LINE, width=1))
    return fig


def box_salary(frame: pd.DataFrame, x: str, title: str, h: int = 400) -> object:
    fig = px.box(frame, x=x, y="salary_mid", points=False, title=title)
    apply_base_layout(fig, title, h)
    fig.update_traces(
        fillcolor="rgba(129,140,248,0.55)",
        line=dict(color="#eef2ff", width=1.5),
        marker=dict(color="#e0e7ff", size=3),
    )
    fig.update_layout(yaxis_title="Salary (mid)", xaxis_title=None)
    if x == "specialty":
        fig.update_layout(xaxis_tickangle=-35)
    return fig


def main() -> None:
    st.set_page_config(page_title="Vacancies", layout="wide", menu_items={"Get Help": None, "Report a bug": None, "About": None})

    st.markdown(
        "<style>"
        ".stApp{background:#0c0e14;color:#f1f5f9;}"
        ".block-container{padding-top:0.75rem;max-width:1400px;}"
        'header[data-testid="stHeader"],div[data-testid="stDecoration"],'
        '[data-testid="stToolbar"],footer,#MainMenu,[data-testid="collapsedControl"]'
        "{display:none!important;visibility:hidden!important;height:0!important;}"
        '[data-testid="stMetric"]{background:#151a26;border:1px solid #334155;border-radius:8px;padding:.5rem .75rem;}'
        "label,p,.stMultiSelect span,.stSlider span{color:#e2e8f0!important;}"
        "</style>",
        unsafe_allow_html=True,
    )

    st.header("Vacancies")

    path = find_csv()
    if not path.is_file():
        st.error(f"File not found: {path}")
        st.stop()

    df = load(path)
    if df.empty:
        st.warning("No rows with a numeric salary.")
        st.stop()

    filt, body = st.columns([1, 3], gap="medium")
    with filt:
        st.subheader("Filters")
        spec_list = sorted(df["specialty"].unique().tolist())
        picked = st.multiselect("Specialty", spec_list, default=spec_list)
        lo, hi = float(df["salary_mid"].min()), float(df["salary_mid"].max())
        r0, r1 = st.slider("Salary (mid)", lo, hi, (lo, hi))

    d = df[df["specialty"].isin(picked)] if picked else df
    d = d[(d["salary_mid"] >= r0) & (d["salary_mid"] <= r1)]
    if d.empty:
        body.warning("No rows match the filters.")
        st.stop()

    with body:
        a, b, c, e = st.columns(4)
        a.metric("Rows", f"{len(d):,}")
        b.metric("Median salary", f"{d['salary_mid'].median():,.0f}")
        c.metric("Specialties", int(d["specialty"].nunique()))
        e.metric("Locations", int(d["location"].nunique()))

        tl = d["location"].value_counts().head(12).reset_index()
        tl.columns = ["Location", "Count"]
        ml = (
            d[d["location"].isin(tl["Location"])]
            .groupby("location", as_index=False)["salary_mid"]
            .median()
            .sort_values("salary_mid")
            .rename(columns={"location": "Location", "salary_mid": "Median"})
        )
        x1, x2 = st.columns(2)
        x1.plotly_chart(bar_h(tl, "Count", "Location", "Top locations"), width="stretch")
        x2.plotly_chart(bar_h(ml, "Median", "Location", "Median salary by location"), width="stretch")

        loc_top = tl["Location"].tolist()
        sub_loc = d[d["location"].isin(loc_top)]
        st.plotly_chart(
            box_salary(sub_loc, "location", "Salary distribution by location (top 12)"),
            width="stretch",
        )

        sn = d["specialty"].value_counts().head(12).reset_index()
        sn.columns = ["Specialty", "Count"]
        ms = (
            d.groupby("specialty", as_index=False)["salary_mid"]
            .median()
            .sort_values("salary_mid")
            .tail(12)
            .rename(columns={"specialty": "Specialty", "salary_mid": "Median"})
        )
        y1, y2 = st.columns(2)
        y1.plotly_chart(bar_h(sn, "Count", "Specialty", "Specialties (count)"), width="stretch")
        y2.plotly_chart(bar_h(ms, "Median", "Specialty", "Median salary by specialty"), width="stretch")

        spec_top = sn["Specialty"].tolist()
        sub_spec = d[d["specialty"].isin(spec_top)]
        st.plotly_chart(
            box_salary(sub_spec, "specialty", "Salary distribution by specialty (top 12)"),
            width="stretch",
        )

        freq: dict[str, int] = {}
        for blob in d["skills"].astype(str):
            for t in tokens(blob):
                freq[t] = freq.get(t, 0) + 1
        top = sorted(freq.items(), key=lambda item: item[1], reverse=True)[:15]
        if top:
            sf = pd.DataFrame(top, columns=["Skill", "Count"]).sort_values("Count")
            st.plotly_chart(bar_h(sf, "Count", "Skill", "Top skills (tokens)"), width="stretch")


if __name__ == "__main__":
    main()
