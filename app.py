import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from dotenv import load_dotenv

from database import (
    init_database,
    create_user,
    verify_user,
    save_message,
    get_messages,
    clear_user_messages
)

from config import (
    BOT_NAME,
    TAGLINE,
    WELCOME_MESSAGE,
    SYSTEM_PROMPT,
    MAX_CONVERSATION_HISTORY
)

from common.chatbot import (
    get_ai_response
)


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "convora-development-secret-key"
)


# ==========================================
# DATABASE
# ==========================================

init_database()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html",
        bot_name=BOT_NAME,
        tagline=TAGLINE,
        welcome_message=WELCOME_MESSAGE
    )


# ==========================================
# LOGIN
# ==========================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # --------------------------------------
    # ALREADY LOGGED IN
    # --------------------------------------

    if "user_id" in session:

        return redirect(
            url_for("home")
        )


    # --------------------------------------
    # GET
    # --------------------------------------

    if request.method == "GET":

        return render_template(
            "login.html"
        )


    # --------------------------------------
    # POST
    # --------------------------------------

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )


    # --------------------------------------
    # VALIDATION
    # --------------------------------------

    if not email or not password:

        return render_template(
            "login.html",
            error="Please enter your email and password."
        )


    # --------------------------------------
    # VERIFY USER
    # --------------------------------------

    user = verify_user(
        email,
        password
    )


    if not user:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    # --------------------------------------
    # CREATE SESSION
    # --------------------------------------

    session.clear()

    session["user_id"] = user["id"]

    session["username"] = user["username"]

    session["email"] = user["email"]


    # --------------------------------------
    # REDIRECT
    # --------------------------------------

    return redirect(
        url_for("home")
    )


# ==========================================
# REGISTER
# ==========================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # --------------------------------------
    # ALREADY LOGGED IN
    # --------------------------------------

    if "user_id" in session:

        return redirect(
            url_for("home")
        )


    # --------------------------------------
    # GET
    # --------------------------------------

    if request.method == "GET":

        return render_template(
            "register.html"
        )


    # --------------------------------------
    # POST
    # --------------------------------------

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # --------------------------------------
    # REQUIRED FIELDS
    # --------------------------------------

    if not username:

        return render_template(
            "register.html",
            error="Please enter a username."
        )


    if not email:

        return render_template(
            "register.html",
            error="Please enter your email."
        )


    if not password:

        return render_template(
            "register.html",
            error="Please create a password."
        )


    if not confirm_password:

        return render_template(
            "register.html",
            error="Please confirm your password."
        )


    # --------------------------------------
    # USERNAME LENGTH
    # --------------------------------------

    if len(username) < 3:

        return render_template(
            "register.html",
            error="Username must be at least 3 characters."
        )


    # --------------------------------------
    # PASSWORD LENGTH
    # --------------------------------------

    if len(password) < 6:

        return render_template(
            "register.html",
            error="Password must be at least 6 characters."
        )


    # --------------------------------------
    # PASSWORD MATCH
    # --------------------------------------

    if password != confirm_password:

        return render_template(
            "register.html",
            error="Passwords do not match."
        )


    # --------------------------------------
    # CREATE USER
    # --------------------------------------

    success = create_user(
        username,
        email,
        password
    )


    # --------------------------------------
    # USER EXISTS
    # --------------------------------------

    if not success:

        return render_template(
            "register.html",
            error="Username or email already exists."
        )


    # --------------------------------------
    # SUCCESS
    # --------------------------------------

    return redirect(
        url_for("login")
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==========================================
# CHAT
# ==========================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    # --------------------------------------
    # LOGIN CHECK
    # --------------------------------------

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401


    # --------------------------------------
    # GET JSON
    # --------------------------------------

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({
            "error": "Invalid request."
        }), 400


    # --------------------------------------
    # GET MESSAGE
    # --------------------------------------

    user_message = data.get(
        "message",
        ""
    ).strip()


    if not user_message:

        return jsonify({
            "error": "Please enter a message."
        }), 400


    # --------------------------------------
    # USER ID
    # --------------------------------------

    user_id = session["user_id"]


    # --------------------------------------
    # GET HISTORY
    # --------------------------------------

    history = get_messages(
        user_id,
        limit=MAX_CONVERSATION_HISTORY
    )


    # --------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------

    save_message(
        user_id,
        "user",
        user_message
    )


    # --------------------------------------
    # BUILD CONVERSATION
    # --------------------------------------

    conversation = []

    for message in history:

        conversation.append({
            "role": message["role"],
            "content": message["content"]
        })


    conversation.append({
        "role": "user",
        "content": user_message
    })


    # --------------------------------------
    # AI RESPONSE
    # --------------------------------------

    try:

        response = get_ai_response(
            SYSTEM_PROMPT,
            conversation
        )


    except Exception as error:

        print(
            "AI ERROR:",
            type(error).__name__,
            str(error)
        )


        return jsonify({
            "error": "Sorry, I couldn't generate a response right now."
        }), 500


    # --------------------------------------
    # SAVE BOT RESPONSE
    # --------------------------------------

    save_message(
        user_id,
        "assistant",
        response
    )


    # --------------------------------------
    # RETURN RESPONSE
    # --------------------------------------

    return jsonify({
        "response": response
    })


# ==========================================
# CHAT HISTORY
# ==========================================

@app.route("/history")
def history():

    # --------------------------------------
    # LOGIN CHECK
    # --------------------------------------

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401


    user_id = session["user_id"]


    messages = get_messages(
        user_id,
        limit=MAX_CONVERSATION_HISTORY
    )


    return jsonify({
        "messages": messages
    })


# ==========================================
# CLEAR CHAT
# ==========================================

@app.route(
    "/reset",
    methods=["POST"]
)
def reset():

    # --------------------------------------
    # LOGIN CHECK
    # --------------------------------------

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401


    user_id = session["user_id"]


    clear_user_messages(
        user_id
    )


    return jsonify({
        "success": True
    })


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "app": BOT_NAME
    })


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )