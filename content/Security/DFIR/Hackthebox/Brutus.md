---
Title: "HTB: Brutus"
date: 2025-05-09
tags: [wtmp, auth_log, linux]
Draft: False
---

## 1. Scenario Introduction

This scenario involves analyzing `auth.log` and `wtmp` logs from a Unix system.
The scenario sets up a situation where a Confluence server is attacked via a brute-force attack on its SSH service. We will explore how to trace the attacker's subsequent activities after gaining access to the server.
While `auth.log` is primarily used for analyzing brute-force attacks, we will investigate its potential for tracing various activities, including privilege escalation, persistence, and command execution.

#### 1-1. Related Technologies
- Unix log analysis
- `wtmp` file analysis
- Brute-force activity analysis
- Timeline creation
- Contextual analysis
- Post-compromise activity analysis

## 2. Background Knowledge
The artifacts used in this analysis are `wtmp` and `auth.log`. Let's explain the role of each log and how the information they contain can be used for analysis.

### 2-1. auth.log
The `auth.log` file primarily tracks authentication mechanisms. When a user attempts to log in, changes users, or performs any action requiring authentication (e.g., `sudo`), the activity is recorded in this log file. Such activities include those requiring authentication like `sshd`, `sudo`, and `cron` jobs.
- `sshd`: Remote login using the SSH protocol.
- `sudo`: Temporarily executes a single command with the privileges of another user (usually `root`).
- `cron`: Periodically performs specific actions using the Linux scheduling system.

#### 2-1-1. `auth.log` File Components
- Date and Time: The timestamp when the event occurred.
- Hostname: The hostname of the server where the event occurred.
- Service: The daemon that reported the event.
- PID: The process ID of the event.
- User: The username used in the authentication process.
- Authentication Status: A detailed description of the success or failure of the authentication attempt.
- IP Address/Hostname: The IP or hostname for remote connections.
- Message: A detailed description related to the event, including error messages or codes related to the authentication attempt.

```bash
Mar 10 10:23:45 exampleserver sshd[19360]: Failed password for invalid user admin from 192.168.1.101 port 22 ssh2
```
In the log above, there was an SSH connection attempt to the `admin` account on the server named `exampleserver` from the remote IP 192.168.1.101 on port 22, but it failed due to an incorrect password.

