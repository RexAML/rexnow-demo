"""RexNow — version CONSULTATION publique (Streamlit Community Cloud).

Lecture seule : lit uniquement des sorties PRÉ-CALCULÉES (dossier ./data), aucun
accès aux API sources, aucune clé, aucun recalcul. Accès protégé par mot de passe
(Secrets Streamlit Cloud : app_password = "…").

Thème CLAIR / SOMBRE automatique : suit le réglage du navigateur/téléphone du
visiteur (détecté via st.context.theme). Modèle et application : Anthony Morlet-Lavidalie — Rexecode.
"""
from __future__ import annotations
import json, datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

DATA = Path(__file__).resolve().parent / "data"
st.set_page_config(page_title="RexNow — Nowcast PIB · Rexecode", page_icon="📈", layout="wide")

# --- thème du visiteur (clair / sombre), détecté côté serveur ---
try:
    DARK = (st.context.theme.type == "dark")
except Exception:
    DARK = False

# --- palettes (couleurs du site rexecode.fr, déclinées clair/sombre) ---
ORANGE = "#F5894D"
if DARK:
    BG, CARD, CARD2 = "#0F1720", "#1B2530", "#223143"
    TXT, MUTED, LINE = "#E7ECF2", "#9FB0C0", "#2C3A49"
    COMBI_BG, BANNER, ACCENT = "#22344A", "#1C3A5C", "#57ADE0"
    AXIS, GRID, IC_RGB = "#9FB0C0", "rgba(150,160,175,0.16)", "87,173,224"
    COL = {"combi": "#57ADE0", "rf": "#F79A5E", "midas": "#43C9AA", "en": "#9CC4E6", "obs": "#E7ECF2"}
else:
    BG, CARD, CARD2 = "#F4F5F7", "#FFFFFF", "#F1F7FC"
    TXT, MUTED, LINE = "#14212E", "#5B6B7A", "#E3E7EC"
    COMBI_BG, BANNER, ACCENT = "#EAF4FB", "#1C5385", "#0077B8"
    AXIS, GRID, IC_RGB = "#5B6B7A", "rgba(130,140,155,0.22)", "0,119,184"
    COL = {"combi": "#0077B8", "rf": "#F5894D", "midas": "#2CA089", "en": "#1C5385", "obs": "#14212E"}

NOM = {"combi": "Combinaison", "rf": "Random Forest", "midas": "MIDAS", "en": "ElasticNet"}
MK = {"combi": "COMBI", "rf": "RandomForest", "midas": "MIDAS", "en": "ElasticNet"}
DUMMIES = {"2008Q3", "2008Q4", "2009Q1", "2020Q1", "2020Q2", "2020Q3", "2020Q4", "2021Q3"}
_PCFG = {"displayModeBar": False}

