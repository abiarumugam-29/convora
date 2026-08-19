import os

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from functools import wraps

from config import (
    BOT_NAME,
    TAGLINE,
    WELCOME_MESSAGE
)

from common.chatbot import Chatbot

from database import (
    init_database,
    create_user,
    get_user_by_email,
    verify_user,
    save_message,
    get_messages,
    clear_user_messages
)


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

# IMPORTANT:
# Render Environment Variables-la SECRET_KEY add pannunga.
app.secret_key = os.getenv(
    "SECRET_KEY",
    "dev-only-change-this-secret-key"
)


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

init_database()


# ==========================================
# USER CHATBOTS
# ==========================================

# Current running server instance-la
# each user-ku separate Chatbot object.
#
# Database-la actual conversation messages
# save aagum.

user_chatbots = {}


# ==========================================
# LOGIN REQUIRED
# ==========================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            if request.path in ["/chat", "/reset"]:

                return jsonify({
                    "error": "Please login to continue."
                }), 401

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# HOME
# ==========================================

@app.route("/")
@login_required
def home():

    return render_template(
        "index.html",
        bot_name=BOT_NAME,
        tagline=TAGLINE,
        welcome_message=WELCOME_MESSAGE
    )


# ==========================================
# REGISTER
# ==========================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if "user_id" in session:

        return redirect(
            url_for("home")
        )

    # GET
    if request.method == "GET":

        return render_template(
            "register.html"
        )

    # POST

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # ======================================
    # VALIDATION
    # ======================================

    if not username:

        return render_template(
            "register.html",
            error="Please enter a username."
        )


    if len(username) < 3:

        return render_template(
            "register.html",
            error="Username must contain at least 3 characters."
        )


    if not email:

        return render_template(
            "register.html",
            error="Please enter your email."
        )


    if not password:

        return render_template(
            "register.html",
            error="Please enter a password."
        )


    if len(password) < 6:

        return render_template(
            "register.html",
            error="Password must contain at least 6 characters."
        )


    if password != confirm_password:

        return render_template(
            "register.html",
            error="Passwords do not match."
        )


    # ======================================
    # CHECK EXISTING USER
    # ======================================

    existing_user = get_user_by_email(
        email
    )

    if existing_user:

        return render_template(
            "register.html",
            error="An account with this email already exists."
        )


    # ======================================
    # CREATE USER
    # ======================================

    created = create_user(
        username,
        email,
        password
    )

    if not created:

        return render_template(
            "register.html",
            error="Username or email already exists."
        )


    # ======================================
    # GET CREATED USER
    # ======================================

    user = get_user_by_email(
        email
    )

    if not user:

        return render_template(
            "register.html",
            error="Unable to create your account. Please try again."
        )


    user_id = user["id"]


    # ======================================
    # CREATE PRIVATE CHATBOT
    # ======================================

    user_chatbots[user_id] = Chatbot()


    # ======================================
    # LOGIN USER
    # ======================================

    session.clear()

    session["user_id"] = user_id

    session["username"] = user["username"]

    session.permanent = True


    print()
    print("================================")
    print("NEW USER REGISTERED")
    print("USERNAME:", user["username"])
    print("EMAIL:", user["email"])
    print("USER ID:", user_id)
    print("================================")
    print()


    return redirect(
        url_for("home")
    )


