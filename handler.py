import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # Base64 에러 처리를 위해 import
import subprocess
import time
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())
def to_nearest_multiple_of_16(value):
    """주어진 값을 가장 가까운 16의 배수로 보정, 최소 16 보장"""
    try:
        numeric_value = float(value)
    except Exception:
        raise Exception(f"width/height 값이 숫자가 아닙니다: {value}")
    adjusted = int(round(numeric_value / 16.0) * 16)
    if adjusted < 16:
        adjusted = 16
    return adjusted
def process_input(input_data, temp_dir, output_filename, input_type):
    """입력 데이터를 처리하여 파일 경로를 반환하는 함수"""
    if input_type == "path":
        # 경로인 경우 그대로 반환
        logger.info(f"📁 경로 입력 처리: {input_data}")
        return input_data
    elif input_type == "url":
        # URL인 경우 다운로드
        logger.info(f"🌐 URL 입력 처리: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        # Base64인 경우 디코딩하여 저장
        logger.info(f"🔢 Base64 입력 처리")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"지원하지 않는 입력 타입: {input_type}")

        
def download_file_from_url(url, output_path):
    """URL에서 파일을 다운로드하는 함수"""
    try:
        # wget을 사용하여 파일 다운로드
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ URL에서 파일을 성공적으로 다운로드했습니다: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wget 다운로드 실패: {result.stderr}")
            raise Exception(f"URL 다운로드 실패: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ 다운로드 시간 초과")
        raise Exception("다운로드 시간 초과")
    except Exception as e:
        logger.error(f"❌ 다운로드 중 오류 발생: {e}")
        raise Exception(f"다운로드 중 오류 발생: {e}")


