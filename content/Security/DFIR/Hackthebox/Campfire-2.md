---
Title: "HTB: Campfire-2"
date: 2025-05-15
tags:
  - windows
  - event_log
  - event_4768
  - event_4769
  - asreproasting
Draft: false
---
## 1. Scenario Introduction

Forela's network is under continuous attack. The security system has raised an alert for an old administrator account requesting a ticket from the Key Distribution Center (KDC) on the domain controller. The inventory shows that this user account is not currently in use, and you have been tasked with investigating this issue. This situation could be an AS-REP Roasting attack, as anyone can request a ticket for a user whose preauthentication is disabled.

#### 1-1. Related Technologies
- Windows Event Log Analysis
- Active Directory

## 2. Background Knowledge
### 2-1. Event Logs
#### 2-1-1. Event ID 4769 – A Kerberos service ticket was requested
- Location: **Domain Controller**
- Description: Recorded when a user requests a **TGS (Service Ticket)**.
- Related Attacks: **Kerberoasting**, Pass-the-Ticket, Brute Force
- Key Fields:
    - **Service Name**: The requested SPN (service account).
    - **Ticket Encryption Type**: 0x17 (RC4-HMAC) → Crackable ticket.
    - **Failure Code**: 0x0 = Success.
    - **Client Address**: The IP of the user who made the request.
🔎 **Detection Points**
- Numerous SPN requests.
- Service names that do not end with `$`.
- Use of RC4-HMAC (0x17).
- Abnormal service requests after a normal login.

#### 2-1-2. Event ID 4768 – A Kerberos authentication ticket (TGT) was requested
- **Location**: **Domain Controller**
- **Description**: Recorded when a user requests a **TGT (Ticket Granting Ticket)**. This typically occurs at login and is the starting point of a user's Kerberos authentication.
- **Related Attacks**: Brute Force, Pass-the-Ticket, Password Spraying, Golden Ticket
- **Key Fields**:
    - **Account Name**: The user account that attempted authentication.
    - **Service Name**: krbtgt (always the same).
    - **Ticket Encryption Type**: The encryption method (e.g., 0x17 = RC4-HMAC, 0x12 = AES256, etc.).
    - **Failure Code**: 0x0 = Success, others are failures (e.g., 0x18 = Bad password).
    - **Client Address**: The IP address of the client that made the request.
🔎 **Detection Points**
- Numerous authentication requests in a short time (suspected Brute Force).
- **Repeated failure codes** (especially 0x18 → bad credentials).
- Authentication attempts at **unusual times**.
- Requests from **unknown client addresses**.
- Use of **non-standard encryption types** (e.g., persistent use of only 0x17).

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `Campfire-2.zip` in the study materials and move it to your analysis OS: [Campfire-2.zip](https://labs.hackthebox.com/api/v4/challenges/736/cdn/redirect?auth_user_id=1568173&expires=1751330652&signature=4165b189758cfb03922f48f36c52ab2244d6fc5e9305dd88eb8d4d03f66967d0)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 3-2. Problem Solving
#### Q1. When did the AS-REP Roasting attack occur, and when did the attacker request a Kerberos ticket for the vulnerable user?

An AS-REP Roasting attack occurs when a client requests a TGT from the KDC, which is the first step of Kerberos authentication, an Authentication Service request.

Clues to detect an AS-REP Roasting attack include:
- Check Event ID 4768: This event occurs when a user requests a TGT (AS-REQ).
- Pre-Authentication Type = 0: This means pre-authentication is not used, allowing an attacker to skip the process of encrypting a timestamp with their credentials and directly request a TGT and receive a response (AS-REP).
- Ticket Encryption Type = 0x17: Attackers prefer RC4-HMAC (0x17) because it is easier to crack than AES.
- Service Name = krbtgt: The requested service account must be the `krbtgt` account, which returns the AS-REP.

Based on this, we extract Event ID 4768 logs from the provided evtx file.

![[Images/content/Security/DFIR/CAMPFIRE-2/campfire-2_1.png]]

By examining the descriptions of the logs based on the criteria above, we find one that matches the conditions.

![[Images/content/Security/DFIR/CAMPFIRE-2/campfire-2_2.png]]

Checking the XML value confirms the time: 2024-05-29 06:36:40

![[Images/content/Security/DFIR/CAMPFIRE-2/campfire-2_3.png]]

#### Q2. What is the user account that the attacker targeted?

The requested user account can be identified from the log above: `arthur.kyle`

#### Q3. What is the SID of the account identified above?

S-1-5-21-3239415629-1862073780-2394361899-1601

#### Q4. It is crucial to identify the compromised user account and the workstation responsible for this attack. To assist our threat hunting team, please provide the internal IP address of the compromised asset.

172.17.79.129

#### Q5. We do not have the artifacts from the source machine yet. Can you help us isolate the compromised account by identifying the user account used for the AS-REP roasting attack using the same DC security logs?

By clearing the log filter and checking in chronological order, we can see the account that requests a service ticket immediately after.

![[Images/content/Security/DFIR/CAMPFIRE-2/campfire-2_4.png]]

The attacker generates a service ticket request event from the same IP.
Here, we can identify the account used.

Compromised account: `happy.grunwald`
