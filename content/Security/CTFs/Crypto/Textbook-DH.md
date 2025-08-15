---
title: "Dreamhack: Textbook-DH"
date: 2025-08-15
tags:
  - crypto
  - ctf
  - diffie-hellman
draft: false
---

##### Link : [Textbook-DH](https://dreamhack.io/wargame/challenges/120)

##### Description
```
Dream is sniffing the communication between Alice and Bob.
Attacking the Key exchanging process to obtain a flag!
```


This challenge was an excellent example of why "Textbook Cryptography" can be dangerously insecure in a real-world context. It's the kind of problem that you could get stuck on if you understand the core principles of Diffie-Hellman but have never tried to break its implementation weaknesses.

## Finding the Foothold

When I first got the source code for the challenge, my primary focus was to understand the overall flow. The code defined a `Person` class, created two instances, Alice and Bob, and had them perform a Diffie-Hellman key exchange.

```python title="challenge.py"
class Person(object):
    def __init__(self, p):
        self.p = p
        self.g = 2
        self.x = random.randint(2, self.p - 1)
    
    def calc_key(self):
        self.k = pow(self.g, self.x, self.p)
        return self.k

    def set_shared_key(self, k):
        self.sk = pow(k, self.x, self.p)
        aes_key = hashlib.md5(str(self.sk).encode()).digest()
        self.cipher = AES.new(aes_key, AES.MODE_ECB)

# ... (abbreviated) ...

alice_k = alice.calc_key()
print(f"Alice sends her key to Bob. Key: {hex(alice_k)}")
print("Let's inturrupt !")
alice_k = int(input(">> "))
# ...
bob.set_shared_key(alice_k)

bob_k = bob.calc_key()
print(f"Bob sends his key to Alice. Key: {hex(bob_k)}")
print("Let's inturrupt !")
bob_k = int(input(">> "))
# ...
alice.set_shared_key(bob_k)
```

While analyzing the code, I spotted a critical section. Right after Alice and Bob calculate their public keys (`alice_k`, `bob_k`), the program prints "Let's inturrupt !" and accepts user input. This input then overwrites the original keys.

This was it—the foothold. The security of the Diffie-Hellman protocol hinges on the integrity of the exchanged public keys. However, this code left a wide-open door for an attacker to manipulate those key values at will. This set up a classic **Man-in-the-Middle (MitM) attack scenario**.



## Planning the Attack

With the vulnerability identified, it was time to plan the attack. The goal was clear: find the AES key that Alice and Bob use for encryption. The AES key is derived from the shared secret key (`sk`), so if I could predict `sk`, I could win.

The shared secret key is calculated as `sk = pow(k, x, p)`. Here, `k` is the public key I can manipulate, and `x` is the other party's private exponent, which is secret. I don't know `x`, but if I choose `k` cleverly, I can force the result of `sk` to a fixed value, regardless of `x`.

What value would be best? I went back to basic mathematical principles.

- `pow(1, x, p)` will always be `1`, no matter the value of `x` or `p`.
- `pow(0, x, p)` will always be `0`.

The number `1` seemed like the simplest and most reliable choice. I checked the server code for any potential filters.

```python title="challenge.py"
if alice_k == alice.g: # g is 2
    exit("Malicious key !!")
```

Fortunately, the code only blocked the value of `g` (which is `2`) and had no checks against `1`. The plan was now concrete.

1. When Alice sends her key to Bob, I'll intercept it and send `1` instead.
2. Bob will calculate his shared secret with the received `1` and his private key `bob_x`. The result will be `pow(1, bob_x, p) = 1`.
3. When Bob sends his key to Alice, I'll intercept that too and send `1`.
4. Alice will calculate her shared secret with `1` and her private key `alice_x`. The result will be `pow(1, alice_x, p) = 1`.

Now, both Alice and Bob will believe their shared secret key is `1`. Consequently, they will both derive the exact same AES key: `hashlib.md5(b'1').digest()`. Since I can generate this key locally, all I have to do is receive their ciphertexts and decrypt them.



## Execution

Translating the plan into code was straightforward. I used `pwntools` to script the interaction with the server.

First, I connected to the server and waited for it to prompt for key input. Then, I sent `1` at both `input()` prompts.

