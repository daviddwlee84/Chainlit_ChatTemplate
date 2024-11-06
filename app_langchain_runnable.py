import chainlit as cl
from chainlit.input_widget import TextInput, Switch
import os

# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.fake import FakeListChatModel
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from chainlit.types import ThreadDict
from langchain_core.messages import HumanMessage, AIMessage


def get_current_chainlit_thread_id() -> str:
    """
    https://github.com/Chainlit/chainlit/issues/1385
    """
    return cl.context.session.thread_id


def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    store = cl.user_session.get("store", {})
    if session_id not in store:
        print("Initialize Chat Message History")
        # BUG: TypeError: Object of type InMemoryChatMessageHistory is not JSON serializable
        store[session_id] = InMemoryChatMessageHistory()
        cl.user_session.set("store", store)
    return store[session_id]


# https://docs.chainlit.io/integrations/langchain
def setup_runnable(api_key: str, streaming: bool = True, use_fake: bool = False):
    """
    Runnable
    https://python.langchain.com/docs/concepts/runnables/
    https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html
    https://python.langchain.com/v0.1/docs/expression_language/interface/
    https://python.langchain.com/v0.1/docs/expression_language/how_to/message_history/

    Chat History
    https://python.langchain.com/docs/versions/migrating_memory/conversation_buffer_memory/#lcel-runnablewithmessagehistory
    https://python.langchain.com/docs/versions/migrating_chains/conversation_chain/
    https://python.langchain.com/v0.2/docs/tutorials/chatbot/#message-history
    TODO: As of the v0.3 release of LangChain, we recommend that LangChain users take advantage of LangGraph persistence to incorporate memory into new LangChain applications.
    https://python.langchain.com/docs/versions/migrating_memory/conversation_buffer_memory/#langgraph
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
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    runnable = prompt | model
    runnable_with_history = (
        RunnableWithMessageHistory(
            runnable=runnable,
            get_session_history=get_by_session_id,
            input_messages_key="question",
            history_messages_key="history",
        )
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable_with_history)


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
    print("Current thread_id is", get_current_chainlit_thread_id(), "(on_chat_start)")

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


# NOTE: this feature requires Literal AI or custom storage
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    chainlit_thread_id = thread.get("id")
    print(chainlit_thread_id, get_current_chainlit_thread_id())  # they are the same!
    print("Resume Chat Message History")
    store = cl.user_session.get("store", {})
    # BUG: TypeError: Object of type InMemoryChatMessageHistory is not JSON serializable
    message_history = InMemoryChatMessageHistory()
    messages = []
    # for message in thread["steps"]:
    #     if message["type"] == "user_message":
    #         message_history.add_user_message(message["output"])
    #     elif message["type"] == "assistant_message":
    #         message_history.add_ai_message(message["output"])
    #     # else:
    #     #     print("Ignored message:", message)
    for message in thread["steps"]:
        if message["type"] == "user_message":
            messages.append(HumanMessage(content=message["output"]))
        elif message["type"] == "assistant_message":
            messages.append(AIMessage(content=message["output"]))
    await message_history.aadd_messages(messages)
    store[chainlit_thread_id] = message_history
    cl.user_session.set("store", store)

    api_key = cl.user_session.get("chat_settings").get(
        "api_key", os.getenv("OPENAI_API_KEY")
    )
    streaming = cl.user_session.get("chat_settings").get("streaming", True)
    use_fake = cl.user_session.get("chat_settings").get("use_fake", False)
    setup_runnable(api_key=api_key, streaming=streaming, use_fake=use_fake)


@cl.on_message
async def handle_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    chainlit_thread_id = get_current_chainlit_thread_id()
    print("Current thread_id is", get_current_chainlit_thread_id(), "(on_message)")
    history = get_by_session_id(chainlit_thread_id)
    print("History message length:", len(history.messages))

    if cl.user_session.get("chat_settings").get("streaming"):
        res = cl.Message(content="")

        async for chunk in runnable.astream(
            {"question": message.content},
            config=RunnableConfig(
                configurable={"session_id": chainlit_thread_id},
                callbacks=[
                    cl.LangchainCallbackHandler()
                ],  # This is used to show intermediate message in Chainlit
            ),
        ):
            await res.stream_token(chunk)
    else:
        res = cl.Message(
            content=runnable.invoke(
                {"question": message.content},
                config=RunnableConfig(
                    configurable={"session_id": chainlit_thread_id},
                    callbacks=[
                        cl.LangchainCallbackHandler()
                    ],  # This is used to show intermediate message in Chainlit
                ),
            )
        )

    await res.send()
