#!/usr/bin/env python3
"""
Sends jsmn_targets.cpp to DeepSeek with a minimal, idiomatic prompt.
No instruction to preserve integer literals or avoid stdlib helpers —
we want DeepSeek's natural porting instincts so the verifier can find
semantic divergences.
"""

import os, sys, requests

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    sys.exit("Error: DEEPSEEK_API_KEY not set in .env")

CPP_FILE = "targets/jsmn_targets.cpp"
OUT_FILE = "targets/jsmn_targets_loose.rs"

with open(CPP_FILE) as f:
    cpp_source = f.read()

PROMPT = f"""Port the following C++ functions to idiomatic Rust.

Requirements:
- Every function must have `#[no_mangle] pub extern "C"` so it can be called from C.
- Match the argument and return types: C `int32_t` → `i32`, C `uint32_t` → `u32`.
- Use natural, idiomatic Rust — feel free to use Rust's standard library methods,
  byte literals, ranges, pattern matching, and whatever makes the code clean.
- Do NOT add `fn main()`. Output only the Rust functions, no `use` statements.

C++ source:
```cpp
{cpp_source}
```

Output only valid Rust code. No explanation."""

print(f"[*] Sending {CPP_FILE} to DeepSeek with loose/idiomatic prompt...")

resp = requests.post(
    "https://api.deepseek.com/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.7,   # some creativity to encourage divergence
    },
    timeout=60,
)

if resp.status_code != 200:
    sys.exit(f"API error {resp.status_code}: {resp.text}")

raw = resp.json()["choices"][0]["message"]["content"].strip()
if raw.startswith("```"):
    lines = raw.splitlines()
    raw = "\n".join(l for l in lines if not l.startswith("```")).strip()

with open(OUT_FILE, "w") as f:
    f.write(raw + "\n")

print(f"[+] Written to {OUT_FILE} ({len(raw.splitlines())} lines)\n")
print("--- Output ---")
print(raw)
