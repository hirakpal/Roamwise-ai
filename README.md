# The Worldly Companion

**A token-efficient, memory-aware AI travel planning agent**

The Worldly Companion is an intelligent conversational travel advisor that prioritizes understanding the traveler before generating itineraries. It combines structured state management, sliding-window context, and automatic summarization to deliver high-quality planning while keeping token usage under control.

---

## Key Features

- **Structured Trip State**  
  Maintains a clean, typed representation of destination, travelers, constraints, preferences, budget, and readiness level.

- **Token-Efficient Context Management**  
  - Sliding window of recent turns  
  - Automatic summarization of older conversation  
  - State extraction limited to recent messages  
  - Compact Trip State injection on every turn

- **Readiness Model**  
  - `Discovery` → `Concept Ready` → `Execution Ready`  
  Prevents premature full itineraries and respects the traveler’s pace.

- **Permission Gate**  
  Asks for confirmation before collecting operational details (dates, budget, hotel preferences, etc.).

- **Human-Centric Design**  
  Special attention to constraints such as mobility limitations, elderly travelers, and pace preferences.

- **Live Observability**  
  Real-time display of Trip State and token usage in the Streamlit UI.

---

## Architecture Overview

```text
┌─────────────────────┐
│   System Prompt     │  (V2.3 Few-Shot)
│  (Identity + Rules) │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│   Compact TripState │  ← Structured external memory
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  Summary (if any)   │  ← Compressed older history
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  Recent Turns (≤5)  │  ← Sliding window
└─────────────────────┘

```
## Project Structure
```
worldly-companion/
├── app/
│   └── main.py                 # Streamlit application
├── core/
│   ├── prompt.py               # System prompt (V2.3)
│   ├── state.py                # TripState Pydantic model
│   ├── llm.py                  # OpenAI client wrapper
│   └── context_manager.py      # Memory + summarization logic
├── tests/
│   ├── test_state_extraction.py
│   ├── test_negation.py
│   └── test_summarization.py
├── requirements.txt
├── .env.example
└── README.md
```
