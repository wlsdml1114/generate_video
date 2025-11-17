# Wan2.2 Generate Video API Client
[English README](README.md)

이 프로젝트는 RunPod의 generate_video 엔드포인트를 통해 **Wan2.2** 모델을 사용하여 이미지에서 비디오를 생성하는 Python 클라이언트를 제공합니다. 클라이언트는 base64 인코딩, LoRA 설정, 배치 처리 기능을 지원합니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

**Wan2.2**는 정적 이미지를 자연스러운 움직임과 사실적인 애니메이션을 가진 동적 비디오로 변환하는 고급 AI 모델입니다. ComfyUI 위에 구축되어 고품질 비디오 생성 기능을 제공합니다.

## 🎨 Engui Studio 통합

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

이 Wan2.2 클라이언트는 포괄적인 AI 모델 관리 플랫폼인 **Engui Studio**를 위해 주로 설계되었습니다. API를 통해 사용할 수 있지만, Engui Studio는 향상된 기능과 더 넓은 모델 지원을 제공합니다.

## ✨ 주요 기능

*   **Wan2.2 모델**: 고품질 비디오 생성을 위한 고급 Wan2.2 AI 모델로 구동됩니다.
*   **이미지-투-비디오 생성**: 정적 이미지를 자연스러운 움직임을 가진 동적 비디오로 변환합니다.
*   **Base64 인코딩 지원**: 이미지 인코딩/디코딩을 자동으로 처리합니다.
*   **LoRA 설정**: 향상된 비디오 생성을 위해 최대 4개의 LoRA 쌍을 지원합니다.
*   **배치 처리**: 단일 작업으로 여러 이미지를 처리할 수 있습니다.
*   **오류 처리**: 포괄적인 오류 처리 및 로깅 기능을 제공합니다.
*   **비동기 작업 관리**: 자동 작업 제출 및 상태 모니터링을 지원합니다.
*   **ComfyUI 통합**: 유연한 워크플로우 관리를 위해 ComfyUI 위에 구축되었습니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 **Wan2.2**를 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: Wan2.2 모델 실행에 필요한 환경을 구성하고 모든 의존성을 설치합니다.
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수를 구현합니다.
*   **entrypoint.sh**: Worker가 시작될 때 초기화 작업을 수행합니다.
*   **new_Wan22_api.json**: Wan2.2 이미지-투-비디오 생성을 위한 단일 워크플로우 파일로 최대 4개 LoRA 쌍까지 지원

## 📖 Python 클라이언트 사용법

### 기본 사용법

```python
from generate_video_client import GenerateVideoClient

# 클라이언트 초기화
client = GenerateVideoClient(
    runpod_endpoint_id="your-endpoint-id",
    runpod_api_key="your-runpod-api-key"
)

# 이미지에서 비디오 생성
result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    negative_prompt="blurry, low quality, distorted",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)

# 성공 시 결과 저장
if result.get('status') == 'COMPLETED':
    client.save_video_result(result, "./output_video.mp4")
else:
    print(f"오류: {result.get('error')}")
```

### LoRA 사용

```python
# LoRA 쌍 설정
lora_pairs = [
    {
        "high": "your_high_lora.safetensors",
        "low": "your_low_lora.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
    }
]

# LoRA를 사용한 비디오 생성
result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    negative_prompt="blurry, low quality, distorted",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0,
    lora_pairs=lora_pairs
)
```

### 배치 처리

```python
# 여러 이미지 처리
batch_result = client.batch_process_images(
    image_folder_path="./input_images",
    output_folder_path="./output_videos",
    prompt="running man, grab the gun",
    negative_prompt="blurry, low quality, distorted",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)

print(f"배치 처리 완료: {batch_result['successful']}/{batch_result['total_files']} 성공")
```

## 🔧 API 참조

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. 이미지는 **경로, URL 또는 Base64** 중 하나의 방법으로 입력할 수 있습니다.

#### 이미지 입력 (하나만 사용)
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | 아니오 | - | 입력 이미지의 로컬 경로 |
| `image_url` | `string` | 아니오 | - | 입력 이미지의 URL |
| `image_base64` | `string` | 아니오 | - | 입력 이미지의 Base64 인코딩된 문자열 |

