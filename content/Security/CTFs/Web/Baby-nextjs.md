---
title: "Dreamhack: Baby-nextjs"
date: 2025-08-13
tags:
  - web
  - ctf
  - nextjs
draft: false
---
##### Link : [Baby-nextjs](https://dreamhack.io/wargame/challenges/1472)

##### Description
```
use nextjs 👶
```

# Solve

## Finding the Foothold

When I first encountered this challenge, the first thing I looked at was the UI and its client-side code. There was an obvious "give me the flag" button, but clicking it did nothing.

![[Baby-nextjs-20250815135702211.png]]

![[Baby-nextjs-20250815135709861.png]]

Opening the developer tools and inspecting `page.js` revealed the reason immediately.

```js title="src/app/page.js"
'use client';

// ...
const IS_PROD = process.env.NODE_ENV === 'production';

export default function Home() {
  // ...
      <button
        onClick={async () => {
          if (IS_PROD) { // This is the culprit!
            setMessage('unavailable in production');
            return;
          }
          const { message } = await getFlag();
          setMessage(message);
        }}
      >
```

I had already confirmed from the `Dockerfile` that the environment was running with `NODE_ENV=production`, meaning the `if` condition would always be true, and the `getFlag()` function would never be called. This was a classic Client-Side Validation flaw. My objective became clear: 'I need to bypass the UI and invoke the `getFlag` Server Action directly.'



## Planning the Attack

To plan the attack, I needed to know how to call the `getFlag` Server Action. This required two things: first, a unique `Action ID` to identify `getFlag`, and second, the correct endpoint and request method to deliver this ID.

I started by hunting for the Action ID in the JavaScript files served by the server.

```bash
# Fetching the client-side JS file with curl
curl http://host1.dreamhack.games:16138/_next/static/chunks/app/page-4690685ea1c3e4a7.js

// ... (obfuscated code) ... (0,t(8064).$)("7be4073b46655ad71ea7fbfe6cd2e95ab20fd3f0") // ...
```

`7be4073b46655ad71ea7fbfe6cd2e95ab20fd3f0`. This was the Action ID. Now, I just had to figure out how to properly send it to the server.



## Execution

My first attempt was based on a simple assumption: 'I'll just send a `POST` request to the page root with the `Next-Action` header.' But this attempt failed, returning only a cryptic internal server error.

```bash
# The initial, failed attempt
curl -X POST -H "Next-Action: 7be4073b46655ad71ea7fbfe6cd2e95ab20fd3f0" http://host1.dreamhack.games:16138/
```

This failure told me that my hypothesis was wrong. Invoking a Next.js Server Action was more complex than just adding a header. After digging a bit deeper into how Next.js handles its internals, especially concerning React Server Components (RSC), I found the real invocation method.

1. **The Endpoint**: It wasn't `/`, but `/_rsc`.
2. **The Header**: `Content-Type: application/json` was mandatory.
3. **The Payload**: The request body had to be a specific JSON array in the format `["$$ACTION_ID", null]`. That `$$` prefix was key.
    
I assembled this information into my final attack command.

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Next-Action: 7be4073b46655ad71ea7fbfe6cd2e95ab20fd3f0" \
  -d '["$$7be4073b46655ad71ea7fbfe6cd2e95ab20fd3f0", null]' \
  http://host1.dreamhack.games:16138/_rsc

1:{"message":"flag{REDACTED}\n"}
```

In the end, this challenge was about more than a simple client-side validation bypass. It was a test of whether one understood the specific, internal API contract of a modern framework. A deep understanding of the framework, hidden behind a seemingly simple flaw, was the real key to solving it.