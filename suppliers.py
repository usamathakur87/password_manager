from datetime import datetime, timedelta
import csv
import unicodedata
import streamlit as st
from database import create_connection
from email_otp import generate_otp, send_otp_via_email

def parse_datetime(dt_string):
    try:
        return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")  # with microseconds
    except ValueError:
        return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")    # without microseconds

def view_supplier_details(current_user):
    """
    Display all supplier details for this user.
    Allows toggling password masking after OTP verification.
    """
    user_id, username, email, _ = current_user

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT supplier_id, supplier_name, office_id, user_id, password, url, last_reset
        FROM suppliers
        WHERE owner_user_id = ?
    """, (user_id,))
    suppliers = cursor.fetchall()

    conn.close()

    if not suppliers:
        st.write("No suppliers added yet.")
        return

    # Show them in a selectbox
    options = [f"{s[0]} - {s[1]}" for s in suppliers]  # "supplier_id - supplier_name"
    selected_option = st.selectbox("Select a supplier to view details:", options)

    # Parse out the supplier_id from the string
    selected_supplier_id = int(selected_option.split(" - ")[0])

    # Retrieve the selected supplier row
    chosen = [s for s in suppliers if s[0] == selected_supplier_id]
    if not chosen:
        st.write("Supplier not found.")
        return

    sup_id, sup_name, office_id, sup_user_id, pw, url, last_reset = chosen[0]

    st.subheader(f"Supplier: {sup_name}")
    st.write(f"Office ID: {office_id if office_id else 'Not Provided'}")
    st.write(f"User ID: {sup_user_id}")

    # By default, mask the password
    masked_pw = "*" * len(pw)
    st.write(f"Password: {masked_pw}")
    st.write(f"Site URL: {url}")
    st.write(f"Last Reset: {last_reset if last_reset else 'Not set'}")

    # Show reset reminder if there's a last_reset
    if last_reset:
        from datetime import datetime, timedelta
        def parse_datetime(dt_string):
            try:
                return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")  # microseconds
            except ValueError:
                return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")    # no microseconds

        last_reset_dt = parse_datetime(last_reset)
        next_reset_dt = last_reset_dt + timedelta(days=30)
        reminder_dt = next_reset_dt - timedelta(days=7)
        st.write(f"Password Reset Reminder: {reminder_dt}")
    else:
        st.write("Password Reset Reminder: Not set")

    # -----------
    # UNMASK FLOW
    # -----------
    # We store OTP in st.session_state to persist across re-runs
    if "unmask_otp" not in st.session_state:
        st.session_state.unmask_otp = None
    if "unmasked_password" not in st.session_state:
        st.session_state.unmasked_password = None

    st.write("---")
    st.write("**Toggle Password Masking (requires OTP):**")

    # Step A: Send OTP
    if st.button("Send OTP to Unmask Password"):
        otp_code = generate_otp()
        if send_otp_via_email(email, otp_code):
            st.session_state.unmask_otp = otp_code
            st.session_state.unmasked_password = None  # reset any previously unmasked password
            st.success("OTP sent! Please enter it below to unmask the password.")
        else:
            st.error("Failed to send OTP. Check your email configuration.")

    # Step B: User enters OTP
    user_otp = st.text_input("Enter OTP:", type="password")

    # Step C: Confirm Unmask
    if st.button("Confirm Unmask"):
        if not st.session_state.unmask_otp:
            st.error("No OTP was sent. Please click 'Send OTP to Unmask Password' first.")
        else:
            if user_otp == st.session_state.unmask_otp:
                st.success("OTP verified. Password unmasked below.")
                st.session_state.unmasked_password = pw
                # Clear the stored OTP so user can't re-use
                st.session_state.unmask_otp = None
            else:
                st.error("OTP mismatch. Password remains masked.")

    # Display unmasked password if we have it
    if st.session_state.unmasked_password:
        st.write(f"**Unmasked Password:** {st.session_state.unmasked_password}")


def modify_supplier_details(current_user):
    """
    Modify or delete suppliers. Also supports deleting all suppliers,
    using a two-step OTP flow for both single and all-supplier deletion.
    """
    user_id, username, email, _ = current_user
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT supplier_id, supplier_name 
        FROM suppliers
        WHERE owner_user_id = ?
    """, (user_id,))
    suppliers_list = cursor.fetchall()

    if not suppliers_list:
        st.write("No suppliers added yet.")
        conn.close()
        return

    st.subheader("Modify Supplier Details")

    # Create a list of strings "ID - Name"
    supplier_opts = [f"{s[0]} - {s[1]}" for s in suppliers_list]
    selected_opt = st.selectbox("Select supplier:", supplier_opts)
    sup_id = int(selected_opt.split(" - ")[0])

    # Radio to pick "Modify", "Delete", or "Delete All"
    operation = st.radio("Choose an operation:", ["Modify", "Delete", "Delete All"])

    # --------------------------
    # 1) MODIFY SUPPLIER
    # --------------------------
    if operation == "Modify":
        field_choice = st.selectbox(
            "Which field do you want to modify?",
            ["supplier_name", "office_id", "user_id", "password", "url"]
        )
        new_val = st.text_input("Enter new value:")

        # STEP A: Send OTP
        if "modify_otp" not in st.session_state:
            st.session_state.modify_otp = None

        if st.button("Send OTP to Modify"):
            otp_code = generate_otp()
            if send_otp_via_email(email, otp_code):
                st.session_state.modify_otp = otp_code
                st.success("OTP sent! Enter it below to confirm the modification.")
            else:
                st.error("Failed to send OTP. Please check email configuration.")

        # STEP B: Prompt user for OTP
        user_otp = st.text_input("Enter OTP for modifying supplier:", type="password")

        # STEP C: Confirm modification
        if st.button("Confirm Modification"):
            if not st.session_state.modify_otp:
                st.error("No OTP was sent yet. Click 'Send OTP to Modify' first.")
            else:
                if user_otp == st.session_state.modify_otp:
                    # Perform update
                    if field_choice == 'password':
                        cursor.execute(
                            f"UPDATE suppliers SET {field_choice} = ?, last_reset = ? WHERE supplier_id = ?",
                            (new_val, str(datetime.now()), sup_id)
                        )
                    else:
                        cursor.execute(
                            f"UPDATE suppliers SET {field_choice} = ? WHERE supplier_id = ?",
                            (new_val, sup_id)
                        )
                    conn.commit()
                    st.success(f"{field_choice} updated successfully.")
                    # Clear the OTP from session
                    st.session_state.modify_otp = None
                else:
                    st.error("OTP mismatch. No changes made.")

    # --------------------------
    # 2) DELETE SINGLE SUPPLIER
    # --------------------------
    elif operation == "Delete":
        st.write(f"You've chosen to delete supplier ID {sup_id}.")

        # STEP A: Send OTP
        if "delete_one_otp" not in st.session_state:
            st.session_state.delete_one_otp = None

        if st.button("Send OTP for Deletion"):
            otp_code = generate_otp()
            if send_otp_via_email(email, otp_code):
                st.session_state.delete_one_otp = otp_code
                st.success("OTP sent to your email. Enter it below to confirm deletion.")
            else:
                st.error("Failed to send OTP.")

        # STEP B: Prompt user for OTP
        user_otp = st.text_input("Enter OTP to confirm single-supplier deletion:", type="password")

        # STEP C: Confirm deletion
        if st.button("Confirm Deletion"):
            if not st.session_state.delete_one_otp:
                st.error("No OTP was sent. Click 'Send OTP for Deletion' first.")
            else:
                if user_otp == st.session_state.delete_one_otp:
                    cursor.execute("DELETE FROM suppliers WHERE supplier_id = ?", (sup_id,))
                    conn.commit()
                    st.success("Supplier deleted successfully.")
                    st.session_state.delete_one_otp = None
                else:
                    st.error("OTP mismatch. Supplier not deleted.")

    # --------------------------
    # 3) DELETE ALL SUPPLIERS
    # --------------------------
    else:  # operation == "Delete All"
        st.warning("This will delete ALL suppliers associated with your account!")
        
        # Extra reconfirmation step
        confirm_delete_all = st.checkbox("I confirm that I want to DELETE ALL suppliers.")

        if "delete_all_otp" not in st.session_state:
            st.session_state.delete_all_otp = None

        # Only allow sending OTP if user checks the box
        if confirm_delete_all:
            if st.button("Send OTP to Delete All"):
                otp_code = generate_otp()
                if send_otp_via_email(email, otp_code):
                    st.session_state.delete_all_otp = otp_code
                    st.success("OTP has been sent. Enter it below to confirm.")
                else:
                    st.error("Failed to send OTP.")
        else:
            st.info("Check the box above to confirm you want to delete ALL suppliers.")

        user_otp = st.text_input("Enter OTP to confirm deleting all suppliers:", type="password")
        
        if st.button("Confirm Delete All"):
            if not confirm_delete_all:
                st.error("Please check the confirmation box above first.")
            else:
                if not st.session_state.delete_all_otp:
                    st.error("No OTP was sent yet. Click 'Send OTP to Delete All'.")
                else:
                    if user_otp == st.session_state.delete_all_otp:
                        cursor.execute("DELETE FROM suppliers WHERE owner_user_id = ?", (user_id,))
                        conn.commit()
                        st.success("All suppliers have been deleted.")
                        del st.session_state.delete_all_otp
                    else:
                        st.error("OTP mismatch. No suppliers were deleted.")

    conn.close()


