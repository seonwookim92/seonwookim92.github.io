---
title: "Dreamhack: EZ_command_injection"
date: 2025-08-15
tags:
  - web
  - ctf
  - command_injection
  - ipv6
draft: false
---
Link : [# EZ_command_injection](https://dreamhack.io/wargame/challenges/1204)

##### Description
```
ez command injection chall
```

# Solve

## Finding the Foothold

When I first encountered this challenge, the first thing I looked at was the `app.py` source code. In CTFs, the core logic of the problem often reveals the creator's intent. As expected, I found a section that executes external commands via a `ping` function, and I immediately sensed the possibility of a Command Injection.

```python title="app.py"
@app.route('/ping', methods=['GET'])
def ping():
    host = request.args.get('host', '')
    try:
        addr = ipaddress.ip_address(host) # 1. Input Validation
    except ValueError:
        # ...

    cmd = f'ping -c 3 {addr}' # 2. Command Construction
    try:
        output = subprocess.check_output(['/bin/sh', '-c', cmd], timeout=8) # 3. Command Execution
        # ...
```

The developer implemented a safeguard using the `ipaddress.ip_address()` function to verify that the input is a valid IP address. Because of this, basic Command Injection payloads like `;` or `&&` were naturally blocked. My initial attempt was to combine an IPv6 link-local address like `fe80::` with a semicolon, but this also resulted in a `ValueError` and failed.

I wasn't going to give up there. I started throwing various payloads to figure out which strings the `ipaddress` library allows and which it blocks. After numerous attempts, I finally found a breakthrough.

The payload `::%eth0;ls` was executed successfully.

`[Screenshot of the payload ::%eth0;ls being sent, showing the file list of the current directory (flag.txt)]`

This success revealed several crucial facts:

1. I had to use the Unspecified Address `::` instead of a specific address like `fe80::`.
2. A seemingly valid Scope ID string, like `eth0`, must follow the `%`.
3. Simple commands without spaces or special characters, like `ls`, could be injected!

Now that I had a foothold, it was time to plan how to escalate the attack.



## Planning the Attack

Although I succeeded in executing `ls`, the real goal was to read the `flag.txt` file. The first command that came to mind was, of course, `cat /app/flag.txt`. However, this command had two major obstacles: the **space** and the **slash (`/`)**.

The fact that `::%eth0;ls` worked also implied that the `ipaddress` library does not allow spaces and slashes.

First, to bypass the space, I tried using the shell's Internal Field Separator, `${IFS}`. But as soon as `$` or `{}` were included in the payload, the library threw an error. The same went for the tab character (`%09`).

Next was the slash problem. I was stuck, needing to specify the path to `flag.txt` without using a slash. At this point, I re-examined the `Dockerfile` and noticed the `WORKDIR` was set to `/app`.

```text title="Dockerfile"
...
WORKDIR /app

COPY ./app /app
...
```

This was great news. It meant the current working directory was already `/app`, so I could access the `flag.txt` file by its name alone, without needing the full `/app/flag.txt` path.

Now, only one task remained: **find a way to read `flag.txt` without using spaces or slashes.**

After some thought, one of the shell's basic features came to mind: **Input Redirection**. The command `cat<flag.txt` performs the exact same function as `cat flag.txt` but uses no spaces at all. I was confident that this payload could pass the tricky `ipaddress` validation.




## Execution

Now all the pieces of the puzzle were in place. The final attack payload is as follows:

- **Base Payload:** `::%eth0;cat<flag.txt`

If you put this string directly into a URL, the browser might misinterpret characters like `%` or `<`, so it needs to be URL-encoded.
- `%` → `%25`
- `<` → `%3C`

The final, complete `curl` command is shown below.

```bash
curl "http://host8.dreamhack.games:10313/ping?host=::%25eth0;cat%3Cflag.txt"
```

Upon executing this command, the flag I had been waiting for was printed to the screen, right along with the ping results.

![[Images/content/Security/CTFs/Web/EZ_command_injection/EZ_command_injection-20250815152322463.png]]

This was a very interesting challenge that required combining knowledge of the `ipaddress` library's unique parsing behavior with fundamental shell features.