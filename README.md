\# 🚀 CareerPilot AI



An AI-powered multi-agent career assistant that helps job seekers optimize resumes, identify skill gaps, discover relevant job opportunities, generate personalized learning roadmaps, and prepare for interviews using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG).



\---



\## 🌟 Features



\### 📄 Resume Analysis

\- Extracts and structures resume information

\- Identifies strengths and weaknesses

\- Provides ATS optimization insights



\### 🎯 Career Goal Analysis

\- Analyzes career aspirations

\- Recommends suitable career paths

\- Maps skills to industry roles



\### 🧠 Skill Gap Detection

\- Compares current skills with target job requirements

\- Identifies missing competencies

\- Suggests improvement areas



\### 🔍 AI Job Search \& Ranking

\- Retrieves relevant job opportunities

\- Matches jobs based on skills and experience

\- Ranks opportunities using AI-driven scoring



\### 📚 Personalized Learning Roadmap

\- Generates customized learning plans

\- Recommends technologies and resources

\- Tracks skill development priorities



\### 🎤 Interview Preparation

\- Generates role-specific interview questions

\- Covers technical and behavioral topics

\- Helps users prepare effectively



\### 📖 RAG-Powered Knowledge Retrieval

\- Retrieves contextual information from a vector database

\- Enhances job matching and recommendations

\- Improves response accuracy



\---



\## 🏗️ System Architecture



```text

User

&#x20;│

&#x20;▼

React Frontend (Vite)

&#x20;│

&#x20;▼

FastAPI Backend

&#x20;│

&#x20;▼

Agent Orchestrator

&#x20;│

&#x20;├── Resume Agent

&#x20;├── Skill Gap Agent

&#x20;├── Career Goal Agent

&#x20;├── Job Search Agent

&#x20;├── Job Ranking Agent

&#x20;├── Learning Roadmap Agent

&#x20;└── Interview Agent

&#x20;│

&#x20;▼

RAG Layer (ChromaDB)

&#x20;│

&#x20;▼

Groq LLM

&#x20;│

&#x20;▼

SQLite Database

```



\---



\## 🔄 Workflow



1\. Upload Resume

2\. Resume Parsing \& Analysis

3\. Skill Extraction

4\. Career Goal Assessment

5\. Job Search \& Retrieval

6\. Job Ranking

7\. Learning Roadmap Generation

8\. Interview Question Generation

9\. Personalized Career Report



\---



\## 🛠️ Tech Stack



\### Frontend

\- React.js

\- Vite

\- JavaScript

\- CSS



\### Backend

\- FastAPI

\- Python



\### AI \& Machine Learning

\- Groq API

\- RAG (Retrieval-Augmented Generation)

\- Sentence Transformers

\- ChromaDB



\### Database

\- SQLite



\### Development Tools

\- Git

\- GitHub

\- VS Code



\---



\## 📂 Project Structure



```text

careerpilot-ai/

│

├── agents/                 # AI agents

├── api/                    # API routes

├── frontend/               # React frontend

├── graph/                  # Agent workflow logic

├── models/                 # Data models

├── rag/                    # RAG implementation

├── uploads/                # Uploaded resumes (ignored)

├── chroma\_db/              # Vector database (ignored)

│

├── main.py                 # FastAPI entry point

├── db.py                   # Database operations

├── package.json

├── README.md

└── .env

```



\---



\## ⚙️ Installation



\### 1. Clone Repository



```bash

git clone https://github.com/YOUR\_USERNAME/CareerPilot-AI.git

cd CareerPilot-AI

```



\---



\### 2. Create Virtual Environment



```bash

python -m venv venv

```



\#### Windows



```bash

venv\\Scripts\\activate

```



\#### Linux/Mac



```bash

source venv/bin/activate

```



\---



\### 3. Install Backend Dependencies



```bash

pip install -r requirements.txt

```



\---



\### 4. Configure Environment Variables



Create a `.env` file:



```env

GROQ\_API\_KEY=your\_groq\_api\_key

```



\---



\### 5. Install Frontend Dependencies



```bash

cd frontend

npm install

```



\---



\## ▶️ Running the Project



\### Start Backend



From project root:



```bash

python main.py

```



or



```bash

uvicorn main:app --reload

```



Backend runs on:



```text

http://127.0.0.1:8000

```



\---



\### Start Frontend



Open a new terminal:



```bash

cd frontend

npm run dev

```



Frontend runs on:



```text

http://localhost:5173

```



\---



\## 🧪 Example Usage



1\. Launch backend and frontend.

2\. Open the web application.

3\. Upload a resume.

4\. Analyze skills and career goals.

5\. View ranked job recommendations.

6\. Generate learning roadmap.

7\. Prepare using AI-generated interview questions.



\---



\## 🔒 Security



The following files are excluded from Git tracking:



\- `.env`

\- `node\_modules/`

\- `uploads/`

\- `chroma\_db/`

\- `\*.pdf`

\- `\*.db`

\- Generated reports and analysis files



Never commit API keys or personal resumes.



\---



\## 🚀 Future Enhancements



\- Multi-user authentication

\- Resume version tracking

\- Real-time job scraping

\- LinkedIn integration

\- AI-powered cover letter generation

\- Deployment using Docker \& Cloud Services

\- Advanced analytics dashboard



\---



\## 👨‍💻 Author



\*\*Shyam Sarath\*\*



B.Tech Artificial Intelligence \& Data Science



Passionate about AI, Machine Learning, Automation, Data Analytics, and Building Intelligent Systems.



\---



\## 📜 License



This project is licensed under the MIT License.

