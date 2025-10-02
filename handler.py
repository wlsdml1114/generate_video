import base64
import binascii  # Base64 에러 처리를 위해 import
import json
import logging
import os
import time
import uuid
from io import BytesIO

import websocket
import urllib.parse
import urllib.request
from PIL import Image, UnidentifiedImageError

import runpod

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())
_comfy_input_dir_env = os.getenv("COMFY_INPUT_DIR")
DEFAULT_IMAGE_PATH = os.getenv("DEFAULT_IMAGE_PATH", "/example_image.png")
RUNPOD_VOLUME_MOUNT = os.getenv("RUNPOD_VOLUME_MOUNT", "/runpod-volume")


def _determine_comfy_input_dir() -> str:
    candidates = []
    if _comfy_input_dir_env:
        candidates.append(_comfy_input_dir_env)
    candidates.extend([
        "/ComfyUI/input",
        "/workspace/ComfyUI/input",
    ])

    seen = []
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.append(candidate)
        abs_candidate = os.path.abspath(candidate)
        if os.path.isdir(abs_candidate):
            logger.info(f"ComfyUI input 디렉터리를 사용합니다: {abs_candidate}")
            return abs_candidate

    for candidate in seen:
        abs_candidate = os.path.abspath(candidate)
        try:
            os.makedirs(abs_candidate, exist_ok=True)
            logger.info(f"ComfyUI input 디렉터리를 생성했습니다: {abs_candidate}")
            return abs_candidate
        except OSError as exc:
            logger.warning(f"ComfyUI input 디렉터리를 생성하지 못했습니다: {abs_candidate} ({exc})")

    raise RuntimeError("ComfyUI input 디렉터리를 찾거나 생성할 수 없습니다.")


COMFY_INPUT_DIR = _determine_comfy_input_dir()


def _strip_base64_header(image_data: str) -> str:
    if not isinstance(image_data, str) or not image_data.strip():
        raise ValueError("Base64 이미지 데이터가 비어 있습니다.")
    cleaned = image_data.strip()
    if cleaned.startswith("data:"):
        header, _, payload = cleaned.partition(",")
        if not payload:
            raise ValueError("Base64 이미지 데이터 형식이 올바르지 않습니다.")
        cleaned = payload
    return cleaned


def _resolve_image_path(path_input: str) -> str:
    if not isinstance(path_input, str) or not path_input.strip():
        raise FileNotFoundError("이미지 경로가 비어 있습니다.")

    normalized = os.path.expanduser(path_input.strip())

    candidates = []

    def _add_candidate(candidate):
        candidate = os.path.abspath(candidate)
        if candidate not in candidates:
            candidates.append(candidate)

    _add_candidate(normalized)

    sanitized = normalized.lstrip("/")
    if sanitized:
        _add_candidate(os.path.join(os.getcwd(), sanitized))
        _add_candidate(os.path.join(RUNPOD_VOLUME_MOUNT, sanitized))

    if not os.path.isabs(normalized):
        _add_candidate(os.path.join(os.getcwd(), normalized))
        _add_candidate(os.path.join(RUNPOD_VOLUME_MOUNT, normalized))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(normalized)

def _normalise_image_mode(image: Image.Image) -> Image.Image:
    mode = image.mode
    if mode in ("RGB", "RGBA", "L"):
        return image
    if mode in ("LA",):
        return image.convert("RGBA")
    if mode in ("CMYK", "YCbCr", "P", "HSV", "I", "I;16", "F"):
        return image.convert("RGB")
    try:
        return image.convert("RGB")
    except Exception:
        return image


def _write_image_to_comfy(image_bytes: bytes, task_id: str) -> str:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.load()
            image = _normalise_image_mode(image)
            os.makedirs(COMFY_INPUT_DIR, exist_ok=True)
            dest_name = f"{task_id}.png"
            dest_path = os.path.join(COMFY_INPUT_DIR, dest_name)
            image.save(dest_path, format="PNG")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("유효하지 않은 이미지 데이터입니다.") from exc

    logger.info(f"이미지를 ComfyUI input 디렉터리에 저장했습니다: {dest_path}")
    return dest_name


def _copy_into_comfy_input(image_path: str, task_id: str) -> str:
    with open(image_path, "rb") as source_file:
        image_bytes = source_file.read()
    return _write_image_to_comfy(image_bytes, task_id)


def _save_base64_image(image_data: str, task_id: str) -> str:
    cleaned = _strip_base64_header(image_data)
    try:
        image_bytes = base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Base64 이미지 디코딩 실패") from exc

    return _write_image_to_comfy(image_bytes, task_id)


def prepare_image_asset(job_input: dict, task_id: str) -> str:
    image_base64_input = job_input.get("image_base64")
    image_path_input = job_input.get("image_path")

    if image_base64_input:
        return _save_base64_image(image_base64_input, task_id)

    path_to_use = image_path_input or DEFAULT_IMAGE_PATH
    resolved_path = _resolve_image_path(path_to_use)
    return _copy_into_comfy_input(resolved_path, task_id)


def _read_output_entry(media_entry: dict) -> bytes:
    fullpath = media_entry.get("fullpath")
    if fullpath and os.path.exists(fullpath):
        with open(fullpath, "rb") as output_file:
            return output_file.read()

    filename = media_entry.get("filename")
    if filename:
        subfolder = media_entry.get("subfolder", "")
        folder_type = media_entry.get("type", "output")
        try:
            return get_image(filename, subfolder, folder_type)
        except Exception as exc:
            logger.warning(f"출력 파일을 HTTP로 읽는 데 실패했습니다: {filename} ({exc})")

    raise FileNotFoundError(fullpath or filename or "output entry")

