let mediaRecorder;
let audioChunks = [];

async function startRecording() {
    audioChunks = []; // Reset the audio chunks array

    // Request permission and get the audio stream
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
            sampleRate: 44100,
            channelCount: 1,
        }
    });
    mediaRecorder = new MediaRecorder(stream);

    // Collect the audio data chunks
    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    // When recording stops, send the audio data to the server
    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { 'type': 'audio/wav' });
        const formData = new FormData();
        formData.append("audio_data", audioBlob);

        // Send the audio blob to the server using fetch API
        fetch("/audio", {
            method: "POST",
            body: formData,
        })
            .then(response => response.text())
            .then(data => {
                console.log(data); // Log server response
            })
            .catch(error => {
                console.error("Error sending audio data:", error);
            });
    };

    // Start recording
    mediaRecorder.start();
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop(); // This triggers the onstop event
    }
}
