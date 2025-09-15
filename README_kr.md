# Wan22 for RunPod Serverless
[English README](README.md)

이 프로젝트는 [Wan22](https://github.com/Comfy-Org/Wan_2.2_ComfyUI_Repackaged)를 RunPod Serverless 환경에서 쉽게 배포하고 사용할 수 있도록 설계된 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

Wan22는 정적 이미지를 자연스러운 움직임과 사실적인 애니메이션을 가진 고품질 비디오로 생성하는 고급 AI 모델입니다.

## ✨ 주요 기능

*   **이미지-투-비디오 생성**: 정적 이미지를 자연스러운 움직임을 가진 동적 비디오로 변환합니다.
*   **고품질 출력**: 사실적인 애니메이션을 가진 고해상도 비디오를 생성합니다.
*   **사용자 정의 가능한 매개변수**: 시드, 너비, 높이, 프롬프트 등 다양한 매개변수로 비디오 생성을 제어할 수 있습니다.
*   **ComfyUI 통합**: 유연한 워크플로우 관리를 위해 ComfyUI 위에 구축되었습니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 Wan22를 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: 모델 실행에 필요한 환경을 구성하고 모든 의존성을 설치합니다.
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수를 구현합니다.
*   **entrypoint.sh**: Worker가 시작될 때 초기화 작업을 수행합니다.
*   **wan22.json**: 이미지-투-비디오 생성을 위한 워크플로우 구성입니다.

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. `image_path`는 **URL, 파일 경로 또는 Base64 인코딩된 문자열**을 지원합니다.

| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **예** | `N/A` | 생성할 비디오에 대한 설명 텍스트입니다. |
| `image_path` | `string` | **예** | `N/A` | 비디오로 변환할 입력 이미지의 경로, URL 또는 Base64 문자열입니다. |
| `seed` | `integer` | **예** | `N/A` | 비디오 생성을 위한 랜덤 시드 (출력의 무작위성에 영향을 줍니다). |
| `width` | `integer` | **예** | `N/A` | 출력 비디오의 픽셀 단위 너비입니다. |
| `height` | `integer` | **예** | `N/A` | 출력 비디오의 픽셀 단위 높이입니다. |

**요청 예시:**

```json
{
  "input": {
    "prompt": "사람이 자연스럽게 걷는 모습.",
    "image_path": "https://path/to/your/image.jpg",
    "seed": 12345,
    "width": 512,
    "height": 512
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
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ 사용법 및 API 참조

1.  이 저장소를 기반으로 RunPod에서 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 아래 API 참조에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64로 인코딩된 파일을 직접 전송하는 대신 RunPod의 Network Volumes를 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 대용량 이미지 파일을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 Network Volume(예: S3 기반 볼륨)을 생성하고 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용하려는 이미지 파일을 생성된 Network Volume에 업로드합니다.
3.  **경로 지정**: API 요청 시 Network Volume 내의 파일 경로를 `image_path`에 지정합니다. 예를 들어, 볼륨이 `/my_volume`에 마운트되고 `image.jpg`를 사용하는 경우 경로는 `"/my_volume/image.jpg"`가 됩니다.

## 🔧 워크플로우 구성

이 템플릿은 다음 워크플로우 구성을 포함합니다:

*   **wan22.json**: 이미지-투-비디오 생성 워크플로우

워크플로우는 ComfyUI를 기반으로 하며 Wan22 처리를 위한 모든 필요한 노드를 포함합니다:
- 프롬프트를 위한 CLIP 텍스트 인코딩
- VAE 로딩 및 처리
- 비디오 생성을 위한 WanImageToVideo 노드
- 이미지 연결 및 처리 노드

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권리는 원본 작성자에게 있습니다.

*   **Wan22:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 라이선스

원본 Wan22 프로젝트는 해당 라이선스를 따릅니다. 이 템플릿도 해당 라이선스를 준수합니다.
