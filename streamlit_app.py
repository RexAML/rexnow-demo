"""RexNow — version CONSULTATION publique (Streamlit Community Cloud).

Lecture seule : lit uniquement des sorties PRÉ-CALCULÉES (dossier ./data), aucun
accès aux API sources, aucune clé, aucun recalcul. Accès protégé par mot de passe
(défini dans les Secrets Streamlit Cloud : app_password = "…").

Modèle et application conçus par Anthony Morlet-Lavidalie — Rexecode.
"""
from __future__ import annotations
import json, datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

DATA = Path(__file__).resolve().parent / "data"

# --- couleurs du site rexecode.fr ---
NAVY, BLEU, ORANGE, TEAL = "#1C5385", "#0077B8", "#F5894D", "#2CA089"
NOIR, GRIS, GRILLE = "#14212E", "#A6A6A6", "#E3E7EC"
BLEU_RGB = "0,119,184"
COL = {"combi": BLEU, "rf": ORANGE, "midas": TEAL, "en": NAVY, "obs": NOIR}
NOM = {"combi": "Combinaison", "rf": "Random Forest", "midas": "MIDAS", "en": "ElasticNet"}
MK = {"combi": "COMBI", "rf": "RandomForest", "midas": "MIDAS", "en": "ElasticNet"}
DUMMIES = {"2008Q3", "2008Q4", "2009Q1", "2020Q1", "2020Q2", "2020Q3", "2020Q4", "2021Q3"}

