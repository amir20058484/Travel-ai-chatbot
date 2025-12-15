# Safar Travel AI Agent

Safar Travel AI Agent is an intelligent, tool-enabled customer service agent designed for **domestic travel services in Iran**.  
The project demonstrates modern **Prompt Engineering**, **LLM-based agent orchestration**, **Tool Calling**, and **RAG (Retrieval-Augmented Generation)** in a real-world scenario.

This system goes beyond a simple chatbot and acts as an **operational AI agent** capable of executing actions such as ticket booking and cancellation.

---

##  Features

-  **Ticket Booking**
  - Book domestic travel tickets within Iran
  - Collects origin, destination, travel date, passenger name, and national ID

-  **Ticket Cancellation**
  - Cancel existing bookings using a ticket ID
  - Calculates refunds based on defined policies

-  **Ticket Information Retrieval**
  - Retrieve booking details and ticket status by ticket ID

-  **Travel Destination Suggestions**
  - AI-powered recommendations for Iranian cities only
  - Based on user preferences (weather, interests, travel style)

-  **Policy Lookup with RAG**
  - Uses ChromaDB to retrieve company policies (refunds, cancellations, baggage rules)
  - Prevents hallucination by relying only on verified knowledge sources

-  **Bilingual Support**
  - Persian (Farsi) and English
  - Automatic language detection
  - Friendly Shirazi-inspired Persian tone as a brand personality

---

##  Architecture Overview

```

Chainlit UI
↓
AgentManager (LLM Orchestration)
↓
LLM (OpenAI-compatible / AvalAI)
↓
Tools Layer
├─ TicketManagementTool
├─ RAGTool (ChromaDB)
└─ DestinationTool

```

### Key Design Principles
- Clear separation of concerns
- Single-agent orchestration
- Tool-driven execution (no hard-coded rules)
- Safe, deterministic behavior with error handling

---

##  Technology Stack

- **Python 3.10+**
- **Chainlit** – Interactive chat UI
- **OpenAI-compatible API** (e.g., AvalAI)
- **ChromaDB** – Vector database for RAG
- **ReportLab** – PDF report generation
- **jdatetime** – Persian (Shamsi) date handling

---

##  Project Structure

```

.
├── chainlit_app.py    
├── run.py               
├── prompts.py           
├── src/
│   ├── manager.py        
│   ├── tools.py         
│   └── data/
│       └── company_policy.txt
├── .env     
├── README.md

````

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/safar-travel-ai-agent.git
cd safar-travel-ai-agent
````

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`:

```env
MODEL_NAME=gpt-5.2
AVALAI_API_KEY=your_api_key_here
AVALAI_BASE_URL=https://api.your-provider.com
APP_NAME=Safar Travel AI Agent
```

---

##  Running the Application

Start the Chainlit app:

```bash
chainlit run chainlit_app.py -w
```

Then open the provided local URL in your browser.

---

##  Notes on RAG

* The file `company_policy.txt` contains company policies used by the RAG system
* On first run, ChromaDB will download an embedding model and cache it locally
* If the policy file is empty, the system safely informs the user that policy data is unavailable

---

##  Safety & Constraints

* Only **Iranian domestic travel** is supported
* The agent never invents tickets, prices, or policies
* All sensitive operations require explicit user input
* Tool usage is strictly controlled by the system prompt

---

##  Project Status

*  Functional MVP
*  Tool-enabled AI agent
*  Prompt-engineering focused design
*  Ready for further expansion (database, monitoring, deployment)

---

##  License

This project is provided for educational purposes as part of a Prompt Engineering course.

```


