---
Title: "HTB: Noted"
date: 2025-05-23
tags: [windows, application_log, notepad]
Draft: False
---

## 1. Scenario Introduction

Simon, a developer at Forela, found a note on his workstation desktop stating, "The system has been compromised, and critical data has been collected," and reported it to the CERT team. The hacker claims to have exfiltrated data and threatens to leak it on the dark web if their demands are not met. The compromised workstation contains critical materials, including project plans, internal development documents, and the codebase.
The CERT team has isolated the workstation for forensic analysis and believes there are signs of direct system manipulation by the attacker. While there is currently no direct means of contacting the threat actor, the threat intelligence team believes the attacker made some mistakes.
The scope of the investigation is limited to Notepad++ related artifacts, which must be analyzed to determine the attack path and trace a means of contact from the threat actor's mistakes. Data exfiltration must be prevented at all costs, and the protection and recovery of all possible critical data are required.

#### 1-1. Related Technologies
- Application Log Analysis

## 2. Analysis

### 2-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `Noted.zip` in the study materials and move it to your analysis OS: [filename](link)
2. Use `7z` to extract the archive. The password is `hacktheblue`.

### 2-2. Initial Analysis
#### 2-2-1. Initial Analysis

![[public/Images/content/Security/DFIR/NOTED/noted_1.png]]

The provided evidence only contains the file list under `C:\Users\Simon.start\AppData\Roaming\Notepad++`.

This path can be useful for tracking user activity and identifying traces of an attack, as it contains user settings and recent work history for Notepad++.

Here is information on the key files:
- sessions.xml : Stores information about open tabs when Notepad++ was closed (file path, cursor position).
- config.xml : Stores configuration settings (user interface, recent file list, etc.).
- backup\ folder : Backup copies of auto-saved files.

### 2-3. Problem Solving
#### Q1. What is the full path of the script Simon uses for his AWS tasks?

Opening the `config.xml` file shows a list of recently opened files at the top.

![[public/Images/content/Security/DFIR/NOTED/noted_2.png]]

The last file in the history appears to be a script related to AWS services, judging by its name.

`C:\Users\Simon.stark\Documents\Dev_Ops\AWS_objects migration.pl`

#### Q2. The attacker, knowing the victim is a SWE and has the necessary utilities, deliberately cloned program code and compiled it on the system. This code is involved in collecting and exfiltrating sensitive data. What is the full path of the file?

This time, we can find the path of the file opened by the attacker in the `session.xml` file.
There are also two files in the `Backup\` path.

![[public/Images/content/Security/DFIR/NOTED/noted_3.png]]

Let's examine the contents of the `LootAndPurge.java` file.

```java
public static void main(String[] args) {
	String username = System.getProperty("user.name");
	String desktopDirectory = "C:\\Users\\" + username + "\\Desktop\\";
	List<String> extensions = Arrays.asList("zip", "docx", "ppt", "xls", "md", "txt", "pdf");
	List<File> collectedFiles = new ArrayList<>();
	
	collectFiles(new File(desktopDirectory), extensions, collectedFiles);
	
	String zipFilePath = desktopDirectory + "Forela-Dev-Data.zip";
	String password = "sdklY57BLghvyh5FJ#fion_7";
	
	createZipArchive(collectedFiles, zipFilePath, password);
	
	System.out.println("Zip archive created successfully at: " + zipFilePath);
}

private static void collectFiles(File directory, List<String> extensions, List<File> collectedFiles) {
	File[] files = directory.listFiles();
	if (files != null) {
		for (File file : files) {
			if (file.isDirectory()) {
				collectFiles(file, extensions, collectedFiles);
			} else {
				String fileExtension = getFileExtension(file.getName());
				if (extensions.contains(fileExtension)) {
					collectedFiles.add(file);
				}
			}
		}
	}
}
```

Based on the content of the main function, the attacker intends to collect files with various extensions from the user's Desktop path, compress them into a `Forela-Dev-Data.zip` file, and protect it with the password `sdklY57BLghvyh5FJ#fion_7`. This behavior suggests it is a malicious file for data exfiltration.

The full path of this file can be found within the `session.xml` file.

![[public/Images/content/Security/DFIR/NOTED/noted_4.png]]

File path: `C:\Users\Simon.stark\Desktop\LootAndPurge.java`

#### Q3. What is the name of the final archive file that contains all the data to be exfiltrated?

As analyzed above, the exfiltrated files are compressed into a file named `Forela-Dev-Data.zip`.

#### Q4. What is the UTC timestamp of the last modification of the program source file by the attacker?

Checking the `session.xml` file, we can find several clues to guess the time:
- backupFilePath : `LootAndPurge.java@2023-07-24_145332`
- originalFileLastModifTimestamp : -1354503710
- originalFileLastModifTimestampHigh : 31047188

Among these, we can use originalFileLastModifTimestamp and originalFileLastModifTimestampHigh to convert to UTC time.

https://community.notepad-plus-plus.org/topic/22662/need-explanation-of-a-few-session-xml-parameters-values/6
 The post above explains how to convert the time.

Based on this, a Python code can be created as follows:

```python
high = 31047188
low = -1354503710
full_value = high * 2**32 + (2**32 + low)
= 31047188 * 4294967296 + (4294967296 -1354503710)
= 133346660033227234
```

The resulting value can be converted to UTC time [online](https://www.epochconverter.com/ldap).

![[public/Images/content/Security/DFIR/NOTED/noted_5.png]]

Therefore, the last file modification time is **2023-07-24 09:53:23**.

#### Q5. After exfiltrating the data, the attacker wrote a data extortion message. What is the cryptocurrency wallet address the attacker demanded payment to?

Checking the attacker's last message, `YOU HAVE BEEN HACKED.txt`, reveals the message.

![[public/Images/content/Security/DFIR/NOTED/noted_6.png]]

At the bottom of the message, there are URLs that are all password-protected. They can be unlocked with the ZIP file password found in the Java code (`sdklY57BLghvyh5FJ#fion_7`).

The confirmed message is as follows:

```
If you are here then you have no other choice then to pay us. Your Sensitive DATA is in our hands and we WILL release it to PUBLIC by midnight if you don't pay us a ransom. 

We want 50000 $ in ETH currency by midnight. This amount is very reasonable as we know FORELA is a multi million dollar company, but since we were able to extort small amount of data, this is our final offer. 

Ethereum wallet : 0xca8fa8f0b631ecdb18cda619c4fc9d197c8affca

Person of contact :  CyberJunkie@mail2torjgmxgexntbrmhvgluavhj7ouul5yar6ylbvjkxwqf6ixkwyd.onion
```

#### Q6. What is the attacker's email address?

`CyberJunkie@mail2torjgmxgexntbrmhvgluavhj7ouul5yar6ylbvjkxwqf6ixkwyd.onion`
