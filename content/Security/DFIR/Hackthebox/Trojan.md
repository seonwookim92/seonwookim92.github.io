---
Title: "HTB: Trojan"
date: 2025-06-06
tags: [windows, pcap, volatility]
Draft: False
---

## 1. Scenario Introduction

While deleting old accounting documents, John Grunewald accidentally deleted an important document he was working on. In a panic, he downloaded recovery software to restore the document, but after installation, his PC began to act strangely. Feeling even more discouraged and depressed, he reported it to the IT department, who immediately locked down the workstation and secured some evidence. It is now your job to analyze the evidence to understand what happened on John's workstation.

#### 1-1. Related Technologies
- TBA

## 2. Background Knowledge
TBA

### 2-1. Background Knowledge
TBA

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `Trojan.zip` in the study materials and move it to your analysis OS: [Trojan.zip](...)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
![[public/Images/content/Security/DFIR/TROJAN/trojan_1.png]]

### 3-2. Initial Analysis
#### 3-2-1. Artifact Types
There are a total of 3 types of artifacts included.
- disk artifacts: Contains disk imaging files for analyzing the file system, etc.
- memory capture: A dump of records stored in volatile memory (RAM) for analyzing recent activities.
- packet capture: To check communication records through network packets.

### 3-3. Problem Solving
#### Q1. What is the build version of the target system's operating system?

By using Volatility on the memory file and checking the `windows.info` value, we can find the build information.

![[public/Images/content/Security/DFIR/TROJAN/trojan_2.png]]

| Item                                       | Description                                                                                             |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| **Kernel Base**                            | The starting address where the kernel is loaded in memory: `0xf8073e400000`                               |
| **DTB**                                    | Directory Table Base, the page directory address used to map process address space (MMU related): `0x1ad000` |
| **Symbols**                                | The path to the symbol file used, the PDB file matching the kernel of the system being analyzed.          |
| **Is64Bit**                                | Whether it is a 64-bit operating system: `True` (64-bit system)                                           |
| **IsPAE**                                  | Whether PAE (Physical Address Extension) is used: `False` (not used)                                      |
| **layer_name**                             | The name of the layer used for memory analysis: `WindowsIntel32e` (Intel format for 64-bit Windows)       |
| **memory_layer**                           | Identifier for the memory layer (VmwareLayer: likely a memory image extracted from VMware)                |
| **base_layer** / **meta_layer**            | Indicates the actual storage location of the original memory dump (`FileLayer`)                           |
| **KdVersionBlock**                         | The address of the kernel version information block for debugging                                         |
| **Major/Minor**                            | Windows OS build number: `15.19041` (likely Windows 10, version 2004)                                     |
| **MachineType**                            | Architecture type: `34404` = `AMD64` (x64)                                                                |
| **KeNumberProcessors**                     | Number of CPU cores: `2`                                                                                  |
| **SystemTime**                             | The time the memory dump was created: `2023-05-30 02:09:03 UTC`                                           |
| **NtSystemRoot**                           | Windows system root path: `C:\Windows`                                                                   |
| **NtProductType**                          | Operating system type: `NtProductWinNt` (Windows for workstations or desktops)                            |
| **NtMajorVersion / NtMinorVersion**        | OS major/minor version: `10.0` (Windows 10)                                                               |
| **PE MajorOperatingSystemVersion / Minor** | OS version information from the executable (kernel) (based on PE header): `10.0`                          |
| **PE Machine**                             | Machine type in the PE header: `34404` (x64)                                                              |
| **PE TimeDateStamp**                       | Kernel binary build time: `January 4, 1995` → **An unusually old value**, which can occur if kernel symbols are incorrect or debugging information is missing. |

Therefore, the build version is 19041.

#### Q2. What is the PC Hostname?

There are two ways to find the hostname:
- Check the value in the registry at `HKLM\SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName`.
- Check traffic like NBNS, LLMNR, DHCP in the PCAP file.

Let's first check the PCAP file, which is easier to check.

![[public/Images/content/Security/DFIR/TROJAN/trojan_3.png]]

Fortunately, we can find the hostname in the NBNS traffic: DESKTOP-38NVPD0

#### Q3. What is the name of the downloaded ZIP file?

In Wireshark, go to `File → Export Objects → HTTP` and apply a text filter for "zip".

![[public/Images/content/Security/DFIR/TROJAN/trojan_4.png]]

Filename: Data_Recovery.zip

#### Q4. What is the domain of the website from which this file was downloaded?

