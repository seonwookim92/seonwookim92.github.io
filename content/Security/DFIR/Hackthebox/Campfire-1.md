---
Title: "HTB: Campfire-1"
date: 2025-05-13
tags: [windows, event_log, kerberoasting, domaincontroller, event_4769, event_4104]
Draft: False
---

## 1. Scenario Introduction

Alonzo discovered strange files on his computer and immediately notified the newly formed SOC team. After assessing the situation, it was determined that a **Kerberoasting attack** might have occurred on the network. Your mission is to **analyze the provided evidence to confirm these suspicions**.
The materials provided to you are as follows:
1.  **Security Logs from the Domain Controller**
2.  **PowerShell-Operational logs from the victim workstation**
3.  **Prefetch files from the victim workstation**
You must analyze these materials to determine if a Kerberoasting attack actually occurred.

#### 1-1. Related Technologies
- Event Log Analysis
- Prefetch Analysis

## 2. Background Knowledge

### 2-1. Kerberoasting Attack
- A technique where an attacker requests a service ticket (TGS) for a domain user account and then **cracks the ticket offline** to steal the **service account's password**.
#### 2-1-1. Attack Conditions
- The attacker must be an **authenticated user in the domain** (even a non-administrator account will do).
- **Kerberos authentication must be in use**.
- An account with a registered Service Principal Name (SPN) must exist.
#### 2-1-2. Signs of an Attack
- A large number of **Event ID 4769** occurrences on the domain controller (service ticket requests).
- Pay attention if the requested service account uses the **RC4-HMAC** encryption algorithm.
- Attackers use tools like `Invoke-Kerberoast`, `Rubeus`, and `Impacket`.
- Traces of related script execution in **PowerShell logs** (`kerberoast`, `base64`, `Invoke`).
- **Prefetch files** may record `rubeus.exe`, `powershell.exe`, `python.exe`, etc.
#### 2-1-3. Detection Methods
- Exclude cases where the service name is `krbtgt`: `krbtgt` is an account used exclusively for issuing tickets and is irrelevant to TGS requests.
- Exclude cases where the service name ends with `$`: Accounts ending with `$` are usually computer accounts, and Kerberoasting attacks primarily target service accounts.
- Look for Ticket Encryption Type 0x17 (RC4-HMAC): Attackers prefer RC4-HMAC (0x17) because it is easier to crack than AES.
- Look for Failure Code 0x0: This indicates that the Kerberos request was successful.

### 2-2. Event Logs
#### 2-2-1. Event ID 4769 – A Kerberos service ticket was requested
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

#### 2-2-2. Event ID 4104 - PowerShell script block logging
- Location: **Workstation or Server (PowerShell execution environment)**
- Description: Records the **full content of script blocks** executed in PowerShell.
- Log Activation Condition: **Script Block Logging** must be enabled.
- Related Attacks: **Use of Kerberoasting tools (`Invoke-Kerberoast`, `Rubeus`, etc.)**, Fileless malware.
- Key Fields:
    - **ScriptBlockText**: The actual executed script code.
    - **UserID**: The user who executed it.
    - **Path**: The execution path (`powershell.exe`, `cmd.exe`, etc.).
🔎 **Detection Points**
- Suspicious functions starting with `Invoke-`.
- Keywords like `base64`, `FromBase64String`, `Add-Type`, `Reflection`.
- Inclusion of tool names (`Rubeus`, `Mimikatz`, etc.).

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find the `campfire-1.zip` file in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 3-2. Initial Analysis
#### 3-2-1. Verify Evidence Files
After extraction, you can see two folders: Domain Controller / Workstation.

![[campfire-1_1.png]]

The Domain Controller folder only contains an Event Log file.

![[campfire-1_2.png]]

The Workstation folder contains an Event Log file and a C drive dump file.

![[campfire-1_3.png]]

#### 3-2-2. Extract Prefetch

To trace file execution history, extract the prefetch files from the workstation's filesystem.
Use `PECmd.exe` by specifying the path `C:\Windows\Prefetch`.

