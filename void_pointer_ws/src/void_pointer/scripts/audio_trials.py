# from flask import Flask, render_template
# from flask_socketio import SocketIO
# import numpy as np
# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# from functools import partial

# app = Flask(__name__)
# app.config["SECRET_KEY"] = "secret!"
# socketio = SocketIO(app)
# global shutdown_requested
# shutdown_requested = False

# # audio_buffer = bytearray()
# CHUNK_SIZE = 1024  # Define your chunk size here
# CHUNK_SIZE = 0  # Define your chunk size here


# def process_audio_chunk(chunk):
#     # Dummy function to process the audio chunk
#     # Convert chunk to numpy array or process as needed
#     print(f"Processed chunk size: {len(chunk)}")
#     try:
#         audio_data = np.frombuffer(chunk, dtype="int16")
#     except Exception as e:
#         print("Exception handling audio: ", e)
#     print(audio_data)
#     print(type(audio_data))


# @app.route("/")
# def index():
#     return render_template("index.html")


# @socketio.on("audio_chunk")
# def handle_audio_chunk(data):
#     audio_buffer = bytearray()
#     # Assuming data is the audio chunk bytes
#     audio_buffer += data
#     print("Received. Current size: ", len(audio_buffer))

#     # If the buffer reaches or exceeds the CHUNK_SIZE, process it
#     if len(audio_buffer) >= CHUNK_SIZE:
#         # chunk_to_process = audio_buffer[:CHUNK_SIZE]
#         chunk_to_process = audio_buffer
#         # audio_buffer = audio_buffer[CHUNK_SIZE:]
#         process_audio_chunk(chunk_to_process)


# async def shutdown():
#     global shutdown_requested
#     print("Kicking off shutdown loop")
#     while not shutdown_requested:
#         try:
#             await asyncio.sleep(0.001)
#         except KeyboardInterrupt:
#             print("Shutting Down")
#             shutdown_requested = True
#         except Exception as e:
#             print("Shutdown with exception: {}".format(str(e)))


# async def main():
#     executor = ThreadPoolExecutor(max_workers=1)
#     shutdown_task = await asyncio.get_event_loop().run_in_executor(
#         executor, shutdown, debug=True
#     )
#     audio_task = await asyncio.get_event_loop().run_in_executor(
#         executor, socketio.run(app, host="0.0.0.0", port=5000, debug=True)
#     )
#     await asyncio.gather(shutdown_task, audio_task)


# if __name__ == "__main__":
#     socketio.run(app, host="0.0.0.0", port=5000, debug=True)
#     asyncio.run(main())


# WORKING VERSION
from aiohttp import web
import numpy as np
import aiohttp_jinja2
import jinja2
import os
import asyncio
import aiohttp_cors
import sys
from pydub import AudioSegment
import io
from functools import partial

shutdown_requested = False
package_path = "/Users/rmalhan/AI/void_pointer/void_pointer_ws/src/void_pointer"
CHUNK = 512

sys.path.append(os.path.join(package_path, "src/void_pointer"))
from utils import contains_non_numbers, bytes_to_chunks


# Webserver for Audio
async def handle_main(request):
    context = {"title": "Audio Recorder"}
    response = aiohttp_jinja2.render_template("index.html", request, context)
    return response


def start_ipython(request):
    from IPython import embed

    embed(colors="neutral")


async def handle_audio_post(request, dtype=np.float32):
    await asyncio.get_running_loop().run_in_executor(
        None, partial(start_ipython, request)
    )

    # Receive the audio file
    data = request.read()
    audio_array = bytearray()
    audio_array += data

    # Convert the audio data to a numpy array (example placeholder, adjust according to actual audio format)
    element_size = np.dtype(dtype).itemsize
    buffer_size = len(audio_array)

    # Ensure the buffer size is a multiple of the element size
    if buffer_size % element_size != 0:
        # Trim the buffer to make it fit, this will remove the last few bytes:
        audio_array = audio_array[: buffer_size - (buffer_size % element_size)]

    audio_stream = io.BytesIO(audio_array)
    audio = (
        AudioSegment.from_file(audio_stream, format="webm")
        .set_frame_rate(16000)
        .set_channels(1)
    )
    wav_bytes = io.BytesIO()
    audio.export(wav_bytes, format="wav")

    # Now convert the buffer to a numpy array
    audio_np = bytes_to_chunks(wav_bytes.getvalue(), chunk_size=CHUNK, dtype=dtype)
    for audio_chunk in audio_np:
        if contains_non_numbers(audio_chunk):
            print("WARNING. Arr has non numbers")
        print(np.min(audio_chunk), np.max(audio_chunk))
    return web.Response(text="Audio received", content_type="text/plain")


async def init_app():
    app = web.Application()
    # Setup CORS
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers=("X-Requested-With", "Content-Type", "Accept", "Origin"),
                allow_methods=["POST", "GET"],
            )
        },
    )

    # Setup Jinja2 for template rendering
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(package_path, "templates"))
    )
    # GET route for index page
    app.router.add_get("/", handle_main, name="main")
    # Add your route
    route = app.router.add_post("/audio", handle_audio_post, name="audio_post")
    # Apply CORS to the route
    cors.add(route)
    # Static routes for JS/CSS
    app.router.add_static(
        "/static/",
        path=os.path.join(package_path, "static"),
        name="static",
    )
    return app


async def main():
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=5004)
    await site.start()
    while True:
        await asyncio.sleep(3600)


asyncio.run(main())

# import sounddevice as sd
# import time


# def create_audio_stream(selected_device, callback):
#     RATE = 16000
#     CHUNK = 512
#     CHANNELS = 1
#     DTYPE = "float32"

#     stream = sd.InputStream(
#         device=selected_device,
#         channels=CHANNELS,
#         samplerate=RATE,
#         callback=callback,
#         dtype=DTYPE,
#         blocksize=CHUNK,
#     )

#     return stream


# def call_back_func(audio_data, frames, time, status):
#     print(min(audio_data))
#     print(max(audio_data))


# stream = create_audio_stream(selected_device=1, callback=call_back_func)
# stream.start()
# time.sleep(2.0)
# stream.stop()
