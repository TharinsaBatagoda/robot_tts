from flask import Flask, request, jsonify, send_from_directory
import edge_tts
import asyncio
import os
import uuid

app = Flask(__name__)

AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

VOICE = "en-US-AriaNeural"

latest_audio_url = None


async def generate_speech(text, output_path):
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(output_path)


@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Robot TTS</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
            }
            textarea {
                width: 100%;
                height: 120px;
                font-size: 18px;
                padding: 10px;
            }
            button {
                margin-top: 10px;
                padding: 12px 20px;
                font-size: 18px;
                cursor: pointer;
            }
            #status {
                margin-top: 15px;
                font-size: 16px;
                color: green;
            }
        </style>
    </head>
    <body>
        <h1>Robot Text to Speech</h1>

        <textarea id="text" placeholder="Type what the robot should say"></textarea>
        <br>
        <button onclick="sendText()">Speak</button>

        <p id="status"></p>

        <script>
            async function sendText() {
                const text = document.getElementById("text").value;

                const response = await fetch("/speak", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ text: text })
                });

                const data = await response.json();
                document.getElementById("status").innerText = data.message;
            }
        </script>
    </body>
    </html>
    """


@app.route("/speak", methods=["POST"])
def speak():
    global latest_audio_url

    data = request.get_json()
    text = data.get("text", "").strip()

    if text == "":
        return jsonify({"message": "Please enter some text"}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(AUDIO_DIR, filename)

    asyncio.run(generate_speech(text, output_path))

    latest_audio_url = request.host_url.rstrip("/") + f"/audio/{filename}"

    return jsonify({
        "message": "Audio created. ESP32 will play it.",
        "audio_url": latest_audio_url
    })


@app.route("/next", methods=["GET"])
def next_audio():
    global latest_audio_url

    if latest_audio_url is None:
        return jsonify({
            "available": False
        })

    audio_url = latest_audio_url
    latest_audio_url = None

    return jsonify({
        "available": True,
        "audio_url": audio_url
    })


@app.route("/audio/<filename>")
def get_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)