#### LoRA 설정
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `lora_pairs` | `array` | 아니오 | `[]` | LoRA 쌍의 배열. 각 쌍은 `high`, `low`, `high_weight`, `low_weight`를 포함 |

**중요**: LoRA 모델을 사용하려면 RunPod 네트워크 볼륨의 `/loras/` 폴더에 LoRA 파일들을 업로드해야 합니다. `lora_pairs`의 LoRA 모델 이름은 `/loras/` 폴더의 파일명과 일치해야 합니다.

#### LoRA 쌍 구조
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `high` | `string` | 예 | - | High LoRA 모델 이름 |
| `low` | `string` | 예 | - | Low LoRA 모델 이름 |
| `high_weight` | `float` | 아니오 | `1.0` | High LoRA 가중치 |
| `low_weight` | `float` | 아니오 | `1.0` | Low LoRA 가중치 |

#### 비디오 생성 매개변수
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | 예 | - | 생성할 비디오에 대한 설명 텍스트 |
| `negative_prompt` | `string` | 아니오 | - | 비디오에서 제외할 원하지 않는 요소에 대한 네거티브 프롬프트 |
| `seed` | `integer` | 아니오 | `42` | 비디오 생성을 위한 랜덤 시드 |
| `cfg` | `float` | 아니오 | `2.0` | 생성을 위한 CFG 스케일 |
| `width` | `integer` | 아니오 | `480` | 출력 비디오의 픽셀 단위 너비 |
| `height` | `integer` | 아니오 | `832` | 출력 비디오의 픽셀 단위 높이 |
| `length` | `integer` | 아니오 | `81` | 생성할 비디오의 길이 |
| `steps` | `integer` | 아니오 | `10` | 디노이징 스텝 수 |
| `context_overlap` | `integer` | 아니오 | `48` | 컨텍스트 오버랩 값 |

**요청 예시:**

#### 1. 기본 생성 (LoRA 없음)
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "length": 81,
    "steps": 10
  }
}
```

#### 2. LoRA 쌍 사용
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "lora_pairs": [
      {
        "high": "your_high_lora.safetensors",
        "low": "your_low_lora.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
      }
    ]
  }
}
```

#### 3. 여러 LoRA 쌍 (최대 4개)
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_path": "/my_volume/image.jpg",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "lora_pairs": [
      {
        "high": "lora1_high.safetensors",
        "low": "lora1_low.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
      },
      {
        "high": "lora2_high.safetensors",
        "low": "lora2_low.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
      }
    ]
  }
}
```

#### 4. URL 이미지 입력
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_url": "https://example.com/image.jpg",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "context_overlap": 48
  }
}
```

### 출력

#### 성공

작업이 성공하면 생성된 비디오가 Base64로 인코딩된 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `video` | `string` | Base64로 인코딩된 비디오 파일 데이터입니다. |

**성공 응답 예시:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### 오류

작업이 실패하면 오류 메시지를 포함한 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `error` | `string` | 발생한 오류에 대한 설명입니다. |

**오류 응답 예시:**

```json
{
  "error": "Video not found."
}
```

## 🛠️ 직접 API 사용법

1.  이 저장소를 기반으로 RunPod에서 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 위의 API 참조에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64로 인코딩된 파일을 직접 전송하는 대신 RunPod의 Network Volumes를 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 대용량 이미지 파일과 LoRA 모델을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 Network Volume(예: S3 기반 볼륨)을 생성하고 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용하려는 이미지 파일과 LoRA 모델을 생성된 Network Volume에 업로드합니다.
3.  **파일 구성**: 
    - 입력 이미지는 Network Volume 내 어디든 배치할 수 있습니다
    - LoRA 모델 파일은 Network Volume 내의 `/loras/` 폴더에 배치해야 합니다
4.  **경로 지정**: API 요청 시 Network Volume 내의 파일 경로를 지정합니다:
    - `image_path`의 경우: 이미지 파일의 전체 경로 사용 (예: `"/my_volume/images/portrait.jpg"`)
    - LoRA 모델의 경우: 파일명만 사용 (예: `"my_lora_model.safetensors"`) - 시스템이 자동으로 `/loras/` 폴더에서 찾습니다

