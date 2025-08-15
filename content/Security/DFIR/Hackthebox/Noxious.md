---
Title: "HTB: Noxious"
date: 2025-05-25
tags: [windows, activedirectory, llmnr, pcap]
Draft: False
---

## 1. Scenario Introduction

An alert from an IDS device has indicated a suspected malicious device on the internal Active Directory network. Additionally, the IDS showed signs of unusual LLMNR traffic, raising the possibility of an LLMNR poisoning attack. The LLMNR traffic was directed to Forela-WKstn002 (IP address 172.17.79.136), and a limited packet capture from that time frame has been provided. This incident appears to have occurred on the Active Directory VLAN, and it is recommended to conduct a network threat hunt focusing on LLMNR poisoning with Active Directory attack vectors in mind.

#### 1-1. Related Technologies
- LLMNR Poisoning Attack
- PCAP File Analysis

## 2. Background Knowledge

### 2-1. LLMNR Poisoning Attack
An LLMNR (Link-Local Multicast Name Resolution) attack primarily occurs in a local network environment and exploits the network's name resolution service to steal a victim's information. LLMNR is similar to DNS (Domain Name System) but is a name resolution protocol that only operates on the local network, used when a DNS server is unavailable or not in use.

**Key Aspects of an LLMNR Attack**
1.  **How LLMNR Works**:
    - LLMNR is used for name resolution on a local network, converting the name of a host whose IP address is unknown into an IP address.
    - If an attacker is on the local network, they can intercept or respond to another host's name resolution request, providing a false IP address.
2.  **Attack Scenario**:
    - The attacker intercepts an LLMNR request and sends a response, impersonating the requested host.
    - The victim trusts the malicious response and attempts to communicate with that IP address, allowing the attacker to intercept the traffic or deliver malicious code.
3.  **Primary Targets**:
    - LLMNR attacks are primarily executed on local networks and can be exploited to steal SMB (file sharing) and authentication information (NTLM).
    - User authentication information can be easily stolen via LLMNR in a Windows environment.
4.  **Effects of the Attack**:
    - By manipulating network name resolution requests, an attacker can intercept user or system authentication information.
    - A network attacker can steal a victim's login information or session cookies.
    - Sensitive information can be stolen by intercepting network traffic through a Man-in-the-Middle (MITM) or redirect attack.

**How to Analyze an LLMNR Attack in Wireshark**:
Wireshark is a tool that can capture and analyze network packets, and it can be used to detect LLMNR attacks. Here is how to analyze an LLMNR attack in Wireshark:
1.  **Filter LLMNR Packets**:
    - LLMNR uses UDP port 5355 by default.
    - To filter LLMNR-related packets in Wireshark, enter `udp.port==5355` in the filter bar.
2.  **Analyze LLMNR Request and Response Packets**:
    - LLMNR Request Packet:
        - You can find "LLMNR Request" messages. These packets typically contain a "query" record with the requested name.
        - When a request comes in, the attacker intercepts it and sends a response.
    - LLMNR Response Packet:
        - Look for "LLMNR Response" packets. If an attacker sends a response, they can reply with an incorrect IP address.
        - If the IP address in the response packet does not exist in the actual network environment or is a malicious IP address, this is a sign of an attack.
3.  **Check the Timeline**:
    - By tracing the timeline of requests and responses in Wireshark, you can identify a pattern of the attacker responding quickly.
    - If the timeline is unusually short or does not match other normal response patterns, it should be considered suspicious.
4.  **Identify the Unique Attacker IP**:
    - By analyzing the responding packets, you can identify the attacker's IP address.
    - Compare it with the IP of the server providing normal responses to identify the suspicious IP.
5.  **Check for DNS or SMB Authentication-Related Traffic**:
    - After an LLMNR attack, you can look for signs of authentication information leakage by examining the DNS or SMB traffic on the network.
    - NTLM hashes or login information contained in SMB traffic may appear in the packets, so analyze them.
6.  **Detailed Packet Analysis**:
    - Analyze the "Name Query" section of the LLMNR packet to compare the requested name and the responded IP address.
    - This can help determine if the packet was exploited.

## 3. Analysis

