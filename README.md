# FIZ ISE LLM API

A proxy interface that adds some authentication and logging to an LLM hosted on one of the ISE servers. (currently Meta-Llama-3-70B-Instruct.Q4_0 but this will become configurable)

The main purpose is to allow API access, so that calls can be made to an [OpenAI compatible interface](https://platform.openai.com/docs/guides/text-generation/chat-completions-api) by external colleagues who do not have access to our internal server infrastructure,.

![Simple Chat](screenshot_chat.png)

The running system can be used at: https://llm.ise.fiz-karlsruhe.de/