From the previously checked record, we can identify the source domain of the download.
: `praetorial-gears.000webhostapp.com`

#### Q5. The user then ran a suspicious application extracted from the ZIP file. What is its process ID?

Since a process is created while the system is running, we need to analyze the memory.
Using Volatility's `windows.pstree` module and searching for the archive name "data_recovery" yields significant results.

![[public/Images/content/Security/DFIR/TROJAN/trojan_5.png]]

The process ID where `Recovery_Setup.bat` was executed: 484

#### Q6. What is the full path of the suspicious process?

Process path: `C:\Users\John\Downloads\Data_Recovery\Recovery_Setup.exe`

#### Q7. What is the SHA-256 hash of the suspicious executable?

We can view the actual file by opening the disk imaging file with FTK Imager.

![[public/Images/content/Security/DFIR/TROJAN/trojan_6.png]]

After exporting the file, we can get the hash value using PowerShell's `Get-FileHash` function.

![[public/Images/content/Security/DFIR/TROJAN/trojan_7.png]]

The extracted SHA256 hash value is: `C34601C5DA3501F6EE0EFCE18DE7E6145153ECFAC2CE2019EC52E1535A4B3193`

#### Q8. What time was the malicious program executed?

Export the entire `C:\Windows\Prefetch` folder using FTK Imager.
Then, use `PECmd.exe` to extract it as a CSV file for analysis.

```bash
PS C:\Users\bokchee\Desktop\EZ tools > .\PECmd.exe -d "C:\Users\bokchee\Desktop\analysis\disk artifacts\prefetch\Prefetch" --csv "C:\Users\bokchee\Desktop\analysis" --csvf prefetch.csv
```

Then, open the CSV file with Timeline Explorer and check the "Source Created" field.

![[public/Images/content/Security/DFIR/TROJAN/trojan_8.png]]

The value of this field is 2023-05-30 02:06:39. Considering that Prefetch records are created 10 seconds after a program is executed, the actual execution time is 2023-05-30 02:06:29.

#### Q9. How many times was the malicious application executed?

![[public/Images/content/Security/DFIR/TROJAN/trojan_9.png]]

The same log has an entry called `RUN_COUNT`. This value indicates the number of times the application was executed.

`RECOVERY_SETUP.EXE` appears to have been executed 2 times.

#### Q10. The malicious application references two `.TMP` files. One is `IS-NJBAT.TMP`, what is the other one?

```bash
PS C:\Users\bokchee\Desktop\analysis\memory capture > strings .\memory.vmem | Select-String ".tmp"

...
\Device\HarddiskVolume3\Users\John\AppData\Local\Temp\is-T97VD.tmp\is-R7RFP.tmp
\Device\HarddiskVolume3\Users\John\AppData\Local\Temp\is-VIBV9.tmp\is-NJBAT.tmp
```

| Honestly, I don't know how this was done... need to check later.

#### Q11. How many of the URLs accessed by the malicious application are listed as malicious on VirusTotal?

![[public/Images/content/Security/DFIR/TROJAN/trojan_10.png]]

When checking all traffic from the victim PC (192.168.116.133) to the outside, apart from the connection attempt to 45.12.253.75, the rest appears to be normal web activity.

The URLs identified here are:
```
http://45.12.253.75/advertising/plus.php
http://45.12.253.72/default/stuk.php
http://45.12.253.72/default/puk.php
http://45.12.253.75/dll.php
```

The results are as follows:

![[public/Images/content/Security/DFIR/TROJAN/trojan_11.png]]

![[public/Images/content/Security/DFIR/TROJAN/trojan_12.png]]
(Also malicious when changing the address to .72)

![[public/Images/content/Security/DFIR/TROJAN/trojan_13.png]]
(Also malicious when changing the address to .72)

![[public/Images/content/Security/DFIR/TROJAN/trojan_14.png]]

A total of 4 URLs are listed as malicious.

#### Q12. The malicious application downloaded a binary file from a C2 URL. What is the name of that file?

Among the php files received from the C2 address, the `puk.php` file, when extracted and examined, can be confirmed not to be an actual php file.

![[public/Images/content/Security/DFIR/TROJAN/trojan_15.png]]

![[public/Images/content/Security/DFIR/TROJAN/trojan_16.png]]

#### Q13. Can you find any clues about the legitimate file the malicious file is trying to impersonate?

| In other solutions, it is said that a banner can be checked on VirusTotal, etc., but this file is encrypted and cannot be checked directly, and the banner could not be confirmed.

FinalRecovery v3.0.7.0325
