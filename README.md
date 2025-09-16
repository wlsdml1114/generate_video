# Wan22 for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use [Wan22](https://github.com/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

Wan22 is an advanced AI model that generates high-quality videos from images with natural motion and realistic animations.

## ✨ Key Features

*   **Image-to-Video Generation**: Converts static images into dynamic videos with natural motion.
*   **High-Quality Output**: Produces high-resolution videos with realistic animations.
*   **Customizable Parameters**: Control video generation with various parameters like seed, width, height, and prompts.
*   **ComfyUI Integration**: Built on top of ComfyUI for flexible workflow management.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run Wan22 as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.
*   **wan22.json**: Workflow configuration for image-to-video generation.

### Input

The `input` object must contain the following fields. `image_path` supports **URL, file path, or Base64 encoded string**.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **Yes** | `N/A` | Description text for the video to be generated. |
| `image_path` | `string` | **Yes** | `N/A` | Path, URL, or Base64 string of the input image to convert to video. |
| `seed` | `integer` | **Yes** | `N/A` | Random seed for video generation (affects the randomness of the output). |
| `width` | `integer` | **Yes** | `N/A` | Width of the output video in pixels. |
| `height` | `integer` | **Yes** | `N/A` | Height of the output video in pixels. |

**Request Example:**

```json
{
  "input": {
    "prompt": "A person walking in a natural way.",
    "image_path": "https://path/to/your/image.jpg",
    "seed": 12345,
    "width": 512,
    "height": 512
  }
}
```

### Output

#### Success

If the job is successful, it returns a JSON object with the generated video Base64 encoded.

| Parameter | Type | Description |
| --- | --- | --- |
| `video` | `string` | Base64 encoded video file data. |

**Success Response Example:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred. |

**Error Response Example:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ Usage and API Reference

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference below.

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large image files.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `image_path`. For example, if the volume is mounted at `/my_volume` and you use `image.jpg`, the path would be `"/my_volume/image.jpg"`.

## 🔧 Workflow Configuration

This template includes a workflow configuration:

*   **wan22.json**: Image-to-video generation workflow

The workflow is based on ComfyUI and includes all necessary nodes for Wan22 processing, including:
- CLIP text encoding for prompts
- VAE loading and processing
- WanImageToVideo node for video generation
- Image concatenation and processing nodes

## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **Wan22:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 License

The original Wan22 project follows its respective license. This template also adheres to that license.
