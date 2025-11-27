#!/usr/bin/env python3
"""
LoRA 체인 테스트 스크립트
LoRA가 제대로 체인에 추가되는지 확인하는 테스트 코드
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional

# handler.py의 함수들을 import하기 위해 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# runpod 모듈을 모킹하여 서버리스 워커가 시작되지 않도록 함
import types
mock_runpod = types.ModuleType('runpod')
mock_runpod.serverless = types.ModuleType('serverless')
mock_runpod.serverless.start = lambda x: None  # 빈 함수로 모킹
mock_runpod.serverless.utils = types.ModuleType('utils')
mock_runpod.serverless.utils.rp_upload = lambda x: None

sys.modules['runpod'] = mock_runpod
sys.modules['runpod.serverless'] = mock_runpod.serverless
sys.modules['runpod.serverless.utils'] = mock_runpod.serverless.utils

# 이제 handler를 import해도 runpod.serverless.start()가 실행되지 않음
from handler import (
    load_workflow,
    apply_lora_chain,
    get_next_available_node_id
)

def print_node_chain(prompt: Dict[str, Any], start_node_id: str, chain_type: str = ""):
    """
    노드 체인을 추적하여 출력하는 함수
    
    Args:
        prompt: 워크플로우 딕셔너리
        start_node_id: 시작 노드 ID
        chain_type: 체인 타입 (HIGH/LOW)
    """
    print(f"\n{'='*60}")
    print(f"{chain_type} LoRA 체인 추적 (시작 노드: {start_node_id})")
    print(f"{'='*60}")
    
    visited = set()
    current_id = start_node_id
    chain = []
    
    while current_id and current_id not in visited:
        visited.add(current_id)
        
        if current_id not in prompt:
            print(f"❌ 노드 {current_id}를 찾을 수 없습니다.")
            break
        
        node = prompt[current_id]
        node_type = node.get("class_type", "Unknown")
        
        chain.append({
            "node_id": current_id,
            "type": node_type,
            "inputs": node.get("inputs", {})
        })
        
        # 다음 노드 찾기
        if node_type == "LoraLoaderModelOnly":
            model_input = node.get("inputs", {}).get("model")
            if model_input and isinstance(model_input, list):
                next_id = str(model_input[0])
                lora_name = node.get("inputs", {}).get("lora_name", "N/A")
                strength = node.get("inputs", {}).get("strength_model", "N/A")
                print(f"  노드 {current_id}: {node_type}")
                print(f"    LoRA: {lora_name}")
                print(f"    강도: {strength}")
                print(f"    입력: 노드 {next_id}")
                current_id = next_id
            else:
                print(f"  노드 {current_id}: {node_type}")
                print(f"    LoRA: {node.get('inputs', {}).get('lora_name', 'N/A')}")
                print(f"    강도: {node.get('inputs', {}).get('strength_model', 'N/A')}")
                print(f"    입력: 없음 (체인 끝)")
                break
        else:
            print(f"  노드 {current_id}: {node_type}")
            break
    
    print(f"\n체인 길이: {len(chain)}개 노드")
    return chain

def test_lora_chain(test_name: str, lora_pairs: List[Dict[str, Any]], is_flf2v: bool = False):
    """
    LoRA 체인 테스트 함수
    
    Args:
        test_name: 테스트 이름
        lora_pairs: LoRA 페어 리스트
        is_flf2v: FLF2V 워크플로우 여부
    """
    print(f"\n{'#'*80}")
    print(f"# 테스트: {test_name}")
    print(f"{'#'*80}")
    print(f"LoRA 개수: {len(lora_pairs)}")
    print(f"워크플로우: {'FLF2V' if is_flf2v else '단일 이미지'}")
    
    # 워크플로우 로드
    workflow_file = "/wan22_flf2v_api.json" if is_flf2v else "/wan22_api.json"
    workflow_path = os.path.join(os.path.dirname(__file__), workflow_file.lstrip("/"))
    
    if not os.path.exists(workflow_path):
        print(f"❌ 워크플로우 파일을 찾을 수 없습니다: {workflow_path}")
        return None
    
    # 원본 워크플로우를 딥카피로 로드 (원본 보존)
    import copy
    prompt_before = load_workflow(workflow_path)
    prompt = copy.deepcopy(prompt_before)
    
    # 워크플로우별 노드 ID 설정
    if is_flf2v:
        high_lora_node_id = "91"
        low_lora_node_id = "92"
        high_sampling_node_id = "54"
        low_sampling_node_id = "55"
    else:
        high_lora_node_id = "101"
        low_lora_node_id = "102"
        high_sampling_node_id = "104"
        low_sampling_node_id = "103"
    
    # LoRA 적용 전 상태 확인
    print(f"\n{'='*60}")
    print("LoRA 적용 전 상태")
    print(f"{'='*60}")
    print(f"HIGH LoRA 노드 ({high_lora_node_id}):")
    if high_lora_node_id in prompt:
        high_node = prompt[high_lora_node_id]
        print(f"  LoRA: {high_node.get('inputs', {}).get('lora_name', 'N/A')}")
        print(f"  강도: {high_node.get('inputs', {}).get('strength_model', 'N/A')}")
        print(f"  입력: {high_node.get('inputs', {}).get('model', 'N/A')}")
    
    print(f"\nLOW LoRA 노드 ({low_lora_node_id}):")
    if low_lora_node_id in prompt:
        low_node = prompt[low_lora_node_id]
        print(f"  LoRA: {low_node.get('inputs', {}).get('lora_name', 'N/A')}")
        print(f"  강도: {low_node.get('inputs', {}).get('strength_model', 'N/A')}")
        print(f"  입력: {low_node.get('inputs', {}).get('model', 'N/A')}")
    
    # LoRA 적용
    if lora_pairs:
        try:
            apply_lora_chain(
                prompt,
                lora_pairs,
                high_lora_node_id,
                low_lora_node_id,
                high_sampling_node_id,
                low_sampling_node_id,
                is_flf2v
            )
        except Exception as e:
            print(f"❌ LoRA 적용 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # LoRA 적용 후 상태 확인
    print(f"\n{'='*60}")
    print("LoRA 적용 후 상태")
    print(f"{'='*60}")
    
    # HIGH LoRA 체인 추적
    high_chain = print_node_chain(prompt, high_sampling_node_id, "HIGH")
    
    # LOW LoRA 체인 추적
    low_chain = print_node_chain(prompt, low_sampling_node_id, "LOW")
    
    # 변경 전후 비교를 위해 원본도 저장
    before_file = f"test_before_{test_name.replace(' ', '_').lower()}.json"
    before_path = os.path.join(os.path.dirname(__file__), before_file)
    with open(before_path, 'w', encoding='utf-8') as f:
        json.dump(prompt_before, f, indent=2, ensure_ascii=False)
    
    # 변경된 워크플로우를 JSON 파일로 저장
    after_file = f"test_after_{test_name.replace(' ', '_').lower()}.json"
    after_path = os.path.join(os.path.dirname(__file__), after_file)
    with open(after_path, 'w', encoding='utf-8') as f:
        json.dump(prompt, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 워크플로우 저장:")
    print(f"   변경 전: {before_path}")
    print(f"   변경 후: {after_path}")
    
    # 주요 노드 비교 출력
    print(f"\n{'='*60}")
    print("주요 노드 비교")
    print(f"{'='*60}")
    
    if is_flf2v:
        high_lora_node_id = "91"
        low_lora_node_id = "92"
        high_sampling_node_id = "54"
        low_sampling_node_id = "55"
    else:
        high_lora_node_id = "101"
        low_lora_node_id = "102"
        high_sampling_node_id = "104"
        low_sampling_node_id = "103"
    
    print(f"\nHIGH LoRA 노드 ({high_lora_node_id}):")
    print(f"  변경 전: {prompt_before.get(high_lora_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    print(f"  변경 후: {prompt.get(high_lora_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    
    print(f"\nHIGH ModelSamplingSD3 노드 ({high_sampling_node_id}):")
    print(f"  변경 전: {prompt_before.get(high_sampling_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    print(f"  변경 후: {prompt.get(high_sampling_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    
    print(f"\nLOW LoRA 노드 ({low_lora_node_id}):")
    print(f"  변경 전: {prompt_before.get(low_lora_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    print(f"  변경 후: {prompt.get(low_lora_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    
    print(f"\nLOW ModelSamplingSD3 노드 ({low_sampling_node_id}):")
    print(f"  변경 전: {prompt_before.get(low_sampling_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    print(f"  변경 후: {prompt.get(low_sampling_node_id, {}).get('inputs', {}).get('model', 'N/A')}")
    
    # 새로 생성된 노드 확인
    new_nodes = set(prompt.keys()) - set(prompt_before.keys())
    if new_nodes:
        print(f"\n새로 생성된 노드: {sorted(new_nodes, key=int)}")
        for node_id in sorted(new_nodes, key=int):
            node = prompt[node_id]
            if node.get("class_type") == "LoraLoaderModelOnly":
                print(f"  노드 {node_id}: {node.get('inputs', {}).get('lora_name', 'N/A')}")
                print(f"    입력: {node.get('inputs', {}).get('model', 'N/A')}")
    
    return prompt

def main():
    """메인 테스트 함수"""
    print("="*80)
    print("LoRA 체인 테스트 시작")
    print("="*80)
    
    # 테스트 1: LoRA 없음
    test_lora_chain(
        "LoRA 없음",
        [],
        is_flf2v=False
    )
    
    # 테스트 2: LoRA 1개
    test_lora_chain(
        "LoRA 1개",
        [
            {
                "high": "test_lora1_high.safetensors",
                "low": "test_lora1_low.safetensors",
                "high_weight": 1.0,
                "low_weight": 1.0
            }
        ],
        is_flf2v=False
    )
    
    # 테스트 3: LoRA 2개
    test_lora_chain(
        "LoRA 2개",
        [
            {
                "high": "test_lora1_high.safetensors",
                "low": "test_lora1_low.safetensors",
                "high_weight": 1.0,
                "low_weight": 1.0
            },
            {
                "high": "test_lora2_high.safetensors",
                "low": "test_lora2_low.safetensors",
                "high_weight": 0.8,
                "low_weight": 0.8
            }
        ],
        is_flf2v=False
    )
    
    # 테스트 4: LoRA 3개
    test_lora_chain(
        "LoRA 3개",
        [
            {
                "high": "test_lora1_high.safetensors",
                "low": "test_lora1_low.safetensors",
                "high_weight": 1.0,
                "low_weight": 1.0
            },
            {
                "high": "test_lora2_high.safetensors",
                "low": "test_lora2_low.safetensors",
                "high_weight": 0.8,
                "low_weight": 0.8
            },
            {
                "high": "test_lora3_high.safetensors",
                "low": "test_lora3_low.safetensors",
                "high_weight": 0.5,
                "low_weight": 0.5
            }
        ],
        is_flf2v=False
    )
    
    # 테스트 5: FLF2V 워크플로우 - LoRA 2개
    test_lora_chain(
        "FLF2V LoRA 2개",
        [
            {
                "high": "test_lora1_high.safetensors",
                "low": "test_lora1_low.safetensors",
                "high_weight": 1.0,
                "low_weight": 1.0
            },
            {
                "high": "test_lora2_high.safetensors",
                "low": "test_lora2_low.safetensors",
                "high_weight": 0.8,
                "low_weight": 0.8
            }
        ],
        is_flf2v=True
    )
    
    print("\n" + "="*80)
    print("모든 테스트 완료!")
    print("="*80)
    print("\n생성된 JSON 파일들을 확인하여 LoRA 체인이 올바르게 구성되었는지 확인하세요:")
    print("  - test_before_*.json: LoRA 적용 전 워크플로우")
    print("  - test_after_*.json: LoRA 적용 후 워크플로우")
    print("\n비교 방법:")
    print("  1. before/after 파일을 열어 노드 연결을 비교")
    print("  2. 새로 생성된 노드가 올바르게 체인에 연결되었는지 확인")
    print("  3. ModelSamplingSD3 노드가 마지막 LoRA를 참조하는지 확인")

if __name__ == "__main__":
    main()

