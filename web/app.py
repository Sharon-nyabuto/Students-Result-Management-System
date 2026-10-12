"""Student Results Management System: web app (Streamlit)."""
import pandas as pd
import streamlit as st

import db
from auth import check_login
from logic import SUBJECTS, calculate_results
from report import class_table, report_card_pdf

st.set_page_config(page_title="Student Results Management System", page_icon="📊", layout="wide")
db.init_db()


MAX_ATTEMPTS = 5


def login_screen():
    st.title("Student Results Management System")
    st.caption("Portfolio demo. All students and marks are fictional.")
    st.session_state.setdefault("attempts", 0)
    locked = st.session_state.attempts >= MAX_ATTEMPTS
    left, _ = st.columns([1, 1])
    with left:
        if locked:
            st.error("Too many failed attempts. Refresh the page to try again.")
        staff, student = st.tabs(["Staff", "Student"])
        with staff:
            with st.form("staff_login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in", type="primary", disabled=locked):
                    role = check_login(username, password)
                    if role:
                        st.session_state.role = role
                        st.session_state.user = username.strip().lower()
                        st.rerun()
                    st.session_state.attempts += 1
                    st.error("Incorrect username or password.")
            st.info("Demo accounts\n\n**admin** / admin-demo (can also import, delete and reset PINs)\n\n"
                    "**teacher** / teacher-demo (can view, add and edit marks)")
        with student:
            with st.form("student_login"):
                adm = st.text_input("Student ID (admission number)")
                pin = st.text_input("PIN", type="password")
                if st.form_submit_button("View my results", type="primary", disabled=locked):
                    sid = db.verify_student_pin(adm, pin)
                    if sid:
                        st.session_state.role = "student"
                        st.session_state.user = adm.strip()
                        st.session_state.student_id = sid
                        st.rerun()
                    st.session_state.attempts += 1
                    st.error("Incorrect student ID or PIN.")
            st.info("Demo student\n\nStudent ID **DEMO-001** (up to DEMO-040), PIN **123456**")


def marks_inputs(prefix, defaults=None):
    cols = st.columns(3)
    marks = {}
    for i, sub in enumerate(SUBJECTS):
        marks[sub] = cols[i % 3].number_input(
            sub, 0.0, 100.0, float((defaults or {}).get(sub, 0.0)), 1.0, key=f"{prefix}_{sub}")
    return marks


def page_student(students):
    me = next((s for s in students if s["id"] == st.session_state.student_id), None)
    if me is None:
        st.error("Your record could not be found.")
        return
    mates = [s for s in students if s["class_name"] == me["class_name"]]
    table = class_table(mates)
    row = table[table["Adm No"] == me["adm_no"]].iloc[0]
    class_avg = table["Average"].mean()
    st.header(f"Hello, {me['name']}")
    st.caption(f"Student ID {me['adm_no']} · {me['class_name']} · view only")
    c = st.columns(4)
    c[0].metric("Your average", f"{row['Average']:.1f}")
    c[1].metric("Class average", f"{class_avg:.1f}", f"{row['Average'] - class_avg:+.1f} vs class", delta_color="normal")
    c[2].metric("Your grade", row["Grade"])
    c[3].metric("Position in class", f"{int(row['Rank'])} of {len(table)}")
    st.subheader("Subject by subject")
    comp = pd.DataFrame({
        "Subject": SUBJECTS,
        "Your mark": [me[s] for s in SUBJECTS],
        "Class average": [round(table[s].mean(), 1) for s in SUBJECTS],
    })
    comp["Difference"] = (comp["Your mark"] - comp["Class average"]).round(1)
    st.dataframe(comp, hide_index=True, width="stretch")
    st.bar_chart(comp.set_index("Subject")[["Class average", "Your mark"]], color=["#A9C1E0", "#1E4E8C"], stack=False)
    st.download_button("Download my report card (PDF)", report_card_pdf(me, int(row["Rank"]), len(table), "class"),
                       f"report_card_{me['adm_no']}.pdf", "application/pdf")


