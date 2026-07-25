# Milestone 1

## Overview
A User Authentication Module — a Streamlit web app with Login, Signup, and Forgot Password pages, backed by JWT session handling, deployed publicly from Google Colab via ngrok, with OTP delivery through Gmail.

## Features Implemented
Login — username/email + password, issues a JWT on success, generic error on failure (doesn't reveal which field was wrong)
Signup — username, email, password, confirm password, security question + answer; unique username enforced
Forgot Password — two recovery routes: security question verification, or email OTP verification; both end in a password reset
JWT session management — token issued at login, checked before showing the Dashboard, cleared on logout
User Dashboard — welcome message with logged-in identity + logout
Admin Dashboard — separate hardcoded admin login, lists all registered users (no passwords shown)
Validation — mandatory fields, email format rule (2+ letters before @, between @ and dot, after dot), password rule (8+ chars, upper, lower, number, special char)


## Tech Stack
Streamlit (UI/frontend)
JWT (session/auth tokens)
ngrok (public URL tunnel for the Colab-hosted app)
Gmail SMTP + App Password (OTP email delivery)
Google Colab (runtime + Secrets manager for JWT_SECRET, NGROK_AUTHTOKEN, EMAIL_PASSWORD, EMAIL_ADDRESS)


## How to Run
1. Open the notebook in Google Colab.
2. Set up Colab Secrets (key icon in sidebar): JWT_SECRET, NGROK_AUTHTOKEN, EMAIL_PASSWORD, EMAIL_ADDRESS — toggle notebook access on for each.
3. Run all cells top to bottom.
4. The app launches via ngrok, which prints a public URL — open that URL in a browser to use the app.
5. Before sharing/uploading: clear all outputs, and double-check no secrets are hardcoded anywhere in the notebook.

## Screenshots
<img width="912" height="478" alt="image" src="https://github.com/user-attachments/assets/294d6a3b-4cc4-4117-bd20-e0f09dae2420" />
<img width="966" height="443" alt="image" src="https://github.com/user-attachments/assets/d1bb2774-18c4-47c2-a489-d4d139750685" />
<img width="1267" height="333" alt="image" src="https://github.com/user-attachments/assets/d8f09658-96d8-46b9-9fc3-5adacc86e028" />
<img width="1397" height="737" alt="image" src="https://github.com/user-attachments/assets/7f0de5d0-7c77-4b12-b147-f3218e3c36e4" />


