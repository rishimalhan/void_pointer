document.getElementById('startRecord').onclick = startRecording;
document.getElementById('stopRecord').onclick = stopRecording;

let mediaRecorder;
let audioChunks = [];

async function startRecording() {
    audioChunks = [];
    document.getElementById('startRecord').disabled = true;
    document.getElementById('stopRecord').disabled = false;

    const stream = await navigator.mediaDevices.getUserMedia({
        audio:
        {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true
        }
    }).then(stream => {
        // Now you can use this stream with MediaRecorder
        const options = { mimeType: 'audio/webm' };
        const mediaRecorder = new MediaRecorder(stream, options);
        // Proceed with setting up event handlers and starting the MediaRecorder
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            sendAudioToServer(audioBlob);
        };

        mediaRecorder.start();
    }).catch(error => {
        console.error('getUserMedia error:', error);
    });
    // mediaRecorder = new MediaRecorder(stream);
}

function stopRecording() {
    document.getElementById('startRecord').disabled = false;
    document.getElementById('stopRecord').disabled = true;

    mediaRecorder.stop();
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    fetch('/audio', {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}
