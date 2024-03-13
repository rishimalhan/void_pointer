let audioContext, scriptProcessor, mediaStreamSource, audioChunks = [];

document.getElementById('startRecord').onclick = startRecording;
document.getElementById('stopRecord').onclick = stopRecording;

async function startRecording() {
    audioChunks = [];
    audioContext = new AudioContext();
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaStreamSource = audioContext.createMediaStreamSource(stream);
    scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);

    scriptProcessor.onaudioprocess = function (audioProcessingEvent) {
        const inputBuffer = audioProcessingEvent.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        audioChunks.push(inputData.slice(0)); // Copy the Float32Array
    };

    mediaStreamSource.connect(scriptProcessor);
    scriptProcessor.connect(audioContext.destination);

    document.getElementById('startRecord').disabled = true;
    document.getElementById('stopRecord').disabled = false;
}

function stopRecording() {
    scriptProcessor.disconnect();
    audioContext.close();

    // Assuming you want to send the data to the server here
    sendAudioToServer(audioChunks);

    document.getElementById('startRecord').disabled = false;
    document.getElementById('stopRecord').disabled = true;
}

function sendAudioToServer(audioData) {
    // Convert audioData to a blob and send it via WebSocket or Fetch API
    const audioBlob = new Blob(audioData, { type: 'audio/wav' });
    // Example using fetch to send the audioBlob
    fetch('/audio', {
        method: 'POST',
        body: audioBlob,
    })
        .then(response => response.text())
        .then(data => console.log(data))
        .catch((error) => console.error('Error:', error));
}
