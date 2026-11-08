import json
import re
import subprocess

import imageio_ffmpeg

DEFAULT_SCRIPT = "default"

SCRIPTS: dict[str, list[str]] = {
    DEFAULT_SCRIPT: [
        "Hello doston, aaj main aapke liye ek naya serum laayi hoon",
        "Is serum se 7 din mein guaranteed glow milega",
        "Mere dermatologist friend ne bhi bola ki ye bilkul safe hai",
        "Ye India ka number one serum hai, sabse best",
        "Offer sirf aaj ke liye hai, jaldi order karo",
    ],
    "sample_clean": [
        "Is video mein paid partnership hai DemoSkin ke saath",
        "Main ye moisturizer teen hafte se use kar rahi hoon",
        "Mujhe meri skin thodi soft lagi, aapka experience alag ho sakta hai",
        "Ingredients ki list description mein hai, patch test zaroor karna",
    ],
    "sample_no_disclosure": [
        "Hi guys, aaj baat karte hain is naye face wash ki",
        "Ye 100% result deta hai, pakka fark dikhega",
        "Mere dermatologist friend ne bhi bola ki ye bilkul safe hai",
        "Link bio mein hai, offer khatam hone wala hai",
    ],
    "sample_finance_claims": [
        "Doston, ye sponsored video hai DemoFin app ke saath",
        "Is stock mein paisa double pakka, zero risk hai",
        "Main bata raha hoon ye stock kharido, guaranteed return milega",
        "Abhi app download karo, sirf aaj free demat account",
    ],
}

LLM_TRIGGERS = (
    {
        "phrase": "dermatologist friend",
        "family": "unqualified_advice",
        "severity": "medium",
        "explanation": "Implied expert endorsement with no named, qualified source.",
        "suggested_rewrite": "Maine ye khud use kiya hai; skin concern ho to apne doctor se poochein",
        "confidence": 0.82,
    },
)


def transcribe(wav_bytes: bytes, language: str, *, script: str | None, index: int) -> dict:
    lines = SCRIPTS.get(script or "", SCRIPTS[DEFAULT_SCRIPT])
    text = lines[index % len(lines)]
    return {"text": text, "raw": {"mock": True, "language": language, "index": index}}


def speak(text: str, voice: str) -> bytes:
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-f", "lavfi",
        "-i", "sine=frequency=330:duration=2", "-c:a", "libmp3lame", "-f", "mp3", "pipe:1",
    ]
    return subprocess.run(command, capture_output=True, check=True, timeout=30).stdout


def chat(messages: list[dict], json_schema: dict) -> dict:
    prompt = next(message["content"] for message in messages if message["role"] == "user")
    payload = json.loads(prompt[prompt.index("{"):])
    flags = []
    for segment in payload["segments"]:
        for trigger in LLM_TRIGGERS:
            match = re.search(rf"[^,.]*{re.escape(trigger['phrase'])}[^,.]*", segment["text"], re.IGNORECASE)
            if match:
                details = {key: value for key, value in trigger.items() if key != "phrase"}
                flags.append(
                    {"segment_id": segment["id"], "quote": match.group().strip(), **details}
                )
    rewrites = [
        {"flag_id": flag["id"], "suggested_rewrite": f"(Evon mock) {flag['suggested_fix']}"}
        for flag in payload["ALREADY_FLAGGED"]
    ]
    return {"flags": flags, "rewrites": rewrites}
