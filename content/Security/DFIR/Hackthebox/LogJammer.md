---
Title: "HTB: LogJammer"
date: 2025-05-19
tags: [windows, event_log]
Draft: False
---

## 1. Scenario Introduction

You have been given the opportunity to work as a junior DFIR (Digital Forensics and Incident Response) consultant at a major consulting firm. However, they have requested that you complete a technical assessment.
The consulting firm **Forela-Security** wants to evaluate your **Windows Event Log analysis** skills.
We suspect that the user account **Cyberjunkie** has logged into a computer and may have **engaged in malicious activities**.
Please analyze the provided event log files and report your findings.

#### 1-1. Related Technologies
- Windows Event Log Analysis

## 2. Background Knowledge

### 2-1. Windows Event Logs
| Event Type | Event ID | Description |
|---|---|---|
| Logon | 4624 | Successful logon |
| Firewall Rule Added | 2004 | A new rule was added to the firewall |
| Event Log Cleared | 104 | The event log was cleared |
| Audit Policy Change | 4719 | The audit policy settings were changed |
| Scheduled Task Created | 4698 | A new scheduled task was created |
| Malware Detected | 1117 | Defender detected a threat and took action |
| PowerShell Command Executed | 4103 | Summary of the executed PowerShell command |
| PowerShell Code Executed | 4104 | The full PowerShell script block that was actually executed |

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `LogJammer.zip` in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 3-2. Initial Analysis
#### 3-2-1. Extracting Event Logs

Use `EvtxECmd.exe` to extract the logs.
`EvtxECmd.exe -d "C:\Users\bokchee\Desktop\analysis\Event-Logs"  --csv "C:\Users\bokchee\Desktop\analysis\Event-Logs" --csvf "LogJammer.csv"`

The extracted CSV file can be analyzed using `Timeline Explorer`.

### 3-3. Problem Solving
#### Q1. What time (UTC) did `cyberjunkie` first successfully log into the computer?

Event ID 4624 signifies a successful logon event.
Filtering by this, we can find a log where `Target: DESKTOP-887GK2L\CyberJunkie`.

![[logjammer_1.png]]

Login time: 27/03/2023 14:37:09

#### Q2. The user changed the system's firewall settings. Analyze the firewall event logs to identify the name of the added firewall rule.

Event ID 2004 can be checked to find events related to the addition of firewall policies.

![[logjammer_2.png]]

Checking the logs from after `cyberjunkie` logged in, we can find several logs.

Among them, we can identify "Metasploit C2 Bypass".

#### Q3. What is the direction of the firewall rule?

**Outbound**

#### Q4. The user changed the computer's audit policy. What is the subcategory of this changed policy?

Event ID 4719 is related to audit policy changes.
Search based on this and view the event in Event Viewer.

![[logjammer_3.png]]

Subcategory name: Other Object Access Events

#### Q5. The `cyberjunkie` user created a scheduled task. What is the name of this task?

Event Log 4698 is related to the registration of a scheduled task.
One entry appears, and its name can be identified.

![[logjammer_4.png]]

HTB-AUTOMATION

#### Q6. What is the full path of the file scheduled in the task?

Check the Payload Detail.

![[logjammer_5.png]]

`C:\Users\CyberJunkie\Desktop\Automation-HTB.ps1`

#### Q7. What are the arguments of the command?

`-A cyberjunkie@hackthebox.eu`

#### Q8. The antivirus running on the system detected a threat and took action. What tool did the antivirus identify as malware?

Event ID 1117 is an event where Windows Defender blocked malware.

![[logjammer_6.png]]

The blocked tool is SharpHound.

#### Q9. What is the full path of the malware that triggered the alert?

`C:\Users\CyberJunkie\Downloads\SharpHound-v1.1.0.zip`

#### Q10. What action did the antivirus program take?

![[logjammer_7.png]]

Quarantine

#### Q11. The user executed a command using PowerShell. What command did the user run?

Check Event IDs 4103, 4104.

```json
{"EventData":{"Data":[{"@Name":"MessageNumber","#text":"1"},{"@Name":"MessageTotal","#text":"1"},{"@Name":"ScriptBlockText","#text":"Get-FileHash -Algorithm md5 .\\Desktop\\Automation-HTB.ps1"},{"@Name":"ScriptBlockId","#text":"b4fcf72f-abdc-4a84-923f-8e06a758000b"},{"@Name":"Path"}]}}
```

**Get-FileHash -Algorithm md5 .\Desktop\Automation-HTB.ps1**

#### Q12. It is suspected that the user deleted some event logs. Which event log file was deleted?

Event ID 104 indicates that an event log was cleared.

```json
{"UserData":{"LogFileCleared":{"SubjectUserName":"CyberJunkie","SubjectDomainName":"DESKTOP-887GK2L","Channel":"Microsoft-Windows-Windows Firewall With Advanced Security/Firewall","BackupPath":""}}}
```

**Microsoft-Windows-Windows Firewall With Advanced Security/Firewall**
