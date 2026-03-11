import os
import json

import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

load_dotenv()
cl.instrument_openai()


@function_tool
async def lookup_weather(city: str) -> str:
    """Returns current weather for a given city."""
    forecasts = {
        "san francisco": {"temp": "18°C", "condition": "Foggy", "wind": "12 km/h"},
        "new york":      {"temp": "25°C", "condition": "Sunny", "wind": "8 km/h"},
        "london":        {"temp": "14°C", "condition": "Rainy", "wind": "20 km/h"},
        "tokyo":         {"temp": "28°C", "condition": "Humid", "wind": "5 km/h"},
    }
    result = forecasts.get(city.lower(), {"temp": "22°C", "condition": "Clear", "wind": "10 km/h"})
    async with cl.Step(name="lookup_weather", type="tool") as step:
        step.input = city
        step.output = json.dumps(result)
    return json.dumps(result)


agent = Agent(
    name="Weather Assistant",
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    instructions="You are a helpful weather assistant. Use the lookup_weather tool to answer weather questions.",
    tools=[lookup_weather],
)


@cl.on_chat_start
async def on_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Hi! I'm a weather assistant. Ask me about the weather in any city.").send()


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history") or []
    history.append({"role": "user", "content": message.content})

    result = await Runner.run(agent, history)
    cl.user_session.set("history", result.to_input_list())
    await cl.Message(content=result.final_output).send()