```bash
PS C:\Users\bokchee\Desktop\EZ tools > .\PECmd.exe -d "C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch" --csv "C:\Users\bokchee\Desktop\analysis\Triage\Workstation" --csvf "prefetch.csv"

...

---------- Processed C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch\WWAHOST.EXE-2CFA09D4.pf in 0.61227520 seconds ----------
Processed 207 out of 212 files in 39.8965 seconds

Failed files
  C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch\FILESYNCCONFIG.EXE-1C1104B5.pf ==> (Invalid signature! Should be 'SCCA')
  C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch\MICROSOFT.SHAREPOINT.EXE-EECBA9B3.pf ==> (Invalid signature! Should be 'SCCA')
  C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch\SVCHOST.EXE-6A4A44E7.pf ==> (Invalid signature! Should be 'SCCA')
  C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch\SVCHOST.EXE-77C41F85.pf ==> (Invalid signature! Should be 'SCCA')
  C:\Users\bokchee\Desktop\analysis\Triage\Workstation\2024-05-21T033012_triage_asset\C\Windows\prefetch\SVCHOST.EXE-B6F285B2.pf ==> (Invalid signature! Should be 'SCCA')

CSV output will be saved to C:\Users\bokchee\Desktop\analysis\Triage\Workstation\prefetch.csv
CSV time line output will be saved to C:\Users\bokchee\Desktop\analysis\Triage\Workstation\prefetch_Timeline.csv
```

The extracted CSV file can be analyzed using Timeline Explorer.

![[campfire-1_7.png]]

### 3-3. Problem Solving
#### Q1. Can you analyze the domain controller's security logs to determine the date and time the Kerberoasting activity occurred?

Event ID 4769 (TGS request log) is generated when a user requests a service ticket (TGS).
A Kerberoasting attack exploits this request to collect tickets and crack them offline.

To distinguish between normal TGS requests and malicious activity, consider the following:

- Exclude service name `krbtgt`: `krbtgt` is only for issuing tickets and is not related to TGS requests.
- Exclude service names ending in `$`: These are usually computer accounts, and Kerberoasting targets service accounts.
- Look for Ticket Encryption Type 0x17 (RC4-HMAC): Attackers prefer RC4-HMAC as it's easier to crack than AES.
- Look for Failure Code 0x0: This means the Kerberos request was successful.

Open the Domain Controller's Event Log with Event Log Explorer and apply a filter (Event ID = 4769).

![[campfire-1_4.png]]

Review the descriptions of the filtered logs to find one that meets the conditions.

![[campfire-1_5.png]]

A request for an `MSSQLService` ticket with RC4 encryption that succeeded (0x0) is likely the Kerberoasting attack.

![[campfire-1_6.png]]

The time of this log is: **2024-05-21 03:18:09**

#### Q2. What is the name of the target service?

Service Name identified in the log: **MSSQLService**

#### Q3. It is crucial to identify the workstation where this activity occurred. What is the workstation's IP address?

Client Address: 172.17.79.129

#### Q4. Now that the workstation has been identified, we provide you with analysis materials, including PowerShell logs and prefetch files, to help you gain a deeper understanding of how this activity occurred on the endpoint. What is the name of the file used to enumerate Active Directory objects and find Kerberoastable accounts on the network?

To check the PowerShell logs mentioned in the problem, you need to look for **Event ID 4104**.
After applying the filter and sorting by time ascending, you will get information about the PowerShell commands executed in chronological order.

The first command, `powershell -ep bypass`, suggests an attempt to allow subsequent script execution.

![[campfire-1_8.png]]

The second log contains a very long script. The repeated appearance of the string "Enum" suggests it is a script for Active Directory enumeration.

![[campfire-1_9.png]]

The last line, in particular, shows the path where the script was executed:
: `C:\Users\alonzo.spire\Downloads\powerview.ps1`

#### Q5. When was this script executed?

![[campfire-1_10.png]]

Check the XML value of the found log to confirm the time the event was recorded: **2024-05-21 03:16:32**

#### Q6. What is the full path of the tool used to perform the actual Kerberoasting attack?

Sort the extracted Prefetch data by time and analyze the files executed after the execution time of `powerview.ps1`.

![[campfire-1_11.png]]

A binary located in the user's Download folder stands out from the other executables:
: `C:\Users\alonzo.spire\Downloads\rubeus.exe`

Indeed, Rubeus is a tool used to perform attacks like Kerberoasting.

#### Q7. When was the credential-dumping tool (`rubeus.exe`) executed?

![[campfire-1_12.png]]

The execution time of `rubeus.exe` is **2024-05-21 03:18:08**.
