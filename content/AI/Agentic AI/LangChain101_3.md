---
title: "LangChain 101 : #3 Setup Ollama on a GPU Server"
date: 2025-07-19
tags:
  - ai
  - agentic_ai
  - langchain
draft: false
---

Recently, using frameworks like LangChain and LangGraph to build LLM-based automation workflows has become increasingly common. While high-performance API models like **GPT-5** and **Claude Sonnet 4** are well-suited for tasks requiring complex reasoning and judgment, using them for numerous, simpler, repetitive tasks can lead to unnecessary API costs.

This is where a **local LLM** setup becomes an excellent alternative. With the rise of powerful open-source models like **Llama 3**, **Qwen 2**, and **Gemma 2**, many are now choosing to host models on their own servers for more cost-effective LLM utilization.

This post will document the step-by-step process of installing **Ollama**, a popular tool for running local LLMs, on a Linux GPU server and configuring its network settings to allow remote access (e.g., from a personal MacBook).

---
### 1. Install Ollama

First, install Ollama using the script provided on the official website. The installation is simple and can be completed by running the command below in your terminal.

```bash
(base) [your-username]@[your-hostname]:~$ curl -fsSL https://ollama.com/install.sh | sh
```

The installation process automatically downloads necessary packages, creates an `ollama` user and group, and registers a `systemd` service.

```bash
>>> Installing ollama to /usr/local
[sudo] password for [your-username]:
>>> Downloading Linux amd64 bundle
######################################################################## 100.0%
>>> Creating ollama user...
>>> Adding ollama user to render group...
>>> Adding ollama user to video group...
>>> Adding current user to ollama group...
>>> Creating ollama systemd service...
WARNING: systemd is not running
>>> NVIDIA GPU installed.
>>> The Ollama API is now available at 127.0.0.1:11434.
>>> Install complete. Run "ollama" from the command line.
```

Once the installation is complete, you can use the `ollama` command. Check the list of available commands with `ollama help`.

```bash
(base) [your-username]@[your-hostname]:~$ ollama help

Large language model runner

Usage:
  ollama [flags]
  ollama [command]

Available Commands:
  serve       Start ollama
  create      Create a model
  show        Show information for a model
  run         Run a model
  ...
```

### 2. Run the Ollama Service and Check for Errors

Immediately after installation, if you try to check the list of locally downloaded models with `ollama list`, you will likely encounter the following error.

```bash
(base) [your-username]@[your-hostname]:~$ ollama list
Error: ollama server not responding - could not connect to ollama server, run 'ollama serve' to start it
```

This occurs because the Ollama server is not yet running. Since it was registered as a `systemd` service during installation, you need to manage it using `systemctl` commands.

### 3. Modify the Service Configuration for Remote Access ⚙️

By default, Ollama's API only accepts requests from `127.0.0.1` (localhost). To connect to this server from an external device, you must modify the service configuration to accept requests from all network interfaces.

First, navigate to the `/etc/systemd/system/` directory where the `ollama.service` file is located.

```bash
(base) [your-username]@[your-hostname]:~$ cd /etc/systemd/system
(base) [your-username]@[your-hostname]:/etc/systemd/system$ ls | grep ollama
ollama.service
```

Now, open the `ollama.service` file with a text editor like `vi` or `nano` (this requires sudo privileges).

```bash
(base) [your-username]@[your-hostname]:/etc/systemd/system$ sudo vi ollama.service
```

```bash
In the file, find the line `Environment="OLLAMA_HOST=127.0.0.1"` within the `[Service]` section and change the IP address to `0.0.0.0`. The address `0.0.0.0` signifies that the service should listen for connections on all available network interfaces.
```

**Before :**

```bash
[Service]
...
Environment="OLLAMA_HOST=127.0.0.1"
...
```

**After :**

```bash
[Service]
...
Environment="OLLAMA_HOST=0.0.0.0"
...
```

### 4. Restart and Check the Systemd Service

Since the service file has been modified, you need to reload the `systemd` daemon to recognize the changes and then restart the Ollama service.

```bash
# Reload the systemd daemon to apply changes
(base) [your-username]@[your-hostname]:/etc/systemd/system$ systemctl daemon-reload

# Restart the Ollama service
(base) [your-username]@[your-hostname]:/etc/systemd/system$ systemctl restart ollama
```

Now, check if the service is running correctly with the `systemctl status ollama` command.

```bash
(base) [your-username]@[your-hostname]:/etc/systemd/system$ systemctl status ollama
● ollama.service - Ollama Service
     Loaded: loaded (/etc/systemd/system/ollama.service; disabled; preset: enabled)
     Active: active (running) since Sun 2025-08-17 16:59:59 KST; 7s ago
   Main PID: 4927 (ollama)
...
... level=INFO source=routes.go:1357 msg="Listening on 0.0.0.0:11434 (version 0.1.xx)"
```

If you see `Active: active (running)` and the message `Listening on 0.0.0.0:11434` in the logs, the server-side configuration is complete.

### 5. Set Client Environment Variables and Verify Connection 🖥️

The server is now ready to accept external requests. However, the `ollama` command-line client running on the server itself still defaults to connecting to `127.0.0.1`, which can cause an error. You need to tell the client which IP address to connect to.

First, find the server's IP address using `ifconfig` or `ip a`.

```bash
(base) [your-username]@[your-hostname]:~$ ifconfig
...
wlx9c5322037270: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.123.112  netmask 255.255.255.0  broadcast 192.168.123.255
...
```

(We'll use `192.168.123.112` as an example. You must replace this with your server's actual IP address.)

Set the `OLLAMA_HOST` environment variable to this IP address and add it to your shell's configuration file (`~/.bashrc` or `~/.zshrc`) to make the change permanent.

```bash
# Set the environment variable and add it to .bashrc
(base) [your-username]@[your-hostname]:~$ echo 'export OLLAMA_HOST=[your-server-ip]:11434' >> ~/.bashrc

# Apply the changes immediately
(base) [your-username]@[your-hostname]:~$ source ~/.bashrc
```

Now, if you run `ollama list` again, it should execute without errors and display an empty list of models.

```bash
(base) [your-username]@[your-hostname]:~$ ollama list
NAME    ID      SIZE    MODIFIED
```

### 6. Download a Model and Enable Auto-Start on Boot 🚀

The setup is complete. You can now download any model you want using the `pull` command.

```bash
(base) [your-username]@[your-hostname]:~$ ollama pull gemma2:9b
pulling manifest
...
success
```

Finally, run `systemctl enable` to ensure the Ollama service starts automatically whenever the server reboots.

```bash
(base) [your-username]@[your-hostname]:~$ sudo systemctl enable ollama
Created symlink /etc/systemd/system/default.target.wants/ollama.service → /etc/systemd/system/ollama.service.
```

Your GPU server is now acting as an LLM server, accessible to other devices on your local network (like a MacBook or Windows PC) at `http://[your-server-ip]:11434`. You can now use it with frameworks like LangChain via its Ollama integration to freely test and utilize models without incurring API costs.