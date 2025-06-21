import os
import asyncio
from dotenv import load_dotenv
from langdetect import detect
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import deepgram, sarvam, silero, google, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# ---------- Real Agent ----------
class MultilangAgent(Agent):
    def __init__(self, lang_code):
        super().__init__(instructions="You are a helpful assistant. Greet and assist the user in their language.")
        self.lang_code = lang_code

    async def on_start(self):
        if self.lang_code == "hi-IN":
            await self.session.say("नमस्ते! मैं आपकी कैसे मदद कर सकती हूँ?")
        else:
            await self.session.say("Hello! How can I help you today?")

# ---------- Language Detection (Pre-session) ----------
async def detect_language_from_microphone():
    stt = deepgram.STT(model="nova-3", language="multi")
    vad = silero.VAD.load()
    print("🎤 Listening for user input to detect language...")

    transcript = await stt.transcribe_with_vad(vad=vad, timeout=10)

    if not transcript:
        print("❌ No speech detected. Defaulting to English.")
        return "en-IN"

    print("🗣 Detected speech:", transcript)
    lang = detect(transcript)
    print("🌐 Detected language:", lang)

    return "hi-IN" if lang.startswith("hi") else "en-IN"

# ---------- Entry Point ----------
async def entrypoint(ctx: agents.JobContext):
    # Step 1: Detect language first
    lang_code = await detect_language_from_microphone()

    # Step 2: Start actual session with correct TTS
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash"),
        tts=sarvam.TTS(
            api_key=SARVAM_API_KEY,
            model="bulbul:v2",
            speaker="anushka",
            target_language_code=lang_code,
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await ctx.connect()

    await session.start(
        room=ctx.room,
        agent=MultilangAgent(lang_code),
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    await session.generate_reply(instructions="Start with a greeting in the user's language.")

# ---------- Run ----------
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))