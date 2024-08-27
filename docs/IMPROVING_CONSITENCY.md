# Improving Consistency of Inference

This document describes the steps to improve the consistency of inference results, from the MUST-HAVE requirements to potential improvements.

If you a case, where recommendation, especially a "thought to be safe" configuration, does not provide consistent results, please file an Issue report alongside the steps to reproduce the issue.


## Recommendations

* [ ] Have test cases that verify the consistency of inference results.
  * Recommendation:
    * Before every release, check if the known input-output pairs are still the same as in previous release. It is very important for known output to be as long as possible, operation errors are cumulative the long output is much more likely showcase inconsistencies.
* [ ] All software dependencies need to be locked to a specific version.
  * Recommendation:
    * Python dependencies: These are the ones that will be most updated. Use [Rye](https://rye.astral.sh/) or [pip-tools](https://github.com/jazzband/pip-tools).
    * Binary dependencies: Use doker images and tags to lock the version of the final image. Treat each tag as a reseed of the inference process.
    * Use same driver version (Please note, that so far we have yet to document a case where driver version affected inference results)
* [ ] Set seed for all random number generators used in the inference process. 
  * Recommendation:
    * For single-threaded apps, use `deterministic_ml.v1.set_seed()` to set the seed for all known random number generator process wide.
    * Whenever initializing a new random generator, explicitly set the seed in deterministic manner.
    * For multi-threaded or async applications ensure that random generators are isolated per thread or task.
* [ ] Disable auto-optimization or JIT compilation in the inference process.
  * Recommendation:
    * Use `deterministic_ml.v1.disable_auto_optimization()` to disable auto-optimization or JIT compilation process wide.
* [ ] Use the same kind of hardware for all inference runs.
  * Recommendation:
    * Use the same GPU chip model and vRAM size for are inference runs. Hardware interface (PCIe, SXM, etc.) does not seem to affect the results, but 2xA100 40G do not return the same results as 1xA100 80G.
    * When testing new, but similar hardware to check if the results are consistent with previously known platform, maximize pseudo-randomization of the inference process (e.g. by setting high temperature and low top-p values).

## Framework Specific Recommendations

### PyTorch

See https://pytorch.org/docs/stable/notes/randomness.html .
The https://docs.nvidia.com/cuda/cublas/index.html#results-reproducibility also apply.

### vLLM

vLLM is PyTorch based, so the same constraints apply.
However, vLLM has much narrower scope, hence other than general recommendations from [MUST-HAVE](#must-have) section, only following is required:
* make sure to use exactly the same parameters for the model initialization
  * `enforce_eager=True` 
* to get the same output for the same input, use the exactly same `SamplingParams` with explicitly set `seed` parameter
* make sure to explicitly set model `revision` parameter, otherwise depending when the model was downloaded, the results may be different


```python
model = vllm.LLM(
    model=model_name,
    revision=model_revision,
    enforce_eager=True,  # Ensure eager mode is enabled
)


sampling_params = vllm.SamplingParams(
    max_tokens=4096,
    # temperature=1000,  # High value encourages pseudo-randomization
    # top_p=0.1,  # Low value encourages pseudo-randomization
    seed=42,
)

response = model.generate(requests, sampling_params)

```


## Unconfirmed advice

### Consistent results across different CUDA hardware

It should be theoretically possible to get consistent results across different hardware, but even if limited to CUDA-capatible GPUs, it will be at the cost of performance.

* [ ] Use `torch.backends.cudnn.deterministic = True` and `torch.backends.cudnn.benchmark = False` to ensure that the results are consistent across different CUDA hardware.
  * Recommendation:
    * Use `deterministic_ml.v1.set_seed()` to set the seed for all known random number generator process wide.
    * Use `deterministic_ml.v1.disable_auto_optimization()` to disable auto-optimization or JIT compilation process wide.
    * Use `torch.backends.cudnn.deterministic = True` and `torch.backends.cudnn.benchmark = False` to ensure that the results are consistent across different CUDA hardware.
    * Use the same GPU chip model and vRAM size for are inference runs. Hardware interface (PCIe, SXM, etc.) does not seem to affect the results, but 2xA100 40G do not return the same results as 1xA100 80G.


See [TO_BE_INVESTIGATED.md](TO_BE_INVESTIGATED.md) for more potential improvements.
