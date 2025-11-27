#!/usr/bin/env python3
"""
Generate Video API client with base64 encoding
Client for generating videos from images using RunPod's generate_video endpoint
"""

import os
import requests
import json
import time
import base64
from typing import Optional, Dict, Any, List, Union
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenerateVideoClient:
    def __init__(
        self,
        runpod_endpoint_id: str,
        runpod_api_key: str
    ):
        """
        Initialize Generate Video client
        
        Args:
            runpod_endpoint_id: RunPod endpoint ID
            runpod_api_key: RunPod API key
        """
        self.runpod_endpoint_id = runpod_endpoint_id
        self.runpod_api_key = runpod_api_key
        self.runpod_api_endpoint = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/run"
        self.status_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/status"
        
        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {runpod_api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"GenerateVideoClient initialized - Endpoint: {runpod_endpoint_id}")
    
    def encode_file_to_base64(self, file_path: str) -> Optional[str]:
        """
        Encode file to base64
        
        Args:
            file_path: File path to encode
        
        Returns:
            Base64 encoded string or None (on failure)
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
            
            logger.info(f"✅ File base64 encoding completed: {file_path}")
            return base64_data
            
        except Exception as e:
            logger.error(f"❌ File base64 encoding failed: {e}")
            return None
    
    @staticmethod
    def encode_image_to_base64(image_data: Union[str, bytes]) -> Optional[str]:
        """
        Encode image data to base64 string
        
        Args:
            image_data: Image file path (str) or image bytes (bytes)
        
        Returns:
            Base64 encoded string or None (on failure)
        """
        try:
            # If it's a file path
            if isinstance(image_data, str) and os.path.exists(image_data):
                with open(image_data, 'rb') as f:
                    image_bytes = f.read()
            # If it's already bytes
            elif isinstance(image_data, bytes):
                image_bytes = image_data
            else:
                logger.error(f"Invalid image data type: {type(image_data)}")
                return None
            
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"✅ Image base64 encoding completed")
            return base64_data
            
        except Exception as e:
            logger.error(f"❌ Image base64 encoding failed: {e}")
            return None
    
    @staticmethod
    def decode_base64_to_file(base64_data: str, output_path: str) -> bool:
        """
        Decode base64 string to file
        
        Args:
            base64_data: Base64 encoded string
            output_path: File path to save decoded data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            decoded_data = base64.b64decode(base64_data)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(decoded_data)
            
            logger.info(f"✅ Base64 decoded and saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Base64 decoding failed: {e}")
            return False
    
    def submit_job(self, input_data: Dict[str, Any]) -> Optional[str]:
        """
        Submit job to RunPod
        
        Args:
            input_data: API input data
        
        Returns:
            Job ID or None (on failure)
        """
        payload = {"input": input_data}
        
        try:
            logger.info(f"Submitting job to RunPod: {self.runpod_api_endpoint}")
            logger.info(f"Input data: {json.dumps(input_data, indent=2, ensure_ascii=False)}")
            
            response = self.session.post(self.runpod_api_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            job_id = response_data.get('id')
            
            if job_id:
                logger.info(f"✅ Job submission successful! Job ID: {job_id}")
                return job_id
            else:
                logger.error(f"❌ Failed to receive Job ID: {response_data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Job submission failed: {e}")
            return None
    
    def wait_for_completion(self, job_id: str, check_interval: int = 10, max_wait_time: int = 1800) -> Dict[str, Any]:
        """
        Wait for job completion
        
        Args:
            job_id: Job ID
            check_interval: Status check interval (seconds)
            max_wait_time: Maximum wait time (seconds)
        
        Returns:
            Job result dictionary
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                logger.info(f"⏱️ Checking job status... (Job ID: {job_id})")
                
                response = self.session.get(f"{self.status_url}/{job_id}", timeout=30)
                response.raise_for_status()
                
                status_data = response.json()
                status = status_data.get('status')
                
                if status == 'COMPLETED':
                    logger.info("✅ Job completed!")
                    return {
                        'status': 'COMPLETED',
                        'output': status_data.get('output'),
                        'job_id': job_id
                    }
                elif status == 'FAILED':
                    logger.error("❌ Job failed.")
                    return {
                        'status': 'FAILED',
                        'error': status_data.get('error', 'Unknown error'),
                        'job_id': job_id
                    }
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    logger.info(f"🏃 Job in progress... (Status: {status})")
                    time.sleep(check_interval)
                else:
                    logger.warning(f"❓ Unknown status: {status}")
                    return {
                        'status': 'UNKNOWN',
                        'data': status_data,
                        'job_id': job_id
                    }
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Status check error: {e}")
                time.sleep(check_interval)
        
        logger.error(f"❌ Job wait timeout ({max_wait_time} seconds)")
        return {
            'status': 'TIMEOUT',
            'job_id': job_id
        }
    
    def save_video_result(self, result: Dict[str, Any], output_path: str) -> bool:
        """
        Save video file from job result
        
        Args:
            result: Job result dictionary
            output_path: File path to save
        
        Returns:
            Save success status
        """
        try:
            if result.get('status') != 'COMPLETED':
                logger.error(f"Job not completed: {result.get('status')}")
                return False
            
            output = result.get('output', {})
            video_b64 = output.get('video')
            
            if not video_b64:
                logger.error("Video data not found")
                return False
            
            # Create directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Decode base64 and save video
            decoded_video = base64.b64decode(video_b64)
            
            with open(output_path, 'wb') as f:
                f.write(decoded_video)
            
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Video saved successfully: {output_path} ({file_size / (1024*1024):.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Video save failed: {e}")
            return False
    
    def create_video_from_image(
        self,
        image: Union[str, bytes] = None,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        end_image: Union[str, bytes] = None,
        end_image_path: Optional[str] = None,
        end_image_url: Optional[str] = None,
        end_image_base64: Optional[str] = None,
        prompt: str = "running man, grab the gun",
        negative_prompt: Optional[str] = None,
        width: int = 720,
        height: int = 1280,
        length: int = 81,
        lora_pairs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate video from image
        
        Args:
            image: Image data (file path, URL, or base64 string) - auto-detected
            image_path: Image file path (alternative to image)
            image_url: Image URL (alternative to image)
            image_base64: Image base64 string (alternative to image)
            end_image: End image data for FLF2V workflow (file path, URL, or base64 string) - auto-detected
            end_image_path: End image file path (alternative to end_image)
            end_image_url: End image URL (alternative to end_image)
            end_image_base64: End image base64 string (alternative to end_image)
            prompt: Prompt text
            negative_prompt: Negative prompt to exclude unwanted elements
            width: Output width (will be adjusted to nearest multiple of 16)
            height: Output height (will be adjusted to nearest multiple of 16)
            length: Number of frames
            lora_pairs: LoRA settings list (unlimited, each item: {"high": "lora_name.safetensors", "low": "lora_name.safetensors", "high_weight": 1.0, "low_weight": 1.0})
        
        Returns:
            Job result dictionary
        """
        # Determine image input (handler supports auto-detection, so we can pass file paths directly)
        image_data = None
        if image is not None:
            # If image is provided, check if it's a file path
            if isinstance(image, str) and os.path.exists(image):
                image_data = image  # Pass file path directly (handler will handle it)
            elif isinstance(image, bytes):
                # If it's bytes, encode to base64
                image_data = self.encode_image_to_base64(image)
                if not image_data:
                    return {"error": "Failed to encode image bytes to base64"}
            else:
                image_data = image  # URL or base64 string
        elif image_path:
            if not os.path.exists(image_path):
                return {"error": f"Image file does not exist: {image_path}"}
            image_data = image_path  # Pass file path directly
        elif image_url:
            image_data = image_url  # Pass URL directly
        elif image_base64:
            image_data = image_base64  # Pass base64 directly
        else:
            return {"error": "No image input provided"}
        
        # Determine end_image input (optional, for FLF2V workflow)
        end_image_data = None
        if end_image is not None:
            # If end_image is provided, check if it's a file path
            if isinstance(end_image, str) and os.path.exists(end_image):
                end_image_data = end_image  # Pass file path directly
            elif isinstance(end_image, bytes):
                # If it's bytes, encode to base64
                end_image_data = self.encode_image_to_base64(end_image)
                if not end_image_data:
                    return {"error": "Failed to encode end_image bytes to base64"}
            else:
                end_image_data = end_image  # URL or base64 string
        elif end_image_path:
            if not os.path.exists(end_image_path):
                return {"error": f"End image file does not exist: {end_image_path}"}
            end_image_data = end_image_path  # Pass file path directly
        elif end_image_url:
            end_image_data = end_image_url  # Pass URL directly
        elif end_image_base64:
            end_image_data = end_image_base64  # Pass base64 directly
        
        # Process LoRA settings
        if lora_pairs is None:
            lora_pairs = []
        
        # Configure API input data
        input_data = {
            "image": image_data,
            "prompt": prompt,
            "width": width,
            "height": height,
            "length": length,
            "lora_pairs": lora_pairs
        }
        
        # Add end_image if provided (enables FLF2V workflow)
        if end_image_data:
            input_data["end_image"] = end_image_data
        
        # Add negative_prompt if provided
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        
        # Submit job and wait
        job_id = self.submit_job(input_data)
        if not job_id:
            return {"error": "Job submission failed"}
        
        result = self.wait_for_completion(job_id)
        return result
    
    def batch_process_images(
        self,
        image_folder_path: str,
        output_folder_path: str,
        valid_extensions: tuple = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff'),
        prompt: str = "running man, grab the gun",
        negative_prompt: Optional[str] = None,
        width: int = 720,
        height: int = 1280,
        length: int = 81,
        lora_pairs: Optional[List[Dict[str, Any]]] = None,
        end_image: Optional[Union[str, bytes]] = None
    ) -> Dict[str, Any]:
        """
        Batch process all image files in folder
        
        Args:
            image_folder_path: Folder path containing image files
            output_folder_path: Folder path to save results
            valid_extensions: Image file extensions to process
            prompt: Prompt text
            negative_prompt: Negative prompt to exclude unwanted elements
            width: Output width (will be adjusted to nearest multiple of 16)
            height: Output height (will be adjusted to nearest multiple of 16)
            length: Number of frames
            lora_pairs: LoRA settings list (unlimited)
            end_image: End image for FLF2V workflow (optional)
        
        Returns:
            Batch processing result dictionary
        """
        # Check path
        if not os.path.isdir(image_folder_path):
            return {"error": f"Image folder does not exist: {image_folder_path}"}
        
        # Create output folder
        os.makedirs(output_folder_path, exist_ok=True)
        
        # Get image file list
        image_files = [
            f for f in os.listdir(image_folder_path)
            if f.lower().endswith(valid_extensions)
        ]
        
        if not image_files:
            return {"error": f"No image files to process: {image_folder_path}"}
        
        logger.info(f"Starting batch processing: {len(image_files)} files")
        
        results = {
            "total_files": len(image_files),
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        # Process each image file
        for filename in image_files:
            logger.info(f"\n==================== Processing started: {filename} ====================")
            
            image_path = os.path.join(image_folder_path, filename)
            
            # Generate video
            result = self.create_video_from_image(
                image_path=image_path,
                end_image=end_image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                length=length,
                lora_pairs=lora_pairs
            )
            
            if result.get('status') == 'COMPLETED':
                # Save result file
                base_filename = os.path.splitext(filename)[0]
                output_filename = os.path.join(output_folder_path, f"result_{base_filename}.mp4")
                
                if self.save_video_result(result, output_filename):
                    logger.info(f"✅ [{filename}] Processing completed")
                    results["successful"] += 1
                    results["results"].append({
                        "filename": filename,
                        "status": "success",
                        "output_file": output_filename,
                        "job_id": result.get('job_id')
                    })
                else:
                    logger.error(f"[{filename}] Result save failed")
                    results["failed"] += 1
                    results["results"].append({
                        "filename": filename,
                        "status": "failed",
                        "error": "Result save failed",
                        "job_id": result.get('job_id')
                    })
            else:
                logger.error(f"[{filename}] Job failed: {result.get('error', 'Unknown error')}")
                results["failed"] += 1
                results["results"].append({
                    "filename": filename,
                    "status": "failed",
                    "error": result.get('error', 'Unknown error'),
                    "job_id": result.get('job_id')
                })
            
            logger.info(f"==================== Processing completed: {filename} ====================")
        
        logger.info(f"\n🎉 Batch processing completed: {results['successful']}/{results['total_files']} successful")
        return results


def main():
    """Usage example"""
    
    # Configuration (change to actual values)
    ENDPOINT_ID = "your-endpoint-id"
    RUNPOD_API_KEY = "your-runpod-api-key"
    
    # Initialize client
    client = GenerateVideoClient(
        runpod_endpoint_id=ENDPOINT_ID,
        runpod_api_key=RUNPOD_API_KEY
    )
    
    print("=== Generate Video Client Usage Example ===\n")
    
    # Example 1: Single image processing
    print("1. Single image processing")
    result1 = client.create_video_from_image(
        image_path="./example_image.png",
        prompt="running man, grab the gun",
        negative_prompt="blurry, low quality, distorted",
        width=720,
        height=1280,
        length=81
    )
    
    if result1.get('status') == 'COMPLETED':
        client.save_video_result(result1, "./output_single.mp4")
    else:
        print(f"Error: {result1.get('error')}")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 2: Processing with multiple LoRAs (unlimited)
    print("2. Processing with multiple LoRAs")
    lora_pairs = [
        {
            "high": "lora1_high.safetensors",
            "low": "lora1_low.safetensors",
            "high_weight": 1.0,
            "low_weight": 1.0
        },
        {
            "high": "lora2_high.safetensors",
            "low": "lora2_low.safetensors",
            "high_weight": 0.8,
            "low_weight": 0.8
        },
        {
            "high": "lora3_high.safetensors",
            "low": "lora3_low.safetensors",
            "high_weight": 0.5,
            "low_weight": 0.5
        }
    ]
    
    result2 = client.create_video_from_image(
        image_path="./example_image.png",
        prompt="running man, grab the gun",
        negative_prompt="blurry, low quality, distorted",
        width=720,
        height=1280,
        length=81,
        lora_pairs=lora_pairs
    )
    
    if result2.get('status') == 'COMPLETED':
        client.save_video_result(result2, "./output_lora.mp4")
    else:
        print(f"Error: {result2.get('error')}")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 3: FLF2V workflow (First-Last Frame to Video)
    print("3. FLF2V workflow (First-Last Frame to Video)")
    result3 = client.create_video_from_image(
        image_path="./start_image.png",
        end_image_path="./end_image.png",
        prompt="smooth transformation from start to end",
        negative_prompt="blurry, low quality, distorted",
        width=720,
        height=1280,
        length=81
    )
    
    if result3.get('status') == 'COMPLETED':
        client.save_video_result(result3, "./output_flf2v.mp4")
    else:
        print(f"Error: {result3.get('error')}")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 4: Using image URL
    print("4. Processing with image URL")
    result4 = client.create_video_from_image(
        image_url="https://example.com/image.jpg",
        prompt="running man, grab the gun",
        width=720,
        height=1280,
        length=81
    )
    
    if result4.get('status') == 'COMPLETED':
        client.save_video_result(result4, "./output_url.mp4")
    else:
        print(f"Error: {result4.get('error')}")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 5: Using base64 encoded image
    print("5. Processing with base64 encoded image")
    # Encode image to base64
    image_base64 = client.encode_file_to_base64("./example_image.png")
    if image_base64:
        result5 = client.create_video_from_image(
            image_base64=image_base64,
            prompt="running man, grab the gun",
            width=720,
            height=1280,
            length=81
        )
        
        if result5.get('status') == 'COMPLETED':
            client.save_video_result(result5, "./output_base64.mp4")
        else:
            print(f"Error: {result5.get('error')}")
    else:
        print("Error: Failed to encode image to base64")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 6: Using static method to encode image
    print("6. Using static method to encode image")
    image_base64_static = GenerateVideoClient.encode_image_to_base64("./example_image.png")
    if image_base64_static:
        result6 = client.create_video_from_image(
            image_base64=image_base64_static,
            prompt="running man, grab the gun",
            width=720,
            height=1280,
            length=81
        )
        
        if result6.get('status') == 'COMPLETED':
            client.save_video_result(result6, "./output_static_base64.mp4")
        else:
            print(f"Error: {result6.get('error')}")
    else:
        print("Error: Failed to encode image to base64")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 5: Batch processing (uncomment to use)
    # print("5. Batch processing")
    # batch_result = client.batch_process_images(
    #     image_folder_path="./input_images",
    #     output_folder_path="./output_videos",
    #     prompt="running man, grab the gun",
    #     width=720,
    #     height=1280,
    #     length=81
    # )
    
    # print(f"Batch processing result: {batch_result}")
    
    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
