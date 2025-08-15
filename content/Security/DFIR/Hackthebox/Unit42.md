---
Title: "HTB: Unit42"
date: 2025-06-08
tags:
  - windows
  - event_log
  - sysmon
  - event_1
  - event_2
  - event_3
  - event_5
  - event_11
  - event_22
Draft: false
---
## 1. Scenario Introduction

Recently, an unidentified UltraVNC program was discovered on a system within the organization. Although it appeared to be a normal remote control tool, it was actually a backdoored version planted by an attacker. Evidence suggests that this was being used to maintain persistent access to the system from the outside. Your task is to trace the initial signs of this intrusion and analyze the attacker's activities.

#### 1-1. Related Technologies
- Windows Event Log Analysis
- Sysmon Log Analysis
- Dropper Behavior Analysis

## 2. Background Knowledge

### 2-1. Sysmon
**Sysmon (System Monitor)** is a powerful system monitoring tool provided by Microsoft that records various activities occurring on a Windows system in detail.

#### 2-1-1. Key Features
- **Process Creation Tracking**: Records which programs were executed, including parent-child process relationships.
- **Network Connection Logging**: Stores a history of network communications, such as connection attempts to external servers.
- **File Creation and Modification Detection**: Records when files in specific locations are newly created or modified.

#### 2-1-2. Importance in Security Analysis
- **Malware Activity Tracking**: Can identify execution traces of malicious programs like backdoors or RATs.
- **Identifying Anomalies**: Detects unusual behavior (e.g., sudden script execution, connection attempts to external sources).
- **Rapid Threat Response**: Enables swift response by detecting suspicious activities early.

#### 2-1-3. Key Events
- Event ID 1: Process creation/execution, includes process path, parent process, command-line arguments, etc.
- Event ID 2: Records file modification times as timestamps.
- Event ID 3: Network connection, includes the process that made the connection and the destination IP/Port information.
- Event ID 5: Process termination, includes the name of the terminated process.
- Event ID 11: File creation, includes the creating process and the absolute path of the file.
- Event ID 22: DNS query, includes the requested domain information and the resolved IP information.

## 3. Analysis

### 3-1. Prepare Evidence File
1. Open the link below in a browser to download the file, or find `unit42.zip` in the study materials and move it to your analysis OS: [unit42.zip](...)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

3. To analyze the `evtx` file, a useful tool is Event Log Explorer. Open the file in it for analysis.

### 3-2. Initial Analysis
#### 3-2-1. Initial Analysis 1

![[public/Images/content/Security/DFIR/UNIT42/unit42_1.png]]

When the file is opened in Event Log Explorer, the logs are displayed in a table format.
Information such as log type, date/time, Event ID, and computer is displayed.

![[public/Images/content/Security/DFIR/UNIT42/unit42_2.png]]

The lower part of the UI shows a detailed description of the selected log.

### 3-3. Problem Solving
#### Q1. How many times did an event with Event ID 11 occur?

You can use the filter function to filter by Event ID.

![[public/Images/content/Security/DFIR/UNIT42/unit42_3.png]]

Enter 11 for the Event ID.

![[public/Images/content/Security/DFIR/UNIT42/unit42_4.png]]

The filtering result shows that 56 logs remain.

#### Q2. Every time a process is created in memory, a log with Event ID 1 is recorded, which includes the command line, hash, process path, parent process path, etc. This information is useful for analyzing malicious activities that have occurred on the system. What malicious process was executed on the infected system?

![[public/Images/content/Security/DFIR/UNIT42/unit42_5.png]]

As before, filtering by Event ID 1 yields 6 logs.
Each description shows the path of the executed process, its hash value, etc.

Since process names are often disguised to be similar or identical to legitimate files, the hash value can be used to determine if it is malicious.

You can search by hash value on VirusTotal.

![[public/Images/content/Security/DFIR/UNIT42/unit42_6.png]]

For a legitimate file, a search by hash value will mostly show "Undetected" as above.

![[public/Images/content/Security/DFIR/UNIT42/unit42_7.png]]

However, for a malicious file, various malicious activities are shown based on previously analyzed data.

The process `C:\Users\CyberJunkie\Downloads\Preventivo24.02.14.exe.exe` appears to be malicious.

#### Q3. What cloud service was used to distribute the malware?

Clear the filter and search for the string "Preventivo".
Then, by examining the surrounding logs, you can find an Event ID 22 (DNS Query) log.

This suggests that the site was visited around that time.

![[public/Images/content/Security/DFIR/UNIT42/unit42_8.png]]

It appears the victim used Dropbox.

#### Q4. Among the many files written to the disk, the initial malicious file used a detection evasion technique called "Time Stomping". This technique changes the file creation time to a much earlier date to make it blend in with other normal files and be less noticeable. What was the timestamp of the PDF file changed to?

Based on the problem description, filter for Event ID 2 file time change logs.
Also, check the log description to find the PDF file.

![[public/Images/content/Security/DFIR/UNIT42/unit42_9.png]]

The log record shows that the time was changed to 2024-01-14 08:10:06.

#### Q5. The malicious dropper wrote several more files to the disk. Where was the "once.cmd" file created?

This time, filter by the string "once.cmd". In addition, it would be good to focus on Event ID 11 for file creation logs.

![[public/Images/content/Security/DFIR/UNIT42/unit42_10.png]]

The identified full path is `C:\Users\CyberJunkie\AppData\Roaming\Photo and Fax Vn\Photo and vn 1.1.2\install\F97891C\WindowsVolume\Games\once.cmd`.

#### Q6. The malicious file attempts to connect to a random domain, likely to check the internet connection status. What domain did it try to connect to?

Filter by Event ID 22.

![[public/Images/content/Security/DFIR/UNIT42/unit42_11.png]]

Excluding the previously identified Dropbox-related URL, the only other domain it attempted to connect to is `www.example.com`.

#### Q7. What is the IP address the malicious process tried to connect to?

Network connection related logs are recorded with Event ID 3.
Filter by this.

![[public/Images/content/Security/DFIR/UNIT42/unit42_12.png]]

One log appears. The IP it tried to connect to is `93.184.216.34`.

#### Q8. The malicious process terminates after infecting the PC with UltraVNC, which is used as a backdoor. What time did the process terminate?

Process termination records are logged with Event ID 5. Filtering by this yields one log.

![[public/Images/content/Security/DFIR/UNIT42/unit42_13.png]]

The process terminated at 2024-02-14 03:41:58.
