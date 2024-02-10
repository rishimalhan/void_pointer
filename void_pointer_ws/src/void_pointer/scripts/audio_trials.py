from flask import Flask, render_template
from flask_socketio import SocketIO
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# audio_buffer = bytearray()
CHUNK_SIZE = 1024  # Define your chunk size here
CHUNK_SIZE = 102400  # Define your chunk size here


def process_audio_chunk(chunk):
    # Dummy function to process the audio chunk
    # Convert chunk to numpy array or process as needed
    print(f"Processed chunk size: {len(chunk)}")
    audio_data = np.frombuffer(chunk, dtype="int16")
    print(audio_data)
    print(type(audio_data))


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    audio_buffer = bytearray()
    # Assuming data is the audio chunk bytes
    audio_buffer += data
    print("Received. Current size: ", len(audio_buffer))

    # If the buffer reaches or exceeds the CHUNK_SIZE, process it
    if len(audio_buffer) >= CHUNK_SIZE:
        chunk_to_process = audio_buffer[:CHUNK_SIZE]
        audio_buffer = audio_buffer[CHUNK_SIZE:]
        process_audio_chunk(chunk_to_process)


async def run_blocking_io():
    loop = asyncio.get_running_loop()
    # None uses the default ThreadPoolExecutor
    await loop.run_in_executor(
        None, socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    )
    print("Audio receiver function has completed")


async def main():
    await run_blocking_io()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    asyncio.run(main())
