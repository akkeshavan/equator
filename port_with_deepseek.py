#!/usr/bin/env python3
"""
Sends jsmn_targets.cpp to DeepSeek and asks it to port all 6 functions
to Rust with #[no_mangle] pub extern "C" signatures.

Usage:
    DEEPSEEK_API_KEY=sk-... python3 port_with_deepseek.py
"""

import os
import sys
import requests

# Load .env if present
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
    sys.exit("Error: DEEPSEEK_API_KEY not set in .env or environment.")

CPP_FILE = "targets/jsmn_targets.cpp"
OUT_FILE = "targets/jsmn_targets.rs"

with open(CPP_FILE) as f:
    cpp_source = f.read()

PROMPT = f"""You are a precise C-to-Rust translator. Port the following C++ source file to Rust.

STRICT RULES — follow every one exactly:
1. Every function must have EXACTLY `#[no_mangle] pub extern "C"` — no exceptions.
2. Match the C ABI types exactly:
   - C `int32_t`  → Rust `i32`
   - C `uint32_t` → Rust `u32`
3. Do NOT use Rust standard library helpers like `is_ascii_hexdigit()`, `is_whitespace()`,
   or any char/byte methods. Translate the logic literally using the same integer comparisons
   and operators as the C code.
4. Do NOT add `fn main()`. Output ONLY the Rust functions, no module declarations, no `use`.
5. Preserve the exact numeric literals (48, 57, 65, 70, 97, 102 — not b'0', b'9', etc.).
6. Preserve operator precedence and all branch conditions exactly as written.
7. For `uint32_t` arguments, keep all comparisons in `u32` — do NOT cast to `i32` before comparing.

C++ source to port:
```cpp
{cpp_source}
```

Output only valid Rust source code. No explanation, no markdown fences."""

print(f"[*] Sending {CPP_FILE} to DeepSeek (deepseek-chat)...")

resp = requests.post(
    "https://api.deepseek.com/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.0,
    },
    timeout=60,
)

if resp.status_code != 200:
    sys.exit(f"API error {resp.status_code}: {resp.text}")

raw = resp.json()["choices"][0]["message"]["content"].strip()

# Strip markdown fences if the model added them despite instructions
if raw.startswith("```"):
    lines = raw.splitlines()
    raw = "\n".join(
        line for line in lines
        if not line.startswith("```")
    ).strip()

with open(OUT_FILE, "w") as f:
    f.write(raw + "\n")

print(f"[+] Rust source written to {OUT_FILE}")
print(f"    ({len(raw.splitlines())} lines)")
print()
print("--- Preview (first 40 lines) ---")
for line in raw.splitlines()[:40]:
    print(line)
