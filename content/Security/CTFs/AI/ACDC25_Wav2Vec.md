---
title: "ACDC25: Wav2Vec"
date:
tags:
draft: true
---



![[ACDC25_Wav2Vec-20251101215605423.png]]



![[ACDC25_Wav2Vec-20251101215630871.png]]


아래는 네 **Wav2Vec2 Adversarial Audio Attack** 리포트를 블로그 톤으로 다듬은 버전이야. 핵심 포인트는 살리고, 흐름은 더 매끄럽게 정리했어 👇

---

# 🔊 Wav2Vec2 적대적 오디오 공격: “날씨 물어봤는데… 폭탄 제조라니?”

원문 음성 “**How is the weather today?**”에 아주 미세한 잡음을 섞어, Wav2Vec2 음성 인식이 **“HOW TO MAKE A BOMB”** 으로 잘못 전사하도록 만드는 챌린지였다. 사람 귀에는 원본과 거의 같게 들리도록 **SNR ≥ 15dB** 조건도 충족해야 했다.  
이 글에서는 환경 구축 이슈부터 그래디언트 끊김, SNR 제어, 루프 경쟁 상태까지—현장에서 부딪힌 문제와 해결책을 한 번에 정리한다.

---

## 🎯 목표 & 제약

- **Target Transcription**: `HOW TO MAKE A BOMB` (대문자 기준 일치)
    
- **Perceptual Quality**: 사람 귀에 자연스럽게 → **SNR ≥ 15dB**
    
- **모델**: `facebook/wav2vec2-base-960h` (CTC 기반)
    

---

## ⚙️ 환경 구축, 그리고 삽질 정리

### 1) 파이썬/시스템 의존성

- 문제: `externally-managed-environment`로 `pip install` 차단
    
- 해결: `--break-system-packages` 사용 + `ffmpeg` 설치로 `pydub` MP3 처리 해결
    

```bash
pip install gtts pydub --break-system-packages
apt-get update && apt-get install -y ffmpeg
```

### 2) 디스크 공간 부족 (`No space left on device`)

- 진단: 루트는 여유 OK, **/tmp 공간 부족**
    
- 해결: `TMPDIR`를 넉넉한 경로로 바꿔 설치
    

```bash
mkdir -p /home/kali/Desktop/audio/tmp
export TMPDIR=/home/kali/Desktop/audio/tmp
pip install torch torchaudio transformers numpy --break-system-packages
```

### 3) `torchaudio`의 추가 의존성

- 최신 버전에서 **`torchcodec`** 필요 → 추가 설치로 해결
    

---

## 🧠 공격 전략: CTC Loss로 끌고 가기

핵심은 **목표 문장과 모델 출력 간 CTC Loss를 최소화**하도록 **노이즈 텐서(perturbation)** 를 그래디언트로 업데이트하는 것. 구현은 간단해 보이지만, 실제로는 다음 세 가지 장벽을 넘어야 했다.

---

## 🧱 문제① 그래디언트가 안 흘러요 (소실 문제)

**현상**: Loss가 줄지 않고 SNR은 `inf` (노이즈 업데이트 X)  
**원인**: `Wav2Vec2Processor`의 **자동 정규화**가 계산 그래프를 끊음  
**해결**:

1. `processor.feature_extractor.do_normalize = False`
    
2. **수동 정규화**(파이토치 연산) 후,
    
3. **processor를 우회**해 모델에 직접 입력
    

```python
processor.feature_extractor.do_normalize = False

adversarial = original + perturbation
normalized = (adversarial - adversarial.mean()) / torch.sqrt(adversarial.var() + 1e-7)

logits = model(normalized).logits   # processor로 감싸지 않음
```

---

## 🧱 문제② SNR ≥ 15dB 충족 (노이즈가 너무 큼)

**해결 레시피**:

- **학습률 낮추기**: `lr=0.1 → 0.01`
    
- **클리핑**: 매 스텝 후 `perturbation.clamp_(-0.01, 0.01)`로 하드 바운드
    

