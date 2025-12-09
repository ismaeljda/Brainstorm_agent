# 🤖 Brainstorm Agent - Multi-Agent Meeting System

A sophisticated multi-agent AI system that simulates a collaborative meeting environment using CrewAI. The system orchestrates intelligent conversations between specialized AI agents to brainstorm, analyze, and make decisions on various topics.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Agents Description](#agents-description)
- [Architecture](#architecture)

---

## 🎯 Overview

Brainstorm Agent is an intelligent multi-agent system that brings together four specialized AI agents to conduct productive meetings:

- **Facilitateur** (Facilitator): Orchestrates the discussion, synthesizes points, and drives toward consensus
- **Stratège Business** (Business Strategist): Analyzes market viability, risks, and business opportunities
- **Tech Lead**: Evaluates technical feasibility, architecture, and implementation details
- **Creative Thinker**: Generates innovative ideas, focuses on UX/UI, and challenges conventions

The system supports both **CLI** (Command Line Interface) and **Web** interface modes.

---

## 📁 Project Structure

```
Brainstorm_agent/
├── README.md                      # This file
├── requirements.txt               # Root dependencies
├── .gitignore                     # Git ignore rules
│
└── src/
    ├── main.py                    # CLI entry point
    ├── requirements.txt           # Source dependencies
    │
    ├── agents/                    # Agent configuration
    │   ├── __init__.py
    │   ├── config.py              # Agent definitions and personalities
    │   └── prompts.py             # Agent system prompts
    │
    ├── orchestrator/              # Meeting orchestration logic
    │   ├── __init__.py
    │   └── orchestrator.py        # Core orchestrator class
    │
    └── web/                       # Web interface (Flask)
        ├── app.py                 # Flask application
        └── templates/
            └── index.html         # Web UI
```

### Key Files

- **`src/main.py`**: Command-line interface for running meetings
- **`src/web/app.py`**: Flask web server for browser-based meetings
- **`src/orchestrator/orchestrator.py`**: Core logic for managing agent conversations
- **`src/agents/config.py`**: Agent configurations (roles, expertise, personalities, colors)
- **`src/agents/prompts.py`**: Detailed prompts defining agent behaviors

---

## ✨ Features

- **Intelligent Agent Selection**: Context-aware selection of which agent should speak next
- **Natural Conversation Flow**: Agents intervene based on their expertise and the discussion context
- **Human Participation**: Users can actively participate in meetings alongside AI agents
- **Consensus Detection**: Automatically detects when agreement is reached
- **Dual Interface**: Run meetings via CLI or web browser
- **Conversation History**: Maintains context throughout the meeting
- **Configurable LLM Models**: Support for multiple OpenAI models (GPT-4o, GPT-4o-mini, GPT-4-turbo)

---

## 🔧 Prerequisites

- **Python**: 3.9 or higher
- **OpenAI API Key**: Required for LLM access
- **Operating System**: macOS, Linux, or Windows

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Brainstorm_agent
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install from root requirements
pip install -r requirements.txt

# Or install from src requirements
pip install -r src/requirements.txt
```

#### Core Dependencies

- `crewai>=0.11.0` - Multi-agent framework
- `crewai-tools>=0.4.0` - Additional CrewAI tools
- `langchain>=0.1.0` - LLM orchestration
- `langchain-openai>=0.0.5` - OpenAI integration
- `openai>=1.12.0` - OpenAI API client
- `flask>=3.0.0` - Web interface (for web mode)
- `flask-cors>=4.0.0` - CORS support (for web mode)
- `python-dotenv>=1.0.0` - Environment variable management

---

## ⚙️ Configuration

### 1. Set Up OpenAI API Key

Create a `.env` file in the root directory:

```bash
# .env
OPENAI_API_KEY=your-openai-api-key-here
```

Or set it as an environment variable:

```bash
# macOS/Linux
export OPENAI_API_KEY="your-openai-api-key-here"

# Windows (CMD)
set OPENAI_API_KEY=your-openai-api-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-openai-api-key-here"
```

### 2. Verify Installation

```bash
python src/main.py
```

You should see the welcome banner if everything is configured correctly.

---

## 🚀 Usage

### Option 1: CLI Mode (Recommended for Terminal Users)

Run meetings directly from the command line:

```bash
python src/main.py
```

**Workflow:**

1. The system will prompt you to define the meeting objective
   ```
   Exemple : 'Définir la stratégie de lancement d'une app mobile de fitness'
   ```

2. Choose your preferred LLM model:
   - `gpt-4o-mini` (fast, economical) - **Default**
   - `gpt-4o` (more intelligent, more expensive)
   - `gpt-4-turbo` (balanced)

3. The facilitator opens the meeting with context

4. **Participate actively**: Type your messages when prompted
   - Press **Enter** without typing to let agents continue
   - Type **"exit"** to end the meeting early

5. Agents will respond based on their expertise and the conversation context

6. The meeting concludes automatically when:
   - Consensus is detected
   - Maximum turns reached (30)
   - User types "exit"

**Example Session:**

```
🎯 RÉUNION MULTI-AGENTS
================================================================================
Objectif : Créer une application de gestion de budget personnel
Tapez votre message pour intervenir (ou 'exit' pour quitter)
================================================================================

[Facilitateur]
Bonjour à tous ! Notre objectif aujourd'hui est de créer une application...

[Votre intervention (Entrée pour passer)] : Je pense qu'on devrait cibler les millennials

[Stratège Business]
Excellente idée ! Les millennials représentent un segment très attractif...

[Tech Lead]
Techniquement, nous pourrions utiliser React Native pour le développement...
```

---

### Option 2: Web Interface (Browser-Based)

Run the Flask web application:

```bash
python src/web/app.py
```

**Access the Interface:**

Open your browser and navigate to:
```
http://localhost:5000
```

**Features:**

- Interactive chat interface
- Real-time message updates
- Visual differentiation of agents (color-coded)
- Start/stop meeting controls
- Define objectives via web form

---

## 👥 Agents Description

### 🎩 Facilitateur (Facilitator)

- **Role**: Meeting animator and synthesizer
- **Expertise**: Discussion structuring, consensus building, meeting management
- **Personality**: Neutral, organized, results-oriented
- **Intervention Triggers**:
  - Confusion in discussion
  - Need for synthesis
  - Consensus detection
  - Topic deviation
  - Closing required

---

### 💼 Stratège Business (Business Strategist)

- **Role**: Business strategy consultant
- **Expertise**: Market analysis, business models, risk management, ROI, competitive positioning
- **Personality**: Analytical, data-driven, pragmatic, long-term vision
- **Intervention Triggers**:
  - Economic viability questions
  - Business risks mentioned
  - Market analysis needed
  - Unclear business model
  - Strategic contradictions

---

### 💻 Tech Lead (Technical Architect)

- **Role**: Technical architect and development expert
- **Expertise**: Software architecture, technical feasibility, stack choices, scalability, performance, DevOps
- **Personality**: Pragmatic, factual, solution-oriented, detail-focused
- **Intervention Triggers**:
  - Technical feasibility questioned
  - Technology choices needed
  - Technical constraints ignored
  - Scalability concerns
  - Technically unrealistic proposals

---

### 🎨 Creative Thinker (Innovation Director)

- **Role**: Creative director and innovation lead
- **Expertise**: Ideation, design thinking, UX/UI, branding, product innovation, storytelling
- **Personality**: Inspiring, divergent thinking, human-centric, optimistic, disruptive
- **Intervention Triggers**:
  - Need for new ideas
  - Too conventional approach
  - Differentiation opportunity
  - User perspective neglected
  - Untapped creative potential

---

## 🏗️ Architecture

### System Components

1. **Orchestrator** (`orchestrator/orchestrator.py`)
   - Manages conversation flow
   - Selects next speaker using LLM-based decision making
   - Maintains conversation history
   - Detects consensus and meeting completion

2. **Agent Configuration** (`agents/config.py`)
   - Defines agent personalities, behaviors, and traits
   - Configures intervention triggers
   - Sets display colors for terminal output

3. **Agent Prompts** (`agents/prompts.py`)
   - Detailed system prompts for each agent
   - Defines expertise areas and communication styles

4. **Main Entry Points**
   - **CLI**: `src/main.py`
   - **Web**: `src/web/app.py`

### Conversation Flow

```
1. User defines meeting objective
2. Facilitator opens the meeting
3. Loop:
   a. Check for human input
   b. Build conversation context
   c. LLM selects next speaker based on context
   d. Selected agent generates response
   e. Check for consensus or completion
4. Facilitator provides final synthesis
5. Meeting summary generated
```

### Agent Selection Logic

The system uses a **hybrid approach**:

1. **Primary Method**: LLM-based intelligent selection
   - Analyzes full conversation context
   - Considers agent expertise domains
   - Prevents immediate re-speaking
   - Returns the most relevant agent ID

2. **Fallback Method**: Keyword-based selection
   - Activates if LLM selection fails
   - Uses domain-specific keywords
   - Business keywords → Stratège Business
   - Tech keywords → Tech Lead
   - Creative keywords → Creative Thinker

---

## 🎓 Example Use Cases

1. **Product Development**
   ```
   Objective: "Développer une nouvelle fonctionnalité de chat vidéo"
   ```

2. **Market Strategy**
   ```
   Objective: "Définir notre stratégie d'entrée sur le marché européen"
   ```

3. **Technical Architecture**
   ```
   Objective: "Choisir la stack technique pour notre nouvelle plateforme"
   ```

4. **Creative Brainstorming**
   ```
   Objective: "Réinventer l'expérience utilisateur de notre application mobile"
   ```

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not defined"

**Solution**: Ensure your API key is properly set in `.env` file or environment variables.

### Issue: "Module not found"

**Solution**: 
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: "Connection error to OpenAI"

**Solution**: 
- Check your internet connection
- Verify your API key is valid
- Check OpenAI service status

---

## 📝 License

[Specify your license here]

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Contact

[Your contact information]

---

## 🙏 Acknowledgments

- Built with [CrewAI](https://www.crewai.com/)
- Powered by [OpenAI](https://openai.com/)
- Web interface with [Flask](https://flask.palletsprojects.com/)
