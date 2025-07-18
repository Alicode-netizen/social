import streamlit as st
import hashlib
import json
import os
import graphviz
import pandas as pd
from datetime import datetime

import streamlit as st

# Page configuration
st.set_page_config(page_title="Social Worker App", page_icon="👥", layout="centered")

# URL of the logo
logo_url = "https://postimg.cc/K1vD6wCc"

# Show logo at top of home page
st.image(logo_url, width=180)

# Sidebar logo
with st.sidebar:
    st.image(logo_url, width=150)


# ---------- Configuration ----------
st.set_page_config(page_title="Social Worker App", page_icon="👥", layout="wide")
USER_FILE = "users.json"
DATA_DIR = "user_data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------- Helper Functions ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def get_user_data_path(email):
    return os.path.join(DATA_DIR, f"{email}.json")

def load_user_data(email):
    path = get_user_data_path(email)
    if os.path.exists(path):
        with open(path, "r") as file:
            return json.load(file)
    return {"bio": {}, "history": []}

def save_user_data(email, data):
    with open(get_user_data_path(email), "w") as file:
        json.dump(data, file, indent=2)

# ---------- Initialize Session State ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

users_db = load_users()

# ---------- Sidebar Login/Sign Up ----------
st.sidebar.title("🔐 Login / Sign Up")
auth_mode = st.sidebar.radio("Choose Option:", ["Login", "Sign Up"])

if auth_mode == "Sign Up":
    st.sidebar.subheader("Create Account")
    new_email = st.sidebar.text_input("Email", key="signup_email")
    new_password = st.sidebar.text_input("Password", type="password", key="signup_password")
    if st.sidebar.button("Sign Up"):
        if new_email in users_db:
            st.sidebar.warning("User already exists.")
        else:
            users_db[new_email] = hash_password(new_password)
            save_users(users_db)
            st.sidebar.success("Account created! Please log in.")

elif auth_mode == "Login":
    st.sidebar.subheader("Log In")
    email = st.sidebar.text_input("Email", key="login_email")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    if st.sidebar.button("Log In"):
        hashed_pw = hash_password(password)
        if email in users_db and users_db[email] == hashed_pw:
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_data = load_user_data(email)
            st.sidebar.success(f"Welcome, {email}!")
        else:
            st.sidebar.error("Invalid credentials.")

