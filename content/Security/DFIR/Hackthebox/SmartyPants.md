---
Title: "HTB: SmartyPants"
date: 2025-06-04
tags: [windows, event_log, smartscreen, event_4624, event_4625, event_4778, event_4779, event_261, event_1149, event_1158]
Draft: False
---

## 1. Scenario Introduction

According to Dutch, the CTO of Forela, their domain environment is exposed across various industries, leading to frequent security breaches. For this reason, critical files have been kept on a separate Windows system. However, on January 24, 2025, an intruder accessed this file server, installed utilities used in attacks, stole critical files, and then deleted them to prevent recovery. This is the scenario we feared most becoming a reality.
The intruder has since attempted extortion, and this fact was immediately reported to our team. They are currently demanding money, and the legal team is handling the matter. In the meantime, we want to conduct a swift triage to determine the scope of this incident.
Administrator's Note: A few days ago, following a security research recommendation, we enabled the SmartScreen debug log feature on all systems. This log may provide quick insights into the incident, so please make sure to use it actively.

#### 1-1. Related Technologies
- Windows Forensics
- Event Log Analysis
- User Behavior Analysis

## 2. Background Knowledge

### 2-1. Windows Event Logs
#### 2-1-1. Security.evtx
- Event ID 4624: Successful logon log
- Event ID 4625: If NLA is turned off, logon type 10 client address, account name
- Event ID 4778: Session reconnected to Window Station (account name/IP)
- Event ID 4779: Session disconnected from Window Station

#### 2-1-2. RDP Related: TerminalServices-RemoteConnectionManager
- Event ID 261: Listener X received a connection (inbound connection)
- Event ID 1149: Remote Desktop Services user authentication succeeded (not logged if NLA is off)
- Event ID 1158: Remote Desktop Services accepted a connection from an IP address

### 2-2. SmartScreen Logging
SmartScreen is a security feature that verifies the safety of websites and files when a user visits a site or downloads and installs a file from the web, and blocks or warns accordingly.

While essentially an endpoint security feature, SmartScreen logs can become forensic artifacts that help track user actions and file executions.

Limitations of SmartScreen Logging:
- Disabled by default: This event log source is disabled by default and can be enabled by running the following command:
  `wevtutil sl Microsoft-Windows-SmartScreen/Debug /e:true`
- GUI-based logging: It only records activities performed through a GUI or RDP and does not log actions executed in PowerShell or CMD-shell.

For a more detailed explanation, refer to this [link](https://www.hackthebox.com/blog/smartscreen-logs-evidence-execution).

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `SmartyPants.zip` in the study materials and move it to your analysis OS: [SmartyPants.zip](https://labs.hackthebox.com/api/v4/challenges/864/cdn/redirect?auth_user_id=1568173&expires=1750125350&signature=4df9b90ae4bdc2ef6df92f224284bd1897b56abde06219b5f6f73162a4c5981b)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 3-2. Initial Analysis

#### 3-2-1. Install Analysis Tools

Useful tools for Windows event log analysis include EvtxECmd and Timeline Explorer, developed by [Eric Zimmerman](https://ericzimmerman.github.io/).
- EvtxECmd: Extracts event logs into csv, xml, or json format.
- Timeline Explorer: A viewer for CSV files based on a timeline.

Online tools (e.g., [evtx-to-xml](https://www.coolutils.com/ko/online/EVTX-to-XML)) are also available.

#### 3-2-2. Convert Event Log Files

The `EvtxECmd` command can be used to convert all event logs in the `Logs` directory into a single csv file.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_1.png]]

The converted file can be read using Timeline Explorer.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_2.png]]

### 3-3. Problem Solving
#### Q1. The attacker accessed the machine where Dutch keeps important files via RDP on January 24, 2025. What was the exact login time?

**Related Event Logs**
- 1102: Event log cleared
- 4624: An account was successfully logged on
- 1149: RDP network connection established

The Windows event log related to RDP is `Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational Log`, and the relevant Event ID is 1149.

According to the question, the `Dutch` account is suspected to have been used.
Also, the time would be January 24, 2025.

The next log to check is ID 4624 "An account was successfully logged on".
We can search by applying a filter for the Event ID.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_4.png]]

