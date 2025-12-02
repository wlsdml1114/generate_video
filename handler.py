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
    """워크플로우 파일을 로드하는 함수"""
    # 상대 경로인 경우 현재 파일 기준으로 절대 경로 변환
    if not os.path.isabs(workflow_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(current_dir, workflow_path)
    with open(workflow_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_next_available_node_id(prompt, start_id=1000):
    """사용 가능한 다음 노드 ID를 찾는 함수"""
    node_id = start_id
    while str(node_id) in prompt:
        node_id += 1
    return str(node_id)

def count_user_loras(lora_pairs):
    """
    사용자 LoRA 개수를 계산하는 함수 (lightx2v_4steps_lora 제외)
    
    Args:
        lora_pairs: LoRA 페어 리스트
    
    Returns:
        lightx2v_4steps_lora를 제외한 LoRA 개수
    """
    if not lora_pairs:
        return 0
    
    count = 0
    for lora_pair in lora_pairs:
        high = lora_pair.get("high", "")
        low = lora_pair.get("low", "")
        
        # lightx2v_4steps_lora가 아닌 경우만 카운트
        if high and "lightx2v_4steps_lora" not in high:
            count += 1
        elif low and "lightx2v_4steps_lora" not in low:
            count += 1
        elif high and low and "lightx2v_4steps_lora" not in high and "lightx2v_4steps_lora" not in low:
            count += 1
    
    return count

def filter_user_loras(lora_pairs):
    """
    lightx2v_4steps_lora를 제외한 사용자 LoRA만 필터링
    
    Args:
        lora_pairs: LoRA 페어 리스트
    
    Returns:
        lightx2v_4steps_lora를 제외한 LoRA 페어 리스트
    """
    if not lora_pairs:
        return []
    
    filtered = []
    for lora_pair in lora_pairs:
        high = lora_pair.get("high", "")
        low = lora_pair.get("low", "")
        
        # lightx2v_4steps_lora가 포함된 경우 제외
        if high and "lightx2v_4steps_lora" in high:
            continue
        if low and "lightx2v_4steps_lora" in low:
            continue
        
        filtered.append(lora_pair)
    
    return filtered

def apply_loras_to_workflow(prompt, lora_pairs, is_flf2v, workflow_file):
    """
    워크플로우에 LoRA 설정을 적용하는 함수
    각 워크플로우 파일에는 이미 LoRA 노드가 설정되어 있으므로, 
    해당 노드의 lora_name과 strength_model만 업데이트
    
    Args:
        prompt: 워크플로우 딕셔너리
        lora_pairs: LoRA 페어 리스트 (lightx2v 제외)
        is_flf2v: FLF2V 워크플로우 여부
        workflow_file: 워크플로우 파일 경로 (노드 ID 매핑을 위해 사용)
    """
    if not lora_pairs:
        return
    
    # 각 workflow 파일별 사용자 LoRA 노드 ID 매핑 (HIGH, LOW 순서)
    # 체인 구조: 
    # HIGH: UNETLoader(230) -> lightx2v(283) -> 사용자LoRA(282) -> 사용자LoRA(339) -> 사용자LoRA(340) -> 사용자LoRA(341) -> TorchCompile(391)
    # LOW: UNETLoader(235) -> lightx2v(284) -> 사용자LoRA(336) -> 사용자LoRA(285) -> 사용자LoRA(286) -> 사용자LoRA(337) -> TorchCompile(390)
    lora_node_mapping = {
        "workflow/wan22_nolora.json": {
            "high": [],
            "low": []
        },
        "workflow/wan22_1lora.json": {
            "high": ["282"],  # lightx2v(283) 다음 첫 번째 사용자 LoRA
            "low": ["336"]   # lightx2v(284) 다음 첫 번째 사용자 LoRA
        },
        "workflow/wan22_2lora.json": {
            "high": ["282", "339"],  # lightx2v(283) -> 282 -> 339
            "low": ["336", "285"]    # lightx2v(284) -> 336 -> 285
        },
        "workflow/wan22_3lora.json": {
            "high": ["282", "339", "340"],  # lightx2v(283) -> 282 -> 339 -> 340
            "low": ["336", "285", "286"]    # lightx2v(284) -> 336 -> 285 -> 286
        },
        "workflow/wan22_4lora.json": {
            "high": ["282", "339", "340", "341"],  # lightx2v(283) -> 282 -> 339 -> 340 -> 341
            "low": ["336", "285", "286", "337"]    # lightx2v(284) -> 336 -> 285 -> 286 -> 337
        },
        "workflow/wan22_flf2v.json": {
            "high": [],  # FLF2V는 별도 확인 필요
            "low": []
        }
    }
    
    # workflow 파일명에서 매핑 찾기
    workflow_key = None
    for key in lora_node_mapping.keys():
        if key in workflow_file:
            workflow_key = key
            break
    
    if workflow_key is None:
        logger.warning(f"워크플로우 파일 {workflow_file}에 대한 LoRA 노드 매핑을 찾을 수 없습니다.")
        return
    
    high_user_nodes = lora_node_mapping[workflow_key]["high"]
    low_user_nodes = lora_node_mapping[workflow_key]["low"]
    
    logger.info(f"워크플로우: {workflow_key}")
    logger.info(f"HIGH 사용자 LoRA 노드: {high_user_nodes}")
    logger.info(f"LOW 사용자 LoRA 노드: {low_user_nodes}")
    
    if len(high_user_nodes) < len(lora_pairs) or len(low_user_nodes) < len(lora_pairs):
        logger.warning(f"워크플로우에 사용자 LoRA 노드가 부족합니다. 필요: HIGH={len(lora_pairs)}, LOW={len(lora_pairs)}, 발견: HIGH={len(high_user_nodes)}, LOW={len(low_user_nodes)}")
        return
    
    # 각 lora_pair에 대해 HIGH와 LOW를 적용
    for i, lora_pair in enumerate(lora_pairs):
        # HIGH LoRA 적용
        if i < len(high_user_nodes) and lora_pair.get("high"):
            high_node_id = high_user_nodes[i]
            prompt[high_node_id]["inputs"]["lora_name"] = lora_pair["high"]
            prompt[high_node_id]["inputs"]["strength_model"] = lora_pair.get("high_weight", 1.0)
            logger.info(f"✅ HIGH LoRA {i+1} 적용: {lora_pair['high']} (강도: {lora_pair.get('high_weight', 1.0)}) -> 노드 {high_node_id}")
        
        # LOW LoRA 적용
        if i < len(low_user_nodes) and lora_pair.get("low"):
            low_node_id = low_user_nodes[i]
            prompt[low_node_id]["inputs"]["lora_name"] = lora_pair["low"]
            prompt[low_node_id]["inputs"]["strength_model"] = lora_pair.get("low_weight", 1.0)
            logger.info(f"✅ LOW LoRA {i+1} 적용: {lora_pair['low']} (강도: {lora_pair.get('low_weight', 1.0)}) -> 노드 {low_node_id}")

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
    
    # LoRA 개수 계산 (lightx2v_4steps_lora 제외)
    lora_pairs = job_input.get("lora_pairs", [])
    user_lora_pairs = filter_user_loras(lora_pairs)
    lora_count = count_user_loras(lora_pairs)
    
    logger.info(f"사용자 LoRA 개수 (lightx2v 제외): {lora_count}")
    
    # LoRA 개수에 따라 워크플로우 파일 선택
    if is_flf2v:
        # FLF2V 워크플로우는 현재 하나만 있음
        workflow_file = "workflow/wan22_flf2v.json"
        logger.info(f"Using FLF2V workflow: {workflow_file}")
    else:
        # 단일 이미지 워크플로우
        if lora_count == 0:
            workflow_file = "workflow/wan22_nolora.json"
        elif lora_count == 1:
            workflow_file = "workflow/wan22_1lora.json"
        elif lora_count == 2:
            workflow_file = "workflow/wan22_2lora.json"
        elif lora_count == 3:
            workflow_file = "workflow/wan22_3lora.json"
        elif lora_count >= 4:
            workflow_file = "workflow/wan22_4lora.json"
            if lora_count > 4:
                logger.warning(f"LoRA 개수가 {lora_count}개입니다. 최대 4개까지만 지원됩니다. 처음 4개만 사용합니다.")
                user_lora_pairs = user_lora_pairs[:4]
        else:
            workflow_file = "workflow/wan22_nolora.json"
        
        logger.info(f"Using single image workflow: {workflow_file} (LoRA 개수: {lora_count})")
    
    prompt = load_workflow(workflow_file)
    
    length = job_input.get("length", 81)
    
    # 해상도(폭/높이) 16배수 보정
    original_width = job_input.get("width", 480)
    original_height = job_input.get("height", 720)
    adjusted_width = to_nearest_multiple_of_16(original_width)
    adjusted_height = to_nearest_multiple_of_16(original_height)
    if adjusted_width != original_width:
        logger.info(f"Width adjusted to nearest multiple of 16: {original_width} -> {adjusted_width}")
    if adjusted_height != original_height:
        logger.info(f"Height adjusted to nearest multiple of 16: {original_height} -> {adjusted_height}")

    # 공통 노드 설정 (FLF2V와 단일 이미지 워크플로우 모두 동일)
    # 이미지 로드: 노드 260
    prompt["260"]["inputs"]["image"] = image_path
    # Positive Prompt: 노드 6 (노드 246을 통해 입력)
    prompt["246"]["inputs"]["value"] = job_input.get("prompt", "")
    # Negative Prompt: 노드 7 (노드 247을 통해 입력)
    negative_prompt = job_input.get("negative_prompt", "bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards")
    prompt["247"]["inputs"]["value"] = negative_prompt
    # Width: 노드 849
    prompt["849"]["inputs"]["value"] = adjusted_width
    # Height: 노드 848
    prompt["848"]["inputs"]["value"] = adjusted_height
    # Length: 노드 846
    prompt["846"]["inputs"]["value"] = length
    
    # FLF2V 전용 설정
    if is_flf2v:
        # End 이미지: 노드 483
        prompt["483"]["inputs"]["image"] = end_image_path_local
    
    # LoRA 설정 적용 (lightx2v 제외한 사용자 LoRA만)
    if user_lora_pairs:
        apply_loras_to_workflow(prompt, user_lora_pairs, is_flf2v, workflow_file)

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