### 3-1. Download Evidence File
1. Open the link below in a browser to download the file, or find `noxious.zip` in the study materials and move it to your analysis OS: [noxious.zip](https://labs.hackthebox.com/api/v4/challenges/747/cdn/redirect?auth_user_id=1568173&expires=1751591599&signature=1e121947a96d79963be7a9914fc381f838262e392cb4b0b48eda9660dc2871de)
2. Use `7z` to extract the archive. The password is `hacktheblue`.
```bash
┌──(kali㉿kali)-[~/Downloads]
└─$ 7z x noxious.zip 

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29
 64-bit locale=en_US.UTF-8 Threads:2 OPEN_MAX:1024, ASM

Scanning the drive for archives:
1 file, 135790571 bytes (130 MiB)

Extracting archive: noxious.zip
--
Path = noxious.zip
Type = zip
Physical Size = 135790571

    
Enter password (will not be echoed):
Everything is Ok   

Size:       137211904
Compressed: 135790571
```

### 3-2. Problem Solving
#### Q1. The security team suspects there is a malicious device on the Forela internal network running a responder tool to perform an LLMNR poisoning attack. What is the malicious IP address of that device?

In Wireshark, filter for `udp.port==5355` and examine the resulting packets.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_1.png]]

You can see that all LLMNR Standard query responses are coming from one IP (172.17.79.135).

Based on this, the malicious IP address performing the LLMNR poisoning attack is 172.17.79.135.

#### Q2. What is the hostname of the malicious computer?

Add a filter for the identified IP address and DHCP packets: `ip.addr==172.17.79.135 and dhcp`.
Due to the nature of the DHCP protocol, a device sends its hostname to the DHCP server, so the hostname information can be exposed there.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_2.png]]

Hostname: kali

#### Q3. Now we need to see if the attacker intercepted a user hash and if it is crackable!! What is the username whose hash was intercepted?

Due to the nature of LLMNR poisoning attacks, NTLM authentication is performed using the SMB protocol immediately after the poisoning.
To find this, apply the filter `smb2 and ntlmssp`.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_3.png]]

Several NTLM authentications are identified, and the username can be found in the Info tab.
: john.deacon

#### Q4. We can see that the victim's credentials were passed to the attacker's machine multiple times in the NTLM traffic. When was the hash first captured?

The earliest timestamp among the NTLM authentication packets: 2024-06-24 11:18:30

#### Q5. What is the typo that caused the credentials to be leaked, which the victim made when trying to navigate to a file share?

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_4.png]]

The typo that would cause a switch from the DNS protocol to LLMNR, enabling the poisoning, can be found by examining the packet details. The typo is: **DCC01**

#### Q6. To get the victim user's actual credentials, we need to concatenate several values from the NTLM negotiation packet. What is the NTLM Server Challenge value?

Further investigation of the same packet reveals the NTLM Server Challenge value.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_5.png]]

Server Challenge value: 601019d191f054f1

#### Q7. Now perform a similar action to find the NTProofStr value.

This time, examine the details of the very next AUTH packet to find the NTProofStr.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_6.png]]

NTProofStr value: c0cc803a6d9fb5a9082253a04dbd4cd4

#### Q8. To test the password complexity, try to recover the password with the information found in the packet capture. This is a crucial step to see if the attacker cracked the password and how fast.

To crack with Hashcat, you need to restore the actual hash value. The format to fill in is: `User::Domain:ServerChallenge:NTProofStr:NTLMv2Response`

All other values have already been obtained, and the NTLMv2Response value can be easily obtained by copying the Hex Stream Dump, excluding the first 32 bytes (NTProofStr).

Reconstructing based on this gives:

```
john.deacon::FORELA:601019d191f054f1:c0cc803a6d9fb5a9082253a04dbd4cd4:010100000000000080e4d59406c6da01cc3dcfc0de9b5f2600000000020008004e0042004600590001001e00570049004e002d00360036004100530035004c003100470052005700540004003400570049004e002d00360036004100530035004c00310047005200570054002e004e004200460059002e004c004f00430041004c00030014004e004200460059002e004c004f00430041004c00050014004e004200460059002e004c004f00430041004c000700080080e4d59406c6da0106000400020000000800300030000000000000000000000000200000eb2ecbc5200a40b89ad5831abf821f4f20a2c7f352283a35600377e1f294f1c90a001000000000000000000000000000000000000900140063006900660073002f00440043004300300031000000000000000000
```

Now, crack this with Hashcat.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_7.png]]

Cracked password: `NotMyPassword0k?`

#### Q9. To get more context on the incident, what was the file share the victim was actually trying to navigate to?

By checking the SMB2 traffic, you can easily find the share the connection was attempting to.

![[public/Images/content/Security/DFIR/NOXIOUS/noxious_8.png]]

File share name: `\\DC01\DC-Confidential`
