import flet as ft
import psycopg2
import psycopg2.extras
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

cloudinary.config(
    cloud_name  = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key     = os.getenv("CLOUDINARY_API_KEY"),
    api_secret  = os.getenv("CLOUDINARY_API_SECRET"),
    secure      = True
)

def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as c:
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, name TEXT, status TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS student_data (
                username TEXT PRIMARY KEY, roll_no TEXT, branch TEXT, semester TEXT,
                email TEXT, phone TEXT, classes_attended TEXT, classes_total TEXT,
                sub1_name TEXT, sub1_s1 TEXT, sub1_s2 TEXT,
                sub2_name TEXT, sub2_s1 TEXT, sub2_s2 TEXT,
                sub3_name TEXT, sub3_s1 TEXT, sub3_s2 TEXT,
                sub4_name TEXT, sub4_s1 TEXT, sub4_s2 TEXT,
                sub5_name TEXT, sub5_s1 TEXT, sub5_s2 TEXT, profile_pic TEXT)''')
            c.execute("INSERT INTO users VALUES ('admin','adminpassword','admin','System Administrator','approved') ON CONFLICT (username) DO NOTHING")
            c.execute("INSERT INTO users VALUES ('aaditya','studentpassword','student','Aaditya Chaudhary','approved') ON CONFLICT (username) DO NOTHING")
            c.execute("""INSERT INTO student_data VALUES
                ('aaditya','2026CS101','Computer Science','4th','aaditya@rkgitm.edu','9876543210',
                 '38','45','Data Structures','42/50','45/50','Operating Systems','38/50','Not Uploaded',
                 'Computer Networks','45/50','48/50','Database Systems','40/50','42/50',
                 'Discrete Math','35/50','Not Uploaded','') ON CONFLICT (username) DO NOTHING""")
        conn.commit()

init_db()

def main(page: ft.Page):
    page.title = "RKGITM Portal"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO

    session = {"username": "", "name": ""}

    # ── Profile pic via URL paste (no FilePicker - fully compatible) ──────────
    pic_url_field = ft.TextField(
        label="Paste image URL (e.g. from imgur.com)",
        width=380,
        hint_text="https://i.imgur.com/yourimage.jpg"
    )
    pic_status = ft.Text(visible=False)

    def close_dialog(e):
        pic_dialog.open = False
        page.update()

    def save_new_pic(e):
        url = pic_url_field.value.strip()
        if not url:
            pic_status.value = "Please paste an image URL first!"
            pic_status.color = ft.colors.RED
            pic_status.visible = True
            page.update()
            return
        try:
            with get_conn() as conn:
                with conn.cursor() as c:
                    c.execute("UPDATE student_data SET profile_pic=%s WHERE username=%s",
                              (url, session["username"]))
                conn.commit()
            pic_dialog.open = False
            pic_status.visible = False
            page.update()
            show_student_dashboard(session["username"], session["name"])
        except Exception as ex:
            pic_status.value = f"Failed: {ex}"
            pic_status.color = ft.colors.RED
            pic_status.visible = True
            page.update()

    pic_dialog = ft.AlertDialog(
        title=ft.Text("Set Profile Picture"),
        content=ft.Column([
            ft.Text("Paste a direct image URL:"),
            pic_url_field,
            ft.Text("Tip: Upload to imgur.com and paste the link here", size=11, color=ft.colors.GREY),
            pic_status
        ], tight=True),
        actions=[
            ft.TextButton("Save", on_click=save_new_pic),
            ft.TextButton("Cancel", on_click=close_dialog)
        ]
    )
    page.overlay.append(pic_dialog)

    def open_pic_dialog(e):
        pic_url_field.value = ""
        pic_status.visible = False
        pic_dialog.open = True
        page.update()

    # ── Auth ──────────────────────────────────────────────────────────────────
    def handle_login(e, username_field, password_field, error_text):
        user     = username_field.value.lower() if username_field.value else ""
        password = password_field.value
        try:
            with get_conn() as conn:
                with conn.cursor() as c:
                    c.execute("SELECT role, name, status FROM users WHERE username=%s AND password=%s",
                              (user, password))
                    record = c.fetchone()
        except Exception as ex:
            error_text.value = f"DB error: {ex}"
            error_text.visible = True
            page.update()
            return
        if record:
            role, name, status = record
            if status == 'pending':
                error_text.value = "Account pending admin approval."
                error_text.visible = True
            else:
                error_text.visible  = False
                session["username"] = user
                session["name"]     = name
                if role == "admin":
                    show_admin_dashboard(name)
                else:
                    show_student_dashboard(user, name)
        else:
            error_text.value   = "Invalid credentials."
            error_text.visible = True
        page.update()

    def handle_registration(e, fields, error_text):
        for field in fields.values():
            if not field.value:
                error_text.value   = "All fields are required!"
                error_text.color   = ft.colors.RED
                error_text.visible = True
                page.update()
                return
        user = fields['username'].value.lower()
        try:
            with get_conn() as conn:
                with conn.cursor() as c:
                    c.execute("INSERT INTO users VALUES (%s,%s,'student',%s,'approved')",
                              (user, fields['password'].value, fields['name'].value))
                    c.execute("""INSERT INTO student_data VALUES
                               (%s,%s,%s,%s,%s,%s,'0','0',
                                'Subject 1','-','-','Subject 2','-','-',
                                'Subject 3','-','-','Subject 4','-','-',
                                'Subject 5','-','-','')""",
                              (user, fields['roll'].value, fields['branch'].value,
                               fields['sem'].value, fields['email'].value, fields['phone'].value))
                conn.commit()
            show_login_page("Registration Successful! You can now log in.")
        except Exception as ex:
            error_text.value   = "Username already exists or error occurred!"
            error_text.color   = ft.colors.RED
            error_text.visible = True
            page.update()

    def logout(e):
        session["username"] = ""
        session["name"]     = ""
        show_login_page()

    # ── Views ─────────────────────────────────────────────────────────────────
    def show_login_page(message=""):
        page.clean()
        username_field   = ft.TextField(label="Username", width=300)
        password_field   = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        login_error_text = ft.Text(value=message,
                                   color=ft.colors.GREEN if message else ft.colors.RED,
                                   visible=bool(message))
        page.add(
            ft.Container(height=50),
            ft.Text("RKGITM Portal", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            username_field,
            password_field,
            login_error_text,
            ft.ElevatedButton("Login",
                on_click=lambda e: handle_login(e, username_field, password_field, login_error_text),
                width=300,
                style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)),
            ft.TextButton("New Student? Register Here", on_click=lambda _: show_register_page()),
            ft.Container(height=20),
            ft.Text("Admin: admin / adminpassword", size=12, color=ft.colors.GREY)
        )
        page.update()

    def show_register_page():
        page.clean()
        reg_fields = {
            'name':     ft.TextField(label="Full Name",           width=300),
            'username': ft.TextField(label="Choose Username",     width=300),
            'password': ft.TextField(label="Choose Password",     password=True, width=300),
            'roll':     ft.TextField(label="Roll Number",         width=300),
            'branch':   ft.TextField(label="Branch (e.g., CSE)", width=300),
            'sem':      ft.TextField(label="Semester",            width=300),
            'email':    ft.TextField(label="Email",               width=300),
            'phone':    ft.TextField(label="Phone Number",        width=300),
        }
        error_text = ft.Text(visible=False)
        page.add(
            ft.Container(height=40),
            ft.Text("Student Registration", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            *reg_fields.values(),
            error_text,
            ft.ElevatedButton("Submit Registration",
                on_click=lambda e: handle_registration(e, reg_fields, error_text),
                width=300,
                style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)),
            ft.TextButton("Back to Login", on_click=lambda _: show_login_page())
        )
        page.update()

    def show_student_dashboard(username, name):
        page.clean()
        with get_conn() as conn:
            with conn.cursor() as c:
                c.execute("SELECT * FROM student_data WHERE username=%s", (username,))
                data = c.fetchone()
        (_, roll, branch, sem, email, phone, att_done, att_tot,
         n1, s1_1, s1_2, n2, s2_1, s2_2, n3, s3_1, s3_2,
         n4, s4_1, s4_2, n5, s5_1, s5_2, profile_pic) = data
        try:
            percent     = round((int(att_done) / int(att_tot)) * 100, 1)
            att_display = f"{att_done}/{att_tot} Classes ({percent}%)"
            att_color   = ft.colors.GREEN_400 if percent >= 75 else ft.colors.RED_400
        except:
            att_display = "No Classes Recorded"
            att_color   = ft.colors.GREY
        subjects = [(n1,s1_1,s1_2),(n2,s2_1,s2_2),(n3,s3_1,s3_2),(n4,s4_1,s4_2),(n5,s5_1,s5_2)]
        subject_rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(sub, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(s1)),
                ft.DataCell(ft.Text(s2))
            ]) for sub, s1, s2 in subjects if sub
        ]
        avatar = (
            ft.CircleAvatar(foreground_image_src=profile_pic, radius=45)
            if profile_pic
            else ft.CircleAvatar(content=ft.Icon(ft.icons.PERSON, size=40), radius=45,
                                 bgcolor=ft.colors.BLUE_GREY_800)
        )
        page.add(
            ft.Container(height=20),
            ft.Row([ft.Text("Student Dashboard", size=24, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.icons.LOGOUT, on_click=logout)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([avatar, ft.Column([
                ft.Text(name, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"{branch} | Semester {sem}", color=ft.colors.BLUE_300),
                ft.ElevatedButton("Set Profile Picture", on_click=open_pic_dialog, height=35)
            ])], alignment=ft.MainAxisAlignment.START),
            ft.Container(height=20),
            ft.Card(content=ft.Container(content=ft.Column([
                ft.Text("Personal Information", weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Roll No: {roll}"),
                ft.Text(f"Email: {email}"),
                ft.Text(f"Phone: {phone}")
            ]), padding=15, width=550)),
            ft.Card(content=ft.Container(content=ft.Column([
                ft.Text("Academics & Attendance", weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(att_display, color=att_color, weight=ft.FontWeight.BOLD, size=18),
                ft.Container(height=10),
                ft.DataTable(
                    columns=[ft.DataColumn(label=ft.Text("Subject")),
                             ft.DataColumn(label=ft.Text("Sessional 1")),
                             ft.DataColumn(label=ft.Text("Sessional 2"))],
                    rows=subject_rows)
            ]), padding=15, width=550)),
            ft.Container(height=40)
        )
        page.update()

    def show_admin_dashboard(name):
        page.clean()
        target_student    = ft.TextField(label="Selected Student", width=390, read_only=True)
        edit_sem          = ft.TextField(label="Current Semester", width=150)
        admin_status_text = ft.Text(visible=False)
        att_attended      = ft.TextField(label="Classes Attended",  width=265)
        att_total         = ft.TextField(label="Total Classes Held", width=265)
        subject_inputs = [
            {"name": ft.TextField(label=f"Sub {i+1} Name", width=260),
             "s1":   ft.TextField(label="S1 Marks", width=130),
             "s2":   ft.TextField(label="S2 Marks", width=130)}
            for i in range(5)
        ]
        students_table = ft.DataTable(
            columns=[ft.DataColumn(label=ft.Text("Name")),
                     ft.DataColumn(label=ft.Text("Roll No")),
                     ft.DataColumn(label=ft.Text("Select"))],
            rows=[]
        )

        def select_student(e, selected_username):
            target_student.value = selected_username
            with get_conn() as conn:
                with conn.cursor() as c:
                    c.execute("SELECT * FROM student_data WHERE username=%s", (selected_username,))
                    data = c.fetchone()
            if data:
                _, _, _, sem, _, _, a_done, a_tot, n1,s1_1,s1_2, n2,s2_1,s2_2, n3,s3_1,s3_2, n4,s4_1,s4_2, n5,s5_1,s5_2, _ = data
                edit_sem.value     = sem
                att_attended.value = a_done
                att_total.value    = a_tot
                for i, vals in enumerate([(n1,s1_1,s1_2),(n2,s2_1,s2_2),(n3,s3_1,s3_2),(n4,s4_1,s4_2),(n5,s5_1,s5_2)]):
                    subject_inputs[i]["name"].value = vals[0]
                    subject_inputs[i]["s1"].value   = vals[1]
                    subject_inputs[i]["s2"].value   = vals[2]
            admin_status_text.value   = f"Editing: {selected_username}"
            admin_status_text.color   = ft.colors.BLUE_300
            admin_status_text.visible = True
            page.update()

        def refresh_table(e=None):
            query = search_bar.value.lower() if search_bar.value else ""
            with get_conn() as conn:
                with conn.cursor() as c:
                    if query:
                        c.execute('''SELECT users.name, student_data.roll_no, student_data.username
                            FROM users JOIN student_data ON users.username=student_data.username
                            WHERE users.role='student'
                            AND (LOWER(users.name) LIKE %s OR LOWER(student_data.roll_no) LIKE %s)''',
                            (f'%{query}%', f'%{query}%'))
                    else:
                        c.execute('''SELECT users.name, student_data.roll_no, student_data.username
                            FROM users JOIN student_data ON users.username=student_data.username
                            WHERE users.role='student' ''')
                    all_students = c.fetchall()
            students_table.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(s_name)),
                    ft.DataCell(ft.Text(s_roll)),
                    ft.DataCell(ft.ElevatedButton("Select",
                        on_click=lambda e, u=s_user: select_student(e, u)))
                ]) for s_name, s_roll, s_user in all_students
            ]
            page.update()

        def handle_upload(e):
            student = target_student.value
            if not student:
                admin_status_text.value   = "Please select a student first!"
                admin_status_text.color   = ft.colors.RED
                admin_status_text.visible = True
                page.update()
                return
            values = (
                edit_sem.value, att_attended.value, att_total.value,
                subject_inputs[0]["name"].value, subject_inputs[0]["s1"].value, subject_inputs[0]["s2"].value,
                subject_inputs[1]["name"].value, subject_inputs[1]["s1"].value, subject_inputs[1]["s2"].value,
                subject_inputs[2]["name"].value, subject_inputs[2]["s1"].value, subject_inputs[2]["s2"].value,
                subject_inputs[3]["name"].value, subject_inputs[3]["s1"].value, subject_inputs[3]["s2"].value,
                subject_inputs[4]["name"].value, subject_inputs[4]["s1"].value, subject_inputs[4]["s2"].value,
                student
            )
            with get_conn() as conn:
                with conn.cursor() as c:
                    c.execute('''UPDATE student_data SET
                        semester=%s, classes_attended=%s, classes_total=%s,
                        sub1_name=%s, sub1_s1=%s, sub1_s2=%s,
                        sub2_name=%s, sub2_s1=%s, sub2_s2=%s,
                        sub3_name=%s, sub3_s1=%s, sub3_s2=%s,
                        sub4_name=%s, sub4_s1=%s, sub4_s2=%s,
                        sub5_name=%s, sub5_s1=%s, sub5_s2=%s
                        WHERE username=%s''', values)
                conn.commit()
            admin_status_text.value   = f"Updated {student} successfully!"
            admin_status_text.color   = ft.colors.GREEN
            admin_status_text.visible = True
            page.update()

        def handle_wipe(e):
            student = target_student.value
            if not student:
                admin_status_text.value   = "Select a student first!"
                admin_status_text.color   = ft.colors.RED
                admin_status_text.visible = True
                page.update()
                return
            with get_conn() as conn:
                with conn.cursor() as c:
                    c.execute('''UPDATE student_data SET
                        classes_attended='0', classes_total='0',
                        sub1_s1='-', sub1_s2='-', sub2_s1='-', sub2_s2='-',
                        sub3_s1='-', sub3_s2='-', sub4_s1='-', sub4_s2='-',
                        sub5_s1='-', sub5_s2='-' WHERE username=%s''', (student,))
                conn.commit()
            admin_status_text.value   = "Data wiped! Set new semester and upload."
            admin_status_text.color   = ft.colors.ORANGE_400
            admin_status_text.visible = True
            select_student(None, student)

        search_bar = ft.TextField(label="Search by Name or Roll No...", width=400, on_change=refresh_table)
        refresh_table()

        page.add(
            ft.Container(height=20),
            ft.Row([ft.Text("Admin Control Panel", size=24, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.icons.LOGOUT, on_click=logout)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Text("Student Database", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_300),
            search_bar, students_table,
            ft.Container(height=30), ft.Divider(),
            ft.Text("Edit Selected Student:", weight=ft.FontWeight.BOLD),
            ft.Row([target_student, edit_sem]),
            ft.Text("Attendance", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_300),
            ft.Row([att_attended, att_total]),
            ft.Text("Subjects & Marks", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_GREY_300),
            *[ft.Row([inp["name"], inp["s1"], inp["s2"]]) for inp in subject_inputs],
            ft.Container(height=10),
            ft.ElevatedButton("Upload All Data", on_click=handle_upload, width=550,
                style=ft.ButtonStyle(bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)),
            ft.ElevatedButton("Start New Semester (Wipe Data)", on_click=handle_wipe, width=550,
                style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE)),
            admin_status_text,
            ft.Container(height=40)
        )
        page.update()

    show_login_page()

port = int(os.getenv("PORT", 8502))
ft.run(main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")