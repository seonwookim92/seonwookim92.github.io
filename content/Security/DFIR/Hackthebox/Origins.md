---
Title: "HTB: Origins"
date: 2025-05-27
tags: [pcap, wireshark, ftp]
Draft: False
---

## 1. Scenario Introduction

A significant security incident recently occurred at Forela. Approximately 20GB of data was stolen from an internal S3 bucket, and the attackers are now blackmailing Forela.
During the root cause analysis, an FTP server was suspected as the starting point of the attack. The investigation revealed that this server was also compromised, some data was exfiltrated from it, and this led to further breaches throughout the environment.
You have been provided with a minimal PCAP file.
Your goal is to find evidence of a brute force attack and data exfiltration.

#### 1-1. Related Technologies
- Network Packet Analysis
- Wireshark, PCAP Utilization
- FTP Protocol

## 2. Background Knowledge

### 2-1. What is a PCAP file?
- **Packet Capture** file: A file that stores network traffic.
- Can be analyzed using tools like **Wireshark**.
- Allows for tracking requests/responses at the packet level.

### 2-2. FTP (File Transfer Protocol)
- Used to **upload/download** files to a server.
- Communicates in plaintext (unencrypted) → easy to analyze.
- Key commands:
    - `USER`, `PASS`: Login
    - `RETR <filename>`: Download a file
    - `STOR <filename>`: Upload a file

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `Origins.zip` in the study materials and move it to your analysis OS: [Origins.zip](https://labs.hackthebox.com/api/v4/challenges/869/cdn/redirect?auth_user_id=1568173&expires=1750207379&signature=91ac619e2553f0318b16c8dd08e5f3d92095911be2eb16c5e20c87db94ed8a8c)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/Origins]
└─$ 7z x Origins.zip    

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 40178 bytes (40 KiB)

Extracting archive: Origins.zip
--
Path = Origins.zip
Type = zip
Physical Size = 40178

    
Enter password (will not be echoed):
Everything is Ok

Size:       77250
Compressed: 40178



┌──(kali㉿kali)-[~/htb_sherlock/Origins]
└─$ ls
ftp.pcap  Origins.zip



┌──(kali㉿kali)-[~/htb_sherlock/Origins]
└─$ file ftp.pcap 
ftp.pcap: pcap capture file, microsecond ts (little-endian) - version 2.4 (Ethernet, capture length 262144)
```

### 3-2. Initial Analysis
#### 3-2-1. Skimming the pcap file
The provided file is a pcap file. This means it is a capture of network traffic and its contents can be viewed using tools like Wireshark or tcpdump.

This time, we will use Wireshark. After opening Wireshark, instead of capturing new traffic, you can open the pcap file via "Open".

![[origins_1.png]]

The initial information provided is that an FTP server is suspected as the starting point of the attack.
Based on this, we add "ftp" to the Wireshark filter.

Some logs are visible, and a significant portion appears to be login attempts. Most seem to fail with a "Login incorrect" message, but there is one instance that appears to succeed with a "Login successful" message.

![[origins_2.png]]

#### 3-2-2. Auxiliary Data Analysis

Let's use the auxiliary analysis tools provided by Wireshark to get an overall picture of the pcap file.

First is "Conversations". This analysis shows how much data was exchanged, broken down by protocol and host.

![[origins_3.png]]

It shows that the most communication was with the IP 15.206.185.207. While communication with other hosts remains at the byte level, a relatively large amount of data (in kB) was exchanged with this IP. Since the volume is not huge, it seems that mostly text-based files or strings were exchanged.

### 3-3. Problem Solving
#### Q1. What is the attacker's IP address?

As confirmed in the initial analysis, it appears that the IP 15.206.185.207 gained FTP service login credentials through a small-scale brute-force attack.

![[origins_2.png]]

#### Q2. Even if the accuracy is low, it is important to get more information about the attacker. Check the location information based on the IP. What city is it located in?

Several websites offer services to check location information based on IP. While not entirely reliable, it can be used as a reference.

![[origins_4.png]]

A check on [ipinfo](https://ipinfo.io) shows that the IP is located in Mumbai.

#### Q3. What FTP application was used as the backup server?

If you "Follow TCP Stream" on a packet from the FTP protocol, the entire stream is displayed.

![[origins_5.png]]

The banner that appears at the very beginning shows the FTP application version: `vsFTPd 3.0.5`

#### Q4. When did the attacker start the brute-force attack?

The Time column, which was previously displayed as Relative Time, can be changed in the "View - Time Display Format" menu.

![[origins_6.png]]

![[origins_7.png]]

The attack started at 2024-05-03 04:12:54 UTC.

#### Q5. What are the credentials the attacker successfully used to authenticate through the brute-force attack?

If you "Follow TCP Stream" on the packet containing the "Login successful" string, the associated packet stream will be displayed. This includes the valid credentials.

![[origins_9.png]]

The credentials the attacker used to successfully log in: `forela-ftp:ftprocks69$`

#### Q6. What command did the attacker use to download files from the FTP server for data exfiltration?

![[origins_10.png]]

It appears the attacker used the `RETR` command to download documents.

#### Q7. The attacker obtained credentials from the FTP server to access a backup SSH server. What is the password?

It appears the attacker used the `RETR` command to download the files `Maintenance-Notice.pdf` and `s3_buckets.txt`.

These files can be extracted via the "File - Export Objects - FTP-DATA" menu.

![[origins_11.png]]

![[origins_12.png]]

The two files identified earlier appear as extractable files.
The PDF file contains the password for the backup server.

![[origins_13.png]]

The password revealed in the document is: `**B@ckup2024!**`

#### Q8. What is the S3 bucket address that has been in use since 2023?

This information can be found in the other file, `s3_bucket.txt`.

![[origins_14.png]]

S3 bucket address: `https://2023-coldstorage.s3.amazonaws.com`

#### Q9. The scope of the incident is quite large. Forela's S3 bucket was also breached, and several GB of data were stolen and exfiltrated. It was also revealed that the attackers used social engineering to access sensitive data and use it for extortion. What is the internal email address used in the phishing email to access the sensitive data stored in the S3 bucket?

Email address found in the text file: `archivebackups@forela.co.uk`
