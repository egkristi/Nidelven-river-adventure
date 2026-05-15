#!/usr/bin/env bash
# Prepare Unity project for CI builds in Docker.
# Removes URP (ShaderGraph GUID issue) and adds compile defines.
set -euo pipefail

python3 -c "
import json
with open('Packages/manifest.json', 'r') as f:
    m = json.load(f)
m['dependencies'].pop('com.unity.render-pipelines.universal', None)
with open('Packages/manifest.json', 'w') as f:
    json.dump(m, f, indent=2)
"

printf '%s\n' '-define:DISABLESTEAMWORKS' '-define:DISABLE_URP' > Assets/csc.rsp