def page_dashboard(students):
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
    c = st.columns(4)
    c[0].metric("Students", len(shown))
    c[1].metric("Class average", f"{table['Average'].mean():.1f}")
    c[2].metric("Pass rate (D or above)", f"{passed:.0f}%")
    c[3].metric("Top student", top["Name"], f"{top['Average']:.1f}", delta_color="off")
    left, right = st.columns(2)
    left.subheader("Average mark by subject")
    left.bar_chart(pd.Series({s: table[s].mean() for s in SUBJECTS}).round(1), color="#1E4E8C")
    right.subheader("Grade distribution")
    grades = table["Grade"].value_counts().reindex(list("ABCDE"), fill_value=0)
    right.bar_chart(grades, color="#7FA3D1")


def page_students(students, role):
    st.header("Students")
    q = st.text_input("Search by name or admission number")
    shown = [s for s in students if q.lower() in s["name"].lower() or q.lower() in s["adm_no"].lower()]
    table = class_table(shown)
    if table.empty:
        st.info("No students match.")
        return
    st.dataframe(table, hide_index=True, width='stretch')
    st.subheader("Open a student")
    labels = {f"{s['adm_no']} · {s['name']}": s for s in shown}
    chosen = labels[st.selectbox("Student", list(labels))]
    avg, grade = calculate_results(chosen)
    everyone = class_table(students)
    pos = int(everyone.loc[everyone["Adm No"] == chosen["adm_no"], "Rank"].iloc[0])
    st.write(f"**{chosen['name']}**: average {avg:.1f}, grade {grade}, position {pos} of {len(students)}")
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
                    st.success("Saved.")
                    st.rerun()
    if role == "admin":
        with st.expander("Reset this student's PIN"):
            if st.button("Generate a new PIN", key=f"pin_{chosen['id']}"):
                st.session_state.new_pin = (chosen["adm_no"], db.reset_pin(chosen["id"]))
            if st.session_state.get("new_pin", ("",))[0] == chosen["adm_no"]:
                st.success(f"New PIN for {chosen['adm_no']}: **{st.session_state.new_pin[1]}** (shown once, give it to the student)")
        with st.expander("Delete this student"):
            sure = st.checkbox("I understand this cannot be undone", key=f"del_{chosen['id']}")
            if st.button("Delete student", disabled=not sure):
                db.delete_student(chosen["id"])
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
                st.success(f"{name} has been added. Their PIN is **{pin}** (shown once, give it to the student).")
            except ValueError as e:
                st.error(str(e))


def page_report(students):
    st.header("Class report")
    table = class_table(students)
    if table.empty:
        st.info("No students yet.")
        return
    st.write(f"**Class average:** {table['Average'].mean():.1f}   |   "
             f"**Top student:** {table.iloc[0]['Name']} ({table.iloc[0]['Average']:.1f})")
    st.dataframe(table, hide_index=True, width='stretch')
    st.download_button("Download as CSV", table.to_csv(index=False), "class_report.csv", "text/csv")


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
    if "import_result" in st.session_state:
        added, problems, pins = st.session_state.import_result
        st.success(f"{added} students imported.")
        for p in problems:
            st.warning(p)
        if added:
            st.download_button("Download the new students' PINs (CSV)", pins.to_csv(index=False),
                               "student_pins.csv", "text/csv")
            st.caption("PINs are stored hashed and cannot be shown again. Keep this file safe, then delete it.")


def main():
    if "role" not in st.session_state:
        login_screen()
        return
    role = st.session_state.role
    if role == "student":
        with st.sidebar:
            st.markdown("### My results")
            st.caption(f"Signed in as **{st.session_state.user}**")
            if st.button("Sign out"):
                st.session_state.clear()
                st.rerun()
        page_student(db.load_students())
        return
    pages = ["Dashboard", "Students", "Add student", "Class report"] + (["Import"] if role == "admin" else [])
    with st.sidebar:
        st.markdown("### Results system")
        st.caption(f"Signed in as **{st.session_state.user}** ({role})")
        page = st.radio("Go to", pages, label_visibility="collapsed")
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()
    students = db.load_students()
    if page == "Dashboard":
        page_dashboard(students)
    elif page == "Students":
        page_students(students, role)
    elif page == "Add student":
        page_add()
    elif page == "Class report":
        page_report(students)
    else:
        page_import()


main()
