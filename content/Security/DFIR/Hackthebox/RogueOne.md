---
Title: "HTB: RogueOne"
date: 2025-06-02
tags: [windows, volatility]
Draft: False
---

## 1. Scenario Introduction

Forela's SIEM (Security Information and Event Management) system generated multiple alerts in less than a minute, indicating potential C2 (Command and Control) communication from Simon Stark's workstation. Simon himself did not notice anything unusual, but the IT team was asked for a screenshot of the Task Manager to check for abnormal processes. However, no suspicious processes were found. Despite this, the alerts for C2 communication continued, prompting the SOC manager to immediately isolate the workstation and collect a memory dump.

As a memory forensics expert, you must assist Forela's SOC team in investigating and resolving this urgent security incident.

#### 1-1. Related Technologies
- Volatility Memory Analysis

## 2. Background Knowledge
TBA

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `RogueOne.zip` in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ 7z x RogueOne.zip 

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 1368047191 bytes (1305 MiB)

Extracting archive: RogueOne.zip
--
Path = RogueOne.zip
Type = zip
Physical Size = 1368047191
64-bit = +
Characteristics = Zip64

    
Enter password (will not be echoed):
Everything is Ok   

Size:       5368709120
Compressed: 1368047191



┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ ls
20230810.mem  RogueOne.zip
```

### 3-2. Initial Analysis
#### 3-2-1. Image Information

```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ vol -f 20230810.mem windows.info     
Volatility 3 Framework 2.26.0

...

Kernel Base     0xf80178400000
DTB     0x16a000
Symbols file:///home/kali/.local/share/pipx/venvs/volatility3/lib/python3.13/site-packages/volatility3/symbols/windows/ntkrnlmp.pdb/3789767E34B7A48A3FC80CE12DE18E65-1.json.xz
Is64Bit True
IsPAE   False
layer_name      0 WindowsIntel32e
memory_layer    1 FileLayer
KdVersionBlock  0xf8017900f398
Major/Minor     15.19041
MachineType     34404
KeNumberProcessors      8
SystemTime      2023-08-10 11:32:00+00:00
NtSystemRoot    C:\WINDOWS
NtProductType   NtProductWinNt
NtMajorVersion  10
NtMinorVersion  0
PE MajorOperatingSystemVersion  10
PE MinorOperatingSystemVersion  0
PE Machine      34404
PE TimeDateStamp        Mon Nov 24 23:45:00 2070
```

### 3-3. Problem Solving
#### Q1. Identify the malicious process and its Process ID.

```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ vol -f 20230810.mem windows.malfind
... (output omitted for brevity)
6812    svchost.exe     0x1b0000        0x1e1fff        VadS    PAGE_EXECUTE_READWRITE  50      1       Disabled  MZ header
...
```

**Malicious Process PID: 6812**

#### Q2. The SOC team believes this malicious process may have spawned another process to allow the attacker to execute commands. What is the Process ID of that child process?

```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ vol -f 20230810.mem windows.pstree  
...
*** 6812        7436    svchost.exe     ...
**** 4364       6812    cmd.exe ...
***** 9204      4364    conhost.exe     ...
...
```

**Spawned Child Process PID: 4364**

#### Q3. The reverse engineering team needs a sample of the malicious file for analysis. The SOC manager has instructed you to find the hash of the file and pass it to the reverse engineering team. What is the MD5 hash of the malicious file?

```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ vol -f 20230810.mem -o dump_6812 windows.dumpfiles --pid 6812
...
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne/dump_6812]
└─$ md5sum file.0x9e8b91ec0140.0x9e8b957f24c0.ImageSectionObject.svchost.exe.img
5bd547c6f5bfc4858fe62c8867acfbb5  file.0x9e8b91ec0140.0x9e8b957f24c0.ImageSectionObject.svchost.exe.img
```

MD5 Hash: 5bd547c6f5bfc4858fe62c8867acfbb5

#### Q4. To understand the scope of the incident, the SOC manager has dispatched the threat hunting team to scour the environment for indicators of compromise. It would be a great help to our team if you could identify the C2 IP address and port.

```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ vol -f 20230810.mem  windows.netscan | grep 6812
0x9e8b8cb58010.0TCPv4   172.17.79.131can64254fin13.127.155.166  8888    ESTABLISHED     6812    svchost.exe     2023-08-10 11:30:03.000000 UTC
```

**IP:PORT: 13.127.155.166:8888**

#### Q5. We need a timeline to understand the scope of the incident and help the DFIR team perform a root cause analysis. Can you confirm when the process was executed and the C2 channel was established?

**10/08/2023 11:30:03**

#### Q6. What is the memory offset of the malicious process?

```bash
┌──(kali㉿kali)-[~/htb_sherlock/RogueOne]
└─$ vol -f 20230810.mem  windows.psscan | grep 6812 
6812    7436    svchost.exe     0x9e8b87762080  ...
```

**Offset: 0x9e8b87762080**

#### Q7. You have been praised by your manager for successfully analyzing the memory dump. The next day, your manager asks for an update on the malicious file. You check VirusTotal and see that the file has already been uploaded, likely by the reverse engineering team. Now you need to find out when the sample was first submitted to VirusTotal.

![[public/Images/content/Security/DFIR/ROGUEONE/rogueone_1.png]]

**10/08/2023 11:58:10**
