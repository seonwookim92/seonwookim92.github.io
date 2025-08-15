---
Title: "HTB: JingleBell"
date: 2025-05-17
tags: [windows, wpndatabase]
Draft: False
---

## 1. Scenario Introduction

Torrin is suspected of being an insider threat at Forela. He appears to have exfiltrated some data and removed certain applications from his workstation. There are also signs that he bypassed several security controls to install unauthorized software. Although the digital forensics team has investigated multiple times, no clear evidence of data exfiltration has been found. As a senior incident responder, you have been tasked with investigating this case and uncovering the conversation between the two individuals involved.

#### 1-1. Related Technologies
- Windows Notification Log Analysis

## 2. Background Knowledge

### 2-1. Windows Push Notification DB (wpndatabase)

##### 2-1-1. File Structure
- `wpndatabase.db`: The **main SQLite database** file, storing notification records.
- `wpndatabase.db-shm`: A **shared memory** file, used for controlling concurrent access.
- `wpndatabase.db-wal`: A **Write-Ahead Log**, storing temporary changes before they are committed.
- If the `.shm` and `.wal` files are in the same directory, SQLite tools will **automatically recognize** them for up-to-date analysis.

##### 2-1-2. wpndatabase.db File
- A data store related to the Windows Notification System (WNS).
- Can contain **push notification records**, **app names**, **titles**, **body content**, **timestamps**, etc.
- Can be used to check notification information from apps like Slack, Outlook, Teams, etc.

##### 2-1-3. Forensic Application Points
- Detecting insider activity attempts or suspicious messages.
- Capturing traces of external communication, such as through Slack.
- Analyzing URLs, file links, commands, etc., included in notification content.
- Can be used to reconstruct a user activity timeline.

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `jinglebell.zip` in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/Jinglebell]
└─$ 7z x jinglebell.zip 

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 478652 bytes (468 KiB)

Extracting archive: jinglebell.zip
--
Path = jinglebell.zip
Type = zip
Physical Size = 478652

    
Enter password (will not be echoed):
Everything is Ok                                                                            

Folders: 9
Files: 3
Size:       2589296
Compressed: 478652


┌──(kali㉿kali)-[~/htb_sherlock/Jinglebell]
└─$ ls
jinglebell.zip  Torrincase
```

### 3-2. Initial Analysis
#### 3-2-1. Artifact Type Analysis

```bash
┌──(kali㉿kali)-[~/htb_sherlock/Jinglebell]
└─$ tree                                         
.
├── jinglebell.zip
└── Torrincase
    └── C
        └── Users
            └── Appdata
                └── Local
                    └── Microsoft
                        └── Windows
                            └── Notifications
                                ├── wpndatabase.db
                                ├── wpndatabase.db-shm
                                ├── wpndatabase.db-wal
                                └── wpnidm
```

The artifact structure suggests it is related to the Windows Push Notification Service (WNS) within the C drive.

![[jinglebell_1.png]]

Opening the `wpndatabase.db` file reveals DB tables related to notifications.

### 3-3. Problem Solving
#### Q1. What software/application did Torrin use to leak Forela's secrets?

Checking the `Notification` table reveals multiple messages related to Slack.

![[jinglebell_2.png]]

#### Q2. What is the name of the competitor company to which Torrin is suspected of leaking data?

Opening the records related to Toast (notification) messages reveals the company name.

![[jinglebell_3.png]]

**Company Name: PrimeTech Innovations**

#### Q3. What is the account name of the employee at the competitor company with whom Torrin shared information?

**Cyberjunkie-PrimeTechDev**

#### Q4. What is the name of the channel where they had their conversation?

![[jinglebell_4.png]]

**Channel Name: forela-secrets-leak**

#### Q5. What is the password for the archive server?

![[jinglebell_5.png]]

Password: `Tobdaf8Qip$re@1`

#### Q6. What is the URL provided to Torrin for uploading files?

![[jinglebell_6.png]]

`https://drive.google.com/drive/folders/1vW97VBmxDZUIEuEUG64g5DLZvFP-Pdll?usp=sharing`

#### Q7. What time was the above URL shared?

The format `1681986889.660179` appears to be a timestamp.
We can convert the Unix Epoch Time format to UTC.

```bash
┌──(kali㉿kali)-[~/…/Local/Microsoft/Windows/Notifications]
└─$ date -u -d @1681986889.660179
Thu Apr 20 10:34:49 AM UTC 2023
```

**2023-04-20 10:34:49**

#### Q8. For how much did Torrin leak Forela's secrets?

"Sent 10,000 £ to the above account as promised, cheers"

**£10,000**
