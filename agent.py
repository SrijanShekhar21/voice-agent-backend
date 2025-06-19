from dotenv import load_dotenv
import os

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
    google,
    speechify,
    sarvam,
)
import aws
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from api import Assistant
from prompts import WELCOME_MESSAGE
from custom_plugins.custom_tts import TTS as SarvamTTS

load_dotenv()

async def entrypoint(ctx: agents.JobContext):

    llm_model = google.LLM(
        model="gemini-2.0-flash",
        temperature=0.8,
    )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=llm_model,
        # tts=speechify.TTS(
        #     model="simba-english",
        #     voice_id="kristy",
        # ),
        # tts=SarvamTTS(
        #     api_key=os.getenv("SARVAM_API_KEY"),
        #     model="bulbul:v2",
        #     speaker="anushka",
        #     pitch=0.0,
        #     pace=1.0,
        #     loudness=1.0,
        #     enable_preprocessing=False,
        #      # Default, will be dynamically updated in say()
        # ),
        tts=aws.TTS(
            voice="Kajal",
            speech_engine="neural",
            language="hi-IN",
            region="ap-south-1",
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    assistant = Assistant()
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=WELCOME_MESSAGE
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

