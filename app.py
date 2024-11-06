import chainlit as cl
from chainlit.input_widget import TextInput, Switch
import os
from langchain_community.chat_models import ChatOpenAI
from langchain_community.chat_models.fake import FakeListChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig


# https://docs.chainlit.io/integrations/langchain
def setup_runnable(api_key: str, streaming: bool = True, use_fake: bool = False):
    """
    Runnable
    https://python.langchain.com/docs/concepts/runnables/
    https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html
    https://python.langchain.com/v0.1/docs/expression_language/interface/
    """
    if not use_fake:
        model = ChatOpenAI(api_key=api_key, streaming=streaming)
    else:
        model = FakeListChatModel(
            responses=[
                "Hello! How can I assist you today?",
                "I'm here to help with your questions.",
                "Feel free to ask me anything.",
            ]
        )
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
            # https://docs.chainlit.io/api-reference/input-widgets/switch
            Switch(id="streaming", label="Stream Tokens", initial=True),
            Switch(id="use_fake", label="Use Fake Model", initial=False),
        ]
    ).send()
    api_key = settings.get("api_key", os.getenv("OPENAI_API_KEY"))
    streaming = settings.get("streaming", True)
    use_fake = settings.get("use_fake", False)
    setup_runnable(api_key=api_key, streaming=streaming, use_fake=use_fake)


# https://docs.chainlit.io/api-reference/chat-settings
@cl.on_settings_update
async def setup_agent(settings: cl.ChatSettings):
    api_key = settings.get("api_key", os.getenv("OPENAI_API_KEY"))
    streaming = settings.get("streaming", True)
    use_fake = settings.get("use_fake", False)
    setup_runnable(api_key=api_key, streaming=streaming, use_fake=use_fake)


@cl.on_message
async def handle_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    if cl.user_session.get("chat_settings").get("streaming"):
        res = cl.Message(content="")

        async for chunk in runnable.astream(
            {"question": message.content},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            await res.stream_token(chunk)
    else:
        res = cl.Message(
            content=runnable.invoke(
                {"question": message.content},
                config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
            )
        )

    await res.send()
