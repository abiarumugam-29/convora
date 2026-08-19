from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps

from config import (
    BOT_NAME,
    TAGLINE,
    WELCOME_MESSAGE
)

from common.chatbot import Chatbot


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

# IMPORTANT:
# Production-ல் இதை random secret key-ஆ மாற்றவும்.
app.secret_key = "convora-change-this-secret-key"


# ==========================================
# USER DATABASE
# ==========================================

# Temporary in-memory users.
#
# IMPORTANT:
# Server restart செய்தால் users disappear ஆகிவிடுவார்கள்.
# Later SQLite database-க்கு மாற்றலாம்.

users = {}


# ==========================================
# USER CHATBOTS
# ==========================================

# ஒவ்வொரு logged-in user-க்கும்
# தனி Chatbot object.
#
# Example:
#
# user1 -> Chatbot()
# user2 -> Chatbot()
#
# User 1 conversation User 2-க்கு தெரியாது.

user_chatbots = {}


# ==========================================
# LOGIN REQUIRED DECORATOR
# ==========================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            # API request என்றால் JSON response
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

    # Already logged in
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
    # CHECK EXISTING EMAIL
    # ======================================

    for user in users.values():

        if user["email"] == email:

            return render_template(
                "register.html",
                error="An account with this email already exists."
            )


    # ======================================
    # CREATE USER
    # ======================================

    user_id = str(
        len(users) + 1
    )


    password_hash = generate_password_hash(
        password
    )


    users[user_id] = {

        "id": user_id,

        "username": username,

        "email": email,

        "password": password_hash
    }


    # ======================================
    # CREATE PRIVATE CHATBOT
    # ======================================

    user_chatbots[user_id] = Chatbot()


    # ======================================
    # LOGIN USER
    # ======================================

    session.clear()

    session["user_id"] = user_id

    session["username"] = username


    print()
    print("================================")
    print("NEW USER REGISTERED")
    print("USERNAME:", username)
    print("EMAIL:", email)
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

    # Already logged in
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


    # ======================================
    # FIND USER
    # ======================================

    user_id = None
    user = None


    for current_id, current_user in users.items():

        if current_user["email"] == email:

            user_id = current_id

            user = current_user

            break


    if user is None:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    # ======================================
    # CHECK PASSWORD
    # ======================================

    if not check_password_hash(
        user["password"],
        password
    ):

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    # ======================================
    # CREATE CHATBOT IF NEEDED
    # ======================================

    if user_id not in user_chatbots:

        user_chatbots[user_id] = Chatbot()


    # ======================================
    # LOGIN
    # ======================================

    session.clear()

    session["user_id"] = user_id

    session["username"] = user["username"]


    print()
    print("================================")
    print("USER LOGIN")
    print("USERNAME:", user["username"])
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
        # GET CURRENT USER
        # ==================================

        user_id = session["user_id"]


        # ==================================
        # GET REQUEST DATA
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
        # GET AI RESPONSE
        # ==================================

        response = chatbot.get_response(
            user_message
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
        # RESET ONLY CURRENT USER
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
# RUN SERVER
# ==========================================

if __name__ == "__main__":

    print()

    print(
        "========================================"
    )

    print(
        "       🎙️ CONVORA"
    )

    print(
        "       Find Your Voice."
    )

    print(
        "========================================"
    )

    print(
        "Running locally..."
    )

    print(
        "http://127.0.0.1:5000"
    )

    print(
        "========================================"
    )

    print()


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True
    )