st.set_page_config(page_title="RexNow — Nowcast PIB · Rexecode", page_icon="📈", layout="wide")
st.markdown(f"""<style>
  .stApp {{ background:#FFFFFF; }}
  section[data-testid="stSidebar"] {{ background:#F1F7FC; }}
  .rex-banner {{ background:{NAVY}; border-radius:12px; padding:22px 28px; margin:0 0 14px 0;
    color:#fff; box-shadow:0 2px 10px rgba(28,83,133,0.18); }}
  .rex-banner .rx {{ font-weight:800; letter-spacing:.6px; font-size:14px; color:#BFD8EC; text-transform:uppercase; }}
  .rex-banner .rx b {{ color:{BLEU}; }}
  .rex-banner h1, .rex-banner h1 span {{ margin:.12em 0 .04em; font-size:30px; font-weight:800; color:#fff !important; }}
  .rex-banner h1 span.nm {{ color:{ORANGE} !important; }}
  .rex-banner .sub {{ color:#DCEAF6; font-size:14.5px; }}
  .rex-banner .by {{ margin-top:10px; font-size:12.5px; color:#9FBEDA; }}
  .rex-banner .by b {{ color:#fff; }}
  div[data-testid="stMetricValue"] {{ color:{NAVY}; }}
  .stTabs [aria-selected="true"] {{ color:{BLEU} !important; }}
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


# ======================= mot de passe =======================
def gate():
    if st.session_state.get("rexnow_ok"):
        return
    try:
        pw_ref = st.secrets["app_password"]
    except Exception:
        pw_ref = None
    if not pw_ref:      # aucun secret configuré → accès ouvert, mais on prévient
        st.session_state.rexnow_ok = True
        st.session_state.rexnow_nopw = True
        return
    st.markdown(f"""<div class="rex-banner"><div class="rx">Re<b>xec</b>ode</div>
      <h1><span class="nm">RexNow</span> — accès protégé</h1>
      <div class="sub">Merci de saisir le mot de passe communiqué par Rexecode.</div></div>""",
                unsafe_allow_html=True)
    pw = st.text_input("Mot de passe", type="password", label_visibility="collapsed",
                       placeholder="Mot de passe")
    if not pw:
        st.stop()
    if pw == pw_ref:
        st.session_state.rexnow_ok = True; st.rerun()
    else:
        st.error("Mot de passe incorrect."); st.stop()


gate()

# ======================= chargement des sorties pré-calculées =======================
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

c1, c2, c3 = st.columns([1, 1, 1.4])
c1.metric("2026 T3 — nowcast (h=0)", fr(f3["COMBI"]) + " %")
c2.metric("2026 T4 — prévision (h=1)", fr(f4["COMBI"]) + " %")
c3.info(f"**RMSE test** (hors crise) — nowcast **{r0['COMBI']:.2f}**, prévision **{r1['COMBI']:.2f}** "
        "pts de croissance. Deux modèles distincts par horizon.")

tab_prev, tab_obs, tab_evo, tab_rmse, tab_var = st.tabs(
    ["Prévisions", "Observé vs prévu", "Évolution & incertitude", "RMSE glissant", "Variables"])

# ---------- Prévisions ----------
with tab_prev:
    st.subheader("Prévision par modèle et combinaison")
    rows = [{"Modèle": NOM[k], "2026 T3 (%)": round(f3[MK[k]], 2), "2026 T4 (%)": round(f4[MK[k]], 2),
             "RMSE test nowcast": r0[MK[k]], "RMSE test prévision": r1[MK[k]]}
            for k in ["rf", "midas", "en", "combi"]]
    colL, colR = st.columns([1.1, 1])
    colL.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    xs = [NOM[k] for k in ["rf", "midas", "en", "combi"]]
    fig = go.Figure()
    fig.add_bar(x=xs, y=[f3[MK[k]] for k in ["rf", "midas", "en", "combi"]], name="T3 (nowcast)", marker_color=BLEU)
    fig.add_bar(x=xs, y=[f4[MK[k]] for k in ["rf", "midas", "en", "combi"]], name="T4 (prévision)", marker_color=ORANGE)
    fig.update_layout(barmode="group", height=320, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis_title="croissance t/t (%)", plot_bgcolor="white", legend=dict(orientation="h", y=1.12))
    fig.update_yaxes(gridcolor=GRILLE, zerolinecolor=GRIS)
    colR.plotly_chart(fig, use_container_width=True)
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
    fig.add_scatter(x=x, y=D["actual"], name="PIB observé", mode="lines", line=dict(color=NOIR, width=2.6))
    for k in sel:
        col = {"combi": "combi", "rf": "RandomForest", "midas": "MIDAS", "en": "ElasticNet"}[k]
        fig.add_scatter(x=x, y=D[col], name=NOM[k], mode="lines", line=dict(color=COL[k], width=1.8))
    fig.add_vrect(x0=qdate("2000Q1"), x1=qdate("2014Q4"), fillcolor=GRIS, opacity=0.10,
                  line_width=0, annotation_text="in-sample", annotation_position="top left")
    fig.add_vline(x=qdate("2015Q1"), line=dict(color=GRIS, dash="dot"))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
                      yaxis_title="croissance t/t (%)", legend=dict(orientation="h", y=1.1), hovermode="x unified")
    fig.update_yaxes(gridcolor=GRILLE, zerolinecolor=GRIS)
    st.plotly_chart(fig, use_container_width=True)
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
                        fillcolor=f"rgba({BLEU_RGB},0.10)", line_width=0, name="IC 95 %", hoverinfo="skip")
        fig.add_scatter(x=x + x[::-1], y=up68 + lo68[::-1], fill="toself",
                        fillcolor=f"rgba({BLEU_RGB},0.22)", line_width=0, name="IC 68 %", hoverinfo="skip")
        fig.add_scatter(x=x, y=center, mode="lines+markers+text", line=dict(color=BLEU, width=2.4),
                        marker=dict(size=11, color=[BLEU if k else "white" for k in known],
                                    line=dict(color=BLEU, width=2)),
                        text=[fr(c) if k else "" for c, k in zip(center, known)],
                        textposition="top center", name="prévision")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), title=titre,
                          plot_bgcolor="white", showlegend=False,
                          xaxis=dict(tickmode="array", tickvals=x, ticktext=stages))
        fig.update_yaxes(gridcolor=GRILLE, zerolinecolor=GRIS, title="croissance t/t (%)")
        return fig

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
    e1.plotly_chart(funnel(st3, rm3, c3v, known3, "2026 T3 — nowcast (h=0)"), use_container_width=True)
    e2.plotly_chart(funnel(st4, rm4, c4v, known4, "2026 T4 — prévision (h=1)"), use_container_width=True)

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
    fig.add_vline(x=qdate("2015Q1"), line=dict(color=GRIS, dash="dot"))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
                      yaxis_title="RMSE (pts)", legend=dict(orientation="h", y=1.1), hovermode="x unified")
    fig.update_yaxes(gridcolor=GRILLE, rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Trimestres de crise neutralisés. À gauche du pointillé : in-sample ; à droite : hors-échantillon.")

# ---------- Variables ----------
with tab_var:
    st.subheader("Catégories de variables les plus utiles")
    agg = pd.Series(loadjson(DATA / "cats_importance.json")).sort_values()
    fig = go.Figure(go.Bar(x=agg.values, y=agg.index, orientation="h", marker_color=BLEU,
                           text=[f"{v:.0f}%" for v in agg.values], textposition="outside"))
    fig.update_layout(height=380, margin=dict(l=10, r=30, t=10, b=10), plot_bgcolor="white",
                      xaxis_title="part de l'importance (%)")
    fig.update_xaxes(gridcolor=GRILLE)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Importance mesurée par la forêt aléatoire (in-sample), agrégée en 7 familles économiques.")

st.divider()
st.caption("**RexNow** · Rexecode — modèle et application : **Anthony Morlet-Lavidalie**. "
           "Version consultation (lecture seule). Sources ouvertes : INSEE, Banque de France, BCE, "
           "Eurostat, Yahoo, NY Fed, CPB, Douanes… Chiffres à revérifier à la source.")
