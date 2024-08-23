# GPU Compute Providers

## vast.ai

For short experiments, vast.ai is a cost-effective solution as it is billed per minute and not per hour.
Please note you also pay for setup time.

Vast.ai comes with limitation of not being able to run docker containers inside rented machines.
Vast.ai allows you to run your own docker image if it is uploaded to public docker registry (or credentials docker registry password are provided), but this avenue was not explored.


## paperspace

Paperspace is billed per hour, and tends to have a higher cost than vast.ai.
The performance seemed to vary a lot, but the root cause was never identified.
