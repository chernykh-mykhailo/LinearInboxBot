import base64
import json
import logging
import re
from typing import Any, Dict, Optional
import httpx

from src.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]


class AIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def _call_gemini(self, contents: list, system_instruction: str) -> Optional[str]:
        if not self.is_configured():
            logger.warning("Gemini API key is not configured.")
            return None

        for model in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                },
                "contents": contents,
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            }

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    else:
                        logger.warning(
                            f"Gemini API returned status {resp.status_code} for {model}: {resp.text}"
                        )
            except Exception as e:
                logger.error(f"Error calling Gemini model {model}: {e}")

        return None

    def _parse_task_json(self, raw_json_text: str, fallback_text: str) -> Dict[str, Any]:
        try:
            cleaned = raw_json_text.strip()
            # Strip markdown codeblocks if model returned them
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            data = json.loads(cleaned)
            title = str(data.get("title", "")).strip()
            description = str(data.get("description", "")).strip()
            priority = int(data.get("priority", 0))
            if priority not in (0, 1, 2, 3, 4):
                priority = 0

            if not title:
                title = fallback_text.split("\n")[0][:80]

            return {
                "title": title,
                "description": description,
                "priority": priority,
                "transcript": data.get("transcript", ""),
            }
        except Exception as e:
            logger.error(f"Failed to parse Gemini JSON output: {e}. Raw: {raw_json_text}")
            lines = fallback_text.strip().split("\n", 1)
            return {
                "title": lines[0][:80],
                "description": lines[1] if len(lines) > 1 else "",
                "priority": 0,
                "transcript": fallback_text,
            }

    async def enhance_text_task(
        self,
        raw_text: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: str = "image/jpeg",
        language: str = "uk",
    ) -> Dict[str, Any]:
        lang_directive = (
            "Write the title and description in Ukrainian."
            if language == "uk"
            else "Write the title and description in English."
        )

        system_instruction = f"""
You are an expert product manager and software engineer assistant converting raw notes and screenshots into professional Linear issues.
{lang_directive}

Rules:
1. title: Short, concise, action-oriented task title (max 70 characters). Start with an imperative verb (e.g., 'Fix...', 'Add...', 'Refactor...', 'Implement...').
   IMPORTANT: If the user mentions multiple problems or items (e.g., 'Fix audio button, fix white screen glitch'), make sure the title covers ALL requested items or summarizes them together. Never drop any part of the request.
2. description: Well-structured Markdown. If a screenshot is provided, analyze the visual interface and incorporate relevant visual context into the problem description. Include:
   - ## Context (brief problem or idea explanation)
   - ## Proposed Solution / Acceptance Criteria (bullet points covering every reported problem)
3. priority: Linear priority integer:
   0 = No priority / Backlog
   1 = Urgent (P0 / critical bug)
   2 = High (P1)
   3 = Medium (P2 - standard feature/fix)
   4 = Low (P3 - minor improvement / nice to have)

Respond ONLY with valid JSON matching this schema:
{{
  "title": "string",
  "description": "string",
  "priority": 0
}}
"""
        parts = [{"text": f"Raw user note:\n{raw_text}"}]
        if image_bytes:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": image_mime_type,
                        "data": base64.b64encode(image_bytes).decode("utf-8"),
                    }
                }
            )

        contents = [{"role": "user", "parts": parts}]

        raw_output = await self._call_gemini(contents, system_instruction)
        if not raw_output:
            lines = raw_text.strip().split("\n", 1)
            return {
                "title": lines[0][:80],
                "description": lines[1] if len(lines) > 1 else "",
                "priority": 0,
                "transcript": raw_text,
            }

        return self._parse_task_json(raw_output, raw_text)

    async def transcribe_and_enhance_audio(
        self, audio_bytes: bytes, mime_type: str = "audio/ogg", language: str = "uk"
    ) -> Dict[str, Any]:
        lang_directive = (
            "Write the title and description in Ukrainian."
            if language == "uk"
            else "Write the title and description in English."
        )

        system_instruction = f"""
You are an expert product manager and software engineer assistant.
You receive an audio recording (voice note) from a developer or product owner describing a task, bug, or idea.
{lang_directive}

Steps:
1. Accurately transcribe the entire audio message verbatim into 'transcript'.
2. Formulate a clean, professional Linear issue based on the transcription:
   - title: Short, concise, action-oriented (max 70 characters). Start with an action verb.
   - description: Markdown with Context and Key Points / Acceptance Criteria.
   - priority: 0 (None), 1 (Urgent), 2 (High), 3 (Medium), 4 (Low).

Respond ONLY with valid JSON matching this schema:
{{
  "transcript": "Full verbatim transcription of the audio",
  "title": "Short issue title",
  "description": "Structured markdown description",
  "priority": 0
}}
"""
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": audio_b64,
                        }
                    },
                    {"text": "Transcribe this audio and format it into a structured Linear task."},
                ],
            }
        ]

        raw_output = await self._call_gemini(contents, system_instruction)
        if not raw_output:
            return {
                "title": "Voice Task Note",
                "description": "Could not transcribe audio via AI.",
                "priority": 0,
                "transcript": "",
            }

        return self._parse_task_json(raw_output, "Voice Task")