st.markdown(f"""<style>
  html, body, .stApp {{ background:{BG} !important; color:{TXT}; }}
  section[data-testid="stSidebar"] {{ background:{CARD2}; }}
  #MainMenu, footer, [data-testid="stStatusWidget"] {{ visibility:hidden; }}
  [data-testid="stHeader"] {{ background:transparent !important; }}
  .block-container {{ max-width:1050px; }}
  .stApp * {{ animation-duration:0s !important; animation-delay:0s !important; }}
  [data-testid="stElementContainer"], .element-container, [data-testid="stMarkdownContainer"] {{ opacity:1 !important; }}
  /* textes : forcés à la couleur du thème courant */
  [data-testid="stHeading"], [data-testid="stHeading"] * {{ color:{TXT} !important; }}
  [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ color:{TXT} !important; }}
  [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{ color:{MUTED} !important; }}
  .stTabs [data-baseweb="tab"] p {{ color:{MUTED} !important; }}
  .stTabs [aria-selected="true"] p {{ color:{ACCENT} !important; }}
  section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h1 {{ color:{TXT} !important; }}
  section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{ color:{TXT} !important; }}
  /* bandeau */
  .rex-banner {{ background:{BANNER}; border-radius:12px; padding:22px 28px; margin:0 0 14px 0;
    color:#fff; box-shadow:0 2px 12px rgba(0,0,0,0.18); }}
  .rex-banner .rx {{ font-weight:800; letter-spacing:.6px; font-size:14px; color:#BFD8EC !important;
    text-transform:uppercase; }}
  .rex-banner .rx b {{ color:{ACCENT} !important; }}
  .rex-banner h1, .rex-banner h1 span {{ margin:.12em 0 .04em; font-size:30px; font-weight:800; color:#fff !important; }}
  .rex-banner h1 span.nm {{ color:{ORANGE} !important; }}
  .rex-banner .sub {{ color:#DCEAF6 !important; font-size:14.5px; }}
  .rex-banner .by {{ margin-top:10px; font-size:12.5px; color:#AEC7DE !important; }}
  .rex-banner .by b {{ color:#fff !important; }}
  /* cartes de synthèse */
  .mrow {{ display:flex; gap:12px; flex-wrap:wrap; margin:4px 0 8px; }}
  .mcard {{ flex:1 1 190px; background:{CARD}; border:1px solid {LINE}; border-left:4px solid {ACCENT};
    border-radius:11px; padding:14px 16px; }}
  .mcard .lbl {{ font-size:12px; color:{MUTED} !important; font-weight:600; text-transform:uppercase; letter-spacing:.02em; }}
  .mcard .val {{ font-size:30px; font-weight:800; color:{ACCENT} !important; line-height:1.05; margin-top:4px; }}
  .mcard.rmse {{ border-left-color:{ORANGE}; background:{CARD2}; }}
  .mcard.rmse .txt, .mcard.rmse .txt b {{ font-size:13px; color:{TXT} !important; margin-top:4px; line-height:1.45; }}
  /* tableau */
  .rex-tw {{ overflow-x:auto; -webkit-overflow-scrolling:touch; border:1px solid {LINE};
    border-radius:11px; margin:2px 0 8px; background:{CARD}; }}
  table.rex {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
  table.rex th, table.rex td {{ padding:9px 12px; text-align:right; white-space:nowrap;
    border-bottom:1px solid {LINE}; font-variant-numeric:tabular-nums; color:{TXT}; }}
  table.rex th:first-child, table.rex td:first-child {{ text-align:left; position:sticky; left:0; background:{CARD}; }}
  table.rex thead th {{ background:{CARD2}; color:{MUTED} !important; font-weight:600; }}
  table.rex tbody tr:last-child td {{ border-bottom:none; }}
  table.rex tr.combi td {{ background:{COMBI_BG}; font-weight:700; color:{ACCENT} !important; }}
  /* graphiques en cartes */
  [data-testid="stPlotlyChart"] {{ background:{CARD}; border:1px solid {LINE}; border-radius:11px; padding:8px 10px; }}
  @media (max-width:640px) {{
    .block-container {{ padding-left:.6rem; padding-right:.6rem; padding-top:1rem; }}
    .rex-banner {{ padding:15px 17px; border-radius:10px; }}
    .rex-banner h1, .rex-banner h1 span {{ font-size:21px; }}
    .rex-banner .sub {{ font-size:12px; }} .rex-banner .rx, .rex-banner .by {{ font-size:11px; }}
    .mcard .val {{ font-size:26px; }}
    div[data-testid="stHorizontalBlock"] {{ flex-wrap:wrap; gap:.4rem; }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{ min-width:100% !important; flex:1 1 100% !important; }}
    .stTabs [role="tablist"] {{ overflow-x:auto; }}
  }}
</style>""", unsafe_allow_html=True)


def loadjson(p):
    raw = Path(p).read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:
            continue
    return json.loads(raw.decode("utf-8", "replace"))


def qdate(q):
    y, t = int(q[:4]), int(q[5]); return pd.Timestamp(y, (t - 1) * 3 + 2, 15)


def fr(x, s=2):
    return ("+" if x >= 0 else "−") + f"{abs(x):.{s}f}".replace(".", ",")


def style_fig(fig, h, ytitle=None, legend=True):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=AXIS), hovermode="x unified",
                      legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"))
    if not legend:
        fig.update_layout(showlegend=False)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=MUTED)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=MUTED, title=ytitle)
    return fig


