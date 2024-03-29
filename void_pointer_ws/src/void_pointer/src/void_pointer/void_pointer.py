#! /usr/bin/python3.8

import asyncio
import sys
import threading
import os
import numpy as np
import logging
from openai import AsyncOpenAI
import torchaudio
from asyncio.queues import Queue
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiohttp_cors
from utils import bytes_to_chunks
from rospkg.rospack import RosPack

from faster_whisper import WhisperModel
from speech_to_text.audio_transcriber import AppOptions
from speech_to_text.audio_transcriber import AudioTranscriber
from speech_to_text.utils.audio_utils import get_valid_input_devices, base64_to_audio
from speech_to_text.utils.file_utils import read_json, write_json, write_audio
from speech_to_text.websoket_server import WebSocketServer
from speech_to_text.openai_api import OpenAIAPI

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

package_path = RosPack().get_path("void_pointer")
client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODEL_NAME = "gpt-3.5-turbo-0125"
TRANSCRIBER = None
CHUNK = 512


class GPTInterface(OpenAIAPI):
    def __init__(self):
        super(GPTInterface, self).__init__()
        self.transcribed_text = Queue()
        self._initialize = False

    async def initialize(self):
        message = {
            "role": "assistant",
            "content": "Your role is to chat with my 6 year old daughter, Myra. You can bring up topics of conversation that kids usually like. Ask follow up questions or change topics but keep the dialogue going. Make sure your response has some follow up question or way to move dialogue forward. Topics can range from music, dancing, cartoons, TV, school, etc. Beware to not say anything inappropriate for kids. While chatting smartly bring up good values as a human being. Keep your responses short and concise. Responses should not be more than a few sentences. Don't start the conversation until Myra starts it with you.",
        }
        response = await client.chat.completions.create(
            messages=[message], model=MODEL_NAME, stream=True
        )
        logger.info(f"GPT initialized: Response:")
        async for chunk in response:
            print(chunk.choices[0].delta.content or "", end="")

    async def ask_gpt(self, message):
        if not self._initialize:
            await self.initialize()

        return_response = ""
        response = await client.chat.completions.create(
            messages=[{"role": "assistant", "content": message}],
            model=MODEL_NAME,
            stream=True,
        )
        logger.info(f"GPT initialized: Response:")
        async for chunk in response:
            if response is None:
                continue
            return_response = " ".join(
                [return_response, chunk.choices[0].delta.content]
            )
        return return_response


gpt_interface = GPTInterface()
TRANSCRIBER: AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None
websocket_server: WebSocketServer = None
openai_api: OpenAIAPI = None
shutdown_requested = False


def get_user_settings():
    data_types = ["app_settings", "model_settings", "transcribe_settings"]
    user_settings = {}

    try:
        data = read_json("settings", "user_settings")
        for data_type in data_types:
            user_settings[data_type] = data[data_type]
    except Exception as e:
        logger.warning("Configuraiton not found")

    return user_settings


async def start_transcription(user_settings):
    global TRANSCRIBER, event_loop, thread, websocket_server, openai_api, gpt_interface
    logger.info("Kicking off transcriber loop")
    try:
        (
            filtered_app_settings,
            filtered_model_settings,
            filtered_transcribe_settings,
        ) = extracting_each_setting(user_settings)

        whisper_model = WhisperModel(**filtered_model_settings)
        filtered_app_settings["audio_device"] = 8
        app_settings = AppOptions(**filtered_app_settings)
        event_loop = asyncio.new_event_loop()

        if app_settings.use_websocket_server:
            websocket_server = WebSocketServer(event_loop)
            asyncio.run_coroutine_threadsafe(
                websocket_server.start_server(), event_loop
            )

        TRANSCRIBER = AudioTranscriber(
            event_loop,
            whisper_model,
            filtered_transcribe_settings,
            app_settings,
            websocket_server,
            gpt_interface,
        )
        asyncio.set_event_loop(event_loop)
        thread = threading.Thread(target=event_loop.run_forever, daemon=True)
        thread.start()

        asyncio.run_coroutine_threadsafe(TRANSCRIBER.start_transcription(), event_loop)
    except Exception as e:
        logger.warning("Exception while starting transcribe: {}".format(str(e)))


async def stop_transcription():
    logger.info("Stopping transcription")
    global TRANSCRIBER, event_loop, thread, websocket_server, openai_api
    if TRANSCRIBER is None:
        return
    transcriber_future = asyncio.run_coroutine_threadsafe(
        TRANSCRIBER.stop_transcription(), event_loop
    )
    transcriber_future.result()

    if websocket_server is not None:
        websocket_server_future = asyncio.run_coroutine_threadsafe(
            websocket_server.stop_server(), event_loop
        )
        websocket_server_future.result()

    if thread.is_alive():
        event_loop.call_soon_threadsafe(event_loop.stop)
        thread.join()
    event_loop.close()
    TRANSCRIBER = None
    event_loop = None
    thread = None
    websocket_server = None
    openai_api = None


