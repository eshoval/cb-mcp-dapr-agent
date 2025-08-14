---

# **Conversational Agent for Couchbase using Dapr Agents and MCP**

This project demonstrates how to build a fully functional, enterprise-ready conversational agent for a Couchbase database. 1 It allows users to ask questions in natural language and receive structured answers and analysis. The solution leverages

**Dapr Agents** with the **Model Context Protocol (MCP)** for database interaction and **Chainlit** for the user interface. 2

## **🏛️ Architecture**

The application consists of several key components that work together to provide a seamless conversational experience:


flowchart TD  
    subgraph User Interface  
        A\[👨‍💻 User\] \--\> B\[🌐 Chainlit UI\];  
    end

    subgraph Application & Dapr  
        B \--\> C{app.py};  
        C \--\> D\[Dapr Sidecar\];  
    end

    subgraph Agents  
        D \--\> E\[LLM Agent\];  
        E \--\> F\[Tools Agent\];  
    end

    subgraph Backend Services  
        F \--\> G\[🔌 Couchbase MCP Server\];  
        G \--\> H\[🗄️ Couchbase DB\];  
        D \--\> I\[💾 Redis / State Store\];  
        E \--\> J\[🤖 OpenAI Service\];  
    end

1. **Chainlit UI**: Provides the web-based chat interface for the user.  
2. **app.py**: The main application logic that orchestrates the agents.  
3. **Dapr Sidecar**: Manages component loading, state persistence, and communication.  
4. **LLM Agent**: An intelligent router that interprets the user's question, decides if a database query is needed, and generates the SQL++ query if required. 3

5. **Tools Agent**: Executes the SQL++ query against the database using the tools provided by the MCP server.  
6. **Couchbase MCP Server**: A middleware service that securely exposes Couchbase operations (like running queries) as tools for the Dapr Agent. 4

7. **Couchbase DB**: The source database containing the data. 5

8. **Redis**: The default Dapr state store used to maintain conversation history. 6

---

## **✨ Features**

* **Natural Language Queries**: Ask complex questions about your data in plain English.  
* **Schema-Aware Agent**: Automatically discovers and utilizes the database schema to generate accurate SQL++ queries.  
* **Tool-Based Execution**: Uses the robust Model Context Protocol (MCP) to safely interact with the database.  
* **Conversation Memory**: Remembers previous interactions in the chat session to provide context-aware responses. 7777

* **Enterprise-Ready**: Built with scalable and maintainable components using Dapr.

---

## **✅ Prerequisites**

Before you begin, ensure you have the following installed:

* **Python**: Version 3.10 or higher. 8

* **Pip**: The Python package manager. 9

* **Dapr CLI**: The command-line interface for Dapr. 10

* **Docker**: To run Couchbase DB locally.  
* **OpenAI API Key**: For the LLM agent to function. 11

---

## **🚀 Setup and Installation**

Follow these steps to set up and run the project locally.

### **1\. Clone the Repository**

Bash

git clone \<your-repository-url\>  
cd \<repository-folder\>

### **2\. Set Up Python Environment**

Create and activate a virtual environment to manage dependencies.

Bash

\# Create a virtual environment \[cite: 32, 33\]  
python3 \-m venv .venv

\# Activate it (on Windows, use \`.venv\\Scripts\\activate\`) \[cite: 34\]  
source .venv/bin/activate

\# Install the required packages \[cite: 36, 37\]  
pip install \-r requirements.txt

### **3\. Configure Environment Variables**

Create a .env file in the root of the project by copying the provided .env file (or creating it from scratch). Then, fill in your specific credentials. 12

**File: .env**


\# LLM Provider Configuration \[cite: 1\]  
DAPR\_LLM\_COMPONENT\_DEFAULT=openai  
OPENAI\_API\_KEY="sk-your-real-openai-api-key"

\# Couchbase Configuration (for scripts and MCP Server) \[cite: 116, 117, 118, 119\]  
CB\_CONNECTION\_STRING="couchbase://localhost"  
CB\_USERNAME="your\_couchbase\_user"  
CB\_PASSWORD="your\_couchbase\_password"  
CB\_BUCKET\_NAME="test-bucket1"  
READ\_ONLY\_QUERY\_MODE=true

\# MCP Server URL (running locally)  
MCP\_SERVER\_URL=http://localhost:8000/sse

### **4\. Set Up Couchbase DB with Docker**

The easiest way to get a Couchbase instance running is with Docker.

Bash

