import os
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv('test.env')

AGENT_ID = os.getenv("AGENT_ID")
API_KEY = os.getenv("API_KEY")
LOG_FILE = os.getenv("LOG_FILE", "conversation_log.txt")


if not API_KEY:
    raise ValueError("API_KEY not found in environment variables")
print("API_KEY loaded successfully")

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs.types import ConversationConfig

user_name = "Robil"
prompt = "You are a helpful assistant."
first_message = f"Hello {user_name}, how can I help you today?"

conversation_override = {
  "agent": {
    "prompt": {
      "prompt": prompt,
    },
    "first_message": first_message,
  },
}

config = ConversationConfig(
  conversation_config_override=conversation_override,
  extra_body={},
  dynamic_variables={},
  user_id=user_name,
)

client = ElevenLabs(api_key=API_KEY)

conversation = None

EXIT_TRIGGERS = {"stop", "exit", "quit", "bye", "goodbye", "end session"}
is_closing = False

def _normalize(text):
  return re.sub(r"[^a-z0-9\s]", "", text.lower())

def _should_end_session(text):
  if not text:
    return False
  norm = _normalize(text)
  return any(trigger in norm for trigger in EXIT_TRIGGERS)

def append_log(speaker, text):
  try:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
      f.write(f"{datetime.now().isoformat(timespec='seconds')} [{speaker}] {text}\n")
  except Exception:
    # Avoid crashing on logging errors
    pass

def print_agent_response(response):
  print(f"Agent: {response}")
  append_log("agent", response)

# def print_interrupted_response(original, corrected):
#   print(f"Agent interrupted, truncated response: {corrected}")

def print_user_transcript(transcript):
  print(f"User: {transcript}")
  append_log("user", transcript)
  try:
    global is_closing
    if is_closing:
      return
    if _should_end_session(transcript):
      print("Ending session on user request...")
      is_closing = True
      if conversation is not None:
        try:
          conversation.end_session()
        except Exception:
          pass
  except Exception:
    pass

conversation = Conversation(
  client,
  AGENT_ID,
  config=config,
  requires_auth=True,
  audio_interface=DefaultAudioInterface(),
  callback_agent_response=print_agent_response,
#   callback_agent_response_correction=print_interrupted_response,
  callback_user_transcript=print_user_transcript,
)

conversation.start_session()