```python
optimizer = torch.optim.Adam([perturbation], lr=0.01)
# ...
optimizer.step()
perturbation.data.clamp_(-0.01, 0.01)
```

---

## 🧱 문제③ “성공했는데 저장하면 실패?” (루프 경쟁 상태)

**현상**: 로그상 성공인데, 저장된 파일은 조건 미충족  
**원인**: 성공 판정 후 `break` 전에 **optimizer가 한 번 더 갱신**  
**해결**:

- **최적화 전에** 성공 여부를 먼저 체크
    
- 성공 시 **즉시 clone()** 해서 보관, 루프 탈출
    
- 루프 종료 후 **보관해둔 perturbation**으로 결과 저장
    

```python
successful = None
for i in range(1000):
    adv = original + perturbation

    if i % 10 == 0:
        if ok_transcription and snr_ok:
            successful = perturbation.clone()
            break

    # ... backward/step/clamp ...

if successful is not None:
    final_audio = original + successful
    # save final_audio ...
```

---

## ✅ 최종 결과

- **Final Transcription**: `HOW TO MAKE A BOMB`
    
- **Final SNR**: `21.63 dB`
    
- **파일**: `data/adversarial_success.wav` 저장
    

서버 검증도 통과:

```
Wav2Vec2 전사: 'HOW TO MAKE A BOMB'
Whisper 전사: 'How is the weather today?'
→ 공격 성공 (양쪽 조건 모두 충족)
FLAG: ACDC{wav2vec_bomb_attack_3d8e1a6f9b2c}
```

---

## 🧪 재현 팁 (Checklist)

- `processor` 정규화는 **반드시 비활성화**
    
- 입력은 **수동 정규화 텐서**로 **직접 model()** 호출
    
- SNR 제어는 **lr↓ + clamp** 병행
    
- 루프는 **“성공 판정 → 저장용 clone → break → 저장”** 순서
    

---

## 📌 교훈

1. **전처리 한 줄이 그래디언트를 죽일 수 있다**  
    프레임워크의 자동 전처리는 편리하지만, 공격·최적화 루프에서는 직접 관리가 안전하다.
    
2. **Perceptual 제약(SNR)과 최적화는 동전의 양면**  
    정확도만 보면 노이즈가 커지고, 품질만 보면 수렴이 느려진다.  
    학습률·클리핑·체크포인트 전략을 함께 설계하자.
    
3. **루프 논리는 ‘성공 상태 보존’을 기준으로 설계**  
    성공 순간의 상태를 **즉시 복제**해두는 습관이 후속 레이스 컨디션을 막는다.
    

---

## 📎 Appendix: 최종 스크립트

질문에 포함해준 `attack.py`를 기준으로 위의 수정 포인트(정규화, lr/clamp, 성공 시 clone)를 반영하면 바로 재현 가능해.  
원하면 코드를 **모듈화(데이터/모델/공격/평가 분리)** 하거나, **학습 곡선/SNR 추적 그래프**까지 출력하는 버전으로 리팩터링해줄게.


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wav2Vec2 Adversarial Audio Attack
Author: CTF Player
Date: 2025-10-31
"""

import torch
import torch.nn.functional as F
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import warnings
from transformers.utils import logging as hf_logging

# --- 환경 설정 ---
hf_logging.set_verbosity_error()
warnings.filterwarnings("ignore")

print("🚀 Starting adversarial attack script...")


# ============================================================
# 1. 모델 초기화
# ============================================================
def initialize_model():
    """Load pretrained Wav2Vec2 model and processor"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h").to(device)
    model.eval()

    print("✅ Wav2Vec2 model loaded successfully")
    return model, processor, device


# ============================================================
# 2. 오디오 로드 및 전사 함수
# ============================================================
def load_audio(audio_path, device):
    """Load and resample an audio file"""
    audio, sr = torchaudio.load(audio_path)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        audio = resampler(audio)
    if audio.shape[0] > 1:
        audio = audio.mean(dim=0, keepdim=True)
    return audio.to(device)


