import os

from dotenv import load_dotenv

from google import genai
from google.genai import types

from groq import Groq


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# API KEYS
# ==========================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
)


# ==========================================
# MODEL SETTINGS
# ==========================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "groq/compound"
)


# ==========================================
# GEMINI CLIENT
# ==========================================

gemini_client = None


if GEMINI_API_KEY:

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ==========================================
# GROQ CLIENT
# ==========================================

groq_client = None


if GROQ_API_KEY:

    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# ==========================================
# CONVERT CONVERSATION FOR GEMINI
# ==========================================

def build_gemini_contents(conversation):

    contents = []


    for message in conversation:

        role = message["role"]

        content = message["content"]


        # User message
        if role == "user":

            contents.append(

                types.Content(

                    role="user",

                    parts=[

                        types.Part(
                            text=content
                        )

                    ]

                )

            )


        # Assistant message
        elif role == "assistant":

            contents.append(

                types.Content(

                    role="model",

                    parts=[

                        types.Part(
                            text=content
                        )

                    ]

                )

            )


    return contents


# ==========================================
# BUILD GROQ MESSAGES
# ==========================================

def build_groq_messages(
    system_prompt,
    conversation
):

    messages = []


    # ======================================
    # SYSTEM PROMPT
    # ======================================

    messages.append({

        "role": "system",

        "content": system_prompt

    })


    # ======================================
    # CONVERSATION
    # ======================================

    for message in conversation:

        role = message["role"]

        content = message["content"]


        if role == "user":

            messages.append({

                "role": "user",

                "content": content

            })


        elif role == "assistant":

            messages.append({

                "role": "assistant",

                "content": content

            })


    return messages


# ==========================================
# GEMINI RESPONSE
# ==========================================

def get_gemini_response(
    system_prompt,
    conversation
):

    # ======================================
    # CHECK CLIENT
    # ======================================

    if not gemini_client:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )


    # ======================================
    # BUILD CONTENTS
    # ======================================

    contents = build_gemini_contents(
        conversation
    )


    # ======================================
    # GEMINI REQUEST
    # ======================================

    response = gemini_client.models.generate_content(

        model=GEMINI_MODEL,

        contents=contents,

        config=types.GenerateContentConfig(

            system_instruction=system_prompt,

            temperature=0.7,

            max_output_tokens=500

        )

    )


    # ======================================
    # CHECK RESPONSE
    # ======================================

    if not response:

        raise RuntimeError(
            "Gemini returned no response."
        )


    if not response.text:

        raise RuntimeError(
            "Gemini returned an empty response."
        )


    return response.text.strip()


# ==========================================
# GROQ RESPONSE
# ==========================================

def get_groq_response(
    system_prompt,
    conversation
):

    # ======================================
    # CHECK CLIENT
    # ======================================

    if not groq_client:

        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )


    # ======================================
    # BUILD MESSAGES
    # ======================================

    messages = build_groq_messages(

        system_prompt,

        conversation

    )


    # ======================================
    # GROQ REQUEST
    # ======================================

    response = groq_client.chat.completions.create(

        model=GROQ_MODEL,

        messages=messages,

        temperature=0.7,

        max_tokens=500

    )


    # ======================================
    # CHECK RESPONSE
    # ======================================

    if not response:

        raise RuntimeError(
            "Groq returned no response."
        )


    if not response.choices:

        raise RuntimeError(
            "Groq returned an empty response."
        )


    text = response.choices[0].message.content


    if not text:

        raise RuntimeError(
            "Groq returned an empty response."
        )


    return text.strip()


# ==========================================
# MAIN AI FUNCTION
# ==========================================

def get_ai_response(
    system_prompt,
    conversation
):

    # ======================================
    # TRY GEMINI FIRST
    # ======================================

    try:

        print()
        print("--------------------------------")
        print("AI PROVIDER: Gemini")
        print(
            "MODEL:",
            GEMINI_MODEL
        )
        print("--------------------------------")


        response = get_gemini_response(

            system_prompt,

            conversation

        )


        print(
            "Gemini response received."
        )


        return response


    # ======================================
    # GEMINI FAILED
    # ======================================

    except Exception as gemini_error:

        print()
        print("================================")
        print("GEMINI ERROR")
        print("================================")

        print(
            "ERROR TYPE:",
            type(gemini_error).__name__
        )

        print(
            "ERROR:",
            str(gemini_error)
        )

        print("================================")


        # ==================================
        # TRY GROQ FALLBACK
        # ==================================

        try:

            print()
            print("--------------------------------")
            print("AI PROVIDER: Groq")
            print(
                "MODEL:",
                GROQ_MODEL
            )
            print("--------------------------------")


            response = get_groq_response(

                system_prompt,

                conversation

            )


            print(
                "Groq fallback response received."
            )


            return response


        # ==================================
        # BOTH FAILED
        # ==================================

        except Exception as groq_error:

            print()
            print("================================")
            print("GROQ ERROR")
            print("================================")

            print(
                "ERROR TYPE:",
                type(groq_error).__name__
            )

            print(
                "ERROR:",
                str(groq_error)
            )

            print("================================")


            raise RuntimeError(

                "Both Gemini and Groq failed "
                "to generate a response."

            )
