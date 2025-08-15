---
Title: "HTB: Reaper"
date: 2025-05-29
tags: [windows, event_log, pcap, activedirectory]
Draft: False
---

## 1. Scenario Introduction

An alert was triggered in the organization's SIEM (System Information and Event Management) system for a **suspicious logon event** that requires immediate analysis. The core of the alert is as follows:
- The **IP address and Source Workstation name used in the logon request do not match**.
- This has raised the possibility of an **NTLM Relay Attack**.
Currently, the analysis team has secured a **network capture file (pcap)** from around the time of the incident and **Windows event logs**.
Your mission is to analyze the evidence focusing on the points below and report the findings to the SOC (Security Operations Center) manager.

#### 1-1. Related Technologies
- PCAP File Analysis
- Windows Event Log Analysis

## 2. Background Knowledge
### 2-1. NTLM Relay Attack Technique
- **NTLM Relay** is an attack where an attacker intercepts authentication information between two systems and reuses it on another system.
- The attacker intercepts communication between a **client** and a **server** and uses it to bypass or escalate authentication on another target server.

#### 2-1-1. NTLM Authentication Method
- **NTLM** (NT LAN Manager) is a Microsoft authentication protocol used for user authentication in a Windows environment.
- It uses a **Challenge-Response mechanism** for authentication between the user and the server.
    - The process involves a sequence from the client to the server to the authentication server.

#### 2-1-2. NTLM Relay Attack Flow
![[public/Images/content/Security/DFIR/REAPER/reaper_13.png]]

### 2-2. Windows Event Log Analysis
- Event ID 4624: Successful Logon Event
	- Recorded when a user successfully logs into the system.
	- The logon type (2: Console, 3: Network, 10: Remote Desktop, etc.) is important.
- Event ID 4662: An operation was performed on an object
	- Recorded when a user or process attempts a specific operation (read/modify, etc.) on a directory object (e.g., an AD account).
	- Useful for analyzing access privilege abuse or suspicious modification activities.
- Event ID 4702: A scheduled task was updated
	- Recorded when a Scheduled Task is modified.
	- Leaves traces when an attacker inserts a script for privilege maintenance or automatic execution.
- Event ID 5140: A network share object was accessed
	- Recorded when a file share (e.g., SMB) is accessed over the network.
	- Used for analyzing signs of internal Lateral Movement or information exfiltration.
	- The access path can be identified through the Logon Type (2: Interactive Shell / 3: Network Remote).

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `Reaper.zip` in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/Reaper]
└─$ 7z x Reaper.zip 

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 116934 bytes (115 KiB)

Extracting archive: Reaper.zip
--
Path = Reaper.zip
Type = zip
Physical Size = 116934


┌──(kali㉿kali)-[~/htb_sherlock/Reaper]
└─$ ls
Reaper  Reaper.zip


┌──(kali㉿kali)-[~/htb_sherlock/Reaper]
└─$ cd Reaper             


┌──(kali㉿kali)-[~/htb_sherlock/Reaper/Reaper]
└─$ ls
ntlmrelay.pcapng  Security.evtx
```
3. In this solution, the `evtx` file will be analyzed using Event Log Explorer on Windows, and the `pcapng` file will be analyzed using Wireshark.

### 3-2. Initial Analysis
#### 3-2-1. Wireshark Analysis

![[public/Images/content/Security/DFIR/REAPER/reaper_1.png]]

Checking the Conversation, most of the communication occurs within the internal IP range of 172.17.x.x, with some communication to external IP ranges as well.

![[public/Images/content/Security/DFIR/REAPER/reaper_2.png]]

It appears that the most packets originated from the 172.17.79.x range.

#### 3-2-2. Windows Event Log Analysis

![[public/Images/content/Security/DFIR/REAPER/reaper_3.png]]

There are only 51 Windows event logs in total, and they are concentrated on a few specific Event IDs. The computer is identified as `Forela-Wkstn001.forela.local`, which seems to be an account within the `forela.local` AD domain.

### 3-3. Problem Solving
#### Q1. What is the IP address of `Forela-Wkstn001`?

By checking the NBNS protocol, one of the naming protocols used in Active Directory, we can find a matching IP record.

![[public/Images/content/Security/DFIR/REAPER/reaper_4.png]]

When filtering for "nbns", we can see an NBNS protocol packet with the message "Refresh NB FORELA-WKSTN001<20>". This is a packet for renewing NetBIOS name information, which a PC periodically sends to the domain NBNS server to maintain its name registration.

By checking the requesting IP and the address information included in the "Additional records", we can identify the IP address: 172.17.79.129

#### Q2. What is the IP address of `Forela-Wkstn002`?

![[public/Images/content/Security/DFIR/REAPER/reaper_5.png]]

Similar to the previous method, we can find the IP address by looking for the "Refresh NB FORELA-WKSTN002" message in the NBNS protocol and checking its Source IP: 172.17.79.136

#### Q3. What is the account name whose hash was compromised by the attacker?

To check if a hash was compromised, we need to check logs related to the attacker likely using that hash to authenticate to the system.

Event ID 4624 (successful logon) in the event logs is relevant here.
We can also check for anomalies in the PCAP file.

First, let's continue to examine the nbns protocol in the PCAP file.

![[public/Images/content/Security/DFIR/REAPER/reaper_6.png]]

While the hostnames for the two previously identified IPs are confirmed, the IP 172.17.79.135 does not seem to have a hostname.

Scrolling down further, we see numerous SMB2 protocol packets, most of which seem to be communicating with one of the two previously identified hosts. To investigate further, we apply a filter:
`smb2 and ip.addr == 172.17.79.135`

![[public/Images/content/Security/DFIR/REAPER/reaper_7.png]]

The Info column shows which account was used for the session connection request: `arthur.kyle`

![[public/Images/content/Security/DFIR/REAPER/reaper_8.png]]

The event logs viewed through Event Log Explorer also confirm that a 4624 (successful logon) event occurred for this account from the same host.

#### Q4. What is the IP address of the Unknown Device used by the attacker to intercept the credentials?

The IP address can be confirmed from the previously checked logs: 172.17.79.135

#### Q5. What is the file share (SMB) that was browsed with the victim user account?

By further examining the SMB2 related packets in the PCAP file, we can identify the path that was attempted to be connected to.

![[public/Images/content/Security/DFIR/REAPER/reaper_9.png]]

Connection path: `\DC01\Trip`

#### Q6. What port did the attacker use to access the workstation with the compromised account?

To check events related to logon authentication, we can refer to Event ID 4624.
We apply a filter to check.

![[public/Images/content/Security/DFIR/REAPER/reaper_10.png]]

There is one log with Logon Type 3. Since the account used for the logon is also `arthur.kyle`, it is presumed that the attacker logged in remotely.

The port used for the logon attempt is 40252.

#### Q7. What is the Logon ID of the malicious session?

This can be confirmed from the previously checked event log: 0x64a799

#### Q8. The detection was possible due to a mismatch between the hostname and the assigned IP. What are the workstation name and IP address?

This can be confirmed from the previously checked event log: FORELA-WKSTN002, 172.17.79.135

#### Q9. What is the UTC time of the logon event?

![[public/Images/content/Security/DFIR/REAPER/reaper_11.png]]

By opening the XML format of the event log, we can find the UTC time: 2024-07-31 04:55:16

#### Q10. What is the name of the share that was exploited by the attacker?

By checking Event ID 5140 in the event logs, we can find events related to accessing a shared object.
There is one such event in the given event logs.

![[public/Images/content/Security/DFIR/REAPER/reaper_12.png]]

Share name: `\\*\IPC$`
