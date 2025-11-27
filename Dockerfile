# Use specific version of nvidia cuda image
# FROM wlsdml1114/my-comfy-models:v1 as model_provider
FROM wlsdml1114/multitalk-base:1.8 as runtime

RUN pip install -U "huggingface_hub[hf_transfer]"
RUN pip install runpod websocket-client

WORKDIR /

RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd /ComfyUI && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone https://github.com/Comfy-Org/ComfyUI-Manager.git && \
    cd ComfyUI-Manager && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-KJNodes && \
    cd ComfyUI-KJNodes && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git && \
    cd ComfyUI-Frame-Interpolation && \
    python install.py
    
RUN cd /ComfyUI/custom_nodes && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite && \
    cd ComfyUI-VideoHelperSuite && \
    pip install -r requirements.txt

RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors -O /ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors -O /ComfyUI/models/vae/wan_2.1_vae.safetensors
RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors -O /ComfyUI/models/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors -O /ComfyUI/models/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors -O /ComfyUI/models/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors -O /ComfyUI/models/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors

COPY . .
RUN mkdir -p /ComfyUI/user/default/ComfyUI-Manager
COPY config.ini /ComfyUI/user/default/ComfyUI-Manager/config.ini
COPY extra_model_paths.yaml /ComfyUI/extra_model_paths.yaml
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]