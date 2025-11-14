---
title: "ACDC25: Babel"
date: 2025-11-01
tags:
  - misc
draft: true
---
![[ACDC25_BABEL-20251101194619170.png]]

> 10가지 언어를 쓰는 사람들이 키워드를 설명하고 있습니다. 
> 키워드를 알아내어 플래그를 획득하세요. 
> 만약 키워드가 apple, banana, carrot 이라면 플래그는 ACDC{APPLE_BANANA_CARROT} 입니다.

Download 버튼을 누르면 Google Drive로 연결된다.
공유된 드라이브 내에는 3개의 mp3 파일이 있다 : `babel1.mp3`, `babel2.mp3`, `babel3.mp3`

![[ACDC25_BABEL-20251101194657520.png]]

모든 파일들을 우선 다운로드 받았다.

![[ACDC25_BABEL-20251101195057310.png]]

음원을 들어보니 알아들을 수 없는 언어로 12초 정도의 소리가 재생된다.

![[ACDC25_BABEL-20251101195134538.png]]

우선 파일들을 변수에 로드해서 담았다.

```python
AUDIO_PATHS = ["/content/babel1.mp3", "/content/babel2.mp3", "/content/babel3.mp3"]

def load_audio(path):
	# Use soundfile to read the audio file
	data, sr = sf.read(path, always_2d=True)
	# Convert data to float32 numpy array
	return data.astype(np.float32), sr

audio_data = {}

for audio_path in AUDIO_PATHS:
	audio, sr_audio = load_audio(audio_path)
	audio_data[audio_path] = {"audio": audio, "sr": sr_audio}
	print(f"Audio loaded from {audio_path}. Shape={audio.shape}, SR={sr_audio}")

>>>

Audio loaded from /content/babel1.mp3. Shape=(565595, 1), SR=44100 
Audio loaded from /content/babel2.mp3. Shape=(566068, 1), SR=44100 
Audio loaded from /content/babel3.mp3. Shape=(573835, 1), SR=44100
```

그 다음 "Whisper-1" STT(Speech-to-Text) 모델로 문자열로 변환시켰다.

```python
transcriptions = {}

for audio_path, data in audio_data.items():
	# Save the audio data to a temporary file
	temp_file_path = f"/content/temp_{os.path.basename(audio_path)}.wav"
	sf.write(temp_file_path, data["audio"], data["sr"])
	
	# Transcribe the audio file using OpenAI API
	with open(temp_file_path, "rb") as audio_file:
		try:
			transcription = client.audio.transcriptions.create(
			model="whisper-1", # Using whisper-1 model for transcription
			file=audio_file,
			response_format="text"
			)
			transcriptions[audio_path] = transcription
			print(f"Transcription for {audio_path}:\n{transcription}\n")
		except Exception as e:
			print(f"Error transcribing {audio_path}: {e}")
		
		# Remove the temporary file
		os.remove(temp_file_path)

>>>

Transcription for /content/babel1.mp3: 
Tresna, magnetinen Motvejth Inaonjesha Nordhur Disha Mata Gajsne Bumi Kandëntang 

Transcription for /content/babel2.mp3: 
Usiku, Lius, Präsentöviakti, Lesk, Univers, Observatorium, Plonto-Ratat, Isäri-Jeskorra, Tähdistö, Katsser. 

Transcription for /content/babel3.mp3: 
Ζνάωστ, Φαφέδα. Τόκο Βούκου, Κανάν. Λίμου Ρουτέγη. Κύριαστο, Πάπερ. Χουσόμα. Σάγα, Κιτάβων Κιδουκάν.
```