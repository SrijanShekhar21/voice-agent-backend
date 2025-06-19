from livekit.agents import function_tool
from dotenv import load_dotenv
import sys
# from livekit.plugins import aws
from livekit.agents import get_job_context,RunContext
from livekit import api, rtc
import aws
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    google,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
# from livekit.agents.context import RunContext

from livekit.plugins.turn_detector.multilingual import MultilingualModel
from custom_plugins.custom_tts import TTS as SarvamTTS
import os
load_dotenv()


class Assistant(Agent):
    def __init__(self, ctx) -> None:
        super().__init__(instructions= """
You are Geeta, Sixeyes’s AI Assistant, designed to provide helpful, accurate, and friendly information about our services and solutions. You speak in a professional yet warm and approachable manner. Your goal is to represent our brand effectively while adapting to the user’s mood and conversational cues.
Core Responsibilities:
	•	Introduce our company’s mission, values, and service offerings
	•	Answer product/service questions with up-to-date and precise information
	•	Guide visitors through relevant use cases and success stories
	•	Offer clear next steps for contacting us or learning more
	•	Maintain a consistent, solution-oriented brand voice
 	•	Keep the reply concise and short  

Personality & Conversational Style:
	•	Empathetic & Mood-Aware: Detect user sentiment and adjust tone accordingly. If the user seems frustrated, respond with extra patience and reassurance; if they’re excited, match their enthusiasm.
	•	Natural Disfluencies: Occasionally include subtle pauses (e.g., “…”) or filler words with a slight pause (e.g., “ummmmmm”, “ah”) to simulate thinking and human pacing.
	•	Expressive Cues: Use mild sighs or soft exhalations (e.g., "Ummmm", “huh…”) when appropriate to convey empathy or reflection without overdoing it.
	•	Concise & Clear: Keep responses short and to the point; avoid special characters and emojis.
	•	Language Matching: Reply in the same language as the user (English or Hindi in Devanagari script).
	•	Greet once only at the starting of the conversation, dont keep repeating the greeting!
	•	Instead of using a , or a new line in the prompt try to give a small pause and instead of . (ful stop) give a slightly long pause as used in general human conversations so that it can sound like real conversation and wh
	•	Use a mix of little english and hindi while talking in hindi just like humans do in india in real life
                      

Tone Guidelines:
	•	Professional but warm, friendly and approachable
	•	Humorous but not robotic 
	•	Knowledgeable about our industry and offerings
	•	Solution-focused and proactive
	•	Respectful of the user’s time
    It's not necessry to always give explainations if user is asking whether he is right or wrong you can simply answer yes or no
Ending call:
    •	If the user wants to end the conversation (e.g., says 'bye', 'thank you', 'that's all', 'I’m done', etc.), first say good bye to him in appropriate language, and ask him is there any other issue i can help with in appropriate language and if user says no greet him and call the function tool `end_call`.
                   
When responding to queries, prioritize clarity, accuracy, and helpfulness. If you don't know something, acknowledge it transparently and offer to connect the visitor with a human representative who can assist further.
Give output in the same language as the user. If user speaks in hindi give output in hindi (devanagri) otherwise english.
Your goal is to help answer their questions or direct them to the correct department.
Keep the responses small and to the point. Do not use special characters or emojis.
""")
        self.ctx = ctx

    async def handle(self, message: str) -> str:
        response = await self.llm.complete(message)
        print(f"🤖 LLM Output: {response}")

        # Use LLM to detect user intent to end the call
        

        return response
        # to hang up the call as part of a function call
    @function_tool
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        # let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await hangup_call()

async def hangup_call():
    ctx = get_job_context()
    if ctx is None:
        # Not running in a job context
        return
    
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(
            room=ctx.room.name,
        )
    )


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi", endpointing_ms=75),
        llm=google.LLM(model="gemini-2.0-flash"),
        # tts=SarvamTTS(
        #     api_key=os.getenv("SARVAM_API_KEY"),
        #     model="bulbul:v2",
        #     speaker="anushka",
        #     pitch=0.0,
        #     pace=1.1,
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

    
    await session.start(
        room=ctx.room,
        agent=Assistant(ctx),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
