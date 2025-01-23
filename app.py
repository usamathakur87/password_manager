import streamlit as st
from database import create_tables
from auth import register, sign_in, reset_password, forgot_password_flow
from suppliers import (
    view_supplier_details,
    modify_supplier_details,
    add_new_suppliers,
    view_password_reset_reminders
)

def main():
    create_tables()

    # Centered title and subtitle using HTML
    st.markdown("<h1 style='text-align: center;'>Password Manager</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Developed by Usama Thakur</p>", unsafe_allow_html=True)
    st.write("---")


    # State management: store user info if signed in
    if "user_data" not in st.session_state:
        st.session_state.user_data = None
    if "sign_in_attempts" not in st.session_state:
        st.session_state.sign_in_attempts = 0

    # Radio to switch between Register & Sign In
    choice = st.radio("Choose an option:", ("Register", "Sign In"))
    
    if choice == "Register":
        st.subheader("Register")
        username = st.text_input("Enter a unique username:")
        email = st.text_input("Enter your email:")
        password = st.text_input("Enter your password:", type="password")
        if st.button("Register"):
            if username and email and password:
                success, msg = register(username, email, password)
                st.write(msg)
            else:
                st.write("Please fill all fields.")

    else:
        # Sign In
        st.subheader("Sign In")
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sign In"):
                if username and password:
                    success, msg, user_data = sign_in(username, password)
                    if success:
                        st.session_state.user_data = user_data
                        st.session_state.sign_in_attempts = 0
                        st.write(msg)
                    else:
                        st.session_state.sign_in_attempts += 1
                        st.write(msg)

                        # If attempts reached 2
                        if st.session_state.sign_in_attempts >= 2:
                            st.warning("You have entered the wrong password twice.")
                            st.write("Options:")
                            st.write(" - Reset password below")
                            st.write(" - Try again")
                            st.write(" - Or simply reload the page to exit sign in")

                else:
                    st.write("Please enter username and password.")

        with col2:
            if st.button("Forgot Password?"):
                # If user typed in a valid username but is failing sign-in
                # or we want to do the reset flow
                if username:
                    # We must fetch the email from DB if user exists
                    success, msg, user_data = sign_in(username, "dummy")  # just to get user_data
                    if user_data:
                        user_id, db_username, db_email, db_password = user_data
                        otp_code = forgot_password_flow(db_email, user_id)
                        if otp_code:
                            st.info("OTP has been sent to your email. Please enter it below:")
                            user_otp = st.text_input("Enter OTP:", type="password")
                            new_pass = st.text_input("Enter your new password:", type="password")
                            if st.button("Reset Now"):
                                if user_otp == otp_code:
                                    reset_password(user_id, new_pass)
                                    st.success("Password has been reset. Please sign in again.")
                                    st.session_state.sign_in_attempts = 0
                                else:
                                    st.error("OTP mismatch.")
                        else:
                            st.error("Failed to send OTP. Check your email configuration.")
                    else:
                        st.error("That username does not exist. Please register or check spelling.")
                else:
                    st.write("Enter a username first, then click 'Forgot Password?' again.")

    # If user_data is set, show the main menu
    if st.session_state.user_data:
        user_id, username, email, db_password = st.session_state.user_data

        st.markdown("---")
        st.subheader("Main Menu")

        menu_choice = st.selectbox("Choose an action:", [
            "View Supplier Details",
            "Modify Supplier Details",
            "Add New Suppliers",
            "View Supplier Password Reset Reminders",
            "Log Out"
        ])

        if menu_choice == "View Supplier Details":
            view_supplier_details(st.session_state.user_data)
        elif menu_choice == "Modify Supplier Details":
            modify_supplier_details(st.session_state.user_data)
        elif menu_choice == "Add New Suppliers":
            add_new_suppliers(st.session_state.user_data)
        elif menu_choice == "View Supplier Password Reset Reminders":
            view_password_reset_reminders(st.session_state.user_data)
        elif menu_choice == "Log Out":
            st.session_state.user_data = None
            st.write("Logged out.")

if __name__ == "__main__":
    main()
