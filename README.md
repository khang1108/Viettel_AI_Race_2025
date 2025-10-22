# Viettel_AI_Race_2025

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

An end-to-end pipeline to automatically extract structured data from complex technical PDFs and enable intelligent querying through a Retrieval-Augmented Generation (RAG) system. This project was built to tackle the **Task 2: Knowledge Extraction from Technical Documents** challenge.

In fields like engineering, aerospace, and biomedicine, millions of pages of technical documents are generated daily as PDFs. These documents are a **goldmine of knowledge**, but they contain complex tables, mathematical notations, and specialized terminology, making automated data access extremely difficult. InsightMiner is designed to unlock this knowledge.

### ✨ **Core Features**

*   **Layout-Aware Parsing:** Accurately preserves the original document structure, including headings, paragraphs, lists, and images.
*   **Advanced Table Extraction:** Handles complex tables that span multiple pages, contain merged cells, or have nested structures.
*   **Markdown Conversion:** Converts processed PDF content into clean, well-structured Markdown files, ensuring data is portable and easy to read.
*   **Natural Language Q&A:** An intelligent chat interface allows users to ask questions in plain English and receive accurate, context-aware answers sourced directly from the documents.

---

## **👥 Team Members**

| No. | Name              | Role                      | GitHub Profile                               |
|:---:|-------------------|---------------------------|----------------------------------------------|
| 1   | [Your Name]       | Team Lead / AI Engineer   | [Link to Your GitHub Profile]                |
| 2   | [Teammate's Name] | Backend Engineer          | [Link to Teammate's GitHub Profile]          |
| 3   | [Teammate's Name] | Frontend Engineer         | [Link to Teammate's GitHub Profile]          |
| 4   | [Teammate's Name] | Data Scientist / ML Ops   | [Link to Teammate's GitHub Profile]          |

---

## **🚀 Tech Stack**

This project leverages a modern, high-performance tech stack:

*   **Backend:**
    *   **Language:** Python 3.9+
    *   **Framework:** FastAPI (for high-speed, asynchronous APIs)
    *   **Async Task Queue:** Celery with RabbitMQ (for processing large PDFs without blocking)
*   **AI / Machine Learning:**
    *   **PDF Parsing:** `PyMuPDF`, `pdfplumber`
    *   **Table Extraction:** `Table Transformer (TATR)`
    *   **Document Layout Analysis:** `LayoutLM`
    *   **RAG Pipeline:**
        *   **Vector Database:** `FAISS`
        *   **Embedding Models:** `sentence-transformers`
        *   **Large Language Model (LLM):** Fine-tuned `Deepseek OCR`
*   **Frontend:**
    *   **Framework:** React.js
    *   **UI Library:** Material-UI / Ant Design
    *   **API Client:** Axios
*   **DevOps & Deployment:**
    *   **Containerization:** Docker, Docker Compose

---

## **📂 Project Structure**

The project is organized into distinct modules for backend, frontend, and data, promoting clean architecture and scalability.

```bash
viettelairace/
├── backend/                  # FastAPI Backend source code & AI/ML pipeline
│   ├── app/viettelairace
│   │   ├── api/              # API endpoint definitions
│   │   ├── services/         # Core business logic (PDF parsing, RAG, etc.)
│   │   └── main.py           # Application entry point
│   ├── Dockerfile            # Docker config for the backend
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React UI source code
│   ├── src/
│   │   ├── api/              # Functions to call backend APIs
│   │   ├── components/       # Reusable UI components
│   │   └── pages/            # Main application pages
│   ├── Dockerfile            # Docker config for the frontend
│   └── package.json          # Node.js dependencies
├── data/                     # Persisted user data (never commit to Git)
│   ├── input_pdfs/
│   ├── output_markdowns/
│   └── vector_db/
├── models/                   # Pre-trained ML model weights (downloaded separately)
├── .env.example              # Environment variable template
├── docker-compose.yml        # Orchestrates all services
└── README.md                 # You are here!
```

---

## **🛠️ Getting Started**

Follow these steps to set up and run the project locally.

### **Prerequisites**

*   [Git](https://git-scm.com/)
*   [Docker](https://www.docker.com/products/docker-desktop/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### **Installation & Launch**

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/insightminer.git
    cd insightminer
    ```

2.  **Set up environment variables:**
    Copy the example `.env` file and customize it with your settings.
    ```sh
    cp .env.example .env
    ```
    Now, open `.env` and fill in any required variables.

3.  **Download AI Models:**
    Download the required pre-trained models (e.g., from Hugging Face) and place them inside the `./models` directory according to the structure defined in the code.

4.  **Build and run the application:**
    Use Docker Compose to build the images and launch all services.
    ```sh
    docker-compose up --build -d
    ```
    The `-d` flag runs the containers in detached mode.

---

## **▶️ Usage**

Once the application is running:

1.  **Open the web interface:** Navigate to `http://localhost:3000` in your browser.
2.  **Upload PDFs:** Use the drag-and-drop interface to upload one or more technical PDF documents.
3.  **View Results:** After processing, the extracted content will be available as a clean Markdown file. Select a file to view it.
4.  **Ask Questions:** Use the chat interface to ask questions about the content of your uploaded documents and receive intelligent answers.

## **📄 License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.