# ======================= mot de passe =======================
def gate():
    if st.session_state.get("rexnow_ok"):
        return
    try:
        pw_ref = st.secrets["app_password"]
    except Exception:
        pw_ref = None
    if not pw_ref:
        st.session_state.rexnow_ok = True
        st.session_state.rexnow_nopw = True
        return
    st.markdown(f"""<div class="rex-banner"><div class="rx">Re<b>xec</b>ode</div>
      <h1><span class="nm">RexNow</span> — accès protégé</h1>
      <div class="sub">Merci de saisir le mot de passe communiqué par Rexecode.</div></div>""",
                unsafe_allow_html=True)
    pw = st.text_input("Mot de passe", type="password", label_visibility="collapsed", placeholder="Mot de passe")
    if not pw:
        st.stop()
    if pw == pw_ref:
        st.session_state.rexnow_ok = True; st.rerun()
    else:
        st.error("Mot de passe incorrect."); st.stop()


gate()

# ======================= chargement =======================
meta = loadjson(DATA / "meta.json")
last_data = meta.get("last_data_fr", meta.get("last_data_iso", "n/a"))
hs = loadjson(DATA / "horizon_summary.json")
ne = loadjson(DATA / "nowcast_evolution.json")
eh = loadjson(DATA / "evolution_h1.json")
P = pd.read_csv(DATA / "fullbench_preds.csv", encoding="utf-8-sig", index_col=0)
P.index = [str(q) for q in P.index]
P["combi"] = P[["RandomForest", "MIDAS", "ElasticNet"]].mean(axis=1)
f3, f4 = hs["forecast_T3_h0"], hs["forecast_T4_h1"]
r0, r1 = hs["rmse_h0"], hs["rmse_h1"]

# ======================= barre latérale =======================
st.sidebar.title("RexNow")
st.sidebar.caption("Nowcast du PIB français — Rexecode")
st.sidebar.metric("Donnée la plus récente", last_data)
st.sidebar.divider()
st.sidebar.info("🔒 **Mode consultation** — navigation libre dans les onglets. "
                "Version partagée en lecture seule ; le modèle n'est pas recalculé ici.")
st.sidebar.caption(f"Thème : {'sombre' if DARK else 'clair'} (suit votre appareil)")
if st.session_state.get("rexnow_nopw"):
    st.sidebar.warning("Aucun mot de passe configuré. Ajoutez `app_password` dans les "
                       "Secrets Streamlit Cloud pour protéger l'accès.")

# ======================= en-tête =======================
st.markdown(f"""<div class="rex-banner">
  <div class="rx">Re<b>xec</b>ode · modèle indépendant</div>
  <h1><span class="nm">RexNow</span> — Nowcast du PIB français</h1>
  <div class="sub">Prévision de la croissance trimestrielle du PIB (volume, CVS-CJO)
    · millésime des données : {last_data}</div>
  <div class="by">Modèle et application conçus par <b>Anthony Morlet-Lavidalie</b> — Rexecode</div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="mrow">
  <div class="mcard"><div class="lbl">2026 T3 — nowcast (h=0)</div><div class="val">{fr(f3['COMBI'])} %</div></div>
  <div class="mcard"><div class="lbl">2026 T4 — prévision (h=1)</div><div class="val">{fr(f4['COMBI'])} %</div></div>
  <div class="mcard rmse"><div class="lbl">RMSE test · hors crise</div>
    <div class="txt">nowcast <b>{r0['COMBI']:.2f}</b> · prévision <b>{r1['COMBI']:.2f}</b> pts<br>
    deux modèles distincts par horizon</div></div>
</div>""", unsafe_allow_html=True)

tab_prev, tab_obs, tab_evo, tab_rmse, tab_var = st.tabs(
    ["Prévisions", "Observé vs prévu", "Évolution & incertitude", "RMSE glissant", "Variables"])

