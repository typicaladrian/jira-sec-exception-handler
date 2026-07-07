# Enterprise GRC Triage & Automation Engine

A production-ready, DevSecOps automation pipeline engineered to ingest, audit, and route IT Governance, Risk, and Compliance (GRC) security exception requests. By shifting from brittle string-matching to local NLP semantic analysis, this utility slashes operational noise for Assurance teams while ensuring strict data privacy in highly regulated environments.

## Architecture & Data Flow

~~~text
 [Line of Business] ──> Submits Request to Jira Board
                              │
                              ▼
 [triage.py Script] ──> Authenticates to Jira
                              │
                              ├─> Fetches Unprocessed Tickets
                              │
                              ▼
 [Local LLM Engine] ──> Semantic Analysis (Ollama / Microsoft Phi-3)
                              │   * Localhost Execution (Zero Data Leakage)
                              │   * Deterministic Boolean JSON Output
                              │
            ┌─────────────────┴─────────────────┐
            ▼ (Missing Fields)                  ▼ (Valid Payload)
 [Automated LOB Pushback]             [Retained for Review]
  * Tags author via Jira API           * Left in To Do column
  * Transitions to pending status      * Clean payload prepared
~~~

## Key Enterprise Features

* **Zero Data Leakage Architecture:** Engineered specifically for the compliance boundaries of institutions handling PII/SPII. By using a localized deployment model (Ollama), sensitive infrastructure data (IPs, domains) never leaves the host environment or touches a public vendor API.
* **Semantic Analysis vs. Brittle Regex:** Replaced strict string-matching with local NLP, allowing the engine to recognize natural language business justifications while utilizing **Negative Constraints** to reject vague, unjustified requests.
* **Deterministic Structured JSON Output:** Enforces a strict schema restriction and a `temperature=0.0` configuration on token generation. It utilizes **Boolean Extraction** to turn highly variable LLM responses into predictable, fail-safe data structures readable by downstream code.
* **Fail-Safe IAM Implementation:** Features proactive session checking via Atlassian’s authentication endpoints (`jira.myself()`) to guarantee configuration integrity, crashing gracefully and alerting immediately on token expiration rather than failing silently.

## Technical Stack

* **Language:** Python 3.11+
* **Orchestration & Workflow:** Jira REST API (`jira` Python library)
* **NLP Inference Engine:** Ollama API client running a localized Microsoft Phi-3 (3.8B Parameter SLM)
* **Environment Management:** `python-dotenv`

---

## Getting Started

### Prerequisites
* Python installed locally
* [Ollama](https://ollama.com/) installed and running on localhost

### 1. Model Initialization
Pull the lightweight open-weight model from the registry via Ollama:
~~~bash
ollama run phi3
~~~

### 2. Configuration Setup
Create a `.env` file in the root directory to store localized environment variables:
~~~ini
# Jira Infrastructure
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your_atlassian_api_token
JIRA_PROJECT_KEY=SEC

# Workflow Mapping
TRANSITION_ID_IN_PROGRESS=31
~~~

### 3. Dependency Installation & Execution
~~~bash
pip install jira python-dotenv ollama
python triage.py
~~~

## 🔍 How the Boolean Extraction Works
To overcome the hallucination and array-generation limitations of Small Language Models (SLMs), this script forces the AI into a strict Boolean JSON schema. The model evaluates the combined Summary and Description payload and outputs `true` or `false` based on explicit prompt rules, allowing the Python wrapper to handle the routing logic safely:

~~~json
{
  "has_business_justification": true,
  "has_technical_parameters": false
}
~~~
If any required field is evaluated as `false`, the script automatically formats a pushback comment tagging the Jira reporter and transitions the ticket state to prevent queue clogging.
