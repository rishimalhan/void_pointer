document.getElementById('startRecord').onclick = startRecording;
document.getElementById('stopRecord').onclick = stopRecording;

let mediaRecorder;
let audioChunks = [];

async function startRecording() {
    audioChunks = [];
    document.getElementById('startRecord').disabled = true;
    document.getElementById('stopRecord').disabled = false;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        sendAudioToServer(audioBlob);
    };

    mediaRecorder.start();
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
