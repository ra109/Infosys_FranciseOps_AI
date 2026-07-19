# Milestone 1 — User Authentication Module

## Overview
This milestone implements a secure user authentication system as part of the 
Infosys Springboard Internship 7.0 project. The goal was to build a login and 
signup flow that verifies users through email-based One-Time Passwords (OTP) 
and issues secure session tokens using JWT (JSON Web Tokens).

## Features Built
- **User Signup** — new users can register with their name, email, and password.
- **Email OTP Verification** — a one-time password is sent to the user's Gmail 
  address to confirm their identity before granting access.
- **User Login** — registered users can log in with their credentials.
- **JWT-based Session Management** — after successful login, a JWT token is 
  generated and used to maintain a secure, stateless session.
- **Password Security** — passwords are hashed before being stored (never saved 
  in plain text).
- **Public Access via ngrok** — the Streamlit app is exposed to the internet 
  using ngrok so it can be tested/accessed outside the local machine (needed 
  since this runs from Google Colab).

## Tech Stack
- **Streamlit** — for building the interactive web UI.
- **JWT (PyJWT)** — for creating and verifying secure authentication tokens.
- **ngrok** — for tunneling the local Streamlit app to a public URL.
- **smtplib / Gmail SMTP** — for sending OTP emails via a Gmail App Password.
- **Google Colab** — as the development and execution environment.
- **Python** — core language used throughout the notebook.

## How to Run the Notebook
1. Open the notebook (`Milestone1.ipynb`) in Google Colab.
2. Add the following secrets in Colab's **Secrets** tab (🔑 icon in the sidebar):
   - `NGROK_AUTH_TOKEN` — your ngrok authentication token.
   - `GMAIL_ADDRESS` — the Gmail address used to send OTP emails.
   - `GMAIL_APP_PASSWORD` — the App Password generated for that Gmail account.
3. Run all cells in order from top to bottom.
4. Once the Streamlit app starts, the notebook will print a public **ngrok URL**.
5. Open that URL in your browser to access the app.
6. Sign up with an email address, retrieve the OTP from that inbox, verify it, 
   and then log in to test the full authentication flow.

## Screenshots
_(See the Screenshots section below for proof-of-run images.)_
