# Debian Packaging

DevCapsule ships a Debian package build path that produces a `.deb` containing a PEX executable at `/opt/devcapsule/devcapsule.pex` and a launcher at `/usr/bin/devcapsule`.

The package expects `python3 >= 3.12` at runtime. The launcher checks the interpreter version before running DevCapsule.

## Build Locally

From the repository root on a Debian-like system with Python 3.12+:

```bash
bash packaging/debian/build-deb.sh
```

The artifact is written to `dist/devcapsule_<version>_<arch>.deb`.

## Build In Docker

```bash
docker build -f packaging/debian/Dockerfile -t devcapsule-deb-builder .
docker run --rm -v "$PWD/dist:/out" devcapsule-deb-builder
```

On PowerShell:

```powershell
docker build -f packaging/debian/Dockerfile -t devcapsule-deb-builder .
docker run --rm -v "${PWD}/dist:/out" devcapsule-deb-builder
```

## Install

```bash
sudo apt install ./dist/devcapsule_0.1.0_amd64.deb
devcapsule doctor
```

If `apt` cannot satisfy Python 3.12+ on the target distribution, install Python 3.12+ first and rerun the package install.