## 🔧 클라이언트 메서드

### GenerateVideoClient 클래스

#### `__init__(runpod_endpoint_id, runpod_api_key)`
RunPod 엔드포인트 ID와 API 키로 클라이언트를 초기화합니다.

#### `create_video_from_image(image_path, prompt, width, height, length, steps, seed, cfg, context_overlap, lora_pairs, negative_prompt)`
단일 이미지에서 비디오를 생성합니다.

**매개변수:**
- `image_path` (str): 입력 이미지 경로
- `prompt` (str): 비디오 생성을 위한 텍스트 프롬프트
- `negative_prompt` (str): 원하지 않는 요소를 제외하기 위한 네거티브 프롬프트 (기본값: None)
- `width` (int): 출력 비디오 너비 (기본값: 480)
- `height` (int): 출력 비디오 높이 (기본값: 832)
- `length` (int): 프레임 수 (기본값: 81)
- `steps` (int): 디노이징 스텝 수 (기본값: 10)
- `seed` (int): 랜덤 시드 (기본값: 42)
- `cfg` (float): CFG 스케일 (기본값: 2.0)
- `context_overlap` (int): 컨텍스트 오버랩 (기본값: 48)
- `lora_pairs` (list): LoRA 설정 쌍 (기본값: None)

#### `batch_process_images(image_folder_path, output_folder_path, valid_extensions, ...)`
폴더 내 여러 이미지를 처리합니다.

**매개변수:**
- `image_folder_path` (str): 이미지가 포함된 폴더 경로
- `output_folder_path` (str): 출력 비디오를 저장할 경로
- `valid_extensions` (tuple): 유효한 이미지 확장자 (기본값: ('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))
- 기타 매개변수는 `create_video_from_image`와 동일

#### `save_video_result(result, output_path)`
비디오 결과를 파일로 저장합니다.

**매개변수:**
- `result` (dict): 작업 결과 딕셔너리
- `output_path` (str): 비디오 파일을 저장할 경로

## 🔧 Wan2.2 워크플로우 구성

이 템플릿은 **Wan2.2**를 위한 단일 워크플로우 구성을 사용합니다:

*   **new_Wan22_api.json**: Wan2.2 이미지-투-비디오 생성 워크플로우 (최대 4개 LoRA 쌍 지원)

워크플로우는 ComfyUI를 기반으로 하며 Wan2.2 처리를 위한 모든 필요한 노드를 포함합니다:
- 프롬프트를 위한 CLIP 텍스트 인코딩
- VAE 로딩 및 처리
- 비디오 생성을 위한 WanImageToVideo 노드
- LoRA 로딩 및 적용 노드 (WanVideoLoraSelectMulti)
- 이미지 연결 및 처리 노드

## 🙏 Wan2.2 소개

**Wan2.2**는 자연스러운 움직임과 사실적인 애니메이션을 가진 고품질 비디오를 생성하는 최첨단 AI 모델입니다. 이 프로젝트는 Wan2.2 모델의 쉬운 배포와 사용을 위한 Python 클라이언트와 RunPod 서버리스 템플릿을 제공합니다.

### Wan2.2의 주요 특징:
- **고품질 출력**: 우수한 시각적 품질과 부드러운 움직임을 가진 비디오 생성
- **자연스러운 애니메이션**: 정적 이미지에서 사실적이고 자연스러운 움직임 생성
- **LoRA 지원**: 세밀한 조정된 비디오 생성을 위한 LoRA (Low-Rank Adaptation) 지원
- **ComfyUI 통합**: 유연한 워크플로우 관리를 위한 ComfyUI 기반 구축
- **사용자 정의 가능한 매개변수**: 비디오 생성 매개변수의 완전한 제어

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권리는 원본 작성자에게 있습니다.

*   **Wan2.2:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 라이선스

원본 Wan2.2 프로젝트는 해당 라이선스를 따릅니다. 이 템플릿도 해당 라이선스를 준수합니다.