### 2-2. wtmp
The `wtmp` file records all login/logout events that have occurred on the system. Since `wtmp` is a binary file, it is not possible to view the logs directly with commands like `cat` or `more`. It is typically recorded in `/var/log/wtmp` and can be read with the `last` command.
※ Depending on the analysis OS environment, it may not be possible to read a `wtmp` file from another system with the `last` command. In this case, the log file can be extracted using [this Python script](https://gist.github.com/4n6ist/99241df331bb06f393be935f82f036a5).

#### 2-2-1. `wtmp` File Components
- Username: The user who logged in/out.
- Terminal: The terminal or remote connection (tty) name. For remote connections, this is usually related to SSH or telnet connections.
- IP Address/Hostname: For remote connections, the IP or hostname of the client that attempted the connection is recorded.
- Login Time: The time the login was attempted.
- Logout Time: The time recorded when the session ended.
- Duration: The duration the session was maintained.

```bash
sebh24 pts/0 192.168.1.100 Sat Mar 10 10:23 - 10:25 (00:02)
```
In the log above, a remote connection was made from 192.168.1.100 with the `sebh24` account, and the session was maintained for 2 minutes.

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `Brutus.zip` in the study materials and move it to your analysis OS: [brutus.zip](https://labs.hackthebox.com/api/v4/challenges/631/cdn/redirect?auth_user_id=1568173&expires=1750037397&signature=aa73346bd146e2caaddead24f87d4f1cbd05d6ae2d2e8a724e2ee5dc5aaddd10)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/brutus]
└─$ 7z x Brutus.zip 

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 5756 bytes (6 KiB)

Extracting archive: Brutus.zip
--
Path = Brutus.zip
Type = zip
Physical Size = 5756

Enter password (will not be echoed):
Everything is Ok

Files: 3
Size:       58201
Compressed: 5756


┌──(kali㉿kali)-[~/htb_sherlock/brutus]
└─$ ls
auth.log  Brutus.zip  utmp.py  wtmp
```

### 3-2. Initial Analysis
#### 3-2-1. `wtmp` File Analysis
Extract the `wtmp` log using the `utmp.py` script.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/brutus]
└─$ python utmp.py -o wtmp.out wtmp  


┌──(kali㉿kali)-[~/htb_sherlock/brutus]
└─$ ls
auth.log  Brutus.zip  utmp.py  wtmp  wtmp.out
```

The `wtmp.out` file created by the script can be viewed with commands like `cat` and `more`, unlike the binary `wtmp`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/brutus]
└─$ head wtmp.out                                            
"type"  "pid"   "line"  "id"    "user"  "host"  "term"  "exit"  "session"       "sec"   "usec"  "addr"
"BOOT_TIME"     "0"     "~"     "~~"    "reboot"        "6.2.0-1017-aws"        "0"     "0"     "0"     "2024/01/25 06:12:17"       "804944"        "0.0.0.0"
"INIT"  "601"   "ttyS0" "tyS0"  ""      ""      "0"     "0"     "601"   "2024/01/25 06:12:31"   "72401" "0.0.0.0"
"LOGIN" "601"   "ttyS0" "tyS0"  "LOGIN" ""      "0"     "0"     "601"   "2024/01/25 06:12:31"   "72401" "0.0.0.0"
"INIT"  "618"   "tty1"  "tty1"  ""      ""      "0"     "0"     "618"   "2024/01/25 06:12:31"   "80342" "0.0.0.0"
"LOGIN" "618"   "tty1"  "tty1"  "LOGIN" ""      "0"     "0"     "618"   "2024/01/25 06:12:31"   "80342" "0.0.0.0"
"RUN_LVL"       "53"    "~"     "~~"    "runlevel"      "6.2.0-1017-aws"        "0"     "0"     "0"     "2024/01/25 06:12:33"       "792454"        "0.0.0.0"
"USER"  "1284"  "pts/0" "ts/0"  "ubuntu"        "203.101.190.9" "0"     "0"     "0"     "2024/01/25 06:13:58"   "354674"    "203.101.190.9"
"DEAD"  "1284"  "pts/0" ""      ""      ""      "0"     "0"     "0"     "2024/01/25 06:15:12"   "956114"        "0.0.0.0"
"USER"  "1483"  "pts/0" "ts/0"  "root"  "203.101.190.9" "0"     "0"     "0"     "2024/01/25 06:15:40"   "806926"   "203.101.190.9"
```

Using the `sed` command and regular expressions, you can remove the quotes (") to make it more readable.
![[public/Images/content/Security/DFIR/BRUTUS/brutus_1.png]]

#### 3-2-2. `auth.log` File Analysis
The `auth.log` file can be read directly without any conversion.
![[public/Images/content/Security/DFIR/BRUTUS/brutus_2.png]]

### 3-3. Problem Solving
#### Q1. Analyze the `auth.log` file. What is the IP address from which the attacker launched the brute-force attack?

To find a brute-force attack in the `auth.log` file, you need to look for repeated instances of logs containing "Invalid user" and "Failed password" in a short period. This indicates frequent login failures (Incorrect Usernames or passwords) that occur during a brute-force attack.

![[public/Images/content/Security/DFIR/BRUTUS/brutus_3.png]]

As can be seen in the log above, `auth.log` shows numerous "Invalid user" and "Failed password" messages around Mar 6 06:31:31.
The source IP is consistently identified as `65.2.161.68`.

#### Q2. The brute-force attack was successful, and the attacker gained access to a specific account. What is that account?

A clue that the brute-force attack was successful can be found in the same logs. While the indicators for identifying a brute-force attack were the phrases "Invalid user" and "Failed password," a successful login is expected to show "Accepted password" or a similar phrase.

We check the last part of the logs originating from the previously identified attacker IP `65.2.161.68` using the `tail` command.

![[public/Images/content/Security/DFIR/BRUTUS/brutus_4.png]]

Two accounts show successful logins with the phrase "Accepted password": `root` and `cyberjunkie`.

#### Q3. Find the UTC timestamp when the attacker logged into the server directly and opened a terminal session. The login time is different from the previously confirmed authentication time. (Hint: Check the `wtmp` log)

The authentication time for the attacker's `root` account in the `auth.log` was Mar 6 06:32:44, but this is not the actual time the attacker connected. During a brute-force attack, the session is immediately terminated after finding valid credentials without opening a session.

You can find the time the attacker directly opened the `pts/1` terminal by searching for the attacker's IP in the `wtmp.out` log.
(You need to re-extract the logs with `TZ=UTC` included in the command to get the UTC time, separate from the previously extracted `wtmp.out`.)

![[public/Images/content/Security/DFIR/BRUTUS/brutus_5.png]]

The time the attacker (`65.2.161.68`) logged in as `root` and created a terminal is confirmed as `2024-03-06 06:32:45`.

#### Q4. SSH sessions are tracked, and each login is assigned a session number. What is the session number assigned to the attacker for the account identified in Q2?

The session number assigned through a remote login is stored in the `auth.log` file. Since logs related to session number assignment do not include the remote IP, they must be checked in conjunction with the remote login success logs. When authentication succeeds with an "Accepted password" log from a remote connection, a session is opened for that account immediately after. In the case below, we printed an additional 20 lines after the "Accepted password" phrase.

```bash
┌──(kali㉿kali)-[~/htb_sherlock/brutus]
└─$ cat auth.log | grep -A 20 "Accepted password"
```

![[public/Images/content/Security/DFIR/BRUTUS/brutus_6.png]]

From the log above, we can see that the attacker was assigned session number 37 and created a terminal.

#### Q5. The attacker created a new account on the server and granted it high privileges for persistence. What is that account?

Taking measures for persistence after a successful initial login is a common behavior. Since the `root` account is a common account with the highest system privileges, it receives a lot of attention and monitoring, making it risky. Therefore, we can observe a pattern of creating a new account with equivalent or sufficiently high privileges.

This behavior can also be observed in the logs confirmed in Q4.

```
Mar  6 06:34:18 ip-172-31-35-28 groupadd[2586]: group added to /etc/group: name=cyberjunkie, GID=1002
Mar  6 06:34:18 ip-172-31-35-28 groupadd[2586]: group added to /etc/gshadow: name=cyberjunkie
Mar  6 06:34:18 ip-172-31-35-28 groupadd[2586]: new group: name=cyberjunkie, GID=1002
Mar  6 06:34:18 ip-172-31-35-28 useradd[2592]: new user: name=cyberjunkie, UID=1002, GID=1002, home=/home/cyberjunkie, shell=/bin/bash, from=/dev/pts/1
Mar  6 06:34:26 ip-172-31-35-28 passwd[2603]: pam_unix(passwd:chauthtok): password changed for cyberjunkie
Mar  6 06:34:31 ip-172-31-35-28 chfn[2605]: changed user 'cyberjunkie' information
```

As seen in the log above, we can confirm that an account named `cyberjunkie` was created.

#### Q6. What is the MITRE ATT&CK sub-technique ID for the act of creating an account for persistence?

According to MITRE ATT&CK, this action corresponds to creating a local account for persistence, which is [T1136.001](https://attack.mitre.org/techniques/T1136/001/).

#### Q7. What time did the attacker's first session, as seen in `auth.log`, end?

By continuing to check the records in `auth.log` after the successful login record, we can find a message related to the session ending.

![[public/Images/content/Security/DFIR/BRUTUS/brutus_7.png]]

According to the log, the session ended at `2024-03-06 06:37:24`.

#### Q8. After logging in with the backdoor account, the attacker uses high privileges to download a script. What command was executed for this?

The persistence backdoor account identified earlier is `cyberjunkie`. We check the actions performed by this account in `auth.log`.

![[public/Images/content/Security/DFIR/BRUTUS/brutus_8.png]]

As can be seen in the log above, the attacker used the `/usr/bin/curl` command to download a script from `https://raw.githubusercontent.com/montysecurity/linper/main/linper.sh`.

`linper.sh` is a script for maintaining persistence on Linux systems.
