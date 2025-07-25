# Email-Classification-and-Extraction-via-AI-Agent

A scalable and modular pipeline for **real-time email ingestion**, **classification**, and **structured data extraction** from various types of e-commerce emails — including order confirmations, shipping updates, returns, refunds, and more.

---

## 🚀 Built With

* ✅ Python 3.11
* ✅ LangGraph + OpenAI (GPT-4o-mini)
* ✅ Supabase (PostgreSQL + Realtime)
* ✅ Docker-ready for containerized deployment
* ✅ Modular LangGraph workflow (nodes + conditional routing)

---

## 📂 Project Structure

```bash
email_pipeline/
├── main.py                      # Realtime listener and orchestrator
├── workflow/graph.py           # LangGraph flow: classify -> route -> extract
├── nodes/                      # Category-specific extractor nodes
│   ├── classify.py
│   ├── order.py
│   ├── shipping.py
│   ├── shipping_update.py
│   ├── refund.py
│   ├── return_confirmation.py
│   ├── return_update.py
├── parser/email_parser.py      # HTML cleaner and item parser utils
├── gpt/extractor.py            # GPT calling + semantic fallback match
├── prompts/templates.py        # Prompt templates for all categories
├── supabase_client/__init__.py # Supabase client with service role
├── shared/types.py             # Shared LangGraph AgentState
├── .env                        # API secrets (not committed)
├── requirements.txt            # Python dependency list
├── Dockerfile                  # Dockerized runtime
└── README.md                   # This file
```

---

## 🚀 Features

* 🔍 GPT-powered Email Classification
* ✨ Structured Extraction to JSON Schema
* 🧠 GPT fallback matching for fuzzy item linking
* 📦 Supabase DB insert/update logic
* 🔄 Real-time Realtime API event processing
* 🔹 Docker-ready for deployment

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/email_pipeline.git
cd email_pipeline
```

### 2. Create `.env` File

Create a `.env` file in the root directory with:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=your-openai-api-key
```

> 📅 `SUPABASE_KEY`: Used for realtime subscriptions
> 💼 `SUPABASE_SERVICE_ROLE_KEY`: Used for DB writes securely
> 🔮 `OPENAI_API_KEY`: Calls GPT-4o-mini for classification + extraction

### 3. Run Locally (optional)

```bash
pip install -r requirements.txt
python main.py
```

---

## 🐳 Docker Instructions

### 1. Build the Image

```bash
docker build -t email_pipeline_app .
```

### 2. Run the Container

```bash
docker run -it --env-file .env email_pipeline_app
```

> 🔗 `-it` allows interactive logs. Use `--rm` to auto-clean after stop.

---

## 📊 Real-Time Flow Diagram

<details> <summary>Click to expand Mermaid flowchart</summary>

```mermaid
graph TD
  A[Email Inserted into Supabase] -->|Realtime Trigger| B[main.py]
  B --> C[classify node (LangGraph)]
  C --> D{category?}
  D -->|retailer order confirmation| E[order node - insert into DB]
  D -->|refund| F[refund node - match & upsert]
  D -->|retailer shipping confirmation| G[shipping node - match & update]
  D -->|return update| H[return update node]
  D -->|return confirmation| I[return confirmation node]
  D -->|shipping update| J[shipping update node]
  D -->|promos, goods receipt, services receipt| K[END - skip]
```
</details>
---

## 🧠 Email Categories Detected

Classifier routes each email into one of these types:

* 🌟 `promos`
* 📄 `goods receipt`
* 📦 `retailer order confirmation`
* 🚚 `retailer shipping confirmation`
* 💡 `services receipt`
* 📢 `shipping update`
* ✅ `retailer order update`
* ↩️ `return confirmation`
* ♻️ `return update`
* 💲 `refund`

Each has a **prompt template**, **extraction schema**, and **database logic**.

---

## 🤖 DB Table Summary

| Table             | Description                            |
| ----------------- | -------------------------------------- |
| `email_extracts`  | Supabase table where new emails arrive |
| `order_details`   | Parsed item-level order/shipping info  |
| `returns_refunds` | All refund and return related rows     |

---

## 🔍 Notes

### ✏️ 1. GPT-4o-mini Usage

* All classification and extraction is done with `gpt-4o-mini`, using structured prompts with JSON schema expectations.
* Prompts are defined in `prompts/templates.py` and customized for each category.

### 🧠 2. LangGraph Workflow

* We use `StateGraph` from LangGraph to define the pipeline:

  * `classify` node predicts the category.
  * Then routes to appropriate extractor node.
  * All paths end in `END` node after DB operations.
* Graph logic lives in `workflow/graph.py`

### 🛠️ 3. Semantic Fallback Matching

* In shipping/refund flows, if DB doesn't match the item:

  * We fallback to GPT with a list of known DB entries.
  * Prompt uses fuzzy logic to find best semantic match.
  * Implemented in `gpt/extractor.py`

### 📊 4. Conditional Inserts/Updates

* `order_details` inserts on new matches.
* `returns_refunds` does fuzzy lookups before updating rows.
* If `return_id` or `order_id` already exists in DB, we **don't overwrite** them unless DB field is null.

### 🔄 5. Supabase Realtime

* `main.py` uses Supabase's websocket listener for `INSERT` on `email_extracts`.
* As soon as a new row is inserted, the pipeline is triggered.
* Supabase credentials and keys are loaded via `.env` file.

### 🌎 6. Docker Logging

* Logs from inside Docker will show:

  * `🚀 Listening for database changes...`
  * `📩 New email received`
  * `✅ Processed in X seconds`
* Use `-it` when running container to view logs in real time.

---

## ✨ Future Improvements

* [ ] Retry logic on OpenAI timeouts or failures
* [ ] Split out LangGraph nodes into isolated services
* [ ] Add async job queue (e.g. Celery or FastAPI BackgroundTasks)
* [ ] Add Sentry for production error tracking
* [ ] Auto-deploy with GitHub Actions + DockerHub

---

## 🛡️ Security Practices

* ❌ Never commit `.env` to version control
* 🔐 Use `SUPABASE_SERVICE_ROLE_KEY` only inside server environments
* ❄️ GPT key is stored securely via Docker env injection

Sure! Here's a clean and professional "About Me" section you can add at the end of your `README.md` to give credit to yourself:

---

## 👤 Author

**Muhammad Amaz Majid**
🧠 AI Engineer | 💻 Backend Developer | 🌐 Freelance Innovator

* 🔭 Currently building intelligent automation pipelines with AI and real-time infrastructure
* 🌍 Based in Pakistan
* 💬 Ask me about AI Agents, Supabase, or scalable backend architectures
* 📫 Connect with me on [LinkedIn](https://www.linkedin.com/in/muhammad-amaz-majid-6715272ab) 
* 📧 Email: [amazmajid462@gmail.com](mailto:amazmajid462@gmail.com]) 

---

