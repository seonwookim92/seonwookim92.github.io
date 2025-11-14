---
title: "ACDC25: Video OCR"
date:
tags:
draft: true
---



![[ACDC25_Video_OCR-20251101215112490.png]]

![[ACDC25_Video_OCR-20251101215103127.png]]

일단 영상을 위아래왼쪽오른쪽 40px씩 자르고, 점으로 생겨서 일반 OCR로 안되서 Sample Frame을 추출하여 0부터 F까지 데이터셋을 만든 다음, 5프레임 간격으로 이미지를 뽑아서 90%이상 비슷한 이미지들만 추출하여, extracted_full.jpg를 만들었습니다.



## 🧩 Challenge Overview

- **Name**: VideoOCR
    
- **Category**: Forensics / Video Analysis
    
- **Flag**: `ACDC{v1dEO2cHAR_rEcON}`
    
- **Given File**: `chall_cropped.mp4`
    
- **Extra Data**: `Sample_Frame/` 폴더 내 0–F 템플릿 이미지
    

---

## 🔍 Step 1. 영상 구조 분석

먼저 FFmpeg와 OpenCV로 영상 메타데이터를 확인했다.

|항목|값|
|---|---|
|FPS|62.5|
|총 프레임 수|313,751|
|길이|약 83분|

초반 1초 이후부터 특정 영역에 **0~F 문자**가 주기적으로 등장한다.  
관찰 결과 약 **60~70프레임 간격(약 1초)** 마다 새로운 문자가 등장하며, 각 문자는 여러 프레임 동안 유지된다.

---

## 💡 Step 2. 접근 전략

### 1️⃣ 템플릿 매칭 기반 OCR

- `cv2.matchTemplate()`를 사용해 각 프레임을 템플릿과 비교
    
- 매칭 결과(`max_val`)가 0.90 이상일 때만 유효 문자로 판정
    
- 템플릿은 문제에서 제공된 `Sample_Frame/*.png` (0~F)
    

### 2️⃣ 프레임 샘플링

- 전체 31만 프레임을 모두 처리하기엔 비효율적 → **5프레임 간격 스캔**
    
- 약 6만여 프레임만 검사하여 속도 확보
    
- 각 프레임의 `(번호, 문자, 신뢰도)` 메타데이터만 저장
    

### 3️⃣ 중복 제거 알고리즘

문자가 여러 프레임 동안 유지되므로, 같은 문자가 반복 검출된다.  
이를 해결하기 위해 “윈도우 그룹화 + 최고 신뢰도 선택” 알고리즘을 사용했다.

`def group_detections(all_detections, window_size=10, min_gap=50):     all_detections.sort(key=lambda x: x[0])     groups, current_group = [], [all_detections[0]]      for detection in all_detections[1:]:         if detection[0] - current_group[-1][0] <= window_size:             current_group.append(detection)         else:             groups.append(current_group)             current_group = [detection]     if current_group:         groups.append(current_group)      final_detections, last_selected = [], -min_gap     for group in groups:         if group[0][0] - last_selected >= min_gap:             group.sort(key=lambda x: x[2], reverse=True)             final_detections.append(group[0])             last_selected = group[0][0]      return final_detections`

### 4️⃣ 메모리 최적화 설계

- 83분짜리 영상을 5프레임 단위로 처리하면 약 6만 프레임
    
- 모든 프레임 이미지를 메모리에 두면 수 GB 필요하므로 **3단계 방식**으로 해결
    

|단계|설명|
|---|---|
|1단계|전체 영상 스캔 – 문자/신뢰도 메타데이터만 저장|
|2단계|그룹화 – 메모리 상에서 최종 문자 선택|
|3단계|선택된 프레임만 다시 로드해 저장|

---

## ⚙️ Step 3. 실행 및 결과

### 🧮 통계 요약

|항목|결과|
|---|---|
|총 검출 문자|약 110개|
|평균 신뢰도|97.6%|
|프레임 간격|평균 67.2 (최소 55, 최대 80)|

### 🧾 추출된 헥스 데이터 (일부)

