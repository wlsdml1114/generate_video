import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from generate_video_client import GenerateVideoClient
from workflow_options import configure_model_retention, get_keep_models_loaded


WORKFLOW_DIR = Path(__file__).parent / "workflow"
DOCKERFILE = Path(__file__).parent / "Dockerfile"


class ModelRetentionTests(unittest.TestCase):
    def test_input_defaults_to_existing_unload_behavior(self):
        self.assertFalse(get_keep_models_loaded({}))

    def test_input_accepts_json_booleans(self):
        self.assertTrue(get_keep_models_loaded({"keep_models_loaded": True}))
        self.assertFalse(get_keep_models_loaded({"keep_models_loaded": False}))

    def test_input_rejects_strings_and_numbers(self):
        for invalid_value in ("true", "false", 0, 1, None):
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaisesRegex(ValueError, "JSON boolean"):
                    get_keep_models_loaded({"keep_models_loaded": invalid_value})

    def test_all_baked_workflows_support_per_request_retention(self):
        workflow_paths = sorted(WORKFLOW_DIR.glob("*.json"))
        self.assertEqual(6, len(workflow_paths))

        for workflow_path in workflow_paths:
            with self.subTest(workflow=workflow_path.name):
                with workflow_path.open(encoding="utf-8") as workflow_file:
                    original_prompt = json.load(workflow_file)

                keep_prompt = copy.deepcopy(original_prompt)
                configured = configure_model_retention(keep_prompt, True)
                self.assertGreaterEqual(configured, 1)
                keep_nodes = [
                    node for node in keep_prompt.values()
                    if node.get("class_type") == "VRAM_Debug"
                ]
                self.assertTrue(keep_nodes)
                self.assertTrue(all(
                    node["inputs"]["unload_all_models"] is False
                    for node in keep_nodes
                ))
                self.assertTrue(all(
                    node["inputs"]["empty_cache"] is True
                    and node["inputs"]["gc_collect"] is True
                    for node in keep_nodes
                ))

                unload_prompt = copy.deepcopy(original_prompt)
                configure_model_retention(unload_prompt, False)
                unload_nodes = [
                    node for node in unload_prompt.values()
                    if node.get("class_type") == "VRAM_Debug"
                ]
                self.assertTrue(all(
                    node["inputs"]["unload_all_models"] is True
                    for node in unload_nodes
                ))

    def test_missing_vram_debug_node_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, "VRAM_Debug"):
            configure_model_retention({}, True)

    def test_python_client_sends_model_retention_option(self):
        client = GenerateVideoClient("test-endpoint", "test-key")
        client.submit_job = Mock(return_value="test-job")
        client.wait_for_completion = Mock(return_value={"status": "COMPLETED"})

        result = client.create_video_from_image(
            image=b"test-image",
            prompt="test prompt",
            keep_models_loaded=True,
        )

        self.assertEqual({"status": "COMPLETED"}, result)
        submitted_input = client.submit_job.call_args.args[0]
        self.assertTrue(submitted_input["keep_models_loaded"])

    def test_python_client_rejects_string_boolean(self):
        client = GenerateVideoClient("test-endpoint", "test-key")
        with self.assertRaisesRegex(TypeError, "boolean"):
            client.create_video_from_image(
                image=b"test-image",
                keep_models_loaded="true",
            )


class BakeConfigurationTests(unittest.TestCase):
    def test_dockerfile_exposes_bake_time_image_and_model_arguments(self):
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("ARG BASE_IMAGE=", dockerfile)
        self.assertIn("FROM ${BASE_IMAGE} AS runtime", dockerfile)
        self.assertIn("ARG WAN_HIGH_NOISE_MODEL_URI=hf://", dockerfile)
        self.assertIn("ARG WAN_LOW_NOISE_MODEL_URI=hf://", dockerfile)
        self.assertIn('pip install --no-cache-dir -U "huggingface_hub[hf_transfer]"', dockerfile)
        self.assertIn("hf --help > /dev/null", dockerfile)
        self.assertIn('hf download "${WAN_HIGH_NOISE_MODEL_URI}"', dockerfile)
        self.assertIn('hf download "${WAN_LOW_NOISE_MODEL_URI}"', dockerfile)
        self.assertIn("--local-dir /tmp/wan-high --force-download", dockerfile)
        self.assertIn("--local-dir /tmp/wan-low --force-download", dockerfile)
        self.assertNotIn("wget ", dockerfile)
        self.assertEqual(dockerfile.count("hf download "), 7)

    def test_baked_models_are_refreshed_and_checksum_verified(self):
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("ARG MODEL_REFRESH=", dockerfile)
        self.assertIn("ARG WAN_HIGH_NOISE_MODEL_SHA256=", dockerfile)
        self.assertIn("ARG WAN_LOW_NOISE_MODEL_SHA256=", dockerfile)
        self.assertIn("${WAN_HIGH_NOISE_MODEL_SHA256}", dockerfile)
        self.assertIn("${WAN_LOW_NOISE_MODEL_SHA256}", dockerfile)
        self.assertEqual(2, dockerfile.count("sha256sum -c -"))

    def test_baked_model_destinations_match_every_workflow(self):
        expected_models = {
            "230": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
            "235": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
        }

        for workflow_path in sorted(WORKFLOW_DIR.glob("*.json")):
            with self.subTest(workflow=workflow_path.name):
                with workflow_path.open(encoding="utf-8") as workflow_file:
                    prompt = json.load(workflow_file)
                for node_id, model_name in expected_models.items():
                    self.assertEqual(
                        model_name,
                        prompt[node_id]["inputs"]["unet_name"],
                    )


if __name__ == "__main__":
    unittest.main()
