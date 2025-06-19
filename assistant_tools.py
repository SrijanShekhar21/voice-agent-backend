from livekit.agents import function_tool, Agent, RunContext
from prompts import INSTRUCTIONS
import enum
from typing import Annotated
import logging
from db_driver import DatabaseDriver
from livekit.agents import get_job_context, RunContext
from livekit import api, rtc

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

class Assistant(Agent):
    def __init__(self, ctx) -> None:
        super().__init__(instructions=INSTRUCTIONS)
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