```bash
% nc host8.dreamhack.games 17250

Prime: 0xd25b92240e1b823c18eef7fe44a10c916b51c53e5232b6f9bb12d26ae6ab6062e296571dff46ab44eefaaf4099b7daa320c75d165c4f97aaf7e9353c9b74bd24f5f7c5355bcb61b9fd5a1233053f09f618040f736deaca3c4b5c11e4c60b32daaf35e0ea61f683aaff6a9bc479d75997e2524aa3126aebd05e4f37ae9b5b5247

Alice sends her key to Bob. Key: 0xcc6fa70e26a6002f934221bf6c1829242a13a1bf639b8c9da7f8b98a98fff565b47d2a582c3ca813ca3ebef53fa07c5b97948881b0c7e016ac2d1affe4ef074531e8395ae1afb9e816f5e1ed63b58f3c40cd126e78f7970ddc27fbfe0e6aa51324c88918fc816101c0aafb355a2f066ef59ece291f898f4140e321bba9230235

Let's inturrupt !

>> 1

Bob sends his key to Alice. Key: 0x1faa306556ef0b52abeb831cc9b06e692f6b4a5d38f6309459845a756839a9aecac14d85cb12354fcc7032b1c9ae49ebbd8469d5264d652b4e9554a38ea5f4c266b12d941a89cc52b5537a6ce325f667b932b088b6c438b292641ddacebe4677e317915065ef0fcaf724c8c61076497710ce04e715b5e2ee40d2b05e2eeb3b81

Let's inturrupt !

>> 1

They are sharing the part of flag

Alice: e48e9174a9103e249f4bb809e13d58d49283e2438954799030be4854328adacbeb310c79bce3e91719f218158359af0d

Bob: 2a69648d494907e551b69b74676f2e528644a526e5f7bc8b6300f1bd8ad5f091a9e40939960ea5bd0ad2ceff23a14f96
```

After that, the server sent back the two encrypted halves of the flag from Alice and Bob. I took these ciphertexts and decrypted them with the AES key I had calculated beforehand.

The complete exploit script is as follows:

```python title="exploit.py"
from pwn import *
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib

# Connect to the remote server
p = remote("host8.dreamhack.games", 17250)

# Receive and discard the initial banner
p.recvuntil(b"Prime: ")
p.recvline()
p.recvuntil(b"Alice sends her key to Bob. Key: ")
p.recvline()

# 1. Intercept Alice -> Bob key exchange and inject '1'
p.recvuntil(b">> ")
p.sendline(b"1")
log.info("Sent malicious key '1' to Bob.")

p.recvuntil(b"Bob sends his key to Alice. Key: ")
p.recvline()

# 2. Intercept Bob -> Alice key exchange and inject '1'
p.recvuntil(b">> ")
p.sendline(b"1")
log.info("Sent malicious key '1' to Alice.")

# 3. Receive the encrypted flag parts
p.recvuntil(b"Alice: ")
enc_flag1 = p.recvline().strip().decode()
p.recvuntil(b"Bob: ")
enc_flag2 = p.recvline().strip().decode()
log.success(f"Received Encrypted Flag Part 1: {enc_flag1}")
log.success(f"Received Encrypted Flag Part 2: {enc_flag2}")

# 4. Locally generate the AES key based on the shared secret '1'
shared_secret = 1
aes_key = hashlib.md5(str(shared_secret).encode()).digest()
cipher = AES.new(aes_key, AES.MODE_ECB)
log.info(f"Calculated AES key from secret '1': {aes_key.hex()}")

# 5. Decrypt the ciphertexts and combine them to get the flag
dec_flag1 = unpad(cipher.decrypt(bytes.fromhex(enc_flag1)), 16)
dec_flag2 = unpad(cipher.decrypt(bytes.fromhex(enc_flag2)), 16)

flag = dec_flag1 + dec_flag2
log.success(f"FLAG: {flag.decode()}")

p.close()
```

Running the script successfully recovered the flag.

```bash
% venv/bin/python exploit.py 

[+] Opening connection to host8.dreamhack.games on port 17250: Done

[*] Sent malicious key '1' to Bob.

[*] Sent malicious key '1' to Alice.

[+] Encrypted Flag Part 1 (Alice): e48e9174a9103e249f4bb809e13d58d49283e2438954799030be4854328adacbeb310c79bce3e91719f218158359af0d

[+] Encrypted Flag Part 2 (Bob): 2a69648d494907e551b69b74676f2e528644a526e5f7bc8b6300f1bd8ad5f091a9e40939960ea5bd0ad2ceff23a14f96

[*] Calculated AES key: c4ca4238a0b923820dcc509a6f75849b

[+] FLAG: DH{6**REDACTED**4}

[*] Closed connection to host8.dreamhack.games port 17250
```

This challenge perfectly demonstrated that while the mathematical principles of the Diffie-Hellman protocol are secure, the entire system can collapse without proper 'authentication' to verify _who_ you are exchanging keys with. It was a great reminder that in cryptography, the implementation is just as critical as the theory.