`FFD8FFE000104A46494600010100000100010000FFDB010410001B001B001B...`

---

## 🧬 Step 4. 파일 시그니처 분석

|HEX|의미|
|---|---|
|`FFD8`|JPEG SOI (Start of Image)|
|`FFE0`|JFIF APP0 Marker|
|`4A464946`|"JFIF" (ASCII)|

> ✅ JPEG 파일로 판별 완료

이 헥스 데이터를 `bytes.fromhex()`로 변환하자 `extracted_full.jpg`가 생성되었다.  
복원된 이미지에는 플래그가 명확히 드러났다.

---

## 🏁 Final Flag

`ACDC{v1dEO2cHAR_rEcON}`

---

## 🧰 Tools & Scripts Used

|도구|용도|
|---|---|
|**Python 3**|메인 로직|
|**OpenCV (cv2)**|템플릿 매칭, 영상 처리|
|**NumPy**|프레임 분석, 연산|
|**ffmpeg**|영상 메타데이터 추출|

### 개발한 스크립트

|파일명|설명|
|---|---|
|`extract_first_2min.py`|초기 테스트 (2분 구간)|
|`extract_first_2min_v2.py`|개선된 탐지 알고리즘|
|`extract_full_video_optimized.py`|전체 영상용 최종 버전 (메모리 최적화 포함)|

---

## 🧠 Lessons Learned

1. **템플릿 매칭의 단순함이 강력함**  
    복잡한 딥러닝 OCR보다 OpenCV 템플릿 매칭이 오히려 정확하고 빠르게 동작했다.
    
2. **대용량 영상 처리의 핵심은 메모리 관리**  
    “모든 프레임 저장” 대신 메타데이터 기반 처리가 안정성과 효율성을 확보했다.
    
3. **윈도우 기반 중복 제거 알고리즘**  
    프레임 간 잔상이나 흔들림에도 안정적으로 유효 문자만 남겼다.
    
4. **점진적 접근의 중요성**  
    처음엔 2분 구간만 실험 → 알고리즘 개선 후 전체 영상 확장.  
    작은 단위 검증이 전체 성공으로 이어졌다.
    

---

## 🧭 Timeline 요약

1. 문제 분석 및 템플릿 확인
    
2. 짧은 구간 테스트 스크립트 작성
    
3. 그룹화 알고리즘 및 신뢰도 임계값 튜닝
    
4. 메모리 최적화 버전 개발
    
5. 전체 영상 분석 및 JPEG 복원
    
6. 최종 플래그 확보 ✅





