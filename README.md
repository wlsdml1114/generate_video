# Wan22 for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use [Wan22](https://github.com/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

Wan22 is an advanced AI model that generates high-quality videos from images with natural motion and realistic animations.

## 🎨 Engui Studio Integration

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

This InfiniteTalk template is primarily designed for **Engui Studio**, a comprehensive AI model management platform. While it can be used via API, Engui Studio provides enhanced features and broader model support.

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

The `input` object must contain the following fields. Images can be input using **path or Base64** - one method for each.

#### Image Input (use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | No | `/example_image.png` | Local path to the input image |
| `image_base64` | `string` | No | `/example_image.png` | Base64 encoded string of the input image |

#### LoRA Configuration
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `lora_pairs` | `array` | No | `[]` | Array of LoRA pairs. Each pair contains `high`, `low`, `high_weight`, `low_weight` |

**Important**: To use LoRA models, you must upload the LoRA files to the `/loras/` folder in your RunPod Network Volume. The LoRA model names in `lora_pairs` should match the filenames in the `/loras/` folder.

#### LoRA Pair Structure
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `high` | `string` | Yes | - | High LoRA model name |
| `low` | `string` | Yes | - | Low LoRA model name |
| `high_weight` | `float` | No | `1.0` | High LoRA weight |
| `low_weight` | `float` | No | `1.0` | Low LoRA weight |

#### Video Generation Parameters
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | Yes | - | Description text for the video to be generated |
| `seed` | `integer` | Yes | - | Random seed for video generation |
| `cfg` | `float` | Yes | - | CFG scale for generation |
| `width` | `integer` | Yes | - | Width of the output video in pixels |
| `height` | `integer` | Yes | - | Height of the output video in pixels |
| `length` | `integer` | No | `81` | Length of the generated video |
| `steps` | `integer` | No | `10` | Number of denoising steps |

**Request Examples:**

#### 1. Basic Generation (No LoRA)
```json
{
  "input": {
    "prompt": "A person walking in a natural way.",
    "image_path": "/my_volume/image.jpg",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512,
    "length": 81,
    "steps": 10
  }
}
```

#### 2. With LoRA Pairs
```json
{
  "input": {
    "prompt": "A person walking in a natural way.",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512,
    "lora_pairs": [
      {
        "high": "lora_high_model.safetensors",
        "low": "lora_low_model.safetensors",
        "high_weight": 1.0,
        "low_weight": 0.8
      }
    ]
  }
}
```

#### 3. Multiple LoRA Pairs (up to 3)
```json
{
  "input": {
    "prompt": "A person walking in a natural way.",
    "image_path": "/my_volume/image.jpg",
    "seed": 12345,
    "cfg": 7.5,
    "width": 512,
    "height": 512,
    "lora_pairs": [
      {
        "high": "lora1_high.safetensors",
        "low": "lora1_low.safetensors",
        "high_weight": 1.0,
        "low_weight": 0.8
      },
      {
        "high": "lora2_high.safetensors",
        "low": "lora2_low.safetensors",
        "high_weight": 0.9,
        "low_weight": 0.7
      }
    ]
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

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large image files and LoRA models.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image files and LoRA models you want to use to the created Network Volume.
3.  **File Organization**: 
    - Place your input images anywhere in the Network Volume
    - Place LoRA model files in the `/loras/` folder within the Network Volume
4.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume:
    - For `image_path`: Use the full path to your image file (e.g., `"/my_volume/images/portrait.jpg"`)
    - For LoRA models: Use only the filename (e.g., `"my_lora_model.safetensors"`) - the system will automatically look in the `/loras/` folder

## 🔧 Workflow Configuration

This template includes multiple workflow configurations that are automatically selected based on the number of LoRA pairs:

*   **wan22_nolora.json**: Image-to-video generation workflow without LoRA
*   **wan22_1lora.json**: Image-to-video generation workflow with 1 LoRA pair
*   **wan22_2lora.json**: Image-to-video generation workflow with 2 LoRA pairs
*   **wan22_3lora.json**: Image-to-video generation workflow with 3 LoRA pairs

### Workflow Selection Logic

The handler automatically selects the appropriate workflow based on the number of LoRA pairs:

| LoRA Pairs Count | Selected Workflow |
|------------------|-------------------|
| 0 | wan22_nolora.json |
| 1 | wan22_1lora.json |
| 2 | wan22_2lora.json |
| 3 | wan22_3lora.json |

The workflows are based on ComfyUI and include all necessary nodes for Wan22 processing, including:
- CLIP text encoding for prompts
- VAE loading and processing
- WanImageToVideo node for video generation
- LoRA loading and application nodes (when applicable)
- Image concatenation and processing nodes

## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **Wan22:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 License

The original Wan22 project follows its respective license. This template also adheres to that license.
