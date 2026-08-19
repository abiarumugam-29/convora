// ==========================================
// CONVORA
// English Learning Chatbot
// ==========================================


// ==========================================
// DOM ELEMENTS
// ==========================================

const messageInput =
    document.getElementById("messageInput");

const sendButton =
    document.getElementById("sendButton");

const messagesContainer =
    document.getElementById("messages");

const welcomeSection =
    document.getElementById("welcomeSection");

const chatSection =
    document.getElementById("chatSection");


// ==========================================
// STATE
// ==========================================

let isSending = false;


// ==========================================
// SEND MESSAGE
// ==========================================

async function sendMessage() {

    if (isSending) {
        return;
    }


    const message =
        messageInput.value.trim();


    if (!message) {
        return;
    }


    // Hide welcome section

    if (welcomeSection) {

        welcomeSection.style.display =
            "none";
    }


    // Show chat section

    if (chatSection) {

        chatSection.classList.add(
            "active"
        );
    }


    // Add user message

    addMessage(
        "user",
        message
    );


    // Clear input

    messageInput.value = "";

    autoResize();


    // Start loading

    setLoading(true);


    try {

        const response = await fetch(
            "/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data =
            await response.json();


        removeTyping();


        let reply = "";


        if (data.response) {

            reply = data.response;

        } else if (data.message) {

            reply = data.message;

        } else if (data.reply) {

            reply = data.reply;

        } else if (data.error) {

            reply = data.error;

        } else {

            reply =
                "Sorry, I couldn't understand the response. Please try again.";
        }


        addMessage(
            "bot",
            reply
        );


    } catch (error) {

        console.error(
            "Chat Error:",
            error
        );


        removeTyping();


        addMessage(
            "bot",
            "Sorry, I couldn't process that right now. Please try again."
        );


    } finally {

        setLoading(false);
    }
}


// ==========================================
// ADD MESSAGE
// ==========================================

function addMessage(
    type,
    text
) {

    const message =
        document.createElement("div");


    message.className =
        `message ${type}`;


    const label =
        document.createElement("div");


    label.className =
        "message-label";


    label.textContent =
        type === "user"
            ? "You"
            : "CONVORA";


    const content =
        document.createElement("div");


    content.className =
        "message-content";


    content.textContent =
        text;


    message.appendChild(label);

    message.appendChild(content);


    messagesContainer.appendChild(
        message
    );


    scrollToBottom();
}


// ==========================================
// TYPING INDICATOR
// ==========================================

function showTyping() {

    removeTyping();


    const message =
        document.createElement("div");


    message.className =
        "message bot";


    message.id =
        "typingMessage";


    const label =
        document.createElement("div");


    label.className =
        "message-label";


    label.textContent =
        "CONVORA";


    const typing =
        document.createElement("div");


    typing.className =
        "typing";


    for (
        let i = 0;
        i < 3;
        i++
    ) {

        const dot =
            document.createElement("span");


        typing.appendChild(dot);
    }


    message.appendChild(label);

    message.appendChild(typing);


    messagesContainer.appendChild(
        message
    );


    scrollToBottom();
}


// ==========================================
// REMOVE TYPING
// ==========================================

function removeTyping() {

    const typingMessage =
        document.getElementById(
            "typingMessage"
        );


    if (typingMessage) {

        typingMessage.remove();
    }
}


// ==========================================
// LOADING
// ==========================================

function setLoading(
    loading
) {

    isSending =
        loading;


    sendButton.disabled =
        loading;


    if (loading) {

        showTyping();

    } else {

        removeTyping();
    }
}


// ==========================================
// SCROLL
// ==========================================

function scrollToBottom() {

    if (!messagesContainer) {
        return;
    }


    setTimeout(
        () => {

            messagesContainer.scrollIntoView({
                behavior: "smooth",
                block: "end"
            });

        },
        50
    );
}


// ==========================================
// AUTO RESIZE
// ==========================================

function autoResize() {

    if (!messageInput) {
        return;
    }


    messageInput.style.height =
        "auto";


    const maxHeight =
        120;


    messageInput.style.height =
        Math.min(
            messageInput.scrollHeight,
            maxHeight
        ) + "px";
}


// ==========================================
// ENTER KEY
// ==========================================

messageInput.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }

    }
);


// ==========================================
// TEXTAREA INPUT
// ==========================================

messageInput.addEventListener(
    "input",
    function () {

        autoResize();

    }
);


// ==========================================
// SEND BUTTON
// ==========================================

sendButton.addEventListener(
    "click",
    function () {

        sendMessage();

    }
);


// ==========================================
// TOPIC SHORTCUTS
// ==========================================

function startTopic(topic) {

    if (!messageInput) {
        return;
    }


    const prompts = {

        grammar:
            "I want to learn English grammar.",

        vocabulary:
            "I want to improve my English vocabulary.",

        practice:
            "Give me an English practice exercise.",

        translation:
            "I want to learn how to translate Tamil sentences into English."

    };


    const selectedPrompt =
        prompts[topic];


    if (!selectedPrompt) {
        return;
    }


    messageInput.value =
        selectedPrompt;


    autoResize();


    messageInput.focus();
}


// ==========================================
// INITIALIZATION
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        autoResize();

        if (messageInput) {

            messageInput.focus();
        }

    }
);
