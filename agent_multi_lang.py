from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    deepgram,
    sarvam,
    cartesia,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

# === Define your specialized agents ===

class ReceptionistAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful receptionist. Speak in English.")

class SalesAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=(
            "तुम एक बिक्री सहायक हो। हमेशा हिंदी में जवाब दो। "
            "उपयोगकर्ताओं को उत्पाद की जानकारी दो और उनकी खरीदारी में मदद करो।"
        ))

class TechSupportAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a technical support agent. Help users with technical issues in English.")

# === This function routes to the correct agent based on topic ===

async def route_to_specialist(ctx: agents.JobContext, topic: str):
    if topic == "sales":
        tts = google.TTS(voice="hi-IN-Wavenet-A")
        agent = SalesAgent()
        greeting = "नमस्ते! मैं बिक्री सहायता में आपकी मदद कर सकती हूँ।"
    elif topic == "tech":
        tts = cartesia.TTS(model="sonic-2", voice="56e35e2d-6eb6-4226-ab8b-9776515a7094")
        agent = TechSupportAgent()
        greeting = "Hi! How can I help with your technical issue?"
    else:
        tts = sarvam.TTS(
            api_key="3e8bc18a-5403-4936-8d67-cb0b212c0975",
            model="bulbul:v2",
            speaker="anushka",
            target_language_code="en-IN",
        )
        agent = ReceptionistAgent()
        greeting = "Hello! How may I assist you?"

    # Start new session with specialist agent
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash"),
        tts=tts,
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(instructions=greeting)

# === Entry Agent just greets ===

class EntryAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a receptionist. Greet the user and ask how you can help.")

# === Entrypoint ===

async def entrypoint(ctx: agents.JobContext):
    # Initial session with Sarvam English voice
    entry_session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash"),
        tts=sarvam.TTS(
            api_key="3e8bc18a-5403-4936-8d67-cb0b212c0975",
            model="bulbul:v2",
            speaker="anushka",
            target_language_code="en-IN",
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await entry_session.start(
        room=ctx.room,
        agent=EntryAgent(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Greet user
    await entry_session.generate_reply(instructions="Hi! How can I help you today?")

    # 🔥 Here's the FIX: actually listen for the user input
    user_turn = await entry_session.receive_turn()
    user_text = user_turn.transcript.lower()
    print("User said:", user_text)

    # Determine routing based on keywords
    if any(w in user_text for w in ["sales", "buy", "purchase", "बिक्री", "खरीद"]):
        await route_to_specialist(ctx, "sales")
    elif any(w in user_text for w in ["tech", "technical", "support", "problem", "issue", "तकनीकी"]):
        await route_to_specialist(ctx, "tech")
    else:
        await route_to_specialist(ctx, "reception")

# === Main App ===

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))