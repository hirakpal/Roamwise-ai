# ====================== context_manager.py (Final Stable Version) ======================
import json
from typing import List, Dict, TYPE_CHECKING
from pydantic import ValidationError
from .state import TripState
if TYPE_CHECKING:
    from llm import LLMClient

# ---------------------------------------------------------------
# Strengthened extraction prompt
# ---------------------------------------------------------------
UPDATE_TRIP_STATE_PROMPT_V3 = """You are a precise information extractor.
Update the TripState based ONLY on the recent conversation and the current state.

CRITICAL FORMAT RULES:
- Return ONLY a valid JSON object with fields that need updating.
- Do NOT return null or empty fields.
- "travelers" must always be a STRING (e.g. "2 adults", "solo traveler", "family of 4"). Never return a number.
- "dates" should capture seasonal or approximate timing as a string (e.g. "spring", "last week of November").
- "duration" should be a string (e.g. "7-10 days", "4 nights").
- For list fields (preferences, constraints, open_questions): return the COMPLETE updated list.
- IMPORTANT: When the user mentions a general category AND specific examples (e.g. "contemporary art, like the Centre Pompidou or Musée d'Orsay"), you MUST include BOTH the general category ("contemporary art") AND the specific examples in the preferences list.
- Negations ("not interested in traditional art" / "rather than traditional") must REMOVE the item from preferences.
- budget = only budget level as string ("moderate", "luxury", etc.)
- hotel_preference = the EXACT phrase the user used (including articles like "a", "an", "the"). 
  Example: if user says "a boutique hotel with a good location", return exactly "a boutique hotel with a good location".
- constraints = only hard limitations (no stairs, wheelchair accessible, diet, etc.)

Current Trip State:
{current_trip_state_json}

Recent Conversation:
"""


class ContextManager:
    def __init__(
        self,
        llm_client: "LLMClient",
        max_recent_turns: int = 5,
        summary_threshold: int = 2800
    ):
        self.llm_client = llm_client
        self.max_recent_turns = max_recent_turns
        self.summary_threshold = summary_threshold

        self.history: List[Dict] = []
        self.summary: str = ""
        self.trip_state = TripState()

        # Token tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.token_log: List[Dict] = []

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------
    def add_message(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": [{"type": "text", "text": content}]
        })

    def add_assistant_message(self, content: str, prompt_tokens: int, completion_tokens: int):
        self.history.append({
            "role": "assistant",
            "content": [{"type": "text", "text": content}]
        })
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.token_log.append({
            "event": "Assistant Response",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        })

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------
    def get_recent_messages(self) -> List[Dict]:
        return self.history[-self.max_recent_turns:]

    def build_messages(self, system_prompt: str) -> List[Dict]:
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": system_prompt}]
            }
        ]

        # Compact Trip State
        messages.append({
            "role": "system",
            "content": [{"type": "text", "text": self.trip_state.to_compact_prompt()}]
        })

        # Summary of older conversation
        if self.summary:
            messages.append({
                "role": "system",
                "content": [{"type": "text", "text": f"Summary of earlier conversation:\n{self.summary}"}]
            })

        # Recent turns
        messages.extend(self.get_recent_messages())
        return messages

    # ------------------------------------------------------------------
    # Summarization (Sliding Window)
    # ------------------------------------------------------------------
    def should_summarize(self) -> bool:
        total_chars = sum(len(str(m.get("content", ""))) for m in self.history)
        estimated_tokens = total_chars // 4
        return (
            estimated_tokens > self.summary_threshold
            and len(self.history) > self.max_recent_turns
        )

    def summarize_older_history(self):
        if len(self.history) <= self.max_recent_turns:
            return

        older = self.history[:-self.max_recent_turns]
        if not older:
            return

        conversation_text = "\n".join(
            f"{msg['role'].upper()}: {msg['content'][0]['text']}"
            for msg in older
            if msg.get("content") and isinstance(msg["content"], list)
        )

        summary_prompt = [
            {
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": (
                        "Summarize the earlier part of the conversation. "
                        "Keep only: confirmed trip details, hard constraints, "
                        "key preferences, decisions already made, and open questions. "
                        "Be very concise (maximum 100 words). Do not invent information."
                    )
                }]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": conversation_text}]
            }
        ]

        summary_content, p_tokens, c_tokens = self.llm_client.chat(
            summary_prompt, temperature=0.2
        )

        self.summary = summary_content
        self.total_prompt_tokens += p_tokens
        self.total_completion_tokens += c_tokens
        self.token_log.append({
            "event": "Summarization",
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens
        })

        # Keep only recent turns
        self.history = self.history[-self.max_recent_turns:]

    # ------------------------------------------------------------------
    # Trip State Update (Token-optimized + Hardened)
    # ------------------------------------------------------------------
    def update_trip_state(self, max_turns_for_extraction: int = 3):
        recent = self.history[-max_turns_for_extraction:]

        escaped_state = (
            self.trip_state.model_dump_json()
            .replace("{", "{{")
            .replace("}", "}}")
        )

        messages = [
            {
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": UPDATE_TRIP_STATE_PROMPT_V3.format(
                        current_trip_state_json=escaped_state
                    )
                }]
            }
        ]
        messages.extend(recent)

        try:
            json_str, p_tokens, c_tokens = self.llm_client.chat(
                messages, temperature=0.1
            )

            self.total_prompt_tokens += p_tokens
            self.total_completion_tokens += c_tokens
            self.token_log.append({
                "event": "State Update",
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens
            })

            parsed = json.loads(json_str)

            # ---------- Post-processing / Hardening ----------
            if "travelers" in parsed:
                if isinstance(parsed["travelers"], (int, float)):
                    parsed["travelers"] = f"{int(parsed['travelers'])} adults"
                else:
                    parsed["travelers"] = str(parsed["travelers"])

            for list_field in ["preferences", "constraints", "open_questions"]:
                if list_field in parsed and not isinstance(parsed[list_field], list):
                    parsed[list_field] = [parsed[list_field]]
            # -------------------------------------------------

            self.trip_state = self.trip_state.model_copy(update=parsed)
            print("Trip State updated successfully.")

            self._update_readiness()

        except json.JSONDecodeError as e:
            print(f"JSON decode error in TripState update: {e}")
            print(f"Raw response: {json_str}")
        except ValidationError as e:
            print(f"Validation error in TripState update: {e}")
        except Exception as e:
            print(f"Unexpected error during TripState update: {e}")

    # ------------------------------------------------------------------
    # Automatic Readiness Detection (Very Conservative)
    # ------------------------------------------------------------------
    def _update_readiness(self):
        ts = self.trip_state

        has_destination = bool(ts.destination)
        has_who = bool(ts.travelers)
        has_when = bool(ts.dates or ts.duration)
        has_preferences = bool(ts.preferences or ts.constraints)
        has_budget = bool(ts.budget)
        has_hotel = bool(ts.hotel_preference)

        # Only move out of Discovery when we have richer information
        if has_destination and has_who and has_when and has_preferences and (has_budget or has_hotel):
            ts.readiness = "Execution Ready"
        elif has_destination and has_who and has_when and has_preferences:
            ts.readiness = "Concept Ready"
        else:
            # Stay in Discovery until we have more than just basic who/where/when
            ts.readiness = "Discovery"
