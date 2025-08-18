---
title: "LangChain 101 : #2 Creating a PromptTemplate and a Simple Chain"
date: 2025-07-10
tags:
  - ai
  - agentic_ai
  - langchain
draft: false
---

When developing applications using Large Language Models (LLMs), one of the most fundamental tasks is giving the model clear and consistent instructions. LangChain is a framework that makes this process more efficient, and among its core concepts are `PromptTemplate` and `Chain`.

In this post, we'll walk through a Python script that uses LangChain to summarize simple information and extract interesting facts. Through this code, we'll explore the role of `PromptTemplate` and learn how to construct a basic `Chain`.

### 1. Background Knowledge

Before diving into the code, let's briefly touch on a few key components.

- **LangChain**: A framework designed to simplify the development of applications powered by LLMs. It provides various components for complex tasks, such as connecting LLMs to external data sources or other APIs.
- **PromptTemplate**: A feature that allows you to create a reusable "template" for a prompt (the instruction sent to the LLM). This makes it easy to dynamically insert different values into a prompt.
- **Chain**: In LangChain, a "chain" refers to a sequence of components linked together. In its simplest form, it's a structure where data flows sequentially through each element, such as 'PromptTemplate → LLM → Output Parser', connected by pipes (`|`).
- **OPENAI_API_KEY**: An authentication key required to use OpenAI's language models (like GPT-4o mini). You can obtain one from the OpenAI website and should set it up as an environment variable for your project.
    

### 2. A Step-by-Step Look at the Code

Now, let's break down the full script to understand the role of each part.

#### Step 1: Setting Up the Environment and Importing Libraries

To use an LLM, we need to manage our API key securely and import the necessary libraries.

```python
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
```

- The `load_dotenv()` function from the `dotenv` library loads environment variables from a `.env` file in the project's root directory. This is a good practice for managing sensitive information like an API key (`OPENAI_API_KEY=sk-...`) without hardcoding it directly into the source code.
- `PromptTemplate`, `ChatOpenAI`, and `StrOutputParser` are core classes from LangChain that we will use to create a prompt template, interact with the OpenAI model, and parse the model's output into a string, respectively.
    

#### Step 2: Preparing the Input Data

Next, we define the source data that the LLM will process.

```python
information = """
Name: Ilon Musk
Age: 52
Location: United States
Profession: Entrepreneur, Investor, Engineer
Interests: Space exploration, renewable energy, artificial intelligence
Education: BSc in Physics from the University of Pennsylvania
Hobbies: Reading, coding, meditation
Relationship Status: Married to Grimes
"""
```

Here, we've prepared information about a person in a simple text format. The content of this `information` variable will later be inserted into our prompt template.

#### Step 3: Creating a PromptTemplate

Now, let's create the "template" for the instructions we'll send to the LLM.

```python
summary_template = """
given the information {information} about a person from I want you to create:
1. a short summary
2. two interesting facts about them
"""

summary_prompt_template = PromptTemplate(
    input_variables=["information"],
    template=summary_template
)
```

- In the `summary_template` string, `{information}` is a placeholder where a variable will be inserted.
- We use the `PromptTemplate` class to formalize this template.
    - `input_variables=["information"]`: This tells LangChain which variable (`{information}`) inside the template will be dynamically filled.
    - `template=summary_template`: This specifies the actual template string to use.

Using a `PromptTemplate` allows us to apply the same task format (e.g., "create a summary and two interesting facts") consistently to different pieces of information.

#### Step 4: Initializing the Language Model (LLM) and Building a Chain

With the prompt ready, we'll initialize the LLM that will process it and define the entire workflow as a "Chain".

```python
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

chain = summary_prompt_template | llm | StrOutputParser()
```

- `ChatOpenAI(model="gpt-4o-mini", temperature=0)`: This sets up the client to use OpenAI's `gpt-4o-mini` model. The `temperature` parameter controls the model's creativity or randomness. A value of `0` makes the output more deterministic and predictable, which is suitable for summarization tasks based on given facts.
    
- `chain = summary_prompt_template | llm | StrOutputParser()`: This line uses the LangChain Expression Language (LCEL), where the pipe (`|`) operator connects components to create a data processing pipeline.
    
    1. **`summary_prompt_template`**: Takes the input data (`information`) and formats it into a complete prompt.
    2. **`llm`**: Sends the formatted prompt to the LLM and receives a response.
    3. **`StrOutputParser`**: Converts the LLM's response (which is typically a complex object) into a simple, human-readable string.

#### Step 5: Executing the Chain and Checking the Result

Finally, we run the configured chain and print the output.

```python
if __name__ == "__main__":
    print("Hello LangChain!")

    result = chain.invoke(input={"information": information})
    print(result)
```

- `chain.invoke()`: This function executes the `chain`.
- `input={"information": information}`: We pass the actual data to the chain. The key, `"information"`, must match the name specified in the `PromptTemplate`'s `input_variables`.
- `print(result)`: This displays the final string output from the `StrOutputParser` after it has passed through all the steps in the chain.

**Example Output:**

```
Hello LangChain! **Summary:** Ilon Musk is a 52-year-old entrepreneur, investor, and engineer based in the United States. He holds a BSc in Physics from the University of Pennsylvania. His primary interests include space exploration, renewable energy, and artificial intelligence, and his hobbies are reading, coding, and meditation. He is married to Grimes. **Two Interesting Facts:** 1. His academic background is in Physics, which underpins his work in complex fields like space exploration and engineering. 2. Despite his high-profile and demanding career, his hobbies include introspective activities like reading and meditation.
```

### Conclusion

In this post, we explored how to use LangChain's `PromptTemplate` to create dynamic prompts and how to connect it with an LLM and an `StrOutputParser` to form a simple `Chain`.

By leveraging LangChain, we can structure our interactions with LLMs into organized and reusable code. This serves as a solid first step toward building more sophisticated LLM-powered applications.