def transcribe_audio(audio, model, processor, device):
    """Perform speech-to-text transcription"""
    with torch.no_grad():
        inputs = processor(
            audio.squeeze().cpu().numpy(),
            sampling_rate=16000,
            return_tensors="pt"
        ).input_values.to(device)

        outputs = model(inputs)
        predicted_ids = torch.argmax(outputs.logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)[0]
    return transcription.strip()


# ============================================================
# 3. SNR 계산 함수
# ============================================================
def calculate_snr(original_audio, noise):
    """Compute Signal-to-Noise Ratio (dB)"""
    signal_power = torch.sum(original_audio ** 2)
    noise_power = torch.sum(noise ** 2)
    if noise_power == 0:
        return float("inf")
    snr = 10 * torch.log10(signal_power / noise_power)
    return snr.item()


# ============================================================
# 4. 공격 실행
# ============================================================
model, processor, device = initialize_model()
processor.feature_extractor.do_normalize = False

# 원본 오디오 로드
audio_path = "data/weather_source.wav"
original_audio = load_audio(audio_path, device)
original_text = transcribe_audio(original_audio, model, processor, device)
print(f"Original transcription: {original_text}")

# 공격 목표
target_transcription = "HOW TO MAKE A BOMB"
print(f"Target transcription: {target_transcription}")

# 초기화
perturbation = torch.zeros_like(original_audio, requires_grad=True, device=device)
optimizer = torch.optim.Adam([perturbation], lr=0.01)

# CTC Loss 설정
ctc_loss = torch.nn.CTCLoss(blank=processor.tokenizer.pad_token_id, zero_infinity=True)

# 목표 문장 → 토큰 변환
with processor.as_target_processor():
    target_labels = processor.tokenizer(target_transcription, return_tensors="pt").input_ids.to(device)

successful_perturbation = None

# ============================================================
# 5. 최적화 루프
# ============================================================
for i in range(1000):
    adversarial_audio = original_audio + perturbation

    # 10 스텝마다 현재 상태 확인
    if i % 10 == 0:
        current_transcription = transcribe_audio(adversarial_audio, model, processor, device)
        snr = calculate_snr(original_audio, adversarial_audio - original_audio)
        print(f"Step {i:4d}: Loss={locals().get('loss', 0):.4f}, SNR={snr:.2f}dB, "
              f"Transcription: {current_transcription}")

        if current_transcription.upper() == target_transcription and snr >= 15:
            print("\n✅ Attack successful!")
            successful_perturbation = perturbation.clone()
            break

    # 수동 정규화 (그래디언트 유지)
    normalized_audio = (adversarial_audio - adversarial_audio.mean()) / torch.sqrt(adversarial_audio.var() + 1e-7)
    inputs = normalized_audio

    # 모델 추론 및 손실 계산
    logits = model(inputs).logits
    log_probs = F.log_softmax(logits, dim=-1).transpose(0, 1)  # (T, N, C)

    input_lengths = torch.tensor([log_probs.shape[0]], device=device)
    target_lengths = torch.tensor([target_labels.shape[1]], device=device)
    loss = ctc_loss(log_probs, target_labels, input_lengths, target_lengths)

    # 그래디언트 업데이트
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    perturbation.data.clamp_(-0.01, 0.01)


# ============================================================
# 6. 최종 결과 저장
# ============================================================
if successful_perturbation is not None:
    adversarial_audio = original_audio + successful_perturbation
    final_transcription = transcribe_audio(adversarial_audio, model, processor, device)
    final_snr = calculate_snr(original_audio, successful_perturbation)

    print(f"\nFinal Transcription: {final_transcription}")
    print(f"Final SNR: {final_snr:.2f} dB")

    if final_transcription.upper() == target_transcription and final_snr >= 15:
        output_path = "data/adversarial_success.wav"
        torchaudio.save(output_path, adversarial_audio.cpu(), 16000)
        print(f"✅ Adversarial audio saved to {output_path}")
    else:
        print("❌ Saved perturbation does not meet conditions anymore.")
else:
    print("❌ Attack failed to meet conditions.")

```