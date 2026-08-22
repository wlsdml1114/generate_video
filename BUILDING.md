# Build and deploy

The Dockerfile bakes ComfyUI, its custom nodes, both Wan 2.2 diffusion models,
the text encoder, VAE, LoRAs, and RIFE checkpoint into one serverless image.
Plan for a large build and registry upload.

The image installs `huggingface_hub` near the start of the build, which
provides the `hf` CLI used by all baked Hugging Face artifact downloads. The
same Docker layer runs `hf --help` so the build fails early if the CLI was not
installed correctly.

## Build locally

Start Docker Desktop, then run from this repository directory. The default
build reproduces the existing base image and Wan 2.2 model pair:

```powershell
docker build --progress=plain --tag <registry>/generate-video-ksampler:model-retention .
docker push <registry>/generate-video-ksampler:model-retention
```

To bake a different compatible high/low Wan model pair or use another base
image, override the build arguments:

```powershell
docker build --progress=plain `
  --build-arg BASE_IMAGE=<base-image:tag> `
  --build-arg WAN_HIGH_NOISE_MODEL_URI=<high-noise-hf-uri> `
  --build-arg WAN_LOW_NOISE_MODEL_URI=<low-noise-hf-uri> `
  --build-arg WAN_HIGH_NOISE_MODEL_SHA256=<high-noise-sha256> `
  --build-arg WAN_LOW_NOISE_MODEL_SHA256=<low-noise-sha256> `
  --build-arg MODEL_REFRESH=<unique-build-value> `
  --tag <registry>/generate-video-ksampler:<new-tag> .

docker push <registry>/generate-video-ksampler:<new-tag>
```

All baked Hugging Face artifacts are downloaded with the Hugging Face CLI
from `hf://` URIs. The two diffusion models are deliberately stored under the
canonical filenames already referenced by every workflow. This means changing the two URIs does
not require editing six workflow files. The replacement files must remain
compatible with the workflows' Wan 2.2 I2V high-noise and low-noise stages.
The SHA-256 arguments make the build fail instead of silently baking an
unexpected or incomplete model. Change `MODEL_REFRESH` for a deliberate fresh
download when rebuilding the same commit and URIs.

Replace `<registry>` with the Docker Hub or private-registry namespace used by
the RunPod endpoint, then update the endpoint to the new immutable tag.

The `.dockerignore` file keeps Git metadata, tests, bytecode, and local logs out
of the image build context.

## Request model retention

Send a real JSON boolean in each request:

```json
{
  "input": {
    "prompt": "your prompt",
    "keep_models_loaded": true
  }
}
```

Omitting the option, or setting it to `false`, preserves the original behavior
and unloads all models at the end of the job.

## Verify after deployment

1. Keep at least one worker warm and submit two jobs to the same worker.
2. Confirm the worker log contains:

   ```text
   Model retention configured: keep_models_loaded=True, unload_all_models=False
   ```

3. At the end of that job, `VRAMdebug: freed memory` should no longer show the
   previous forced release of roughly 14.57 GB.
4. Compare the second job's `Requested to load` timings with the baseline. Some
   selective model eviction can still occur when ComfyUI needs VRAM.