```python
#!/usr/bin/env python3
import os
import time
import cv2

# =====================================================
# Config
# =====================================================

TEMPLATE_DIR = "Sample_Frame"
OUTPUT_DIR = "detected_chars_full"


# =====================================================
# Template Utilities
# =====================================================

def load_templates():
    """Load all character templates from Sample_Frame directory."""
    templates = {}

    # 0-9, A-F
    chars = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "A", "B", "C", "D", "E", "F",
    ]

    for char in chars:
        template_path = os.path.join(TEMPLATE_DIR, f"{char}.png")
        if os.path.exists(template_path):
            template = cv2.imread(template_path)
            if template is not None:
                templates[char] = template

    return templates


def match_template(frame, templates, threshold=0.90):
    """Recognize a character in the frame using template matching."""
    best_match = None
    best_score = 0.0

    for char, template in templates.items():
        result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val > best_score:
            best_score = max_val
            best_match = char

    if best_score >= threshold:
        return best_match, best_score
    return None, best_score


# =====================================================
# Grouping / Post-processing
# =====================================================

def group_detections(all_detections, window_size=10, min_gap=50):
    """
    Group detections and pick the final character per group by confidence.

    Parameters
    ----------
    all_detections : list[tuple]
        List of (frame_num, char, score). Images are not stored (memory efficient).
    window_size : int
        Frames considered the same group if distance <= window_size.
    min_gap : int
        Minimum gap in frames between selected outputs to avoid duplicates.
    """
    if not all_detections:
        return []

    all_detections.sort(key=lambda x: x[0])  # sort by frame number

    groups = []
    current_group = [all_detections[0]]

    for detection in all_detections[1:]:
        frame_num = detection[0]
        last_frame = current_group[-1][0]

        if frame_num - last_frame <= window_size:
            current_group.append(detection)
        else:
            groups.append(current_group)
            current_group = [detection]

    if current_group:
        groups.append(current_group)

    final_detections = []
    last_selected_frame = -min_gap

    for group in groups:
        # respect min_gap between selections
        if group[0][0] - last_selected_frame >= min_gap:
            group.sort(key=lambda x: x[2], reverse=True)  # highest score first
            best = group[0]
            final_detections.append(best)
            last_selected_frame = best[0]

    return final_detections


# =====================================================
# Main
# =====================================================

def main():
    cropped_video = "chall_cropped.mp4"

    if not os.path.exists(cropped_video):
        print(f"크롭된 영상이 없습니다: {cropped_video}")
        return

    # Prepare output directory
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, f))
    else:
        os.makedirs(OUTPUT_DIR)

    print("=" * 70)
    print("메모리 최적화 OCR - 전체 영상 분석 (신뢰도 90% 이상)")
    print("=" * 70)
    print()

    # Load templates
    print("템플릿 로드 중...")
    templates = load_templates()
    print(f"총 {len(templates)}개의 템플릿 로드 완료\n")

    if len(templates) == 0:
        print("템플릿이 없습니다. Sample_Frame 폴더를 확인하세요.")
        return

    # Open video
    cap = cv2.VideoCapture(cropped_video)
    if not cap.isOpened():
        print("크롭된 영상을 열 수 없습니다.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_seconds = total_frames / fps if fps else 0

    print("영상 정보:")
    print(f"  FPS: {fps}")
    print(f"  총 프레임: {total_frames}")
    print(f"  총 시간: {total_seconds:.1f}초 ({total_seconds/60:.1f}분)")
    print()

    # Parameters
    scan_interval = 5
    window_size = 10
    min_gap = 50
    threshold = 0.90

    print("설정:")
    print(f"  스캔 간격: {scan_interval} 프레임")
    print(f"  검출 윈도우: {window_size} 프레임")
    print(f"  최소 글자 간격: {min_gap} 프레임")
    print(f"  매칭 임계값: {threshold}")
    print()

    # Stage 1: Scan whole video (memory optimized)
    print("1단계: 전체 영상 스캔 중 (메모리 최적화)...\n")

    all_detections = []  # (frame_num, char, score)
    start_time = time.time()

    for frame_num in range(0, total_frames, scan_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            continue

        char, score = match_template(frame, templates, threshold)
        if char:
            all_detections.append((frame_num, char, score))

        # Progress log
        if frame_num % 1000 == 0:
            progress = (frame_num / total_frames) * 100 if total_frames else 0
            elapsed = time.time() - start_time
            if frame_num > 0:
                eta = (elapsed / frame_num) * (total_frames - frame_num)
                print(
                    f"  진행: {progress:.1f}% "
                    f"({frame_num}/{total_frames} 프레임, {len(all_detections)}개 검출, "
                    f"ETA: {eta/60:.1f}분)"
                )
            else:
                print(
                    f"  진행: {progress:.1f}% "
                    f"({frame_num}/{total_frames} 프레임, {len(all_detections)}개 검출)"
                )

    elapsed_time = time.time() - start_time
    print(f"\n  총 {len(all_detections)}개 검출 완료 (소요 시간: {elapsed_time/60:.1f}분)\n")

    # Stage 2: Grouping
    print("2단계: 그룹화 및 최종 문자 선택 중...")
    final_detections = group_detections(all_detections, window_size, min_gap)
    print(f"  {len(final_detections)}개 최종 문자 선택 완료\n")

    # Stage 3: Save selected frames & aggregate hex
    print("3단계: 최종 선택된 프레임 이미지 저장 중...")
    hex_data = ""
    saved_count = 0

    for i, (frame_num, char, score) in enumerate(final_detections, 1):
        time_sec = frame_num / fps if fps else 0
        hex_data += char

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if ret:
            img_filename = f"{i:04d}_frame{frame_num:06d}_{char}_{score:.3f}.png"
            img_path = os.path.join(OUTPUT_DIR, img_filename)
            cv2.imwrite(img_path, frame)
            saved_count += 1

        # Print first 20, every 100th, last 20
        if i <= 20 or i % 100 == 0 or i > len(final_detections) - 20:
            print(f"{i:4d}. 프레임 {frame_num:6d} ({time_sec:6.2f}초): {char} (신뢰도: {score:.3f})")
        elif i == 21:
            print("  ...")

    print(f"\n  {saved_count}개 이미지 저장 완료\n")

    cap.release()

    print("=" * 70)
    print(f"총 {len(final_detections)}개의 헥스 문자 검출")

    if final_detections:
        print("\n프레임 간격 통계:")
        intervals = [final_detections[i][0] - final_detections[i - 1][0]
                     for i in range(1, len(final_detections))]
        if intervals:
            print(f"  평균: {sum(intervals)/len(intervals):.1f} 프레임")
            print(f"  최소: {min(intervals)} 프레임")
            print(f"  최대: {max(intervals)} 프레임")

        print("\n신뢰도 통계:")
        scores = [d[2] for d in final_detections]
        print(f"  평균: {sum(scores)/len(scores):.3f}")
        print(f"  최소: {min(scores):.3f}")
        print(f"  최대: {max(scores):.3f}")

    print("\n최종 헥스 데이터 (처음 200자):")
    print(f"{hex_data[:200]}...")
    print(f"\n길이: {len(hex_data)} 문자 ({len(hex_data)//2} 바이트)")

    # Write results
    with open("full_video_result.txt", "w", encoding="utf-8") as f:
        f.write("전체 영상 추출 결과 (신뢰도 90% 이상)\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"검출된 문자 수: {len(final_detections)}\n\n")
        f.write("헥스 데이터:\n")
        for i in range(0, len(hex_data), 80):
            f.write(f"{hex_data[i:i+80]}\n")
        f.write(f"\n길이: {len(hex_data)} 문자 ({len(hex_data)//2} 바이트)\n\n")
        f.write("상세 정보:\n")
        for i, (frame, char, score) in enumerate(final_detections, 1):
            time_sec = frame / fps if fps else 0
            f.write(
                f"{i:4d}. 프레임 {frame:6d} ({time_sec:6.2f}초): {char} (신뢰도: {score:.3f})\n"
            )

    with open("full_video_hex.txt", "w", encoding="utf-8") as f:
        f.write(hex_data)

    print("\n결과 저장 완료:")
    print("  - 상세 결과: full_video_result.txt")
    print("  - 헥스 데이터: full_video_hex.txt")
    print(f"  - 이미지: {OUTPUT_DIR}/ ({saved_count}개 파일)")

    # Try binary reconstruction if hex length is even
    if len(hex_data) % 2 == 0:
        try:
            binary_data = bytes.fromhex(hex_data)
            with open("extracted_full.bin", "wb") as f:
                f.write(binary_data)
            print(f"  - 바이너리: extracted_full.bin ({len(binary_data)} 바이트)")

            # File signature checks
            if binary_data[:2] == b"\xff\xd8":
                print("\n✓ JPEG 이미지로 감지됨!")
                with open("extracted_full.jpg", "wb") as f:
                    f.write(binary_data)
                print("  → extracted_full.jpg 저장")
            elif binary_data[:8] == b"\x89PNG\r\n\x1a\n":
                print("\n✓ PNG 이미지로 감지됨!")
                with open("extracted_full.png", "wb") as f:
                    f.write(binary_data)
                print("  → extracted_full.png 저장")
        except Exception as e:
            print(f"\n바이너리 변환 오류: {e}")


if __name__ == "__main__":
    main()
```


![[ACDC25_Video_OCR-20251101215329574.png]]

`https://shorturl.at/Ky2bC`


![[ACDC25_Video_OCR-20251101215350052.png]]