"""Eastside High School: Student Results Management System (Streamlit web app)."""
import altair as alt
import pandas as pd
import streamlit as st

import db
from auth import check_login
from logic import SUBJECTS, calculate_results, grade_for, outcome, remedial_subjects
from report import SCHOOL, class_table, report_card_pdf

SCHOOL_NAME = SCHOOL.title()
BURGUNDY, DEEP, SAND, ROSE = "#8A2D4A", "#2E1420", "#C9A25B", "#D9A5B3"
MAX_ATTEMPTS = 5

st.set_page_config(page_title=f"{SCHOOL_NAME} | Results", page_icon="🎓", layout="wide")
db.init_db()

st.markdown(
    f"""
    <style>
    h1, h2, h3 {{ color: {BURGUNDY} !important; }}
    input::placeholder {{ font-style: italic; opacity: .5; }}
    .block-container {{ padding-top: 4.2rem !important; }}
    [data-testid="stMetricValue"] {{ color: {DEEP}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- small helpers ----------

def flash(message):
    """Remember a success message so it shows after the page reruns."""
    st.session_state.flash = message
    st.toast(message, icon="✅")


def show_flash():
    msg = st.session_state.pop("flash", None)
    if msg:
        st.success(msg, icon="✅")


def bar_chart(df, x, y, color, height=300):
    """A bar chart that does not zoom or rescale when the page is scrolled over it."""
    return alt.Chart(df).mark_bar(color=color).encode(
        x=alt.X(f"{x}:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y}:Q", title=None, scale=alt.Scale(domain=[0, df[y].max() if y == "Students" else 100], nice=True)),
        tooltip=[x, y],
    ).properties(height=height)


def low_marks_red(value):
    return "color: #B3261E; font-weight: 600" if isinstance(value, (int, float)) and value < 50 else ""


def outcome_message(row_or_marks):
    out = outcome(row_or_marks)
    weak = remedial_subjects(row_or_marks)
    if out == "Repeats class":
        st.error("Outcome: repeats the class. The overall average is below 40 (grade F).", icon="⛔")
    elif weak:
        st.warning("Outcome: promoted, but remedial classes are recommended in " + ", ".join(weak) + ".", icon="📘")
    else:
        st.success("Outcome: promoted to the next class.", icon="🎓")


def marks_inputs(prefix, defaults=None):
    cols = st.columns(3)
    marks = {}
    for i, sub in enumerate(SUBJECTS):
        marks[sub] = cols[i % 3].number_input(
            sub, 0.0, 100.0, float((defaults or {}).get(sub, 0.0)), 1.0, key=f"{prefix}_{sub}")
    return marks


# ---------- login ----------

def login_screen():
    st.session_state.setdefault("attempts", 0)
    locked = st.session_state.attempts >= MAX_ATTEMPTS
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown(
            f"""
            <div style="text-align:center;margin:2.5rem 0 1.2rem">
              <div style="font-size:2.6rem;line-height:1">🎓</div>
              <div style="font-family:Georgia,serif;font-size:1.9rem;font-weight:600;color:{BURGUNDY};margin-top:.3rem">{SCHOOL_NAME}</div>
              <div style="letter-spacing:.14em;text-transform:uppercase;font-size:.72rem;color:#6B5159;margin-top:.2rem">Results portal</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            if locked:
                st.error("Too many failed attempts. Refresh the page to try again.")
            student_tab, teacher_tab, admin_tab = st.tabs(["Student", "Teacher", "Admin"])
            with student_tab:
                with st.form("student_login", border=False):
                    adm = st.text_input("Student ID", placeholder="Demo ID: DEMO-001")
                    pin = st.text_input("PIN", type="password", placeholder="Demo PIN: 123456")
                    if st.form_submit_button("View my results", type="primary", disabled=locked, width="stretch"):
                        sid = db.verify_student_pin(adm, pin)
                        if sid:
                            st.session_state.role = "student"
                            st.session_state.user = adm.strip()
                            st.session_state.student_id = sid
                            st.rerun()
                        st.session_state.attempts += 1
                        st.error("Incorrect student ID or PIN.")
            for tab, role, demo_user, demo_pass in ((teacher_tab, "teacher", "teacher", "teacher-demo"),
                                                    (admin_tab, "admin", "admin", "admin-demo")):
                with tab:
                    with st.form(f"{role}_login", border=False):
                        username = st.text_input("Username", placeholder=f"Demo username: {demo_user}", key=f"{role}_u")
                        password = st.text_input("Password", type="password",
                                                 placeholder=f"Demo password: {demo_pass}", key=f"{role}_p")
                        if st.form_submit_button(f"Sign in as {role}", type="primary", disabled=locked, width="stretch"):
                            if check_login(username, password) == role:
                                st.session_state.role = role
                                st.session_state.user = username.strip().lower()
                                st.rerun()
                            st.session_state.attempts += 1
                            st.error("Incorrect username or password.")
        st.markdown(
            "<p style='text-align:center;font-size:.8rem;color:#9A8389;margin-top:.8rem'>"
            "Portfolio demo. All students and marks are fictional.</p>",
            unsafe_allow_html=True,
        )


# ---------- student ----------

def page_student(students):
    me = next((s for s in students if s["id"] == st.session_state.student_id), None)
    if me is None:
        st.error("Your record could not be found.")
        return
    show_flash()
    mates = [s for s in students if s["class_name"] == me["class_name"]]
    table = class_table(mates)
    row = table[table["Adm No"] == me["adm_no"]].iloc[0]
    class_avg = table["Average"].mean()

    st.header(f"Hello, {me['name']}")
    st.caption(f"Student ID {me['adm_no']} · {me['class_name']} · view only")

    a, b, _ = st.columns([1, 1, 2])
    a.metric("Your average", f"{row['Average']:.1f}")
    b.metric("Your grade", row["Grade"])
    outcome_message(me)

    st.subheader("Your marks")
    marks = pd.DataFrame({"Subject": SUBJECTS, "Marks": [me[s] for s in SUBJECTS],
                          "Grade": [grade_for(me[s]) for s in SUBJECTS]})
    st.dataframe(marks.style.map(low_marks_red, subset=["Marks"]).format({"Marks": "{:.0f}"}),
                 hide_index=True, width="stretch")

    c, d, _ = st.columns([1, 1, 2])
    c.metric("Class average", f"{class_avg:.1f}", f"{row['Average'] - class_avg:+.1f} vs class")
    d.metric("Position in class", f"{int(row['Rank'])} of {len(table)}")
    st.download_button("Download my report card (PDF)", report_card_pdf(me, int(row["Rank"]), len(table), "class"),
                       f"report_card_{me['adm_no']}.pdf", "application/pdf")

    st.subheader("Raise an issue")
    st.caption("Missing a mark or something looks wrong? Tell the administrator.")
    with st.form("issue", clear_on_submit=True, border=False):
        msg = st.text_area("Your message", max_chars=500, height=90, label_visibility="collapsed",
                           placeholder="For example: my History mark is missing.")
        if st.form_submit_button("Send to admin"):
            try:
                db.add_issue(me["id"], msg)
                flash("Your issue has been sent to the administrator.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    mine = db.load_issues(student_id=me["id"])
    if mine:
        st.dataframe(pd.DataFrame([{"Sent": i["created_at"][:10], "Message": i["message"], "Status": i["status"],
                                    "Admin reply": i["reply"] or ""} for i in mine]),
                     hide_index=True, width="stretch")

    st.subheader("You compared with the class")
    comp = pd.DataFrame({
        "Subject": SUBJECTS * 2,
        "Series": ["Class average"] * len(SUBJECTS) + ["Your mark"] * len(SUBJECTS),
        "Mark": [round(table[s].mean(), 1) for s in SUBJECTS] + [me[s] for s in SUBJECTS],
    })
    st.altair_chart(
        alt.Chart(comp).mark_bar().encode(
            x=alt.X("Subject:N", sort=SUBJECTS, title=None, axis=alt.Axis(labelAngle=0)),
            xOffset="Series:N",
            y=alt.Y("Mark:Q", title=None, scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Series:N", scale=alt.Scale(domain=["Class average", "Your mark"], range=[ROSE, BURGUNDY]),
                            legend=alt.Legend(orient="top", title=None)),
            tooltip=["Subject", "Series", "Mark"],
        ).properties(height=320),
        width="stretch",
    )


# ---------- staff pages ----------

def page_dashboard():
    students = db.load_students()
    show_flash()
    st.header("Dashboard")
    classes = ["All classes"] + sorted({s["class_name"] for s in students})
    pick = st.selectbox("Class", classes)
    shown = [s for s in students if pick == "All classes" or s["class_name"] == pick]
    if not shown:
        st.info("No students yet.")
        return
    table = class_table(shown)
    top = table.iloc[0]
    passed = (table["Average"] >= 50).mean() * 100
    c = st.columns(5)
    c[0].metric("Students", len(shown))
    c[1].metric("Class average", f"{table['Average'].mean():.1f}")
    c[2].metric("Pass rate (D or above)", f"{passed:.0f}%")
    c[3].metric("Need remedial", int((table["Remedial in"] != "None").sum()))
    c[4].metric("Repeat the class", int((table["Outcome"] == "Repeats class").sum()))

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 students")
        st.dataframe(table.head(10)[["Rank", "Name", "Class", "Average", "Grade"]], hide_index=True, width="stretch")
    with right:
        st.subheader("Needs attention")
        attention = table[table["Outcome"] != "Promoted"].sort_values("Average")
        if attention.empty:
            st.info("No students need remedial work or repeat the class.")
        else:
            st.dataframe(attention[["Name", "Average", "Outcome"]].head(10),
                         hide_index=True, width="stretch")
            if len(attention) > 10:
                st.caption(f"Showing the lowest 10 of {len(attention)}. The full list is in Class report.")

    left, right = st.columns(2)
    with left:
        st.subheader("Average mark by subject")
        avg = pd.DataFrame({"Subject": SUBJECTS, "Average": [round(table[s].mean(), 1) for s in SUBJECTS]})
        st.altair_chart(bar_chart(avg, "Subject", "Average", BURGUNDY), width="stretch")
    with right:
        st.subheader("Grade distribution")
        grades = table["Grade"].value_counts().reindex(list("ABCDEF"), fill_value=0)
        dist = pd.DataFrame({"Grade": grades.index, "Students": grades.values})
        st.altair_chart(bar_chart(dist, "Grade", "Students", ROSE), width="stretch")


def page_students():
    students = db.load_students()
    role = st.session_state.role
    show_flash()
    st.header("Students")
    q = st.text_input("Search by name or admission number")
    shown = [s for s in students if q.lower() in s["name"].lower() or q.lower() in s["adm_no"].lower()]
    table = class_table(shown)
    if table.empty:
        st.info("No students match.")
        return
    st.dataframe(table, hide_index=True, width="stretch")
    st.subheader("Open a student")
    labels = {f"{s['adm_no']} · {s['name']}": s for s in shown}
    chosen = labels[st.selectbox("Student", list(labels))]
    avg, grade = calculate_results(chosen)
    everyone = class_table(students)
    pos = int(everyone.loc[everyone["Adm No"] == chosen["adm_no"], "Rank"].iloc[0])
    st.write(f"**{chosen['name']}**: average {avg:.1f}, grade {grade}, position {pos} of {len(students)}")
    outcome_message(chosen)
    st.download_button("Download report card (PDF)", report_card_pdf(chosen, pos, len(students)),
                       f"report_card_{chosen['adm_no']}.pdf", "application/pdf")
    with st.expander("Edit this student"):
        with st.form(f"edit_{chosen['id']}"):
            name = st.text_input("Name", chosen["name"])
            class_name = st.text_input("Class", chosen["class_name"])
            marks = marks_inputs(f"e{chosen['id']}", chosen)
            if st.form_submit_button("Save changes", type="primary"):
                if not name.strip() or not class_name.strip():
                    st.error("Name and class are required.")
                else:
                    db.update_student(chosen["id"], name, class_name, marks)
                    flash(f"Changes saved for {name.strip()}.")
                    st.rerun()
    if role == "admin":
        with st.expander("Reset this student's PIN"):
            if st.button("Generate a new PIN", key=f"pin_{chosen['id']}"):
                st.session_state.new_pin = (chosen["adm_no"], db.reset_pin(chosen["id"]))
            if st.session_state.get("new_pin", ("",))[0] == chosen["adm_no"]:
                st.success(f"New PIN for {chosen['adm_no']}: **{st.session_state.new_pin[1]}** "
                           "(shown once, give it to the student)")
        with st.expander("Delete this student"):
            sure = st.checkbox("I understand this cannot be undone", key=f"del_{chosen['id']}")
            if st.button("Delete student", disabled=not sure):
                db.delete_student(chosen["id"])
                flash(f"{chosen['name']} has been deleted.")
                st.rerun()


def page_add():
    st.header("Add a student")
    with st.form("add", clear_on_submit=True):
        a, b, c = st.columns(3)
        adm = a.text_input("Admission number")
        name = b.text_input("Full name")
        class_name = c.text_input("Class", "Form 3 East")
        marks = marks_inputs("add")
        if st.form_submit_button("Add student", type="primary"):
            try:
                _, pin = db.add_student(adm, name, class_name, marks)
                st.toast(f"{name.strip()} added.", icon="✅")
                st.success(f"{name.strip()} has been added. Their PIN is **{pin}** (shown once, give it to the student).")
            except ValueError as e:
                st.error(str(e))


def page_report():
    students = db.load_students()
    st.header("Class report")
    classes = ["All classes"] + sorted({s["class_name"] for s in students})
    pick = st.selectbox("Class", classes)
    shown = [s for s in students if pick == "All classes" or s["class_name"] == pick]
    table = class_table(shown)
    if table.empty:
        st.info("No students yet.")
        return
    st.write(f"**Class average:** {table['Average'].mean():.1f}   |   "
             f"**Top student:** {table.iloc[0]['Name']} ({table.iloc[0]['Average']:.1f})")

    st.subheader("Averages by subject")
    subj = pd.DataFrame({
        "Subject": SUBJECTS,
        "Class average": [round(table[s].mean(), 1) for s in SUBJECTS],
        "Highest": [table[s].max() for s in SUBJECTS],
        "Lowest": [table[s].min() for s in SUBJECTS],
        "Pass rate": [f"{(table[s] >= 50).mean() * 100:.0f}%" for s in SUBJECTS],
        "Below 50 (remedial)": [int((table[s] < 50).sum()) for s in SUBJECTS],
    })
    st.dataframe(subj.style.format({"Highest": "{:.0f}", "Lowest": "{:.0f}", "Class average": "{:.1f}"}),
                 hide_index=True, width="stretch")

    st.subheader("Results by student")
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button("Download as CSV", table.to_csv(index=False), "class_report.csv", "text/csv")


def page_issues():
    show_flash()
    st.header("Issues to address")
    open_issues = db.load_issues("Open")
    if not open_issues:
        st.info("No open issues. Students can raise one from their results page.")
    for i in open_issues:
        with st.container(border=True):
            st.markdown(f"**{i['name']}** ({i['adm_no']}, {i['class_name']}) · {i['created_at']} UTC")
            st.write(i["message"])
            reply = st.text_input("Reply to the student (optional)", key=f"reply_{i['id']}")
            if st.button("Mark as resolved", key=f"res_{i['id']}", type="primary"):
                db.resolve_issue(i["id"], reply)
                flash(f"Issue from {i['name']} marked as resolved.")
                st.rerun()
    done = db.load_issues("Resolved")
    if done:
        with st.expander(f"Resolved issues ({len(done)})"):
            st.dataframe(pd.DataFrame([{"Student": f"{i['name']} ({i['adm_no']})", "Message": i["message"],
                                        "Reply": i["reply"] or "", "Resolved": i["resolved_at"]} for i in done]),
                         hide_index=True, width="stretch")


def page_import():
    st.header("Import students (CSV)")
    st.write("Columns: `adm_no`, `name`, `class_name`, " + ", ".join(f"`{s}`" for s in SUBJECTS))
    template = pd.DataFrame(columns=["adm_no", "name", "class_name"] + SUBJECTS)
    st.download_button("Download blank template", template.to_csv(index=False), "students_template.csv", "text/csv")
    up = st.file_uploader("Upload CSV", type="csv")
    if up and st.button("Import", type="primary"):
        try:
            df = pd.read_csv(up, dtype={"adm_no": str})
        except Exception:
            st.error("Could not read that file as CSV.")
            return
        missing = [c for c in ["adm_no", "name", "class_name"] + SUBJECTS if c not in df.columns]
        if missing:
            st.error("Missing columns: " + ", ".join(missing))
            return
        added, problems, pins = 0, [], []
        for i, row in df.iterrows():
            try:
                _, pin = db.add_student(str(row["adm_no"]), str(row["name"]), str(row["class_name"]),
                                        {s: row[s] for s in SUBJECTS})
                pins.append({"adm_no": str(row["adm_no"]), "name": str(row["name"]), "pin": pin})
                added += 1
            except (ValueError, TypeError) as e:
                problems.append(f"Row {i + 2}: {e}")
        st.session_state.import_result = (added, problems, pd.DataFrame(pins))
        st.toast(f"{added} students imported.", icon="✅")
    if "import_result" in st.session_state:
        added, problems, pins = st.session_state.import_result
        st.success(f"{added} students imported.")
        for p in problems:
            st.warning(p)
        if added:
            st.download_button("Download the new students' PINs (CSV)", pins.to_csv(index=False),
                               "student_pins.csv", "text/csv")
            st.caption("PINs are stored hashed and cannot be shown again. Keep this file safe, then delete it.")


# ---------- routing ----------

def header_bar(role):
    left, right = st.columns([3, 1], vertical_alignment="center")
    left.markdown(f"<span style='font-family:Georgia,serif;font-weight:600;color:{BURGUNDY};font-size:1.1rem'>"
                  f"🎓 {SCHOOL_NAME}</span>", unsafe_allow_html=True)
    with right:
        who, out = st.columns([2, 1], vertical_alignment="center")
        who.caption(f"{st.session_state.user} ({role})")
        if out.button("Sign out", width="stretch"):
            st.session_state.clear()
            st.rerun()


def main():
    if "role" not in st.session_state:
        login_screen()
        return
    role = st.session_state.role
    if role == "student":
        header_bar(role)
        page_student(db.load_students())
        return
    pages = [
        st.Page(page_dashboard, title="Dashboard", url_path="dashboard", default=True),
        st.Page(page_students, title="Students", url_path="students"),
        st.Page(page_add, title="Add student", url_path="add"),
        st.Page(page_report, title="Class report", url_path="report"),
    ]
    if role == "admin":
        n = len(db.load_issues("Open"))
        pages.append(st.Page(page_issues, title=f"Issues ({n})" if n else "Issues", url_path="issues"))
        pages.append(st.Page(page_import, title="Import", url_path="import"))
    nav = st.navigation(pages, position="top")
    header_bar(role)
    nav.run()


main()
