---
title: "LangChain 101 : #4 Connecting to Ollama Server"
date: 2025-07-25
tags:
  - ai
  - agentic_ai
  - langchain
draft: false
---
Last time, I finished installing Ollama on my Linux GPU server and did the basic setup for remote access. This time, I wanted to document the process of verifying the connection and using the server's LLM from my MacBook with LangChain, mostly as a record for my future self.

### 1. Verifying Server Readiness

Before I started writing any code, I first double-checked that the server was ready to accept requests from the outside.
#### **1.1. Confirming the API Response on the Server**

First, I SSH'd back into the server to check if the API was returning the model list correctly with `curl`. To keep things consistent with my last post, I based this on the `gemma2:9b` model.

```bash
# Executed in the server's terminal
# Since I had set the OLLAMA_HOST environment variable, I could check with this command.
$ curl http://$OLLAMA_HOST/api/tags
```

**Successful Response Example:** I confirmed that the `gemma2:9b` model was installed correctly because I got a JSON response like this.

```json
{"models":[
  {"name":"gemma2:9b","model":"gemma2:9b","modified_at":"..."}
]}
```

#### **1.2. Checking the Firewall Configuration (UFW)**

I've run into firewall issues many times before where the API works locally but is blocked externally. So, this time I made sure to open port **11434**, which Ollama uses, in the `ufw` firewall.

```bash
# Executed in the server's terminal

# 1. Check the firewall status
$ sudo ufw status
Status: active

# 2. Add a rule to allow port 11434
$ sudo ufw allow 11434

# 3. Apply the new rules
$ sudo ufw reload
```

By running `ufw allow 11434`, I opened up the port to allow external connections.

---
### 2. Verifying the Connection from My MacBook

Next, it was time to confirm that I could actually connect to the server from my development machine, my MacBook. I found this was easy to check not just with `curl`, but also with a web browser.

I opened Chrome on my MacBook and typed the following into the address bar:

`http://[your-server-ip]:11434/api/tags`

As you can see in the screenshot, the exact same JSON response that I saw with `curl` on the server appeared in my browser. This confirmed to me that I was ready to send HTTP requests from my MacBook to the server.

---
### 3. Setting Up My LangChain Project

Now for the LangChain code. I find it much better to manage settings like server addresses in a `.env` file instead of hardcoding them, so that's what I did.

I created a `.env` file in my project folder and added the following lines.

```bash
# .env file

OLLAMA_BASE_URL="http://[your-server-ip]:11434"
OLLAMA_MODEL="gemma2:9b"
```

I put my actual server IP in `[your-server-ip]` and the name of the installed model in `OLLAMA_MODEL`.

---
### 4. Calling the Remote LLM with LangChain Code

Finally, I wrote a simple Python script to call the remote Ollama server using the settings from my `.env` file.

> **Note**: In recent LangChain versions, `ChatOllama` moved to the `langchain_community` package. I had already run `pip install langchain-community`.

```python
# main.py

import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables from the .env file
load_dotenv()

def run_remote_ollama_test():
    """
    A function to connect to the remote Ollama server based on info
    from the .env file and test it with a simple question.
    """
    try:
        # 1. Get server info from the .env file
        ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        ollama_model = os.getenv("OLLAMA_MODEL")

        if not ollama_base_url or not ollama_model:
            raise ValueError("OLLAMA_BASE_URL or OLLAMA_MODEL not set in .env file.")

        print("Attempting to connect to the remote Ollama server...")
        print(f"Server URL: {ollama_base_url}")
        print(f"Model: {ollama_model}")

        # 2. Initialize the LangChain ChatOllama model
        llm = ChatOllama(
            base_url=ollama_base_url,
            model=ollama_model
        )
        
        # 3. Create a simple prompt template and chain
        prompt = ChatPromptTemplate.from_template("Explain the basics of {topic} in a simple way.")
        output_parser = StrOutputParser()
        
        chain = prompt | llm | output_parser

        # 4. Run the chain and print the result
        print("\n--- Sending Question ---")
        topic = "how artificial intelligence learns"
        response = chain.invoke({"topic": topic})
        
        print(f"Question: {topic}")
        print("--- Response ---")
        print(response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_remote_ollama_test()
```

I wrote this code to read the server address and model name from the `.env` file, create a `ChatOllama` object, build a simple LCEL chain, ask a question about "how artificial intelligence learns," and then print the response from the remote server.

**Execution :**