As can be seen in the log above, a login as `CTO-FILESVR\Dutch` is confirmed at 2025-01-24 10:52:07. This matches our initial suspicion that the `Dutch` account was used.

Now let's check the RDP logs. This record can be found by filtering the `RemoteConnectionManager` channel by Event ID 1149.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_5.png]]

We can see that an RDP session was connected with the `Dutch` account at 2025-01-24 10:15:14.

#### Q2. The attacker downloaded several utilities to use for data exfiltration. What is the name of the first tool they used?

**Hint: SmartScreen Debug Log**

**Related Event Log**
- Microsoft-Windows-SmartScreen/Debug: Stores SmartScreen debugging logs.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_6.png]]

After filtering for logs where the channel includes SmartScreen and the payload includes the message "isFileSupported", and sorting by time, the logs appear as above. The first one, `C:\Program Files (x86)\Edge\Application\msedge.exe`, is a browser software already installed on the system, so we skip it. The next one found in the downloads folder is `C:\Users\Dutch\Downloads\winrar-x64-701.exe`.

#### Q3. The attackers also downloaded a portable version of an executable effective for file searching. What is the full path of that file?

A widely used software for file searching on Windows is Everything.
This software can be identified in the logs above. It appears to have been downloaded after WinRAR.

Full path: `C:\Users\Dutch\Downloads\Everything.exe`

#### Q4. What time was the tool found in the question above (Q3) executed?

By checking the value of the "Time Created" field in the log found in the previous question, we can find the execution time of the file.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_7.png]]

The execution time of `Everything.exe` is 2025-01-24 10:17:33.

#### Q5. The tool identified earlier was used to search for important confidential documents stored on the host. What is the first document the attacker opened and exfiltrated?

Since SmartScreen logs also inspect document files, we can identify the documents opened by the attacker in the logs.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_8.png]]

The file opened immediately after `Everything.exe` can be considered the first document opened and exfiltrated.
Document path: `C:\Users\Dutch\Documents\2025- Board of directors Documents\Ministry of Defense Audit.pdf`

#### Q6. What was the second file to be exfiltrated?

Document path opened immediately after the previously found file: `C:\Users\Dutch\Documents\2025- Board of directors Documents\2025-BUDGET-ALLOCATION-CONFIDENTIAL.pdf`

#### Q7. The attacker also installed a cloud-related utility to exfiltrate the stolen data. What is that utility?

In the SmartScreen event logs, we can also find execution records of files suspected to be cloud utilities.
- C:\Users\Dutch\Downloads\MEGAsyncSetup64.exe
- C:\Users\Dutch\AppData\Local\MEGAsync\MEGAsync.exe

Therefore, the executed cloud utility is MEGAsync.

#### Q8. What time was this cloud utility executed?

Of the two files mentioned above (`MEGAsyncSetup64.exe`, `MEGAsync.exe`), the Setup file is for installation, and the actual utility is `MEGAsync.exe`, which was installed via the Setup file.

The execution time confirmed from the log is 2025-01-24 10:22:19.

#### Q9. The attacker took measures to delete data on the host to prevent recovery. What utility was used for this?

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_9.png]]

From the logs, it is presumed that a file named `File Shredder` is related to file deletion, judging by its name.

#### Q10. The attacker thought they had erased all traces by deleting two important logs. What time was the Security log deleted?

Let's check the Security log first. Apply a filter for Channel "=Security" and sort by Time Created.

![[Images/content/Security/DFIR/SMARTYPANTS/smartypants_3.png]]

Ominously, the first log that appears when sorted by time is "Event log cleared" at 2025-01-24 10:28:41.
This means that all events that occurred before this log was generated may have been deleted.
