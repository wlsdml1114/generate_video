# Wan2.2 Generate Video API Client
[한국어 README 보기](README_kr.md)

This project provides a Python client for generating videos from images using **Wan2.2** model through RunPod's generate_video endpoint. The client supports base64 encoding, LoRA configurations, and batch processing capabilities.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

**Wan2.2** is an advanced AI model that converts static images into dynamic videos with natural motion and realistic animations. It's built on top of ComfyUI and provides high-quality video generation capabilities.

## 🎨 Engui Studio Integration

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

This Wan2.2 client is primarily designed for **Engui Studio**, a comprehensive AI model management platform. While it can be used via API, Engui Studio provides enhanced features and broader model support.

## ✨ Key Features

*   **Wan2.2 Model**: Powered by the advanced Wan2.2 AI model for high-quality video generation.
*   **Image-to-Video Generation**: Converts static images into dynamic videos with natural motion.
*   **Base64 Encoding Support**: Handles image encoding/decoding automatically.
*   **LoRA Configuration**: Supports up to 4 LoRA pairs for enhanced video generation.
*   **Batch Processing**: Process multiple images in a single operation.
*   **Error Handling**: Comprehensive error handling and logging.
*   **Async Job Management**: Automatic job submission and status monitoring.
*   **ComfyUI Integration**: Built on ComfyUI for flexible workflow management.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run **Wan2.2** as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for Wan2.2 model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.
*   **new_Wan22_api.json**: Single workflow file supporting up to 4 LoRA pairs for Wan2.2 image-to-video generation.

## 📖 Python Client Usage

### Basic Usage

```python
from generate_video_client import GenerateVideoClient

# Initialize client
client = GenerateVideoClient(
    runpod_endpoint_id="your-endpoint-id",
    runpod_api_key="your-runpod-api-key"
)

# Generate video from image
result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)

# Save result if successful
if result.get('status') == 'COMPLETED':
    client.save_video_result(result, "./output_video.mp4")
else:
    print(f"Error: {result.get('error')}")
```

### Using LoRA

```python
# Configure LoRA pairs
lora_pairs = [
    {
        "high": "your_high_lora.safetensors",
        "low": "your_low_lora.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
    }
]

# Generate video with LoRA
result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0,
    lora_pairs=lora_pairs
)
```

### Batch Processing

```python
# Process multiple images
batch_result = client.batch_process_images(
    image_folder_path="./input_images",
    output_folder_path="./output_videos",
    prompt="running man, grab the gun",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)

print(f"Batch processing completed: {batch_result['successful']}/{batch_result['total_files']} successful")
```

## 🔧 API Reference

### Input

The `input` object must contain the following fields. Images can be input using **path, URL or Base64** - one method for each.

#### Image Input (use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | No | - | Local path to the input image |
| `image_url` | `string` | No | - | URL of the input image |
| `image_base64` | `string` | No | - | Base64 encoded string of the input image |

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
| `seed` | `integer` | No | `42` | Random seed for video generation |
| `cfg` | `float` | No | `2.0` | CFG scale for generation |
| `width` | `integer` | No | `480` | Width of the output video in pixels |
| `height` | `integer` | No | `832` | Height of the output video in pixels |
| `length` | `integer` | No | `81` | Length of the generated video |
| `steps` | `integer` | No | `10` | Number of denoising steps |
| `context_overlap` | `integer` | No | `48` | Context overlap value |

**Request Examples:**

#### 1. Basic Generation (No LoRA)
```json
{
  "input": {
    "prompt": "running man, grab the gun",
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

#### 2. With LoRA Pairs
```json
{
  "input": {
    "prompt": "running man, grab the gun",
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

#### 3. Multiple LoRA Pairs (up to 4)
```json
{
  "input": {
    "prompt": "running man, grab the gun",
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

#### 4. URL Image Input
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "image_url": "https://example.com/image.jpg",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "context_overlap": 48
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
  "error": "Video not found."
}
```

## 🛠️ Direct API Usage

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference above.

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

## 🔧 Client Methods

### GenerateVideoClient Class

#### `__init__(runpod_endpoint_id, runpod_api_key)`
Initialize the client with RunPod endpoint ID and API key.

#### `create_video_from_image(image_path, prompt, width, height, length, steps, seed, cfg, context_overlap, lora_pairs)`
Generate video from a single image.

**Parameters:**
- `image_path` (str): Path to the input image
- `prompt` (str): Text prompt for video generation
- `width` (int): Output video width (default: 480)
- `height` (int): Output video height (default: 832)
- `length` (int): Number of frames (default: 81)
- `steps` (int): Denoising steps (default: 10)
- `seed` (int): Random seed (default: 42)
- `cfg` (float): CFG scale (default: 2.0)
- `context_overlap` (int): Context overlap (default: 48)
- `lora_pairs` (list): LoRA configuration pairs (default: None)

#### `batch_process_images(image_folder_path, output_folder_path, valid_extensions, ...)`
Process multiple images in a folder.

**Parameters:**
- `image_folder_path` (str): Path to folder containing images
- `output_folder_path` (str): Path to save output videos
- `valid_extensions` (tuple): Valid image extensions (default: ('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))
- Other parameters same as `create_video_from_image`

#### `save_video_result(result, output_path)`
Save video result to file.

**Parameters:**
- `result` (dict): Job result dictionary
- `output_path` (str): Path to save the video file

## 🔧 Wan2.2 Workflow Configuration

This template uses a single workflow configuration for **Wan2.2**:

*   **new_Wan22_api.json**: Wan2.2 image-to-video generation workflow (supports up to 4 LoRA pairs)

The workflow is based on ComfyUI and includes all necessary nodes for Wan2.2 processing:
- CLIP text encoding for prompts
- VAE loading and processing
- WanImageToVideo node for video generation
- LoRA loading and application nodes (WanVideoLoraSelectMulti)
- Image concatenation and processing nodes

## 🙏 About Wan2.2

**Wan2.2** is a state-of-the-art AI model for image-to-video generation that produces high-quality videos with natural motion and realistic animations. This project provides a Python client and RunPod serverless template for easy deployment and usage of the Wan2.2 model.

### Key Features of Wan2.2:
- **High-Quality Output**: Generates videos with excellent visual quality and smooth motion
- **Natural Animation**: Creates realistic and natural-looking movements from static images
- **LoRA Support**: Supports LoRA (Low-Rank Adaptation) for fine-tuned video generation
- **ComfyUI Integration**: Built on ComfyUI for flexible workflow management
- **Customizable Parameters**: Full control over video generation parameters

## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **Wan2.2:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 License

The original Wan2.2 project follows its respective license. This template also adheres to that license.