def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_videos(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id, node_output in history['outputs'].items():
        videos_output = []
        for media_key in ("gifs", "videos"):
            media_entries = node_output.get(media_key)
            if not media_entries:
                continue
            for media_entry in media_entries:
                try:
                    media_bytes = _read_output_entry(media_entry)
                    video_data = base64.b64encode(media_bytes).decode('utf-8')
                    videos_output.append(video_data)
                except Exception as exc:
                    logger.warning(f"출력 미디어를 처리하는 중 오류 발생 ({media_key}): {exc}")
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)

def handler(job):
    job_input = job.get("input", {})

    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    try:
        image_filename = prepare_image_asset(job_input, task_id)
    except FileNotFoundError as exc:
        logger.error(f"이미지 파일을 찾을 수 없습니다: {exc}")
        return {"error": f"이미지 파일을 찾을 수 없습니다: {exc}"}
    except ValueError as exc:
        logger.error(f"유효하지 않은 이미지 입력입니다: {exc}")
        return {"error": str(exc)}
    except Exception as exc:
        logger.exception("이미지를 준비하는 중 예기치 못한 오류가 발생했습니다.")
        return {"error": f"이미지를 준비하는 중 오류가 발생했습니다: {exc}"}
    
    # LoRA 설정 확인 - 배열로 받아서 처리
    lora_pairs = job_input.get("lora_pairs", [])
    
    # LoRA 개수에 따라 적절한 워크플로우 파일 선택
    lora_count = len(lora_pairs)
    if lora_count == 0:
        workflow_file = "/wan22_nolora.json"
        logger.info("Using no LoRA workflow")
    elif lora_count == 1:
        workflow_file = "/wan22_1lora.json"
        logger.info("Using 1 LoRA pair workflow")
    elif lora_count == 2:
        workflow_file = "/wan22_2lora.json"
        logger.info("Using 2 LoRA pairs workflow")
    elif lora_count == 3:
        workflow_file = "/wan22_3lora.json"
        logger.info("Using 3 LoRA pairs workflow")
    else:
        logger.warning(f"LoRA 개수가 {lora_count}개입니다. 최대 3개까지만 지원됩니다. 3개로 제한합니다.")
        lora_count = 3
        workflow_file = "/wan22_3lora.json"
        lora_pairs = lora_pairs[:3]  # 처음 3개만 사용
    
    prompt = load_workflow(workflow_file)
    
    length = job_input.get("length", 81)
    steps = job_input.get("steps", 10)

    prompt["260"]["inputs"]["image"] = image_filename
    prompt["846"]["inputs"]["value"] = length
    prompt["246"]["inputs"]["value"] = job_input["prompt"]
    prompt["835"]["inputs"]["noise_seed"] = job_input["seed"]
    prompt["830"]["inputs"]["cfg"] = job_input["cfg"]
    prompt["849"]["inputs"]["value"] = job_input["width"]
    prompt["848"]["inputs"]["value"] = job_input["height"]
    
    # step 설정 적용
    if "834" in prompt:
        prompt["834"]["inputs"]["steps"] = steps
        logger.info(f"Steps set to: {steps}")
        lowsteps = int(steps*0.6)
        prompt["829"]["inputs"]["step"] = lowsteps
        logger.info(f"LowSteps set to: {lowsteps}")
    
    # LoRA 설정 적용
    if lora_count > 0:
        # LoRA 노드 ID 매핑 (각 워크플로우에서 LoRA 노드 ID가 다름)
        lora_node_mapping = {
            1: {
                "high": ["282"],
                "low": ["286"]
            },
            2: {
                "high": ["282", "339"],
                "low": ["286", "337"]
            },
            3: {
                "high": ["282", "339", "340"],
                "low": ["286", "337", "338"]
            }
        }
        
        current_mapping = lora_node_mapping[lora_count]
        
        for i, lora_pair in enumerate(lora_pairs):
            if i < lora_count:
                lora_high = lora_pair.get("high")
                lora_low = lora_pair.get("low")
                lora_high_weight = lora_pair.get("high_weight", 1.0)
                lora_low_weight = lora_pair.get("low_weight", 1.0)
                
                # HIGH LoRA 설정
                if i < len(current_mapping["high"]):
                    high_node_id = current_mapping["high"][i]
                    if high_node_id in prompt and lora_high:
                        prompt[high_node_id]["inputs"]["lora_name"] = lora_high
                        prompt[high_node_id]["inputs"]["strength_model"] = lora_high_weight
                        logger.info(f"LoRA {i+1} HIGH applied: {lora_high} with weight {lora_high_weight}")
                
                # LOW LoRA 설정
                if i < len(current_mapping["low"]):
                    low_node_id = current_mapping["low"][i]
                    if low_node_id in prompt and lora_low:
                        prompt[low_node_id]["inputs"]["lora_name"] = lora_low
                        prompt[low_node_id]["inputs"]["strength_model"] = lora_low_weight
                        logger.info(f"LoRA {i+1} LOW applied: {lora_low} with weight {lora_low_weight}")

    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    
    # 먼저 HTTP 연결이 가능한지 확인
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    
    # HTTP 연결 확인 (최대 1분)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            import urllib.request
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP 연결 성공 (시도 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            time.sleep(1)
    
    ws = websocket.WebSocket()
    # 웹소켓 연결 시도 (최대 3분)
    max_attempts = int(180/5)  # 3분 (1초에 한 번씩 시도)
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
    videos = get_videos(ws, prompt)
    ws.close()

    # 이미지가 없는 경우 처리
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}
    
    return {"error": "비디오를를 찾을 수 없습니다."}

runpod.serverless.start({"handler": handler})
