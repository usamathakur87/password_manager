# main.py
from database import create_tables
from auth import sign_in, register
from suppliers import (
    view_supplier_details,
    modify_supplier_details,
    add_new_suppliers,
    view_password_reset_reminders
)

def main_menu():
    st.subheader("Main Menu")
    st.sidebar.write(f"Logged in as: {st.session_state['current_user']['username']}")

    menu_choice = st.sidebar.radio(
        "Menu Options", ["Option 1", "Option 2", "Logout"]
    )

    if menu_choice == "Logout":
        st.session_state["current_user"] = None
        st.session_state["page"] = "sign_in"  # Return to login
        st.experimental_rerun()  # Ensure the app reruns after logout


def main():
    st.markdown(
        "<h2 style='text-align: center;'>"
        "Password Manager - Streamlit Version"
        "</h2>"
        "<p style='text-align: center;'>"
        "Developed by Usama Thakur"
        "</p>",
        unsafe_allow_html=True
    )

    # Initialize session state variables
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "sign_in"

    # Debugging: Display current state
    st.write("Debug: Current page:", st.session_state["page"])
    st.write("Debug: Current user:", st.session_state["current_user"])

    # If no user is logged in, allow toggling between Sign In and Register
    if not st.session_state["current_user"]:
        page_choice = st.radio("Choose an Action:", ["Sign In", "Register"])

        if page_choice == "Sign In":
            st.session_state["page"] = "sign_in"
        elif page_choice == "Register":
            st.session_state["page"] = "register"

    # Route based on the current page state
    if st.session_state["page"] == "sign_in":
        streamlit_sign_in()
    elif st.session_state["page"] == "register":
        streamlit_register()
    elif st.session_state["page"] == "main_menu":
        main_menu()



def welcome_screen():
    """
    Display the welcome screen and prompt user to sign in, register or exit.
    """
    while True:
        print("\nWelcome to the Password Manager developed by Usama Thakur")
        print("1. Sign In")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            user_data = sign_in()
            if user_data:
                main_menu(user_data)
        elif choice == '2':
            register()
        elif choice == '3':
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    create_tables()
    welcome_screen()