```bash
$ python main.py

Attempting to connect to the remote Ollama server...
Server URL: http://192.168.123.112:11434
Model: gemma2:9b

--- Sending Question ---
Question: how artificial intelligence learns
--- Response ---
### Think of AI as a very eager student

Imagine you’re a student who wants to learn how to recognize pictures of cats, write a poem, or play chess.  
You’ll learn this only by:

1. **Seeing many examples** (the teacher shows you many pictures or game moves).  
2. **Getting feedback** (the teacher tells you which answers are right or wrong).  
3. **Adjusting your own “rules”** so you get better next time.

Artificial intelligence (AI) does exactly the same thing, only in a way that a computer can handle billions of examples at once.

---

## 1. The “Brain” – A Neural Network

- **What it looks like**: A chain of layers made up of tiny units called *neurons* (like LEGO bricks).  
- **What it does**: Each neuron takes numbers in, applies a simple math operation (weighted sum + bias), passes it through a squashing function (e.g., sigmoid, ReLU), and sends it to the next layer.  
- **Why we call it a *model***: The collection of all the weights and biases is the *model’s memory* that will be tuned during learning.

---

## 2. Training Data – The Classroom

- **Examples**: For image recognition, each example is an image with a label (“cat” or “dog”).  
- **Quantity matters**: More data usually means the model can learn better patterns.  
- **Clean data matters too**: If the examples are noisy or mislabeled, the student will learn the wrong things.

---

## 3. Loss Function – The Teacher’s Grade

- **What it measures**: How far the model’s prediction is from the true answer.  
- **Common choices**:
  - *Mean Squared Error* for regression (predicting a number).
  - *Cross‑entropy* for classification (choosing a category).

The loss function is like the teacher’s rubric: the lower the loss, the closer the model is to the desired answer.

---

## 4. Back‑Propagation – The Feedback Loop

1. **Forward pass**: Feed an example through the network to get a prediction.  
2. **Compute loss**: Compare prediction to the true label.  
3. **Back‑propagate**: Calculate how each weight contributed to the loss (using calculus – the chain rule).  
4. **Adjust weights**: Move each weight a little in the direction that would reduce the loss.

This is analogous to a student realizing “I guessed too high on the last question, so I’ll lower my estimate next time.”

---

## 5. Gradient Descent – How the Student Moves

- **Gradient**: The slope of the loss surface; tells the direction to change weights.  
- **Descent step**: Multiply the gradient by a small learning rate (step size) and subtract from the weight.  
- **Iterate**: Repeat millions of times over the whole dataset until the loss stops improving.

Think of it as walking downhill in a foggy valley; each step is guided by a map that tells you which way is lower.

---

## 6. Types of Learning – Different Classroom Styles

| Style | Goal | How it Works |
|-------|------|--------------|
| **Supervised** | Learn from labeled data (image → “cat”). | Teacher provides correct answer for every example. |
| **Unsupervised** | Find hidden structure (group similar images). | Teacher gives no labels; the model discovers patterns itself. |
| **Reinforcement** | Learn a policy from rewards (robot learning to walk). | The model gets a score after each action and improves its strategy. |

---

## 7. Why It Works (High‑Level Intuition)

- **Expressive Power**: Neural networks can approximate almost any function (universal approximation theorem).  
- **Large Data & Compute**: With enough data and compute, the network can adjust its many weights to capture subtle patterns.  
- **Regularization & Generalization**: Techniques like dropout, weight decay, or data augmentation help the model perform well on *new* examples, not just the training set.

---

## 8. Putting It All Together – A Mini‑Example

1. **Task**: Distinguish handwritten digits (0–9).  
2. **Data**: 60 000 training images from the MNIST dataset.  
3. **Model**: A simple 3‑layer CNN.  
4. **Training loop**:
   - Load a mini‑batch of 128 images.
   - Forward pass → logits.
   - Compute cross‑entropy loss.
   - Back‑propagate → gradients.
   - Update weights with Adam optimizer (adaptive learning rate).
5. **Result**: After ~10 epochs, the model achieves >99% accuracy on a held‑out test set.

---

## 9. Bottom Line

- **AI learns by trial and error**: Try a guess, see how far off it is, adjust.  
- **The learning is driven by data**: More, higher‑quality examples = better learning.  
- **The math is a lot of weighted sums and tiny corrections**: Each iteration nudges the model closer to the goal.  

Once the model’s weights are set, it can perform the task much faster than any human could, but the process that got it there is surprisingly simple when broken down into: data → prediction → feedback → update → repeat.
```

When I ran the script, the response generated by the `gemma2:9b` model on my server appeared correctly in my MacBook's terminal. This successfully concluded the process of connecting my local dev environment to my remote LLM server. Now I can use this `llm` object to build more complex things like RAG or agents.