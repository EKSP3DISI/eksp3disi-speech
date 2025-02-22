import os
import signal
from dotenv import load_dotenv
from typing import Optional
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface


class ConversationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConversationManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Load environment variables
        load_dotenv()

        # Set your API key and initialize client
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable is not set")

        # Set your agent ID
        self.agent_id = os.getenv("ELEVENLABS_AGENT_ID")

        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=self.api_key)

    def start_session(self):
        # Initialize conversation
        self.conversation = Conversation(
            self.client,
            self.agent_id,
            requires_auth=True,
            audio_interface=DefaultAudioInterface(),
            callback_agent_response=lambda response: print(
                f"Agent: {response}"),
            callback_agent_response_correction=lambda original, corrected: print(
                f"Agent: {original} -> {corrected}"),
            callback_user_transcript=lambda transcript: print(
                f"User: {transcript}"),
        )
        """Start a new conversation session"""
        self.conversation.start_session()
        signal.signal(signal.SIGINT, lambda sig, frame: self.end_session())

    def end_session(self):
        """End the current conversation session"""
        self.conversation.end_session()
        conversation_id = self.conversation.wait_for_session_end()
        print(f"Conversation ID: {conversation_id}")

    @staticmethod
    def play_audio(audio_data: bytes, sample_rate: Optional[int] = None, blocking: bool = False):
        """Play audio data"""
        play(audio_data)


# Create a global instance
conversation_manager = ConversationManager()