async def audio_transcription(user_settings, base64data):
    global TRANSCRIBER, openai_api
    try:
        (
            filtered_app_settings,
            filtered_model_settings,
            filtered_transcribe_settings,
        ) = extracting_each_setting(user_settings)

        whisper_model = WhisperModel(**filtered_model_settings)
        app_settings = AppOptions(**filtered_app_settings)

        if app_settings.use_openai_api:
            openai_api = OpenAIAPI()

        TRANSCRIBER = AudioTranscriber(
            event_loop,
            whisper_model,
            filtered_transcribe_settings,
            app_settings,
            None,
            openai_api,
        )

        audio_data = base64_to_audio(base64data)
        if len(audio_data) > 0:
            write_audio("web", "voice", audio_data)
            TRANSCRIBER.batch_transcribe_audio(audio_data)

    except Exception as e:
        logger.warning("Exception while transcribing: {}".format(str(e)))

    openai_api = None


def get_filtered_app_settings(settings):
    valid_keys = AppOptions.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def get_filtered_model_settings(settings):
    valid_keys = WhisperModel.__init__.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def get_filtered_transcribe_settings(settings):
    valid_keys = WhisperModel.transcribe.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def extracting_each_setting(user_settings):
    filtered_app_settings = get_filtered_app_settings(user_settings["app_settings"])
    filtered_model_settings = get_filtered_model_settings(
        user_settings["model_settings"]
    )
    filtered_transcribe_settings = get_filtered_transcribe_settings(
        user_settings["transcribe_settings"]
    )

    write_json(
        "settings",
        "user_settings",
        {
            "app_settings": filtered_app_settings,
            "model_settings": filtered_model_settings,
            "transcribe_settings": filtered_transcribe_settings,
        },
    )

    return filtered_app_settings, filtered_model_settings, filtered_transcribe_settings


async def shutdown():
    global shutdown_requested
    logger.info("Kicking off shutdown loop")
    while not shutdown_requested:
        try:
            await asyncio.sleep(0.001)
        except KeyboardInterrupt:
            logger.info("Shutting Down")
            await stop_transcription()
            shutdown_requested = True
            return True
        except Exception as e:
            logger.warning("Shutdown with exception: {}".format(str(e)))
            return True


async def trigger_gpt():
    logger.info("Kicking off GPT interface")
    global shutdown_requested
    while not shutdown_requested:
        text = None
        try:
            text = gpt_interface.transcribed_text.get_nowait()
            gpt_interface.transcribed_text.task_done()
        except asyncio.QueueEmpty:
            pass
        if text:
            logger.info(f"STT: {text}")
            response = await gpt_interface.ask_gpt(message=text)
            logger.info("GPT: {}".format(response))
            # audio_array = generate_audio_from_long_text(response)
            # sd.play(audio_array, SAMPLE_RATE)
        await asyncio.sleep(0.001)


# Webserver for Audio
async def handle_main(request):
    context = {"title": "Audio Recorder"}
    response = aiohttp_jinja2.render_template("index.html", request, context)
    return response


async def handle_audio_post(request, dtype=np.float32):
    # Receive the audio file
    data = await request.read()
    audio_array = bytearray()
    audio_array += data

    # Convert the audio data to a numpy array (example placeholder, adjust according to actual audio format)
    element_size = np.dtype(dtype).itemsize
    buffer_size = len(audio_array)

    # Ensure the buffer size is a multiple of the element size
    if buffer_size % element_size != 0:
        # Trim the buffer to make it fit, this will remove the last few bytes:
        audio_array = audio_array[: buffer_size - (buffer_size % element_size)]

    # Now convert the buffer to a numpy array
    logger.info("DEBUG: Sending audio for processing.")
    audio_np = bytes_to_chunks(audio_array, chunk_size=CHUNK, dtype=dtype)
    for audio_chunk in audio_np:
        TRANSCRIBER.process_audio(audio_chunk)
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
    app.on_startup.append(start_background_tasks)
    return app


async def start_background_tasks(app):
    user_settings = get_user_settings()
    transcription_task = asyncio.create_task(
        partial(start_transcription, user_settings)()
    )
    shutdown_task = asyncio.create_task(shutdown())
    trigger_gpt_task = asyncio.create_task(trigger_gpt())
    app["background_task"] = asyncio.gather(
        transcription_task, shutdown_task, trigger_gpt_task
    )


async def main():
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=5000)
    await site.start()
    results = await app["background_task"]
    logger.info(f"Shutdown Completed With Results: {results}")


asyncio.run(main())
