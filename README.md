# Chainlit Chat Template

Basic Chainlit application with password authentication and user history

## Getting Started

```bash
pip install -r requirements.txt

# Get CHAINLIT_AUTH_SECRET
# You must provide a JWT secret in the environment to use authentication
chainlit create-secret

# (optional) Get LITERAL_API_KEY
# https://cloud.getliteral.ai/

# Add them in .env
cp example.env .env

chainlit run app_langchain_runnable.py -w
```

## Todo

- [ ] `@cl.on_chat_resume`
  - [X] Able to resume chat history by thread id
  - [ ] Resume chat should kept the history on UI: [Chat history is not getting retrieved on the chat resume · Issue #1499 · Chainlit/chainlit](https://github.com/Chainlit/chainlit/issues/1499)
- [ ] Fix bug of `TypeError: Object of type InMemoryChatMessageHistory is not JSON serializable`
- [ ] Self-host Literal AI: [Manual Deployment - Literal AI Documentation](https://docs.literalai.com/self-hosting/deployment)
- [ ] Try [Custom Data Layer - Chainlit](https://docs.chainlit.io/api-reference/data-persistence/custom-data-layer) (Literal AI replacement)

## Resources

Chainlit

- [Chainlit/chainlit: Build Conversational AI in minutes ⚡️](https://github.com/Chainlit/chainlit)
- [Overview - Chainlit](https://docs.chainlit.io/get-started/overview)
- [Chainlit/cookbook: Chainlit's cookbook repo](https://github.com/Chainlit/cookbook)
  - [cookbook/resume-chat at main · Chainlit/cookbook](https://github.com/Chainlit/cookbook/tree/main/resume-chat): the `app.py` is using LangChain v0.1 legacy syntax, recommend refer to the lean example `app_lean.py`

Literal AI

- [Literal AI - Chainlit](https://docs.chainlit.io/llmops/literalai): Shows how to intergrade Chainlit with Literal AI
- [Overview - Literal AI Documentation](https://docs.literalai.com/get-started/overview)
- [Literal AI Cloud - Dashboard](https://cloud.getliteral.ai): See records here
- [Chainlit/literalai-cookbooks: Cookbooks and tutorials on Literal AI](https://github.com/Chainlit/literalai-cookbooks)
- [Chainlit/literalai-python](https://github.com/Chainlit/literalai-python)
