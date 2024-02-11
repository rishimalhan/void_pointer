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

from aiohttp import web
import numpy as np
import aiohttp_jinja2
import jinja2
import os

script_dir = os.path.dirname(os.path.abspath(__file__))


async def handle_audio(request):
    # Receive the audio file
    data = await request.read()
    # Convert the audio data to a numpy array (example placeholder, adjust according to actual audio format)
    audio_np = np.frombuffer(data, dtype=np.int16)
    print("Received audio data", audio_np)
    return web.Response(text="Audio received")


async def init_app():
    app = web.Application()
    # Setup Jinja2 for template rendering
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))
    # Static routes for JS/CSS
    app.router.add_static("/static/", path=static_dir, name="static")
    # POST route for audio data
    app.router.add_post("/audio", handle_audio)
    # GET route for index page
    app.router.add_get(
        "/",
        lambda request: aiohttp_jinja2.render_template(
            os.path.join(templates_dir, "index.html"), request, {}
        ),
    )
    return app


web.run_app(init_app(), host="127.0.0.1", port=5000)
