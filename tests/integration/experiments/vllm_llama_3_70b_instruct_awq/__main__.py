import argparse
import contextlib
import io
import pathlib
import sys
import time
from pprint import pprint

import torch
import vllm
import yaml
from deterministic_ml.v1 import set_deterministic
from vllm import SamplingParams

SEED = 42

set_deterministic(SEED)


@contextlib.contextmanager
def timed(name):
    print(f"Starting {name}")
    start = time.time()
    yield
    took = time.time() - start
    print(f"{name} took {took:.2f} seconds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_path", type=pathlib.Path, help="Path to save the output")
    parser.add_argument(
        "--model",
        default="casperhansen/llama-3-70b-instruct-awq@e578178ea893ca5e3326afd15da5aefa37e84d69",
        help="Model name",
    )
    args = parser.parse_args()

    gpu_count = torch.cuda.device_count()
    print(f"{gpu_count=}")

    model_name = args.model
    if "@" in model_name:
        model_name, revision = model_name.split("@")
    else:
        revision = None

    with timed("model loading"):
        model = vllm.LLM(
            model=model_name,
            revision=revision,
            # quantization="AWQ",
            tensor_parallel_size=gpu_count,
            # quantization="AWQ",  # Ensure quantization is set if needed
            # tensor_parallel_size=1,  # Set according to the number of GPUs available
            enforce_eager=True,  # Ensure eager mode is enabled
        )
        model.llm_engine.tokenizer.eos_token_id = 128009

    def make_prompt(prompt):
        role_templates = {
            "system": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{{{{ {} }}}}<|eot_id|>",
            "user": "<|start_header_id|>user<|end_header_id|>\n{{{{ {} }}}}<|eot_id|>",
            "assistant": "<|start_header_id|>assistant<|end_header_id|>\n{{{{ {} }}}}<|eot_id|>",
            "end": "<|start_header_id|>assistant<|end_header_id|>",
        }
        msgs = [
            {"role": "system", "content": "You are a helpful AI assistant"},
            {"role": "user", "content": prompt},
        ]
        full_prompt = io.StringIO()
        for msg in msgs:
            full_prompt.write(role_templates[msg["role"]].format(msg["content"]))
        full_prompt.write(role_templates["end"])
        return full_prompt.getvalue()

    sampling_params = SamplingParams(
        max_tokens=4096,
        temperature=1000,
        top_p=0.1,
        seed=SEED,
    )

    def generate_responses(prompts: list[str]):
        requests = [make_prompt(prompt) for prompt in prompts]
        response = model.generate(requests, sampling_params, use_tqdm=True)
        return response

    import hashlib

    output_hashes = {}
    output_full = {}
    prompts = [
        "Count to 1000, skip unpopular numbers",
        "Describe justice system in UK vs USA in 2000-5000 words",
        "Describe schooling system in UK vs USA in 2000-5000 words",
        "Explain me some random problem for me in 2000-5000 words",
        "Tell me entire history of USA",
        "Write a ballad. Pick a random theme.",
        "Write an epic story about a dragon and a knight",
        "Write an essay about being a Senior developer.",
    ]

    with timed(f"{len(prompts)} responses generation"):
        for prompt, r in zip(prompts, generate_responses(prompts)):
            hasher = hashlib.blake2b()
            text_response = r.outputs[0].text
            output_full[prompt] = text_response
            hasher.update(text_response.encode("utf8"))
            output_hashes[prompt] = hasher.hexdigest()
        sys.stderr.flush()

    pprint(output_hashes)
    with open(args.output_path / "output.yaml", "w") as f:
        yaml.safe_dump(output_hashes, f, sort_keys=True)

    with open(args.output_path / "output_full.yaml", "w") as f:
        yaml.safe_dump(output_full, f, sort_keys=True)


if __name__ == "__main__":
    main()
