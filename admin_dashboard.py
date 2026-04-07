# admin_dashboard.py
"""
Streamlit Analytics-Dashboard fuer die Japanese Learning Website.

Starten:  streamlit run admin_dashboard.py
Zugriff:  http://localhost:8501

Benoetigt DATABASE_URL in .env oder als Umgebungsvariable.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env laden (gleiche wie Flask-App)
load_dotenv(Path(__file__).parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    st.error("DATABASE_URL ist nicht gesetzt. Bitte .env-Datei pruefen.")
    st.stop()


@st.cache_resource
def get_engine():
    """Erstellt eine SQLAlchemy-Engine (gecacht ueber Session-Lifetime)."""
    return create_engine(DATABASE_URL)


def run_query(query: str) -> pd.DataFrame:
    """Fuehrt ein SQL-Query aus und gibt ein DataFrame zurueck."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


# ── Seiten-Konfiguration ──────────────────────────────────────
st.set_page_config(
    page_title="JP Admin Dashboard",
    page_icon="🗾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Japanese Learning Website — Admin Dashboard")

# ── Sidebar-Navigation ────────────────────────────────────────
page = st.sidebar.radio(
    "Navigation",
    ["Uebersicht", "Benutzer", "Lektionen & Kurse", "Content", "Umsatz"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "[Zurueck zum Admin](/admin) | [CRUD-Panel](/admin-panel)"
)


# ══════════════════════════════════════════════════════════════
# SEITE: Uebersicht
# ══════════════════════════════════════════════════════════════
if page == "Uebersicht":
    st.header("Uebersicht")

    # Kennzahlen in einer Reihe
    col1, col2, col3, col4 = st.columns(4)

    users = run_query("SELECT COUNT(*) AS cnt FROM \"user\"")
    lessons = run_query("SELECT COUNT(*) AS cnt FROM lesson")
    courses = run_query("SELECT COUNT(*) AS cnt FROM course")
    vocab = run_query("SELECT COUNT(*) AS cnt FROM vocabulary")

    col1.metric("Benutzer", int(users["cnt"].iloc[0]))
    col2.metric("Lektionen", int(lessons["cnt"].iloc[0]))
    col3.metric("Kurse", int(courses["cnt"].iloc[0]))
    col4.metric("Vokabeln", int(vocab["cnt"].iloc[0]))

    col5, col6, col7, col8 = st.columns(4)

    grammar = run_query("SELECT COUNT(*) AS cnt FROM grammar")
    kanji = run_query("SELECT COUNT(*) AS cnt FROM kanji")
    kana = run_query("SELECT COUNT(*) AS cnt FROM kana")
    quizzes = run_query("SELECT COUNT(*) AS cnt FROM quiz_question")

    col5.metric("Grammatik", int(grammar["cnt"].iloc[0]))
    col6.metric("Kanji", int(kanji["cnt"].iloc[0]))
    col7.metric("Kana", int(kana["cnt"].iloc[0]))
    col8.metric("Quiz-Fragen", int(quizzes["cnt"].iloc[0]))

    # Content pro Lektion
    st.subheader("Content-Items pro Lektion (Top 20)")
    content_per_lesson = run_query("""
        SELECT l.title AS "Lektion", COUNT(lc.id) AS "Content-Items"
        FROM lesson l
        LEFT JOIN lesson_content lc ON l.id = lc.lesson_id
        GROUP BY l.id, l.title
        ORDER BY COUNT(lc.id) DESC
        LIMIT 20
    """)
    if not content_per_lesson.empty:
        st.bar_chart(content_per_lesson.set_index("Lektion"))
    else:
        st.info("Noch keine Lektionen vorhanden.")


# ══════════════════════════════════════════════════════════════
# SEITE: Benutzer
# ══════════════════════════════════════════════════════════════
elif page == "Benutzer":
    st.header("Benutzer-Statistiken")

    # Abo-Verteilung
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Abo-Verteilung")
        subs = run_query("""
            SELECT subscription_level AS "Stufe", COUNT(*) AS "Anzahl"
            FROM "user"
            GROUP BY subscription_level
            ORDER BY COUNT(*) DESC
        """)
        if not subs.empty:
            st.bar_chart(subs.set_index("Stufe"))
            st.dataframe(subs, use_container_width=True)

    with col2:
        st.subheader("Admin-Benutzer")
        admins = run_query("""
            SELECT username AS "Benutzername", email AS "E-Mail"
            FROM "user"
            WHERE is_admin = true
            ORDER BY username
        """)
        st.dataframe(admins, use_container_width=True)

    # Lernfortschritt
    st.subheader("Lernfortschritt der Benutzer")
    progress = run_query("""
        SELECT
            u.username AS "Benutzer",
            COUNT(ulp.id) AS "Gestartete Lektionen",
            SUM(CASE WHEN ulp.is_completed THEN 1 ELSE 0 END) AS "Abgeschlossen",
            ROUND(AVG(ulp.progress_percentage)::numeric, 1) AS "Durchschn. Fortschritt (%)"
        FROM "user" u
        LEFT JOIN user_lesson_progress ulp ON u.id = ulp.user_id
        GROUP BY u.id, u.username
        HAVING COUNT(ulp.id) > 0
        ORDER BY AVG(ulp.progress_percentage) DESC
    """)
    if not progress.empty:
        st.dataframe(progress, use_container_width=True)
    else:
        st.info("Noch keine Fortschrittsdaten vorhanden.")


# ══════════════════════════════════════════════════════════════
# SEITE: Lektionen & Kurse
# ══════════════════════════════════════════════════════════════
elif page == "Lektionen & Kurse":
    st.header("Lektionen & Kurse")

    tab1, tab2 = st.tabs(["Lektionen", "Kurse"])

    with tab1:
        st.subheader("Alle Lektionen")
        lessons_df = run_query("""
            SELECT
                l.id,
                l.title AS "Titel",
                COALESCE(lc.name, '–') AS "Kategorie",
                l.lesson_type AS "Typ",
                l.difficulty_level AS "Schwierigkeit",
                l.is_published AS "Publiziert",
                l.price AS "Preis (CHF)",
                COUNT(DISTINCT lco.id) AS "Content-Items",
                COUNT(DISTINCT qq.id) AS "Quiz-Fragen"
            FROM lesson l
            LEFT JOIN lesson_category lc ON l.category_id = lc.id
            LEFT JOIN lesson_content lco ON l.id = lco.lesson_id
            LEFT JOIN quiz_question qq ON lco.id = qq.lesson_content_id
            GROUP BY l.id, l.title, lc.name, l.lesson_type,
                     l.difficulty_level, l.is_published, l.price
            ORDER BY l.order_index
        """)
        if not lessons_df.empty:
            # Filter
            pub_filter = st.selectbox("Status", ["Alle", "Publiziert", "Entwurf"])
            if pub_filter == "Publiziert":
                lessons_df = lessons_df[lessons_df["Publiziert"]]
            elif pub_filter == "Entwurf":
                lessons_df = lessons_df[~lessons_df["Publiziert"]]

            st.dataframe(lessons_df, use_container_width=True)

            # Fortschritts-Heatmap
            st.subheader("Durchschnittlicher Lernfortschritt pro Lektion")
            avg_progress = run_query("""
                SELECT
                    l.title AS "Lektion",
                    ROUND(AVG(ulp.progress_percentage)::numeric, 1) AS "Fortschritt (%)",
                    COUNT(ulp.id) AS "Lernende"
                FROM lesson l
                LEFT JOIN user_lesson_progress ulp ON l.id = ulp.lesson_id
                GROUP BY l.id, l.title
                HAVING COUNT(ulp.id) > 0
                ORDER BY AVG(ulp.progress_percentage) DESC
            """)
            if not avg_progress.empty:
                st.bar_chart(avg_progress.set_index("Lektion")["Fortschritt (%)"])
                st.dataframe(avg_progress, use_container_width=True)
            else:
                st.info("Noch keine Fortschrittsdaten.")
        else:
            st.info("Noch keine Lektionen vorhanden.")

    with tab2:
        st.subheader("Alle Kurse")
        courses_df = run_query("""
            SELECT
                c.id,
                c.title AS "Titel",
                c.is_published AS "Publiziert",
                c.price AS "Preis (CHF)",
                COUNT(DISTINCT cl.lesson_id) AS "Lektionen"
            FROM course c
            LEFT JOIN course_lessons cl ON c.id = cl.course_id
            GROUP BY c.id, c.title, c.is_published, c.price
            ORDER BY c.title
        """)
        if not courses_df.empty:
            st.dataframe(courses_df, use_container_width=True)
        else:
            st.info("Noch keine Kurse vorhanden.")


# ══════════════════════════════════════════════════════════════
# SEITE: Content
# ══════════════════════════════════════════════════════════════
elif page == "Content":
    st.header("Content-Analyse")

    tab1, tab2, tab3 = st.tabs(["Vokabeln", "Grammatik", "KI-Content"])

    with tab1:
        st.subheader("Vokabeln nach JLPT-Level")
        vocab_jlpt = run_query("""
            SELECT
                COALESCE(CAST(jlpt_level AS VARCHAR), 'Kein Level') AS "JLPT",
                COUNT(*) AS "Anzahl",
                SUM(CASE WHEN created_by_ai THEN 1 ELSE 0 END) AS "Davon KI"
            FROM vocabulary
            GROUP BY jlpt_level
            ORDER BY jlpt_level
        """)
        if not vocab_jlpt.empty:
            st.bar_chart(vocab_jlpt.set_index("JLPT")["Anzahl"])
            st.dataframe(vocab_jlpt, use_container_width=True)

    with tab2:
        st.subheader("Grammatik nach JLPT-Level")
        grammar_jlpt = run_query("""
            SELECT
                COALESCE(CAST(jlpt_level AS VARCHAR), 'Kein Level') AS "JLPT",
                COUNT(*) AS "Anzahl",
                SUM(CASE WHEN created_by_ai THEN 1 ELSE 0 END) AS "Davon KI"
            FROM grammar
            GROUP BY jlpt_level
            ORDER BY jlpt_level
        """)
        if not grammar_jlpt.empty:
            st.bar_chart(grammar_jlpt.set_index("JLPT")["Anzahl"])
            st.dataframe(grammar_jlpt, use_container_width=True)

    with tab3:
        st.subheader("KI-generierter Content — Genehmigungsstatus")

        col1, col2, col3 = st.columns(3)

        kanji_status = run_query("""
            SELECT status AS "Status", COUNT(*) AS "Anzahl"
            FROM kanji WHERE created_by_ai = true
            GROUP BY status
        """)
        with col1:
            st.markdown("**Kanji (KI)**")
            if not kanji_status.empty:
                st.dataframe(kanji_status, use_container_width=True)
            else:
                st.info("Keine KI-Kanji.")

        vocab_status = run_query("""
            SELECT status AS "Status", COUNT(*) AS "Anzahl"
            FROM vocabulary WHERE created_by_ai = true
            GROUP BY status
        """)
        with col2:
            st.markdown("**Vokabeln (KI)**")
            if not vocab_status.empty:
                st.dataframe(vocab_status, use_container_width=True)
            else:
                st.info("Keine KI-Vokabeln.")

        grammar_status = run_query("""
            SELECT status AS "Status", COUNT(*) AS "Anzahl"
            FROM grammar WHERE created_by_ai = true
            GROUP BY status
        """)
        with col3:
            st.markdown("**Grammatik (KI)**")
            if not grammar_status.empty:
                st.dataframe(grammar_status, use_container_width=True)
            else:
                st.info("Keine KI-Grammatik.")


# ══════════════════════════════════════════════════════════════
# SEITE: Umsatz
# ══════════════════════════════════════════════════════════════
elif page == "Umsatz":
    st.header("Umsatz & Kaeufe")

    col1, col2 = st.columns(2)

    # Lektions-Kaeufe
    with col1:
        st.subheader("Lektions-Kaeufe")
        lesson_purchases = run_query("""
            SELECT
                l.title AS "Lektion",
                COUNT(lp.id) AS "Kaeufe",
                ROUND(SUM(lp.price_paid)::numeric, 2) AS "Umsatz (CHF)"
            FROM lesson_purchase lp
            JOIN lesson l ON lp.lesson_id = l.id
            GROUP BY l.id, l.title
            ORDER BY SUM(lp.price_paid) DESC
        """)
        if not lesson_purchases.empty:
            st.dataframe(lesson_purchases, use_container_width=True)
            total_lesson = lesson_purchases["Umsatz (CHF)"].sum()
            st.metric("Total Lektions-Umsatz", f"CHF {total_lesson:,.2f}")
        else:
            st.info("Noch keine Lektions-Kaeufe.")

    # Kurs-Kaeufe
    with col2:
        st.subheader("Kurs-Kaeufe")
        course_purchases = run_query("""
            SELECT
                c.title AS "Kurs",
                COUNT(cp.id) AS "Kaeufe",
                ROUND(SUM(cp.price_paid)::numeric, 2) AS "Umsatz (CHF)"
            FROM course_purchase cp
            JOIN course c ON cp.course_id = c.id
            GROUP BY c.id, c.title
            ORDER BY SUM(cp.price_paid) DESC
        """)
        if not course_purchases.empty:
            st.dataframe(course_purchases, use_container_width=True)
            total_course = course_purchases["Umsatz (CHF)"].sum()
            st.metric("Total Kurs-Umsatz", f"CHF {total_course:,.2f}")
        else:
            st.info("Noch keine Kurs-Kaeufe.")

    # Transaktions-Uebersicht
    st.subheader("Letzte Transaktionen")
    transactions = run_query("""
        SELECT
            pt.transaction_id AS "Transaktion",
            u.username AS "Benutzer",
            pt.item_type AS "Typ",
            pt.amount AS "Betrag (CHF)",
            pt.currency AS "Waehrung",
            pt.state AS "Status",
            pt.created_at AS "Datum"
        FROM payment_transaction pt
        LEFT JOIN "user" u ON pt.user_id = u.id
        ORDER BY pt.created_at DESC
        LIMIT 50
    """)
    if not transactions.empty:
        st.dataframe(transactions, use_container_width=True)
    else:
        st.info("Noch keine Transaktionen vorhanden.")
