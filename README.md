# RVC Text-to-Speech WebUI

This is a text-to-speech Gradio webui for [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) models, using [edge-tts](https://github.com/rany2/edge-tts).

[🤗 Online Demo](https://huggingface.co/spaces/litagin/rvc_okiba_TTS)

This can run on CPU without GPU (but slow).

![Screenshot](assets/screenshot.jpg)

## Install

Requirements: Tested for Python 3.10 on Windows 11. Python 3.11 is probably not supported, so please use Python 3.10.

```bash
git clone https://github.com/litagin02/rvc-tts-webui.git
cd rvc-tts-webui

# Download models in root directory
curl -L -O https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt
curl -L -O https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt

# Make virtual environment
python -m venv venv
# Activate venv (for Windows)
venv\Scripts\activate

# Install PyTorch manually if you want to use NVIDIA GPU (Windows)
# See https://pytorch.org/get-started/locally/ for more details
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install requirements
pip install -r requirements.txt
```

## Locate RVC models

Place your RVC models in `weights/` directory as follows:

```bash
weights
├── model1
│   ├── my_model1.pth
│   └── my_index_file_for_model1.index
└── model2
    ├── my_model2.pth
    └── my_index_file_for_model2.index
...
```

Each model directory should contain exactly one `.pth` file and at most one `.index` file. Directory names are used as model names.

It seems that non-ASCII characters in path names gave faiss errors (like `weights/モデル1/index.index`), so please avoid them.

## Launch

```bash
# Activate venv (for Windows)
venv\Scripts\activate

python app.py
```

## Update

```bash
git pull
venv\Scripts\activate
pip install -r requirements.txt --upgrade
```

## FOR USE WITH OPEN-WEBUI:

First of all, the steps above will need to be followed. 

Your setup steps for will need to align with your overall setup, but however you have Open-WebUI and RVC running, they will need to be able to connect to each other - in the case of a docker-compose setup (like mine), for instance, they should be on the same network. 

In case it may be useful to someone, the section for RVC in my my docker-compose.yml looks something like this: 

```
  rvc-tts-webui:
    build:
      context: ./projects/rvc-tts-webui
    container_name: rvc-tts-webui
    ports:
      - "9000:9000"
      - "8002:8002"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    volumes:
      - ./projects/rvc-tts-webui/weights:/app/weights
      - ./projects/rvc-tts-webui/output:/app/output
    command: [ "/app/start_services.sh" ]
    networks:
      - ai_services
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [ gpu ]
```

After that is completed, (again, as of Open-WebUI v0.3.13) - you will need to edit the main.py file in Open-WebUI/backend/apps/audio. My 'speech' method has been replaced with the following: 

```
@app.post("/speech")
async def speech(request: Request, user=Depends(get_verified_user)):
    body = await request.body()
    name = hashlib.sha256(body).hexdigest()

    file_path = SPEECH_CACHE_DIR.joinpath(f"{name}.mp3")
    file_body_path = SPEECH_CACHE_DIR.joinpath(f"{name}.json")

    # Check if the file already exists in the cache
    if file_path.is_file():
        return FileResponse(file_path)

    headers = {
        "Authorization": f"Bearer {app.state.config.TTS_OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        body = body.decode("utf-8")
        body_json = json.loads(body)
        body_json.update({
            "rvc_model_name": app.state.config.TTS_MODEL,
            "speed": 0,
            "tts_text": body_json.get("input"),
            "tts_voice": app.state.config.TTS_VOICE,
            "f0_key_up": 0,
            "f0_method": "rmvpe",
            "index_rate": 1,
            "protect0": 0.5
        })
        body = json.dumps(body_json).encode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request format")

    r = None
    try:
        r = requests.post(
            url=f"{app.state.config.TTS_OPENAI_API_BASE_URL}/audio/speech",
            data=body,
            headers=headers,
            stream=True,
        )

        r.raise_for_status()

        # Save the streaming content to a file
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        with open(file_body_path, "w") as f:
            json.dump(body_json, f)

        # Return the saved file
        return FileResponse(file_path)

    except Exception as e:
        error_detail = "Open WebUI: Server Connection Error"
        if r is not None:
            try:
                res = r.json()
                if "error" in res:
                    error_detail = f"External: {res['error']['message']}"
            except Exception as json_err:
                error_detail = f"External: {e}"

        raise HTTPException(
            status_code=r.status_code if r != None else 500,
            detail=error_detail,
        )
```

Then, (as of Open-WebUI v0.3.13), you will need to edit the "Audio" section in Open-WebUI's Admin Panel > Settings. Again, your setup as a whole will dictate what needs to go in here, but in my case (using Docker-Compose for everything), my API base url is "http://rvc-tts-webui:8002/v1". In the "TTS Voice" section, you will need to put the Edge-tts speaker you want to use for the model (you can find these by opening RVC on its own - in my case, that's at http://localhost:9000/). The model itself will be the name of the RVC model you want to use. Make sure it matches the folder name that you put the index and .pth files into in the weights folder, otherwise it won't find them properly.


If the steps above have all been completed, TTS should work for your configured TTS voice for both manual TTS as well as voice calls with your AI model.

## Troubleshooting

```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
  ERROR: Failed building wheel for fairseq
Failed to build fairseq
ERROR: Could not build wheels for fairseq, which is required to install pyproject.toml-based projects
```

Maybe fairseq needs Microsoft C++ Build Tools.
[Download installer](https://visualstudio.microsoft.com/ja/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16) and install it.
