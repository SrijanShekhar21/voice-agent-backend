from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import sarvam, deepgram, google, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from dataclasses import dataclass

load_dotenv()

# --------- Session Data ---------
@dataclass
class DemoSessionData:
    name: str = ""
    email: str = ""
    query_type: str = ""
    language_code: str = ""
    notes: str = ""

# --------- Greeting Agent ---------
class MultilingualReceptionist(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are an intelligent multilingual receptionist named Ria. Greet the user in their preferred language. Ask if they need help with sales, technical support, or customer support. Forward them accordingly."
        )

    async def on_start(self):
        await self.session.say("Hi! I'm Ria, your virtual assistant. How may I help you today?")

    @agents.function_tool()
    async def route_request(self, query: str):
        query = query.lower()
        if any(word in query for word in ["buy", "price", "product"]):
            await self.session.say("Transferring you to Geeta from sales.")
            return SalesAgent()
        elif any(word in query for word in ["not working", "problem", "issue"]):
            await self.session.say("Connecting you with Meetu from technical support.")
            return TechnicalSupportAgent()
        else:
            await self.session.say("Alright, I'll transfer you to Siya from customer support.")
            return CustomerSupportAgent()

# --------- Sales Agent ---------
class SalesAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are Geeta, a helpful sales agent. Ask for name, email, and the product they are interested in.")

    async def on_start(self):
        await self.session.say("Hi, I'm Geeta from sales. What are you looking to buy today?")

# --------- Technical Support Agent ---------
class TechnicalSupportAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are Meetu, a technical expert. Ask about the issue they are facing.")

    async def on_start(self):
        await self.session.say("Hi, I'm Meetu from technical support. Please describe your issue.")

# --------- Customer Support Agent ---------
class CustomerSupportAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are Siya, a kind customer support agent. Ask for name and customer ID.")

    async def on_start(self):
        await self.session.say("Hi, I'm Siya from customer support. How can I assist you today?")

# --------- Entry Point ---------
async def entrypoint(ctx: agents.JobContext):
    language_code = "hi-IN"
    vad_model = silero.VAD.load()
    turn_model = None if language_code.startswith("hi") else MultilingualModel()

    session = AgentSession[DemoSessionData](
        userdata=DemoSessionData(language_code=language_code),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-1.5-flash"),
        tts=sarvam.TTS(
            api_key="3e8bc18a-5403-4936-8d67-cb0b212c0975",
            model="bulbul:v2",
            speaker="anushka",
            target_language_code=language_code,
        ),
        vad=vad_model,
        turn_detection=turn_model,
    )

    await session.start(
        room=ctx.room,
        agent=MultilingualReceptionist(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()
    await session.say("Greet the user and route them to the appropriate department.")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
