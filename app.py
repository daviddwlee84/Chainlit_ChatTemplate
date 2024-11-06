import chainlit as cl
from chainlit.input_widget import TextInput
import os


@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="api_key", label="API Key", initial=os.getenv("OPENAI_API_KEY")
            ),
        ]
    ).send()
    value = settings["api_key"]
    print(value)
    cl.user_session.set("api_key", value)


# https://docs.chainlit.io/api-reference/chat-settings
@cl.on_settings_update
async def setup_agent(settings: cl.ChatSettings):
    print("on_settings_update", settings)
    value = settings["api_key"]
    print(value)
    cl.user_session.set("api_key", value)


@cl.on_message
async def handle_message(message: cl.Message):
    user_api_key = cl.user_session.get("api_key")
    # Use the user_api_key for your API calls
    await cl.Message(f"Your API key is: {user_api_key}").send()
