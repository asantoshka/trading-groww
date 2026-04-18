import asyncio
import json
from datetime import datetime

import websockets


WS_URL = "ws://localhost:8000/ws/feed"


def format_message(raw_message: str) -> str:
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError:
        return f"[{datetime.now().strftime('%H:%M:%S')}] RAW | {raw_message}"

    event_type = str(payload.get("type", "unknown")).upper()
    details = " ".join(
        f"{key}: {value}"
        for key, value in payload.items()
        if key != "type"
    )
    return f"[{datetime.now().strftime('%H:%M:%S')}] {event_type} | {details}"


async def listen_forever() -> None:
    while True:
        try:
            async with websockets.connect(WS_URL) as websocket:
                print("Connected to feed. Waiting for events...")
                async for message in websocket:
                    print(format_message(message))
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"Connection error: {exc}. Retrying in 3s...")
            await asyncio.sleep(3)


def main() -> None:
    try:
        asyncio.run(listen_forever())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
