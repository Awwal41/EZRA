# Site profiles (HPC)

Every cluster has different partitions, accounts, modules, and scratch paths.
EZRA stores that once in a **site profile** under `sites/<name>/`.

The full how-to in the repository checkout is
[sites/README.md](https://github.com/awwalola/EZRA/blob/main/sites/README.md).

## Quick start

```bash
ezra hpc init-site my-cluster --models-dir /scratch/$USER/ezra/models
# edit sites/my-cluster/ezra.yaml and modules.sh
export EZRA_SITE=my-cluster
ezra doctor
ezra hpc submit download --dry-run
```

Then commit `sites/my-cluster/` so others on the same HPC can reuse it.

See also [HPC / SLURM](hpc.md) and [Configuration](configuration.md).
