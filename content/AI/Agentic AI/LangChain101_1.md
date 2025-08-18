---
title: "LangChain 101 : #1 Concept"
date: 2025-07-02
tags:
  - ai
  - agentic_ai
  - langchain
draft: false
---

As major LLM providers like Gemini-CLI are launching their own Agentic Platforms, I've realized that I often need a more customized flow tailored to my specific purposes.

Also, since LangChain is heavily used in LangGraph, I thought it would be beneficial to understand its concepts more deeply beyond simple usage, so I'm starting this study to get a comprehensive overview.

---
### What is LangChain?

**Custom Application Development 🛠️**

LangChain truly shines when customizing LLMs for specific data and purposes of a company or individual.

- **Enhanced Accuracy (RAG):** By training the LLM on internal documents or specialized knowledge from a specific field, it reduces hallucinations and generates accurate, fact-based answers. This is an essential feature in industries where accuracy is critical.
- **Examples:** In-house regulation chatbots, specific product description AI, legal document analyzers, etc.

**Infinite Possibilities as an Agent 🤖**

It equips LLMs to become **agents that think and act on their own**, going beyond simple text generation.

- **Integration with Various Tools:** LLMs can autonomously use pre-built tools like Google Search, calculators, and database queries to perform complex tasks. It's also possible to create and add custom tools.
- **Service Expansion through API Integration:** As most modern services provide their functionalities via APIs, LangChain agents can call these APIs to automate real-world tasks like booking flights, sending emails, or controlling cloud services. This trend of service integration further enhances the value of agents.


---
### Core concepts of LangChain

Agents and RAG are highly practical distinctions based on the **core operational methods and goals** of applications you can build with LangChain. In other words, they represent two major approaches to **'how to make an LLM work.'**

##### 1. RAG (Retrieval-Augmented Generation) - Knowledge-Based Answering 📚

RAG is a technique that enables an LLM to **'find information it doesn't know from external data and provide intelligent, evidence-based answers.'** The key goal is to reduce LLM hallucinations and incorporate the latest information or specialized knowledge into its responses.

- **Analogy:** It's like letting an LLM take an **'open-book exam.'** Instead of answering based solely on memorized knowledge, the LLM refers to external materials (like a Vector DB) in real-time to compose its answers.
    
- **How it works:**
    1. **Retrieval:** Finds the most relevant information for the user's question from an external data source (documents, DB, etc.).
    2. **Augmented:** Includes the retrieved information along with the original user question in the prompt.
    3. **Generation:** Sends the augmented prompt to the LLM to generate an accurate and well-founded answer based on the provided information.
        
- **Primary Purpose:** Used when **'providing accurate information'** is crucial, such as in information retrieval, Q&A systems, and chatbots based on internal documents.

##### 2. Agents - Autonomous Action 🤖

Agents enable an LLM to go beyond just answering questions and **'think for itself, make plans, and autonomously use various tools to achieve a given goal.'**

- **Analogy:** It's like turning an LLM into a **'self-sufficient employee' or a 'smart assistant.'** If you ask, "What's the weather like today?", it doesn't just give you the weather forecast. For a more complex request like, "Book a table at a good restaurant near Gangnam Station for 7 PM tonight," it will perform steps like searching for restaurants, checking your calendar, and calling a reservation API to complete the goal.
    
- **How it works:**
    1. **Thinking:** Understands the user's goal and creates a step-by-step plan to achieve it.
    2. **Tool Using:** Selects and uses the necessary tools (e.g., Google Search, calculator, code interpreter, APIs) according to the plan.
    3. **Observation:** Observes the results of the tool usage and evaluates if they are sufficient to meet the goal.
    4. **Repeat:** Repeats the cycle of thinking, tool use, and observation until the goal is completed.
        
- **Primary Purpose:** Used when **'autonomous task execution'** is important, such as in complex problem-solving, task automation, data analysis and reporting, and personal assistants.

---

### How to use LangChain

##### 1. Load LLM models

LangChain is not dependent on a specific LLM and is compatible with various LLMs.
The way to use them is also very similar.

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

llm_claude = ChatAnthropic(model='claude-3-opus-20240229')
llm_gpt = ChatOpenAI(model='gpt-5', temperature=0)
llm_llama = ChatOllama(model='llama3.2')
```

As you can see above, any LLM model can be defined and used in a very similar format.
This demonstrates the versatility of being able to change and adapt LLMs for different purposes at any time.


##### 2. Prompt Templates

Another element of LangChain is the Prompt Template.
It formats user input or presets into a prompt that the LLM can understand and allows applying user input to a predefined template. It also serves to limit the scope of user input to ensure the LangChain application is used for its intended purpose by the developer.

```python
from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template("Tell me a joke about {topic}")

prompt_template.invoke({"topic":"cats"})
```

As seen in the code above, it looks similar to the format string syntax in Python.



##### 3. Load various data sources

LangChain also provides pre-defined modules for loading existing materials for various purposes such as RAG or knowledge-base extension. Without these modules, the user would probably have to create everything themselves using APIs. However, in LangChain, most of the tasks the user intends to do are often already implemented, which is very convenient.

```python
from langchain_community.document_loaders import NotionDirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredEmailLoader

notion_loader = NotionDirectoryLoader("Notion_DB")
notion_docs = notion_loader.load()

pdf_loader = PyPDFLoader("your_file.pdf")
pdf_docs = pdf_loader.load()

email_loader = UnstructuredEmailLoader('example-email.eml')
email_docs = email_loader.load()
```

For the most part, you create a module instance with specific settings (e.g., file name, path) and then call the `load()` function.