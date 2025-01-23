# auth.py

import streamlit as st
from database import create_connection
from email_otp import generate_otp, send_otp_via_email

def forgot_password_flow(db_email, user_id):
    """
    Generate and email an OTP for password reset. Return the OTP code if sent successfully.
    """
    otp_code = generate_otp()
    if send_otp_via_email(db_email, otp_code):
        return otp_code  # We'll compare this code in app.py
    else:
        return None

def reset_password(user_id, new_password):
    """
    Reset the user's password in the database.
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password = ? WHERE user_id = ?",
        (new_password, user_id)
    )
    conn.commit()
    conn.close()
    return True

def register(username, email, password):
    """
    Example registration function that returns (success_bool, message).
    """
    conn = create_connection()
    cursor = conn.cursor()
    # Check uniqueness
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username, email)
    )
    row = cursor.fetchone()

    if row:
        conn.close()
        return False, "That username or email is already registered."
    else:
        # Insert new user
        cursor.execute("""
            INSERT INTO users (username, email, password) 
            VALUES (?, ?, ?)
        """, (username, email, password))
        conn.commit()
        conn.close()
        return True, "Registration successful!"

def sign_in(username, password_attempt):
    """
    Example sign-in function that returns (success_bool, message, user_data).
    user_data is a tuple: (user_id, username, email, db_password)
    """
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    if not user_data:
        conn.close()
        return False, "No such user found. Please register first.", None

    user_id, db_username, db_email, db_password = user_data
    if password_attempt == db_password:
        conn.close()
        return True, "Sign in successful!", user_data
    else:
        conn.close()
        return False, "Incorrect password.", user_data
