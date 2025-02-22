import os
import signal
from dotenv import load_dotenv
from typing import Optional
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Load environment variables
load_dotenv()

# Set your API key and initialize client
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
# Set your agent ID
agent_id = os.getenv("ELEVENLABS_AGENT_ID")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

conversation = Conversation(
    # API client and agent ID.
    client,
    agent_id,

    # Assume auth is required when API_KEY is set.
    requires_auth=True,

    # Use the default audio interface.
    audio_interface=DefaultAudioInterface(),

    # Simple callbacks that print the conversation to the console.
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(
        f"Agent: {original} -> {corrected}"),
    callback_user_transcript=lambda transcript: print(f"User: {transcript}"),

    # Uncomment if you want to see latency measurements.
    # callback_latency_measurement=lambda latency: print(f"Latency: {latency}ms"),
)

def start_session():
    conversation.start_session()
    
def end_session():
    conversation.end_session()
    conversation.wait_for_session_end()

def play_audio(audio_data: bytes, sample_rate: Optional[int] = None, blocking: bool = False):
    play(audio_data)