def remove_invisible_chars(s: str) -> str:
    """
    Remove (or normalize away) invisible Unicode characters such as \u202A
    """
    filtered = "".join(ch for ch in s if ch.isprintable())
    filtered = unicodedata.normalize('NFKC', filtered)
    return filtered

def add_new_suppliers(current_user):
    """
    Add new suppliers either by CSV or manually.
    """
    user_id, username, email, _ = current_user
    conn = create_connection()
    cursor = conn.cursor()

    st.subheader("Add New Suppliers")
    import_method = st.radio("Import Method", ["CSV", "Manual"])

    if import_method == "CSV":
        csv_path = st.text_input("Enter the full path of the CSV file:")
        if st.button("Import CSV"):
            csv_path = remove_invisible_chars(csv_path)
            try:
                with open(csv_path, 'r', encoding='utf-8-sig') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        supplier_name = row.get("Supplier Name", "").strip()
                        office_id = row.get("Office ID", "").strip()
                        supplier_user_id = row.get("User ID", "").strip()
                        password = row.get("Password", "").strip()
                        url = row.get("URL", "").strip()

                        if not supplier_name or not password:
                            # Minimal check - must have at least name & password
                            continue

                        # Duplicate check
                        cursor.execute("""
                            SELECT 1 FROM suppliers
                            WHERE owner_user_id = ?
                              AND supplier_name = ?
                              AND user_id = ?
                        """, (user_id, supplier_name, supplier_user_id))
                        existing = cursor.fetchone()
                        if existing:
                            st.write(f"Supplier '{supplier_name}' with UserID '{supplier_user_id}' already exists. Skipping...")
                            continue

                        # Insert
                        cursor.execute("""
                            INSERT INTO suppliers
                              (supplier_name, office_id, user_id, password, url, last_reset, owner_user_id) 
                            VALUES (?, ?, ?, ?, ?, DATETIME('now'), ?)
                        """, (supplier_name, office_id, supplier_user_id, password, url, user_id))
                    conn.commit()
                st.write("Suppliers imported successfully from CSV.")
            except Exception as e:
                st.write(f"Error importing from CSV: {e}")

    else:  # Manual
        with st.form("manual_supplier_form"):
            supplier_name = st.text_input("Supplier Name:")
            office_id = st.text_input("Office ID (optional):")
            supplier_user_id = st.text_input("User ID:")
            password = st.text_input("Password:", type="password")
            url = st.text_input("URL:")
            submitted = st.form_submit_button("Add Supplier")

            if submitted:
                if not supplier_name or not password:
                    st.write("Supplier name and password are required.")
                else:
                    # Duplicate check
                    cursor.execute("""
                        SELECT 1 FROM suppliers
                        WHERE owner_user_id = ?
                          AND supplier_name = ?
                          AND user_id = ?
                    """, (user_id, supplier_name, supplier_user_id))
                    existing = cursor.fetchone()
                    if existing:
                        st.write("Supplier already added!")
                    else:
                        cursor.execute("""
                            INSERT INTO suppliers
                              (supplier_name, office_id, user_id, password, url, last_reset, owner_user_id)
                            VALUES (?, ?, ?, ?, ?, DATETIME('now'), ?)
                        """, (supplier_name, office_id, supplier_user_id, password, url, user_id))
                        conn.commit()
                        st.write("Supplier added successfully!")

def view_password_reset_reminders(current_user):
    """
    Display suppliers whose password is due to expire in 7 days or less.
    """
    user_id, username, email, _ = current_user
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT supplier_name, last_reset
        FROM suppliers
        WHERE owner_user_id = ?
    """, (user_id,))
    suppliers_data = cursor.fetchall()
    conn.close()

    if not suppliers_data:
        st.write("No suppliers found.")
        return

    reminders = []
    for sup in suppliers_data:
        sup_name, last_reset = sup
        if last_reset:
            try:
                last_reset_dt = parse_datetime(last_reset)
            except ValueError:
                continue
            expiry_dt = last_reset_dt + timedelta(days=30)
            reminder_dt = expiry_dt - timedelta(days=7)
            now = datetime.now()
            if reminder_dt <= now < expiry_dt:
                reminders.append((sup_name, expiry_dt.strftime("%Y-%m-%d %H:%M:%S")))

    if reminders:
        st.write("Suppliers requiring password reset soon:")
        for item in reminders:
            sup_name, exp_time = item
            st.write(f"- {sup_name}, Expiry Date: {exp_time}")
    else:
        st.write("No supplier passwords are due for reset in the next 7 days.")