# ==========================================
# LOGIN
# ==========================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if "user_id" in session:

        return redirect(
            url_for("home")
        )


    # GET

    if request.method == "GET":

        return render_template(
            "login.html"
        )


    # POST

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    if not email or not password:

        return render_template(
            "login.html",
            error="Please enter your email and password."
        )


    # ======================================
    # VERIFY USER
    # ======================================

    user = verify_user(
        email,
        password
    )


    if user is None:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    user_id = user["id"]


    # ======================================
    # CREATE CHATBOT
    # ======================================

    if user_id not in user_chatbots:

        user_chatbots[user_id] = Chatbot()


    # ======================================
    # LOGIN
    # ======================================

    session.clear()

    session["user_id"] = user_id

    session["username"] = user["username"]

    session.permanent = True


    print()
    print("================================")
    print("USER LOGIN")
    print("USERNAME:", user["username"])
    print("USER ID:", user_id)
    print("================================")
    print()


    return redirect(
        url_for("home")
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
@login_required
def logout():

    username = session.get(
        "username",
        "Unknown"
    )

    session.clear()


    print()
    print("================================")
    print("USER LOGOUT")
    print("USERNAME:", username)
    print("================================")
    print()


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
@login_required
def chat():

    try:

        # ==================================
        # CURRENT USER
        # ==================================

        user_id = session["user_id"]


        # ==================================
        # REQUEST DATA
        # ==================================

        data = request.get_json(
            silent=True
        ) or {}


        user_message = data.get(
            "message",
            ""
        ).strip()


        # ==================================
        # EMPTY MESSAGE
        # ==================================

        if not user_message:

            return jsonify({
                "error": "Message cannot be empty."
            }), 400


        # ==================================
        # GET USER CHATBOT
        # ==================================

        if user_id not in user_chatbots:

            user_chatbots[user_id] = Chatbot()


        chatbot = user_chatbots[user_id]


        # ==================================
        # SAVE USER MESSAGE
        # ==================================

        save_message(
            user_id,
            "user",
            user_message
        )


        # ==================================
        # LOG
        # ==================================

        print()
        print("==============================")
        print(
            "USER:",
            session.get(
                "username",
                "Unknown"
            )
        )
        print(
            "MESSAGE:",
            user_message
        )
        print("==============================")


        # ==================================
        # AI RESPONSE
        # ==================================

        response = chatbot.get_response(
            user_message
        )


        # ==================================
        # SAVE AI RESPONSE
        # ==================================

        save_message(
            user_id,
            "assistant",
            response
        )


        # ==================================
        # LOG RESPONSE
        # ==================================

        print(
            "CONVORA:",
            response
        )

        print(
            "=============================="
        )

        print()


        # ==================================
        # RETURN RESPONSE
        # ==================================

        return jsonify({

            "response": response

        }), 200


    except Exception as error:

        print()
        print("================================")
        print("CHAT ERROR")
        print("================================")
        print(
            "ERROR TYPE:",
            type(error).__name__
        )
        print(
            "ERROR:",
            str(error)
        )
        print("================================")
        print()


        return jsonify({

            "error":
                "Sorry, I couldn't process your message right now. "
                "Please try again."

        }), 500


# ==========================================
# CHAT HISTORY
# ==========================================

@app.route(
    "/history",
    methods=["GET"]
)
@login_required
def history():

    try:

        user_id = session["user_id"]

        messages = get_messages(
            user_id,
            limit=20
        )

        return jsonify({
            "messages": messages
        }), 200


    except Exception as error:

        print(
            "HISTORY ERROR:",
            str(error)
        )

        return jsonify({
            "error": "Unable to load chat history."
        }), 500


# ==========================================
# RESET CHAT
# ==========================================

@app.route(
    "/reset",
    methods=["POST"]
)
@login_required
def reset_chat():

    try:

        user_id = session["user_id"]


        # ==================================
        # DELETE DATABASE HISTORY
        # ==================================

        clear_user_messages(
            user_id
        )


        # ==================================
        # CREATE NEW CHATBOT
        # ==================================

        user_chatbots[user_id] = Chatbot()


        return jsonify({

            "message":
                "Conversation reset successfully."

        }), 200


    except Exception as error:

        print(
            "RESET ERROR:",
            str(error)
        )


        return jsonify({

            "error":
                "Unable to reset the conversation."

        }), 500


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "app": BOT_NAME
    }), 200


# ==========================================
# LOCAL DEVELOPMENT
# ==========================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("       🎙️ CONVORA")
    print("       Find Your Voice.")
    print("========================================")
    print("Running locally...")
    print("http://127.0.0.1:5000")
    print("========================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
