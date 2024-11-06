import chainlit as cl
from chainlit.input_widget import TextInput
import os
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig


# https://docs.chainlit.io/integrations/langchain
def setup_runnable(api_key: str, streaming: bool = True):
    """
    https://python.langchain.com/docs/concepts/runnables/
    https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html
    https://python.langchain.com/v0.1/docs/expression_language/interface/
    """
    model = ChatOpenAI(api_key=api_key, streaming=streaming)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You're a very knowledgeable historian who provides accurate and eloquent answers to historical questions.",
            ),
            ("human", "{question}"),
        ]
    )

    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


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
    api_key = settings.get("api_key", os.getenv("OPENAI_API_KEY"))
    setup_runnable(api_key=api_key)


# https://docs.chainlit.io/api-reference/chat-settings
@cl.on_settings_update
async def setup_agent(settings: cl.ChatSettings):
    api_key = settings.get("api_key", os.getenv("OPENAI_API_KEY"))
    setup_runnable(api_key=api_key)


@cl.on_message
async def handle_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    res = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)

    await res.send()