# ---------- Prévisions ----------
with tab_prev:
    st.subheader("Prévision par modèle et combinaison")
    head = "".join(f"<th>{h}</th>" for h in ["Modèle", "T3 (%)", "T4 (%)", "RMSE now.", "RMSE prév."])
    body = ""
    for k in ["rf", "midas", "en", "combi"]:
        cls = ' class="combi"' if k == "combi" else ""
        body += (f"<tr{cls}><td>{NOM[k]}</td><td>{f3[MK[k]]:.2f}</td><td>{f4[MK[k]]:.2f}</td>"
                 f"<td>{r0[MK[k]]:.3f}</td><td>{r1[MK[k]]:.3f}</td></tr>")
    st.markdown(f'<div class="rex-tw"><table class="rex"><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table></div>', unsafe_allow_html=True)
    xs = [NOM[k] for k in ["rf", "midas", "en", "combi"]]
    fig = go.Figure()
    fig.add_bar(x=xs, y=[f3[MK[k]] for k in ["rf", "midas", "en", "combi"]], name="T3 (nowcast)", marker_color=ACCENT)
    fig.add_bar(x=xs, y=[f4[MK[k]] for k in ["rf", "midas", "en", "combi"]], name="T4 (prévision)", marker_color=ORANGE)
    fig.update_layout(barmode="group")
    st.plotly_chart(style_fig(fig, 320, "croissance t/t (%)"), use_container_width=True, config=_PCFG, theme=None)
    st.caption("La combinaison (moyenne des 3) est le modèle opérationnel : elle lisse les erreurs propres à chacun.")

# ---------- Observé vs prévu ----------
with tab_obs:
    st.subheader("PIB observé vs prévu")
    cc1, cc2 = st.columns([3, 1])
    excl = cc2.toggle("Exclure 2020 (Covid, hors échelle)", value=True)
    sel = cc1.multiselect("Modèles affichés", ["combi", "rf", "midas", "en"],
                          default=["combi"], format_func=lambda k: NOM[k])
    D = P.copy()
    if excl:
        D = D[~D.index.str.startswith("2020")]
    x = [qdate(q) for q in D.index]
    fig = go.Figure()
    fig.add_scatter(x=x, y=D["actual"], name="PIB observé", mode="lines", line=dict(color=COL["obs"], width=2.6))
    for k in sel:
        col = {"combi": "combi", "rf": "RandomForest", "midas": "MIDAS", "en": "ElasticNet"}[k]
        fig.add_scatter(x=x, y=D[col], name=NOM[k], mode="lines", line=dict(color=COL[k], width=1.8))
    fig.add_vrect(x0=qdate("2000Q1"), x1=qdate("2014Q4"), fillcolor=MUTED, opacity=0.08,
                  line_width=0, annotation_text="in-sample", annotation_position="top left")
    fig.add_vline(x=qdate("2015Q1"), line=dict(color=MUTED, dash="dot"))
    st.plotly_chart(style_fig(fig, 420, "croissance t/t (%)"), use_container_width=True, config=_PCFG, theme=None)
    st.caption("Zone grisée = entraînement (2000-2014). À droite du pointillé = test hors-échantillon (2015→).")

