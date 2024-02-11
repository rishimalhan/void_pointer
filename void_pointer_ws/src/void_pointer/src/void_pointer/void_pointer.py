#! /usr/bin/python3.8

import asyncio
import sys
import threading
import os
import numpy as np
import logging
import openai
import torchaudio
from asyncio.queues import Queue
from queue import Queue as sync_q
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from aiohttp import web
import socketio

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


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

openai.api_key = api_key
TRANSCRIBER = None


class GPTInterface(OpenAIAPI):
    def __init__(self):
        super(GPTInterface, self).__init__()
        self.transcribed_text = Queue()
        self.initialize()

    def initialize(self):
        message = "Your role is to chat with my 6 year old daughter, Myra. You can bring up topics of conversation that kids usually like. Ask follow up questions or change topics but keep the dialogue going. Make sure your response has some follow up question or way to move dialogue forward. Topics can range from music, dancing, cartoons, TV, school, etc. Beware to not say anything inappropriate for kids. While chatting smartly bring up good values as a human being. Keep your responses short and concise. Responses should not be more than a few sentences."
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",  # You can use other engines as necessary
            prompt=message,
            max_tokens=150,  # Adjust as necessary
        )
        logger.info(f"GPT initialized: {response.choices[0].text.strip()}")

    async def ask_gpt(self, message):
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",  # You can use other engines as necessary
            prompt=message,
            max_tokens=150,  # Adjust as necessary
        )
        return response.choices[0].text.strip()


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
        except Exception as e:
            logger.warning("Shutdown with exception: {}".format(str(e)))


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


# Create a Socket.IO server
sio = socketio.AsyncServer(async_mode="aiohttp")
app = web.Application()
sio.attach(app)


# Define the event for connecting
@sio.event
async def connect(sid, environ):
    print("Client connected", sid)


# Define the event for disconnecting
@sio.event
async def disconnect(sid):
    print("Client disconnected", sid)


# Handle audio data received from the client
@sio.event
async def audio_chunk(sid, data):
    print(f"Received audio chunk from {sid}, length: {len(data)}")
    # Process the audio data...
    audio_buffer = bytearray()
    # Assuming data is the audio chunk bytes
    audio_buffer += data
    audio_buffer = np.frombuffer(audio_buffer, dtype="int16")
    print("Received. Current size: ", len(audio_buffer))
    TRANSCRIBER.process_audio(audio_buffer)


# Define a simple HTTP GET route for testing
async def index(request):
    return web.Response(
        text="Void Pointer Server is Running!", content_type="text/html"
    )


app.router.add_get("/", index)


async def main():
    executor = ThreadPoolExecutor(max_workers=4)

    user_settings = get_user_settings()
    transcription_task = await asyncio.get_event_loop().run_in_executor(
        executor, partial(start_transcription, user_settings)
    )
    shutdown_task = await asyncio.get_event_loop().run_in_executor(executor, shutdown)
    trigger_gpt_task = await asyncio.get_event_loop().run_in_executor(
        executor, trigger_gpt
    )
    audio_input_task = await asyncio.get_event_loop().run_in_executor(
        executor, web.run_app(app, port=5000)
    )

    await asyncio.gather(
        audio_input_task, transcription_task, shutdown_task, trigger_gpt_task
    )


asyncio.run(main())
