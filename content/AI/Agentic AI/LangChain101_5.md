---
title: "LangChain 101 : #5 LangChain as an Agent"
date: 2025-08-02
tags:
  - ai
  - agentic_ai
  - langchain
draft: false
---
LLMs are trained on data from a specific point in time. This means they often can't answer questions about current events or topics that have evolved since their training, and in worse cases, they can produce inaccurate, "hallucinated" responses. The concept of an "Agent" was introduced to solve these fundamental problems.

### Agents and Tools: Extending the LLM

An agent is an entity that performs tasks on behalf of a user. It uses an LLM as its core "brain" but doesn't rely solely on the LLM's internal knowledge. Instead, it leverages **Tools** to interact with the outside world, gather information, and handle complex tasks.

![[LangChain101_5-20250818230946508.png]]

Here, a Tool refers to a third-party service or API external to the LangChain framework. For instance, you can connect various tools depending on the objective, such as Google Search, Twitter, Notion, or a specific website's API. Any external service can be turned into a tool by simply implementing a function to handle its HTTP requests/responses, and you can also add custom-defined tools if needed.

The core operational principle of an agent is as follows:

1. It receives a user's request.
2. The LLM determines if it can answer using its own capabilities.
3. If it detects a limitation, it reviews the descriptions of the available tools and selects the most appropriate one.
4. It formats the input according to the chosen tool's requirements and executes the tool.
5. It analyzes the response (the output) from the tool to either generate a final answer or decide on the next action.

At the heart of this process is the LLM, which **"judges, uses, and processes."** In other words, it creates an autonomous cycle of actions based on the LLM's reasoning capabilities.

---
### Differences in Behavior: ReAct vs. Flow

There are several ways an LLM can decide on actions through reasoning. Based on the level of autonomy and structure, we can distinguish between concepts like ReAct and Flow.

#### ReAct (Reason + Act)

As its name suggests, `ReAct` is a method that closely resembles human thought processes by repeating a cycle of **Reason** and **Act**. When given a task, it continuously thinks, acts, and observes the results to reach the final goal.

Through this `Thought -> Action -> Observation` loop, a ReAct agent dynamically determines its next step. Its greatest strength is its flexibility, allowing it to adjust its plan and gather necessary information by observing intermediate outcomes, even for problems that seemed daunting at first.

A simple implementation of a ReAct agent is shown below. This example uses a search tool to answer a question.

```python
# Install necessary libraries
# pip install langchain langchain-openai langchain-community tavily-python

import os
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

# Set environment variables (API keys)
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"
os.environ["TAVILY_API_KEY"] = "YOUR_TAVILY_API_KEY"

# 1. Initialize the LLM
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 2. Define tools (Tavily Search)
tools = [TavilySearchResults(max_results=1)]

# 3. Pull the ReAct prompt template
prompt = hub.pull("hwchase17/react")

# 4. Create the ReAct agent
agent = create_react_agent(llm, tools, prompt)

# 5. Create the Agent Executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. Run the agent
response = agent_executor.invoke({
    "input": "Who is the current president of South Korea, and until when does his term last?"
})

print(response['output'])
```

When you run this code, the `verbose=True` option allows you to see the agent's detailed `Thought`, `Action`, and `Observation` process. You can observe how it autonomously determines that a search is needed, creates a search query, executes the search tool, and then formulates the final answer based on the results.

#### Flow

A `Flow` is less about a continuous series of autonomous decisions like ReAct and more akin to **executing a series of standardized actions sequentially**. It follows a predefined sequence of tasks or a data flowchart, where each step is executed in order. This is easily implemented using **LangGraph**, an extension project of LangChain.

LangGraph allows you to build complex workflows by creating a graph composed of nodes (which hold a state) and edges connecting them. Each node is a function that performs a specific task, and the edges define the flow of work.

For example, you can implement a flow that "takes a topic, writes a blog post draft, and then writes the final article based on that draft."

```python
# Install necessary libraries
# pip install langchain langchain-openai langgraph

import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Set environment variables
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o")

# 1. Define the agent's state
class BlogWorkflowState(TypedDict):
    topic: str
    draft: str
    final_post: str

# 2. Define the nodes (functions) for each step
def generate_draft(state: BlogWorkflowState):
    print("--- Generating Draft ---")
    topic = state['topic']
    prompt = f"Write a simple blog post draft about '{topic}'."
    draft = llm.invoke(prompt).content
    return {"draft": draft}

def write_final_post(state: BlogWorkflowState):
    print("--- Writing Final Post ---")
    topic = state['topic']
    draft = state['draft']
    prompt = f"Based on the following draft, write a complete, high-quality blog post about '{topic}'.\n\nDraft:\n{draft}"
    final_post = llm.invoke(prompt).content
    return {"final_post": final_post}

# 3. Create the workflow graph
workflow = StateGraph(BlogWorkflowState)

# 4. Add the nodes
workflow.add_node("generate_draft", generate_draft)
workflow.add_node("write_final_post", write_final_post)

# 5. Define the edges (the flow)
workflow.set_entry_point("generate_draft")
workflow.add_edge("generate_draft", "write_final_post")
workflow.add_edge("write_final_post", END)

# 6. Compile and run the graph
app = workflow.compile()

inputs = {"topic": "Comparing ReAct and Flow concepts in LangChain Agents"}
final_state = app.invoke(inputs)

print("\n--- Final Result ---")
print(final_state['final_post'])
```

In this code, the workflow is fixed: `generate_draft` -> `write_final_post`. There is no room for the LLM to decide to perform a different action in between. As such, a `Flow` is suitable for domains where predictable and stable results are required.

---
### In Conclusion

I've recapped the concept of agents designed to overcome LLM limitations and the core role of tools. The representative agent behaviors, ReAct and Flow, each have clear advantages and disadvantages.

- **ReAct**: Excels at flexible and dynamic problem-solving. It's easier to debug as it mimics human thought.
    
- **Flow (LangGraph-based)**: Reliably processes tasks in a predefined order. It offers high predictability.
    

The choice of which method to use will depend on the nature of the problem you are trying to solve. Applying ReAct to complex, unpredictable situations and a Flow-based approach to tasks requiring a structured process will be most effective. Looking ahead, the ability to properly combine and utilize these two concepts will be crucial when designing agents.

### Reference

[The AIEdge NEWSLETTER](https://newsletter.theaiedge.io/p/deep-dive-building-a-smart-chatbot)
[Medium : LLMs & Tools @pramodchandrayan](https://ai.plainenglish.io/langchain-tutorial-series-agents-tools-part-4-0233dd4e18b4)