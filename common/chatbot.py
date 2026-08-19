# ==========================================
# CONVORA
# Chatbot Conversation Manager
# ==========================================

from common.llm import get_ai_response

from config import (
    SYSTEM_PROMPT,
    MAX_CONVERSATION_HISTORY
)


# ==========================================
# CHATBOT CLASS
# ==========================================

class Chatbot:

    def __init__(self):

        # Store conversation history
        self.conversation = []


    # ==========================================
    # GET RESPONSE
    # ==========================================

    def get_response(self, user_message):

        # --------------------------------------
        # Validate message
        # --------------------------------------

        if not user_message:

            raise ValueError(
                "User message cannot be empty."
            )


        # --------------------------------------
        # Add user message
        # --------------------------------------

        self.conversation.append({

            "role": "user",

            "content": user_message

        })


        # --------------------------------------
        # Keep recent conversation
        # --------------------------------------

        self.conversation = (

            self.conversation[
                -MAX_CONVERSATION_HISTORY:
            ]

        )


        # --------------------------------------
        # Get AI response
        # --------------------------------------

        response = get_ai_response(

            SYSTEM_PROMPT,

            self.conversation

        )


        # --------------------------------------
        # Store AI response
        # --------------------------------------

        self.conversation.append({

            "role": "assistant",

            "content": response

        })


        # --------------------------------------
        # Limit history again
        # --------------------------------------

        self.conversation = (

            self.conversation[
                -MAX_CONVERSATION_HISTORY:
            ]

        )


        # --------------------------------------
        # Return response
        # --------------------------------------

        return response


    # ==========================================
    # RESET CONVERSATION
    # ==========================================

    def reset(self):

        self.conversation = []


    # ==========================================
    # GET CONVERSATION
    # ==========================================

    def get_conversation(self):

        return self.conversation.copy()