def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Base64 데이터를 파일로 저장하는 함수"""
    try:
        # Base64 문자열 디코딩
        decoded_data = base64.b64decode(base64_data)
        
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(temp_dir, exist_ok=True)
        
        # 파일로 저장
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)
        
        logger.info(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 디코딩 실패: {e}")
        raise Exception(f"Base64 디코딩 실패: {e}")
    
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
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # fullpath를 이용하여 직접 파일을 읽고 base64로 인코딩
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)

def get_next_available_node_id(prompt, start_id=1000):
    """사용 가능한 다음 노드 ID를 찾는 함수"""
    node_id = start_id
    while str(node_id) in prompt:
        node_id += 1
    return str(node_id)

def add_lora_to_chain(prompt, existing_lora_node_id, lora_name, strength, is_flf2v):
    """
    기존 LoRA 체인에 새로운 LoRA를 추가하는 함수 (Linked list 방식)
    
    Args:
        prompt: 워크플로우 딕셔너리
        existing_lora_node_id: 기존 LoRA 노드 ID (문자열)
        lora_name: 새로 추가할 LoRA 파일명
        strength: LoRA 강도
        is_flf2v: FLF2V 워크플로우 여부
    
    Returns:
        새로 생성된 LoRA 노드 ID
    """
    # 기존 LoRA 노드 확인
    if existing_lora_node_id not in prompt:
        raise Exception(f"기존 LoRA 노드 {existing_lora_node_id}를 찾을 수 없습니다.")
    
    existing_lora = prompt[existing_lora_node_id]
    if existing_lora.get("class_type") != "LoraLoaderModelOnly":
        raise Exception(f"노드 {existing_lora_node_id}는 LoRA 노드가 아닙니다.")
    
    # 기존 LoRA의 입력(이전 노드)을 찾음
    previous_node_input = existing_lora["inputs"].get("model")
    if not previous_node_input or not isinstance(previous_node_input, list):
        raise Exception(f"기존 LoRA 노드 {existing_lora_node_id}의 입력을 찾을 수 없습니다.")
    
    previous_node_id = str(previous_node_input[0])
    
    # 새로운 LoRA 노드 생성
    new_lora_node_id = get_next_available_node_id(prompt)
    
    # 새 LoRA 노드 생성 (기존 LoRA 노드의 구조를 복사)
    new_lora_node = {
        "inputs": {
            "lora_name": lora_name,
            "strength_model": strength,
            "model": [
                previous_node_id,  # 기존 LoRA가 받던 입력을 새 LoRA가 받음
                0
            ]
        },
        "class_type": "LoraLoaderModelOnly",
        "_meta": {
            "title": f"LoRA 로드 (모델 전용) - {lora_name}"
        }
    }
    
    # 새 LoRA 노드를 워크플로우에 추가
    prompt[new_lora_node_id] = new_lora_node
    
    # 기존 LoRA 노드의 입력을 새 LoRA 노드로 변경
    existing_lora["inputs"]["model"] = [new_lora_node_id, 0]
    
    logger.info(f"✅ LoRA 추가: {previous_node_id} -> {new_lora_node_id} -> {existing_lora_node_id} (LoRA: {lora_name}, 강도: {strength})")
    
    return new_lora_node_id

def apply_lora_chain(prompt, lora_list, high_lora_node_id, low_lora_node_id, high_sampling_node_id, low_sampling_node_id, is_flf2v):
    """
    LoRA 리스트를 체인에 추가하는 함수
    
    Args:
        prompt: 워크플로우 딕셔너리
        lora_list: LoRA 리스트, 각 항목은 {"high": "lora_name.safetensors", "low": "lora_name.safetensors", "high_weight": 1.0, "low_weight": 1.0}
        high_lora_node_id: HIGH LoRA의 시작 노드 ID
        low_lora_node_id: LOW LoRA의 시작 노드 ID
        high_sampling_node_id: HIGH ModelSamplingSD3 노드 ID
        low_sampling_node_id: LOW ModelSamplingSD3 노드 ID
        is_flf2v: FLF2V 워크플로우 여부
    
    Returns:
        (마지막 HIGH LoRA 노드 ID, 마지막 LOW LoRA 노드 ID)
    """
    if not lora_list:
        return (high_lora_node_id, low_lora_node_id)
    
    # 첫 번째 LoRA는 기존 노드를 업데이트
    first_lora = lora_list[0]
    
    # HIGH LoRA 첫 번째 처리
    if first_lora.get("high"):
        prompt[high_lora_node_id]["inputs"]["lora_name"] = first_lora["high"]
        prompt[high_lora_node_id]["inputs"]["strength_model"] = first_lora.get("high_weight", 1.0)
        logger.info(f"✅ HIGH LoRA 1 적용: {first_lora['high']} (강도: {first_lora.get('high_weight', 1.0)})")
    
    # LOW LoRA 첫 번째 처리
    if first_lora.get("low"):
        prompt[low_lora_node_id]["inputs"]["lora_name"] = first_lora["low"]
        prompt[low_lora_node_id]["inputs"]["strength_model"] = first_lora.get("low_weight", 1.0)
        logger.info(f"✅ LOW LoRA 1 적용: {first_lora['low']} (강도: {first_lora.get('low_weight', 1.0)})")
    
    # 나머지 LoRA들을 체인에 추가
    current_high_lora_id = high_lora_node_id
    current_low_lora_id = low_lora_node_id
    
    for i, lora_pair in enumerate(lora_list[1:], start=2):
        # HIGH LoRA 체인에 추가
        if lora_pair.get("high"):
            current_high_lora_id = add_lora_to_chain(
                prompt, 
                current_high_lora_id, 
                lora_pair["high"], 
                lora_pair.get("high_weight", 1.0),
                is_flf2v
            )
        
        # LOW LoRA 체인에 추가
        if lora_pair.get("low"):
            current_low_lora_id = add_lora_to_chain(
                prompt, 
                current_low_lora_id, 
                lora_pair["low"], 
                lora_pair.get("low_weight", 1.0),
                is_flf2v
            )
    
    # ModelSamplingSD3 노드가 마지막 LoRA 노드를 참조하도록 업데이트
    if high_sampling_node_id in prompt:
        prompt[high_sampling_node_id]["inputs"]["model"] = [current_high_lora_id, 0]
        logger.info(f"✅ HIGH ModelSamplingSD3 노드({high_sampling_node_id})가 마지막 HIGH LoRA({current_high_lora_id})를 참조하도록 업데이트")
    
    if low_sampling_node_id in prompt:
        prompt[low_sampling_node_id]["inputs"]["model"] = [current_low_lora_id, 0]
        logger.info(f"✅ LOW ModelSamplingSD3 노드({low_sampling_node_id})가 마지막 LOW LoRA({current_low_lora_id})를 참조하도록 업데이트")
    
    return (current_high_lora_id, current_low_lora_id)

def handler(job):
    job_input = job.get("input", {})

    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    # 이미지 입력 처리 (image, image_path, image_url, image_base64 중 하나만 사용)
    image_path = None
    if "image" in job_input:
        # image 파라미터가 제공된 경우, 자동으로 타입 감지
        image_data = job_input["image"]
        if isinstance(image_data, str):
            if image_data.startswith("http://") or image_data.startswith("https://"):
                image_path = process_input(image_data, task_id, "input_image.jpg", "url")
            elif os.path.exists(image_data) or image_data.startswith("/"):
                image_path = process_input(image_data, task_id, "input_image.jpg", "path")
            else:
                # Base64로 간주
                image_path = process_input(image_data, task_id, "input_image.jpg", "base64")
        else:
            raise Exception("image 파라미터는 문자열이어야 합니다.")
    elif "image_path" in job_input:
        image_path = process_input(job_input["image_path"], task_id, "input_image.jpg", "path")
    elif "image_url" in job_input:
        image_path = process_input(job_input["image_url"], task_id, "input_image.jpg", "url")
    elif "image_base64" in job_input:
        image_path = process_input(job_input["image_base64"], task_id, "input_image.jpg", "base64")
    else:
        # 기본값 사용
        image_path = "/example_image.png"
        logger.info("기본 이미지 파일을 사용합니다: /example_image.png")

    # 엔드 이미지 입력 처리 (end_image, end_image_path, end_image_url, end_image_base64 중 하나만 사용)
    end_image_path_local = None
    if "end_image" in job_input:
        # end_image 파라미터가 제공된 경우, 자동으로 타입 감지
        end_image_data = job_input["end_image"]
        if isinstance(end_image_data, str):
            if end_image_data.startswith("http://") or end_image_data.startswith("https://"):
                end_image_path_local = process_input(end_image_data, task_id, "end_image.jpg", "url")
            elif os.path.exists(end_image_data) or end_image_data.startswith("/"):
                end_image_path_local = process_input(end_image_data, task_id, "end_image.jpg", "path")
            else:
                # Base64로 간주
                end_image_path_local = process_input(end_image_data, task_id, "end_image.jpg", "base64")
        else:
            raise Exception("end_image 파라미터는 문자열이어야 합니다.")
    elif "end_image_path" in job_input:
        end_image_path_local = process_input(job_input["end_image_path"], task_id, "end_image.jpg", "path")
    elif "end_image_url" in job_input:
        end_image_path_local = process_input(job_input["end_image_url"], task_id, "end_image.jpg", "url")
    elif "end_image_base64" in job_input:
        end_image_path_local = process_input(job_input["end_image_base64"], task_id, "end_image.jpg", "base64")
    
    # 워크플로우 파일 선택 (end_image_*가 있으면 FLF2V 워크플로 사용)
    is_flf2v = end_image_path_local is not None
    workflow_file = "/wan22_flf2v_api.json" if is_flf2v else "/wan22_api.json"
    logger.info(f"Using {'FLF2V' if is_flf2v else 'single image'} workflow")
    
    prompt = load_workflow(workflow_file)
    
    length = job_input.get("length", 81)
    
    # 해상도(폭/높이) 16배수 보정
    original_width = job_input.get("width", 720)
    original_height = job_input.get("height", 1280)
    adjusted_width = to_nearest_multiple_of_16(original_width)
    adjusted_height = to_nearest_multiple_of_16(original_height)
    if adjusted_width != original_width:
        logger.info(f"Width adjusted to nearest multiple of 16: {original_width} -> {adjusted_width}")
    if adjusted_height != original_height:
        logger.info(f"Height adjusted to nearest multiple of 16: {original_height} -> {adjusted_height}")

    if is_flf2v:
        # FLF2V 워크플로우 (wan22_flf2v_api.json)
        # Start 이미지: 노드 102
        prompt["102"]["inputs"]["image"] = image_path
        # End 이미지: 노드 103
        prompt["103"]["inputs"]["image"] = end_image_path_local
        # Positive Prompt: 노드 6
        prompt["6"]["inputs"]["text"] = job_input.get("prompt", "")
        # Negative Prompt: 노드 7
        prompt["7"]["inputs"]["text"] = job_input.get("negative_prompt", "bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards")
        # Width: 노드 99
        prompt["99"]["inputs"]["value"] = adjusted_width
        # Height: 노드 100
        prompt["100"]["inputs"]["value"] = adjusted_height
        # Length: 노드 67
        prompt["67"]["inputs"]["length"] = length
    else:
        # 단일 이미지 워크플로우 (wan22_api.json)
        # 이미지 로드: 노드 97
        prompt["97"]["inputs"]["image"] = image_path
        # Positive Prompt: 노드 93
        prompt["93"]["inputs"]["text"] = job_input.get("prompt", "")
        # Negative Prompt: 노드 89
        prompt["89"]["inputs"]["text"] = job_input.get("negative_prompt", "bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards")
        # Width/Height: 노드 118 (ResizeAndPadImage)
        prompt["118"]["inputs"]["target_width"] = adjusted_width
        prompt["118"]["inputs"]["target_height"] = adjusted_height
        # Length: 노드 98
        prompt["98"]["inputs"]["length"] = length
    
    # LoRA 설정 적용
    lora_list = job_input.get("lora_pairs", [])
    if lora_list:
        if is_flf2v:
            # FLF2V 워크플로우: HIGH LoRA(91), LOW LoRA(92), HIGH Sampling(54), LOW Sampling(55)
            apply_lora_chain(prompt, lora_list, "91", "92", "54", "55", is_flf2v)
        else:
            # 단일 이미지 워크플로우: HIGH LoRA(101), LOW LoRA(102), HIGH Sampling(104), LOW Sampling(103)
            apply_lora_chain(prompt, lora_list, "101", "102", "104", "103", is_flf2v)

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
        import time
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