# ---------- Authenticated UI ----------
if st.session_state.authenticated:
    tabs = st.tabs(["🏠 Home", "📚 History", "👤 Biodata", "🧰 Tools"])

    with tabs[0]:  # Home
        st.title("🏠 User Home Page")
        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown(f"**Name:** {st.session_state.user_data.get('bio', {}).get('name', 'Not set')}")
        st.markdown(f"**Logged in at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with tabs[1]:  # History
        st.title("📚 History of Generated Maps")
        history = st.session_state.user_data.get("history", [])
        if history:
            for item in history:
                st.markdown(f"**{item['type']}** - {item['title']} ({item['timestamp']})")
                st.graphviz_chart(item['dot'])
        else:
            st.info("No maps generated yet.")

    with tabs[2]:  # Biodata
        st.title("👤 Update Biodata")
        with st.form("biodata_form"):
            name = st.text_input("Full Name", value=st.session_state.user_data.get("bio", {}).get("name", ""))
            age = st.text_input("Age", value=st.session_state.user_data.get("bio", {}).get("age", ""))
            occupation = st.text_input("Occupation", value=st.session_state.user_data.get("bio", {}).get("occupation", ""))
            submitted = st.form_submit_button("Save Biodata")
            if submitted:
                st.session_state.user_data["bio"] = {"name": name, "age": age, "occupation": occupation}
                save_user_data(st.session_state.user_email, st.session_state.user_data)
                st.success("Biodata updated.")

    with tabs[3]:  # Tools
        st.title("🧰 Tools")
        tool = st.selectbox("Choose a Tool", ["Select", "Genogram", "Ecomap", "Social Network Diagram", "Life Roadmap"])

        def save_to_history(dot, title, diagram_type):
            entry = {
                "title": title,
                "dot": dot.source,
                "type": diagram_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.user_data["history"].append(entry)
            save_user_data(st.session_state.user_email, st.session_state.user_data)

        if tool == "Genogram":
            st.subheader("👨‍👩‍👧‍👦 Genogram Builder")
            root_name = st.text_input("Enter your name:")
            if root_name:
                parents = st.text_area("Parents (comma-separated)")
                spouse = st.text_input("Spouse")
                siblings = st.text_area("Siblings (comma-separated)")
                children = st.text_area("Children (comma-separated)")
                if st.button("Generate Genogram"):
                    dot = graphviz.Digraph()
                    dot.node(root_name, root_name, shape="box", color="blue")
                    parent_list = [p.strip() for p in parents.split(",") if p.strip()]
                    for p in parent_list:
                        dot.node(p, p, shape="oval", color="green")
                        dot.edge(p, root_name)
                    if spouse:
                        dot.node(spouse, spouse, shape="oval", color="red")
                        dot.edge(root_name, spouse, label="spouse")
                    for sib in siblings.split(","):
                        sib = sib.strip()
                        if sib:
                            dot.node(sib, sib, shape="box")
                            for p in parent_list:
                                dot.edge(p, sib)
                    for child in children.split(","):
                        child = child.strip()
                        if child:
                            dot.node(child, child, shape="box")
                            dot.edge(root_name, child)
                    st.graphviz_chart(dot)
                    save_to_history(dot, f"Genogram for {root_name}", "Genogram")

        elif tool == "Ecomap":
            st.subheader("🌐 Ecomap Generator")
            user_node = st.text_input("Enter your name:", key="ecomap_user")
            connections = st.text_area("Connections (Name, Type, Emotion)", height=200)
            if st.button("Generate Ecomap"):
                dot = graphviz.Digraph()
                dot.node(user_node, user_node, shape="circle", color="blue")
                for line in connections.strip().split("\n"):
                    if line.strip():
                        try:
                            name, relation, emotion = [x.strip() for x in line.split(",")]
                            color = {"strong": "green", "weak": "gray", "negative": "red"}.get(emotion.lower(), "black")
                            style = {"strong": "bold", "weak": "dashed", "negative": "dotted"}.get(emotion.lower(), "solid")
                            dot.node(name, f"{name}\n({relation})")
                            dot.edge(user_node, name, color=color, style=style)
                        except:
                            st.warning(f"Invalid format: {line}")
                st.graphviz_chart(dot)
                save_to_history(dot, f"Ecomap for {user_node}", "Ecomap")

        elif tool == "Social Network Diagram":
            st.subheader("🤝 Social Network Diagram")
            center_name = st.text_input("Your Name:")
            contacts = st.text_area("Contacts (Name, Relationship)", height=200)
            if st.button("Generate Social Network"):
                dot = graphviz.Graph()
                dot.node(center_name, center_name, shape="ellipse", color="blue")
                for line in contacts.strip().split("\n"):
                    if line.strip():
                        try:
                            name, relation = [x.strip() for x in line.split(",")]
                            dot.node(name, f"{name}\n({relation})")
                            dot.edge(center_name, name)
                        except:
                            st.warning(f"Invalid format: {line}")
                st.graphviz_chart(dot)
                save_to_history(dot, f"Social Network for {center_name}", "Social Network")

        elif tool == "Life Roadmap":
            st.subheader("📅 Life Roadmap")
            if "life_events" not in st.session_state:
                st.session_state.life_events = []
            with st.form("life_form", clear_on_submit=True):
                time = st.text_input("Time (age/year)")
                description = st.text_input("Event Description")
                impact = st.slider("Impact Score", -10, 10, 0)
                submitted = st.form_submit_button("Add Event")
                if submitted and time and description:
                    st.session_state.life_events.append((time, description, impact))
            if st.session_state.life_events:
                df = pd.DataFrame(st.session_state.life_events, columns=["Time", "Event", "Impact"])
                st.line_chart(df.set_index("Time")["Impact"])
                save_to_history(graphviz.Digraph(comment="Life Roadmap"), "Life Roadmap", "Life Roadmap")

else:
    st.title("👥 Social Worker App")
    st.info("Please log in from the sidebar to use the tools.")
