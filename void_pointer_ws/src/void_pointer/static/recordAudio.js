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
            echoCancellation: true,
        }
    });
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
    fetch('/audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'audio/webm', // or the appropriate type for your audio Blob
        },
        body: audioBlob
    }).then(response => {
        if (response.ok) {
            return response.json(); // or .text() or whatever the server responds with
        }
        throw new Error('Network response was not ok.');
    }).then(data => {
        console.log(data); // Handle the response data
    }).catch(error => {
        console.error('There was a problem with your fetch operation:', error);
    });
}

// function sendAudioToServer(audioBlob) {
//     const formData = new FormData();
//     formData.append('audio', audioBlob);

//     fetch('/audio', {
//         method: 'POST',
//         body: formData,
//     })
//         .then(response => response.json())
//         .then(data => {
//             console.log('Success:', data);
//         })
//         .catch((error) => {
//             console.error('Error:', error);
//         });
// }