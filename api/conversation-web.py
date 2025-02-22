import asyncio
import json
from urllib.parse import urlparse, parse_qs
import websockets


async def handler_send(websocket, path):
    parsed = urlparse(path)
    if parsed.path != '/v1/convai/conversation':
        await websocket.close(code=4001, reason="Invalid endpoint")
        return
    
    query = parse_qs(parsed.query)
    agent_ids = query.get("agent_id")

    if not agent_ids:
        await websocket.close(code=4002, reason="Missing required agent_id parameter")
        return
    agent_id = agent_ids[0]
    print(f"[INFO] Connection accepted for agent_id: {agent_id}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                error = {"error": "Invalid JSON format"}
                await websocket.send(json.dumps(error))
                continue

            # Dispatch based on send schema first:
            if "user_audio_chunk" in data:
                print("[MESSAGE] Received User Audio Chunk.")
                # Process user audio chunk here.
            elif data.get("type") == "pong":
                print(f"[MESSAGE] Received Pong. Event ID: {data.get('event_id')}")
            elif data.get("type") == "conversation_initiation_client_data":
                print("[MESSAGE] Received Conversation Initiation Client Data.")
                print(f"         First Message: {data.get('first_message')}")
                # Further processing of conversation_config_override,
                # agent, prompt, language, tts, etc.
            elif data.get("type") == "client_tool_result":
                print("[MESSAGE] Received Client Tool Result.")
                print(f"         Tool Call ID: {data.get('tool_call_id')}")
            # Dispatch based on receive schema:
            elif data.get("type") in ["conversation_initiation_metadata", "user_transcript",
                                    "agent_response", "agent_response_correction", "audio",
                                    "interruption", "ping"]:
                print(f"[MESSAGE] Received receive schema message of type: {data.get('type')}")
            else:
                print("[WARNING] Unknown message type received:", data)

            # Send back a simple acknowledgment with echo of received data
            ack = {"status": "received", "echo": data}
            await websocket.send(json.dumps(ack))

    except websockets.ConnectionClosed as e:
        print(f"[INFO] Connection closed: {e}")
    finally:
        print(f"[INFO] Connection closed for agent_id: {agent_id}")

async def handle_conversation_initiation_metadata(data, websocket):
    metadata = data.get("conversation_initiation_metadata_event", {})
    conversation_id = metadata.get("conversation_id")
    agent_audio_format = metadata.get("agent_output_audio_format")
    user_audio_format = metadata.get("user_input_audio_format")
    print("[RECEIVE] Conversation Initiation Metadata:")
    print(f" Conversation ID: {conversation_id}")
    print(f" Agent Audio Format: {agent_audio_format}")
    print(f" User Audio Format: {user_audio_format}")
    ack = {"status": "metadata_received", "conversation_id": conversation_id}
    await websocket.send(json.dumps(ack))

async def handle_user_transcript(data, websocket):
    transcript_event = data.get("user_transcription_event", {})
    transcript = data.get("user_transcript")
    print("[RECEIVE] User Transcript:")
    print(f" Transcript: {transcript}")
    ack = {"status": "transcript_received", "transcript": transcript}
    await websocket.send(json.dumps(ack))

async def handle_agent_response(data, websocket):
    response_event = data.get("agent_response_event", {})
    agent_response = data.get("agent_response")
    print("[RECEIVE] Agent Response:")
    print(f" Response: {agent_response}")
    ack = {"status": "agent_response_received"}
    await websocket.send(json.dumps(ack))

async def handle_agent_response_correction(data, websocket):
    correction_event = data.get("correction_event", {})
    corrected_response = data.get("corrected_response")
    print("[RECEIVE] Agent Response Correction:")
    print(f" Corrected Response: {corrected_response}")
    ack = {"status": "agent_response_correction_received"}
    await websocket.send(json.dumps(ack))

async def handle_audio(data, websocket):
    audio_event = data.get("audio_event", {})
    audio_base64 = data.get("audio_base_64")
    event_id = data.get("event_id")
    print("[RECEIVE] Audio Response:")
    print(f" Audio Base64 Data: {audio_base64[:30]}...") # log only beginning snippet
    print(f" Event ID: {event_id}")
    ack = {"status": "audio_received", "event_id": event_id}
    await websocket.send(json.dumps(ack))

async def handle_interruption(data, websocket):
    interruption_event = data.get("interruption_event", {})
    event_id = data.get("event_id")
    print("[RECEIVE] Interruption:")
    print(f" Interrupted Event ID: {event_id}")
    ack = {"status": "interruption_received", "event_id": event_id}
    await websocket.send(json.dumps(ack))

async def handle_ping(data, websocket):
    ping_event = data.get("ping_event", {})
    event_id = data.get("event_id")
    ping_ms = data.get("ping_ms")
    print("[RECEIVE] Ping:")
    print(f" Ping Event ID: {event_id}")
    print(f" Measured Ping (ms): {ping_ms}")
    # Optionally respond to ping if needed:
    pong_response = {"type": "pong", "event_id": event_id}
    await websocket.send(json.dumps(pong_response))


async def handler_receive(websocket, path):
    # Parse path and query parameters:
    parsed = urlparse(path)
    if parsed.path != '/v1/convai/conversation':
    # Close if path is not matching
        await websocket.close(code=4001, reason="Invalid endpoint")
        return

    query = parse_qs(parsed.query)
    agent_ids = query.get("agent_id")
    if not agent_ids:
        await websocket.close(code=4002, reason="Missing required agent_id parameter")
        return

    agent_id = agent_ids[0]
    print(f"[INFO] Connection accepted for agent_id: {agent_id}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                error = {"error": "Invalid JSON format"}
                await websocket.send(json.dumps(error))
                continue

            # First, check send schema messages:
            if "user_audio_chunk" in data:
                print("[SEND] Received User Audio Chunk.")
                # Additional processing can be added here.
                ack = {"status": "user_audio_chunk_received"}
                await websocket.send(json.dumps(ack))
            elif data.get("type") == "pong":
                print(f"[SEND] Received Pong. Event ID: {data.get('event_id')}")
                ack = {"status": "pong_received"}
                await websocket.send(json.dumps(ack))
            elif data.get("type") == "conversation_initiation_client_data":
                print("[SEND] Received Conversation Initiation Client Data.")
                print(f"         First Message: {data.get('first_message')}")
                ack = {"status": "conversation_initiation_data_received"}
                await websocket.send(json.dumps(ack))
            elif data.get("type") == "client_tool_result":
                print("[SEND] Received Client Tool Result.")
                print(f"         Tool Call ID: {data.get('tool_call_id')}")
                ack = {"status": "client_tool_result_received"}
                await websocket.send(json.dumps(ack))
            # Next, check receive schema messages:
            elif data.get("type") in ["conversation_initiation_metadata", "user_transcript",
                                    "agent_response", "agent_response_correction", "audio",
                                    "interruption", "ping"]:
                msg_type = data.get("type")
                if msg_type == "conversation_initiation_metadata":
                    await handle_conversation_initiation_metadata(data, websocket)
                elif msg_type == "user_transcript":
                    await handle_user_transcript(data, websocket)
                elif msg_type == "agent_response":
                    await handle_agent_response(data, websocket)
                elif msg_type == "agent_response_correction":
                    await handle_agent_response_correction(data, websocket)
                elif msg_type == "audio":
                    await handle_audio(data, websocket)
                elif msg_type == "interruption":
                    await handle_interruption(data, websocket)
                elif msg_type == "ping":
                    await handle_ping(data, websocket)
                else:
                    print(f"[WARNING] Unhandled receive message type: {msg_type}")
            else:
                print("[WARNING] Unknown message received:", data)
                error = {"error": "Unknown message type"}
                await websocket.send(json.dumps(error))

    except websockets.exceptions.ConnectionClosed as e:
        print(f"[INFO] Connection closed: {e}")
    