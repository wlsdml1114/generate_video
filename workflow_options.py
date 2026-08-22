"""Per-request workflow options for the RunPod handler."""


def get_keep_models_loaded(job_input):
    """Return the validated model-retention option from a RunPod input object."""
    keep_models_loaded = job_input.get("keep_models_loaded", False)
    if not isinstance(keep_models_loaded, bool):
        raise ValueError("keep_models_loaded must be a JSON boolean")
    return keep_models_loaded


def configure_model_retention(prompt, keep_models_loaded):
    """Toggle forced end-of-job model unloading on every VRAM Debug node."""
    if not isinstance(keep_models_loaded, bool):
        raise ValueError("keep_models_loaded must be a boolean")

    configured_nodes = 0
    for node in prompt.values():
        if node.get("class_type") != "VRAM_Debug":
            continue

        node.setdefault("inputs", {})["unload_all_models"] = not keep_models_loaded
        configured_nodes += 1

    if configured_nodes == 0:
        raise ValueError("workflow does not contain a VRAM_Debug node")

    return configured_nodes
