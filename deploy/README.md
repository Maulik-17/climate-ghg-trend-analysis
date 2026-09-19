# Deployment files

Everything in this folder (plus `.github/workflows/`) exists only to host the Streamlit app as a
container. **You do not need any of it to run or use the project**; to run the app
locally, follow the instructions in the top-level [README](../README.md).

| File | Purpose |
| --- | --- |
| `Dockerfile` | Builds the app image: only `app.py` and the three CSVs it reads, with the pinned runtime set from `requirements-app.txt`. Runs as a non-root user and listens on port 8501. |
| `Dockerfile.dockerignore` | Keeps the build context small. Docker (BuildKit) picks it up automatically because it sits next to the Dockerfile. |
| `requirements-app.txt` | Runtime dependencies of `app.py` only (a subset of the top-level `requirements.txt`, same versions). |
| `compose.yml` | Production stack: runs an immutable `IMAGE_REF`, publishes no host ports and joins the reverse proxy's network. |

## Build and run locally

Run from the repository root (the build context must be the root, not this folder):

```bash
docker build -f deploy/Dockerfile -t climate-app .
docker run --rm -p 127.0.0.1:8501:8501 climate-app   # http://127.0.0.1:8501
```

## Releases

- `.github/workflows/ci.yml` builds the image on every pull request and push to `main`, waits for the
  container to report healthy and runs the app headless with Streamlit `AppTest`.
- `.github/workflows/release.yml` runs only when a `v*.*.*` tag is pushed and the tagged commit is on
  `main`. It pushes the image to GHCR and deploys it by digest (never `latest`) to the server, which
  verifies the public health check and rolls back to the previous image if it fails.
- The deploy job uses the `production` GitHub environment, which provides `VPS_SSH_KEY`,
  `VPS_KNOWN_HOSTS`, `VPS_HOST` and `VPS_USER`. Their values are not stored in this repository.
