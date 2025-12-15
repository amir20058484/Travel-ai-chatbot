import os
import chainlit as cl
from dotenv import load_dotenv
from src.manager import AgentManager
from src.tools import TICKET_DB

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.2")
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL")
APP_NAME = os.getenv("APP_NAME", "Safar Travel AI Agent")

@cl.on_chat_start
async def on_chat_start():
    """
    Initializes the AgentManager at the start of a new chat session.
    """
    
    if not AVALAI_API_KEY or not AVALAI_BASE_URL:
        await cl.Message(
            content="**ERROR:** Missing API configuration. Please ensure `AVALAI_API_KEY` and `AVALAI_BASE_URL` are set in your `.env` file.",
            author="System"
        ).send()
        return

    try:
        agent = AgentManager(
            model_name=MODEL_NAME,
            api_key=AVALAI_API_KEY,
            base_url=AVALAI_BASE_URL
        )
        cl.user_session.set("agent", agent)
        
        welcome_message = f"""
**{APP_NAME}** - **سفر تراول**
با سلام! من دستیار هوشمند شما در سفر تراول هستم. 
در زمینه رزرو بلیط، لغو، دریافت اطلاعات بلیط‌های داخلی ایران و همچنین پیشنهاد مقاصد سفر در خدمت شما هستم.
لطفاً درخواست خود را به فارسی یا انگلیسی مطرح کنید. 
مثال: *I want to book a flight to Shiraz* یا *سیاست کنسلی بلیط چیست؟*
"""
        await cl.Message(
            content=welcome_message,
            author="Safar AI Agent"
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"**FATAL ERROR** during agent initialization: {str(e)}",
            author="System"
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Processes a user message and generates a response from the AgentManager.
    """
    agent: AgentManager = cl.user_session.get("agent")
    
    if not agent:
        await cl.Message(content="Agent is not initialized. Please restart the chat.", author="System").send()
        return

    msg = cl.Message(content="")
    await msg.send()
    
    try:
        response_text = agent.process_message(message.content)
        
        debug_info = ""
        if TICKET_DB:
            debug_info = "\n\n---\n**Tickets (Debug)**:\n"
            for ticket_id, details in TICKET_DB.items():
                 debug_info += f"- **{ticket_id}**: {details['origin']} -> {details['destination']} ({details['status']})\n"

        msg.content = response_text + debug_info

        msg.author = "Safar AI Agent" 
        
        await msg.update() 

    except Exception as e:
        error_msg = f"An unexpected error occurred while processing your request: {str(e)}"
        
        msg.content = error_msg
        msg.author = "Safar AI Agent"
        await msg.update()