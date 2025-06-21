from dotenv import load_dotenv
from livekit.plugins import aws, sarvam
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google, cartesia, deepgram, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from dataclasses import dataclass

load_dotenv()

# ---------- Session Data Structure ----------
@dataclass
class DemoSessionData:
    name: str = ""
    email: str = ""
    issue: str = ""
    product_interest: str = ""
    customer_id: str = ""
    language_code: str = ""

# ---------- Front Desk Agent ----------
class FrontDeskAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a friendly receptionist. Ask the user how you can help—sales, technical support, or customer support—and route accordingly. Be friendly, calm and polite while speaking."
        )

    @agents.function_tool()
    async def route_query(self, query: str):
        query = query.lower()
        if "buy" in query or "price" in query or "product" in query:
            await self.session.say("I'm transferring you to Geeta from sales.")
            return SalesAgent()
        elif "not working" in query or "problem" in query or "issue" in query:
            await self.session.say("I'm transferring you to Meetu from technical support.")
            return TechnicalSupportAgent()
        else:
            await self.session.say("I'm transferring you to Siya from customer support.")
            return CustomerSupportAgent()

# ---------- Sales Agent ----------
class SalesAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            instructions="You are Maya, a helpful sales assistant. Greet the user and ask for their name, email, and product of interest.",
            **kwargs
        )

    async def on_start(self):
        await self.session.say("Hi, I'm Maya from sales. How can I help you today?")

    @agents.function_tool()
    async def record_name(self, name: str):
        self.session.userdata.name = name

    @agents.function_tool()
    async def record_email(self, email: str):
        self.session.userdata.email = email

    @agents.function_tool()
    async def record_product(self, product: str):
        self.session.userdata.product_interest = product

# ---------- Technical Support Agent ----------
class TechnicalSupportAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            instructions="You are Maya, a technical support agent. Greet the user and ask for name, email, and a description of the issue.",
            **kwargs
        )

    async def on_start(self):
        await self.session.say("Hi, I'm Maya from technical support. How can I assist you today?")

    @agents.function_tool()
    async def record_name(self, name: str):
        self.session.userdata.name = name

    @agents.function_tool()
    async def record_email(self, email: str):
        self.session.userdata.email = email

    @agents.function_tool()
    async def record_issue(self, issue: str):
        self.session.userdata.issue = issue

# ---------- Customer Support Agent ----------
class CustomerSupportAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            instructions="You are Maya, a customer support agent. Greet the user and ask for their name and customer ID.",
            **kwargs
        )

    async def on_start(self):
        await self.session.say("Hi, I'm Maya from customer support. What can I do for you today?")

    @agents.function_tool()
    async def record_name(self, name: str):
        self.session.userdata.name = name

    @agents.function_tool()
    async def record_customer_id(self, customer_id: str):
        self.session.userdata.customer_id = customer_id

# ---------- Entry Point ----------
async def entrypoint(ctx: agents.JobContext):
    # Default values for dynamic EOU control
    language_code = "hi-IN"

    # Select VAD-only if Hindi, otherwise use multilingual model
    vad_model = silero.VAD.load()
    turn_model = None if language_code.startswith("hi") else MultilingualModel()

    session = AgentSession[DemoSessionData](
        userdata=DemoSessionData(language_code=language_code),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash"),
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
        agent=FrontDeskAgent(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and ask how you can help: sales, technical support, or customer service."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
