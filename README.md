# From Prompt to Agent: Your First Intelligent AI System

**Workshop | 18 April 2026 | University of Hertfordshire**

---

## 🥇 Challenge Winner — Session 5

<p align="center">
  <img src="<img width="988" height="1600" alt="WhatsApp Image 2026-04-18 at 9 18 13 PM" src="https://github.com/user-attachments/assets/0619e3d1-b796-4c1a-bf5d-53b630e66ae8" />
" width="140" style="border-radius:50%;border:4px solid gold"/>
</p>

<p align="center">
  <strong>🏆 First Place — Smart Budget RobotChef Challenge</strong><br/>
  University of Hertfordshire · 18 April 2026
</p>

| Field | Detail |
|---|---|
| **Name** | Mahaboob Shaik |
| **Student ID** | 24164385 |
| **LinkedIn** | [linkedin.com/in/shaik-mahaboob07](https://www.linkedin.com/in/shaik-mahaboob07/) |
| **Project** | Smart Budget RobotChef — A2A Multi-Agent System with `fit_budget`, `get_nutrition`, `get_price` MCP tools |

> *"The system extended the RobotChef A2A baseline with a budget-aware Food Analysis Agent that picks the best dish within a user-defined budget and dietary constraints, then passes a full task specification to the Robotics Designer Agent."*

---

## Presenters

| Presenter | Role | LinkedIn |
|---|---|---|
| **Abolfazl Zaraki** | Senior Lecturer in Robotics and AI | [Profile](https://www.linkedin.com/in/abolfazl-zaraki-8b48b12a/) |
| **M. Reza Shahabian A.** | Principal AI Engineer \| AI Researcher | [Profile](https://www.linkedin.com/in/mrshahabian/) |
| **Khashayar Ghamati** | Principal AI Engineer \| AI Researcher | [Profile](https://www.linkedin.com/in/khashayarghamati/) |
| **Ali Fallahi** | AI UX Researcher \| HRI | [Profile](https://www.linkedin.com/in/ali-fallahi/) |
| **Danial Zafaranchizadeh M.** | AI Engineer \| Robotics Researcher | [Profile](https://www.linkedin.com/in/danial-za/) |

Brought to you by **PARSAI** and the **School of Physics, Engineering and Computer Science, University of Hertfordshire**.

---

## Quick Start

```bash
git clone https://github.com/UH-Workshop-M726/FromPromptsToAgents.git
cd FromPromtsToAgents/
```

Each session is self-contained. Follow the steps in order within each session folder.

---

## Python Environment Setup

Create a virtual environment once at the root of the repo, then activate it before running any session code.

**Create and activate:**
```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (Command Prompt):
.venv\Scripts\activate.bat

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

Your prompt will show `(.venv)` when the environment is active.

**Install dependencies for the session you are working on:**
```bash
pip install -r session1/requirements.txt
```

> **Tip:** You only need to create the virtual environment once. Just re-run the `activate` command each time you open a new terminal.

---

## LLM Setup — Choose Your Backend

### Option 1: Local University LLM (Primary)
### Option 2: Google Gemini (Free Fallback)

1. Go to **https://aistudio.google.com**
2. Sign in → click **"Get API Key"** → **"Create API key"** → copy it
3. In your `.env` file set:
4. **Test your connection:**
```bash
cd session1
cp .env.example .env
python llm_client.py
```

---

## How to Follow Along

### Session 1 : Building Blocks
```bash
cd session1
pip install -r requirements.txt
cp .env.example .env

python steps/step1_hello_llm.py
python steps/step2_conversation.py
python steps/step3_temperature.py
streamlit run steps/step4_chatbot.py
streamlit run steps/step5_personas.py
```

### Session 2 : MCP & Robotics Agent
```bash
cd session2
pip install -r requirements.txt
cp .env.example .env

python steps/step1_explore_data.py
python steps/step2_test_tools.py
python steps/step3_run_agent.py
```

### Session 3 : RAG Concepts
```bash
cd session3
pip install -r requirements.txt
cp .env.example .env

python rag_demo.py
streamlit run rag_streamlit.py
```

### Session 4 : Recipe Agent
```bash
cd session4
pip install -r requirements.txt
cp .env.example .env

python steps/step1_explore_dishes.py
python steps/step2_test_tools.py
python steps/step3_run_agent.py
```

### Session 5 : A2A — Smart Budget RobotChef 🏆
```bash
cd session5
pip install -r requirements.txt
cp .env.example .env

streamlit run app.py
```

**Session 5 features (Challenge winner's extension):**
- 💰 **Smart Budget Mode** — set a budget (£5–£50), number of people, and dietary filter
- 🥗 **`fit_budget`** — ranks all dishes by protein-per-£1 value score within budget
- 🧪 **`get_nutrition`** — returns protein, carbs, fat, kcal, vitamins scaled to servings
- 💷 **`get_price`** — returns cost per person and value score
- 🤖 **Full A2A pipeline** — Agent 1 picks the dish, Agent 2 designs the robot

---

## Prerequisites

- Python 3.10+
- A Google account (for Gemini API key)
- VS Code (recommended)
- A GitHub account

---

## Troubleshooting

**"No LLM backend available"**
→ Check your `.env` has either `LLM_API_TOKEN` or `GEMINI_API_KEY`.

**"ModuleNotFoundError"**
→ Run `pip install -r requirements.txt` in the current session folder.

**Gemini 429 Too Many Requests**
→ Get your own free key at https://aistudio.google.com and update `.env`.

**Streamlit not accepting keyboard input**
→ Run from a standalone terminal, not inside VS Code or PyCharm.

**Local service not reachable**
→ Check `LLM_SERVICE_URL` and `LLM_API_TOKEN` in `.env`.

---

## Community & Communication

**Discord:** https://discord.gg/UGsfhZq3

---

**The Workshop Team — PARSAI**
School of Physics, Engineering and Computer Science | University of Hertfordshire