\# Pull the official image \[cite: 65\]  
docker pull couchbase

\# Run the container, mapping the necessary ports \[cite: 69\]  
docker run \-d \--name couchbase-db \-p 8091-8096:8091-8096 \-p 11210-11211:11210-11211 couchbase

* Once the container is running, open your browser to  
  **http://localhost:8091**. 13

* Complete the setup wizard:  
  * Create a cluster (can be a single node).  
  * **Crucially**, create a bucket named **test-bucket1**. 14141414

  * Create a user with the credentials you specified in your .env file (e.g., your\_couchbase\_user). Grant this user **Query and Data Write** permissions on the test-bucket1 bucket.

### **5\. Populate Couchbase with Sample Data**

The project includes a script to generate and insert realistic medical data. 15

⚠️ **Security Note:** The generate\_test\_data.py script contains hardcoded credentials. For this demo, it's recommended to **edit the script** and replace these with the credentials you configured.

Run the script to populate your database with

patient, test, and prescription documents: 161616161616161616

Bash

python generate\_test\_data.py

### **6\. Initialize Dapr and Configure Components**

If you haven't already, initialize Dapr in your local environment.

Bash

\# This will install Redis as a default state store for conversation memory \[cite: 39, 139\]  
dapr init

Next, create a components folder in the project root and add the following two files. These files tell Dapr how to connect to OpenAI and where to store conversation history.

**File: ./components/openai.yaml** 17

YAML

apiVersion: dapr.io/v1alpha1  
kind: Component  
metadata:  
  \[cite\_start\]name: "openai" \[cite: 47\]  
spec:  
  \[cite\_start\]type: conversation.openai \[cite: 49\]  
  metadata:  
    \- name: key  
      \[cite\_start\]value: "\<YOUR\_OPENAI\_API\_KEY\>" \[cite: 51, 52\]  
    \- name: model  
      \[cite\_start\]value: "gpt-4-turbo" \[cite: 53, 54\]

**File: ./components/conversationmemory.yaml**

YAML

apiVersion: dapr.io/v1alpha1  
kind: Component  
metadata:  
  name: conversationstore  
spec:  
  type: state.redis  
  version: v1  
  metadata:  
  \- name: "redisHost"  
    value: "localhost:6379"  
  \- name: "redisPassword"  
    value: ""

---

## **▶️ Running the Application**

To run the full application, you need to start three separate processes in three different terminals.

### **Terminal 1: Start the Couchbase MCP Server**

The MCP server acts as the bridge between the Dapr Agent and your database. 18

Bash

\# Ensure your virtual environment is active  
\# The command uses the CB\_ variables from your .env file  
\# Ensure you are in the correct directory for the mcp\_server.py script  
python src/mcp\_server.py \--transport=sse \[cite: 126\]

You should see a confirmation that the server is listening on port 8000\. 19

### **Terminal 2: Run Schema Discovery (One-Time Step)**

The agent needs a JSON file describing the database schema. Run the cb\_discovery.py script to generate this file. **You only need to do this once**, or whenever your database schema changes.

Bash

\# Ensure your virtual environment is active  
python cb\_discovery.py

This will create the schema\_context.json file in your project root, which is required by app.py.

### **Terminal 3: Run the Chat Agent**

Finally, launch the main application using the Dapr CLI.

Bash

\# This command starts the Chainlit app with Dapr enabled \[cite: 132\]  
dapr run \--app-id chat-agent \--dapr-http-port 3500 \--components-path ./components \-- \\  
chainlit run app.py \-w \--port 8001

* Dapr will start and load the components from the ./components directory.  
* Chainlit will start the web server.  
* A browser window should automatically open to  
  **http://localhost:8001**. 20

---

## **💬 How to Use**

Once the application is running, you can start asking questions in the chat interface. Based on the sample data, here are some examples: 21

* "How many patients are there in total?"  
* "Show me all the tests for patient with ID 162422580"  
* "Who is the patient with the most tests?" 22

* "What were the results for test ID t997dc369?"  
* "Hello, how are you?" 23

The agent will either answer directly or generate and execute a SQL++ query, showing you both the query and the result.

---

## **📁 Project Structure**

.  
├── components/  
│   ├── conversationmemory.yaml  
│   └── openai.yaml  
├── prompts/  
│   └── llm\_router\_prompt.txt  
├── .env  
├── app.py  
├── cb\_discovery.py  
├── generate\_test\_data.py  
├── requirements.txt  
├── schema\_context.json  
└── README.md  
