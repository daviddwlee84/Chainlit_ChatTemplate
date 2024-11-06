import chainlit as cl
from chainlit.input_widget import TextInput
import os


# https://docs.chainlit.io/authentication/password
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if password == "admin":
        return cl.User(
            identifier=username,
            display_name=username,
            metadata={"role": "admin", "provider": "credentials"},
        )
    else:
        return None


@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            # https://docs.chainlit.io/api-reference/input-widgets/textinput
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
    await cl.Message(
        f"Hi {cl.user_session.get('user').display_name}, Your API key is: {user_api_key}"
    ).send()
