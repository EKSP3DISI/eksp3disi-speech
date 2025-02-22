import asyncio
import websockets
import json
import logging
from typing import Set
from contextlib import asynccontextmanager
from websockets.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server configuration
HOST = "0.0.0.0"
PORT = 8765
HEARTBEAT_INTERVAL = 30  # seconds
active_connections: Set[WebSocketServerProtocol] = set()

@asynccontextmanager
async def track_connection(websocket: WebSocketServerProtocol):
    active_connections.add(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Client {client_info} successfully connected. Active connections: {len(active_connections)}")
    try:
        yield
    finally:
        active_connections.remove(websocket)
        logger.info(f"Client {client_info} disconnected. Active connections: {len(active_connections)}")

async def heartbeat(websocket: WebSocketServerProtocol):
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await websocket.ping()
    except websockets.ConnectionClosed:
        pass

async def handler(websocket: WebSocketServerProtocol):  # Remove path parameter
    async with track_connection(websocket):
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New connection from {client_info}")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat(websocket))
        
        try:
            async for data in websocket:
                try:
                    message = json.loads(data)
                    
                    if not isinstance(message, dict) or "type" not in message or "data" not in message:
                        raise ValueError("Invalid message format")
                    
                    if message["type"] == "command":
                        command = message["data"]
                        logger.info(f"Received command from {client_info}: {command}")
                        
                        if command == "start_conversation":
                            response = {"type": "ack", "data": "Conversation started"}
                            await websocket.send(json.dumps(response))
                            
                    elif message["type"] == "audio":
                        audio_chunk = message["data"]
                        logger.info(f"Received audio data from {client_info}: {len(audio_chunk)} bytes")
                        # Process audio chunk here
                    
                    else:
                        logger.warning(f"Unknown message type from {client_info}: {message['type']}")
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {client_info}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "data": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from {client_info}: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "data": "Internal server error"
                    }))
                    
        except websockets.ConnectionClosed as e:
            logger.info(f"Connection closed with {client_info}: {e}")
        finally:
            heartbeat_task.cancel()

async def shutdown(signal):
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [ws.close() for ws in active_connections]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Shutdown complete.")

async def main():
    try:
        logger.info(f"Starting WebSocket server on ws://{HOST}:{PORT}")
        async with websockets.serve(
            handler,  # Updated handler without path parameter
            HOST,
            PORT,
            ping_interval=None  # Disable built-in ping as we have our own heartbeat
        ):
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")