# ---------- Évolution & IC ----------
with tab_evo:
    st.subheader("Évolution de la prévision et de son intervalle de confiance")
    st.caption("Bande = IC issu de l'erreur historique par étape (68 % foncé, 95 % clair). "
               "Point plein = information disponible, contour = projeté.")

    def funnel(stages, rmse, center, known, titre):
        x = list(range(len(stages)))
        up95 = [c + 1.96 * r for c, r in zip(center, rmse)]; lo95 = [c - 1.96 * r for c, r in zip(center, rmse)]
        up68 = [c + r for c, r in zip(center, rmse)]; lo68 = [c - r for c, r in zip(center, rmse)]
        fig = go.Figure()
        fig.add_scatter(x=x + x[::-1], y=up95 + lo95[::-1], fill="toself",
                        fillcolor=f"rgba({IC_RGB},0.12)", line_width=0, name="IC 95 %", hoverinfo="skip")
        fig.add_scatter(x=x + x[::-1], y=up68 + lo68[::-1], fill="toself",
                        fillcolor=f"rgba({IC_RGB},0.26)", line_width=0, name="IC 68 %", hoverinfo="skip")
        fig.add_scatter(x=x, y=center, mode="lines+markers+text", line=dict(color=ACCENT, width=2.4),
                        marker=dict(size=11, color=[ACCENT if k else CARD for k in known],
                                    line=dict(color=ACCENT, width=2)),
                        text=[fr(c) if k else "" for c, k in zip(center, known)],
                        textposition="top center", textfont=dict(color=TXT), name="prévision")
        fig.update_layout(title=dict(text=titre, font=dict(color=TXT)),
                          xaxis=dict(tickmode="array", tickvals=x, ticktext=stages))
        return style_fig(fig, 360, "croissance t/t (%)", legend=False)

    def carry(vals, known):
        out, last = [], None
        for v, k in zip(vals, known):
            if k and v is not None:
                last = v
            out.append(round(last if last is not None else 0.0, 3))
        return out

    st3 = ne["stages"]; rm3 = [ne["rmse_stage"][s] for s in st3]
    p3 = ne["paths"]["2026Q3"]; known3 = [s in p3 for s in st3]
    c3v = carry([p3.get(s) for s in st3], known3)
    if "aujourd'hui" in p3:
        li = max(i for i, k in enumerate(known3) if k)
        if li + 1 < len(st3):
            c3v[li + 1] = round(p3["aujourd'hui"], 3); known3[li + 1] = True
            for j in range(li + 2, len(st3)):
                c3v[j] = round(p3["aujourd'hui"], 3)
    st4 = eh["stages"]; rm4 = [eh["rmse_stage"][s] for s in st4]
    p4 = eh["path_T4"]; known4 = [s in p4 for s in st4]
    c4v = carry([p4.get(s) for s in st4], known4)

    e1, e2 = st.columns(2)
    e1.plotly_chart(funnel(st3, rm3, c3v, known3, "2026 T3 — nowcast (h=0)"), use_container_width=True, config=_PCFG, theme=None)
    e2.plotly_chart(funnel(st4, rm4, c4v, known4, "2026 T4 — prévision (h=1)"), use_container_width=True, config=_PCFG, theme=None)

# ---------- RMSE glissant ----------
with tab_rmse:
    st.subheader("RMSE en moyenne mobile sur 2 ans")
    err = {}
    for k, col in [("rf", "RandomForest"), ("midas", "MIDAS"), ("en", "ElasticNet"), ("combi", "combi")]:
        e = (P[col] - P["actual"]).copy()
        e[[q in DUMMIES for q in P.index]] = np.nan
        err[k] = np.sqrt((e ** 2).rolling(8, min_periods=8).mean())
    x = [qdate(q) for q in P.index]
    fig = go.Figure()
    for k in ["rf", "midas", "en", "combi"]:
        fig.add_scatter(x=x, y=err[k], name=NOM[k], mode="lines",
                        line=dict(color=COL[k], width=2.6 if k == "combi" else 1.6))
    fig.add_vline(x=qdate("2015Q1"), line=dict(color=MUTED, dash="dot"))
    st.plotly_chart(style_fig(fig, 420, "RMSE (pts)"), use_container_width=True, config=_PCFG, theme=None)
    st.caption("Trimestres de crise neutralisés. À gauche du pointillé : in-sample ; à droite : hors-échantillon.")

# ---------- Variables ----------
with tab_var:
    st.subheader("Catégories de variables les plus utiles")
    agg = pd.Series(loadjson(DATA / "cats_importance.json")).sort_values()
    fig = go.Figure(go.Bar(x=agg.values, y=agg.index, orientation="h", marker_color=ACCENT,
                           text=[f"{v:.0f}%" for v in agg.values], textposition="outside",
                           textfont=dict(color=TXT)))
    fig.update_layout(xaxis_title="part de l'importance (%)")
    st.plotly_chart(style_fig(fig, 380, None, legend=False), use_container_width=True, config=_PCFG, theme=None)
    st.caption("Importance mesurée par la forêt aléatoire (in-sample), agrégée en 7 familles économiques.")

st.divider()
st.caption("**RexNow** · Rexecode — modèle et application : **Anthony Morlet-Lavidalie**. "
           "Version consultation (lecture seule). Sources ouvertes : INSEE, Banque de France, BCE, "
           "Eurostat, Yahoo, NY Fed, CPB, Douanes… Chiffres à revérifier à la source.")
