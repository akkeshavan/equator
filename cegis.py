#!/usr/bin/env python3
"""
cegis.py — Counterexample-Guided Inductive Synthesis loop.

For each function that the verifier flags as diverging:
  1. Run verifier  → get counterexample (inputs, C++ result, Rust result)
  2. Build a repair prompt  → paste C++ source + current Rust + counterexample
  3. Ask DeepSeek to fix the Rust
  4. Recompile to LLVM IR
  5. Re-verify  → loop back to 1 or declare PROVEN EQUIVALENT

Caps at MAX_ITER iterations per function so the loop terminates.

Usage:
    .venv/bin/python3 cegis.py
"""

import os, re, sys, subprocess, textwrap, requests

# ── config ──────────────────────────────────────────────────────────────────
CPP_IR   = "targets/jsmn_cpp.ll"
RUST_SRC = "targets/jsmn_targets_cegis.rs"   # working file, mutated each iter
RUST_IR  = "targets/jsmn_cegis.ll"
CPP_SRC  = "targets/jsmn_targets.cpp"
MAX_ITER = 6

FUNCS = [
    "jsmn_is_valid_char", "jsmn_is_delimiter", "jsmn_is_hex_digit",
    "jsmn_escape_valid",  "jsmn_alloc_check",  "jsmn_safe_next",
    "extend_sign",        "bit_parity",         "saturating_shl",
]

# ── load API key ─────────────────────────────────────────────────────────────
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


# ── helpers ──────────────────────────────────────────────────────────────────

def ask_deepseek(prompt: str) -> str:
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.0},
        timeout=90,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek API error {resp.status_code}: {resp.text[:300]}")
    raw = resp.json()["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```")).strip()
    return raw


def compile_rust_to_ir(src_path: str, ir_path: str) -> tuple[bool, str]:
    """Compile Rust source to LLVM IR. Returns (success, stderr)."""
    stem = os.path.splitext(os.path.basename(ir_path))[0]
    tmp_ll = f"targets/{stem}_tmp"
    res = subprocess.run(
        ["rustc", "-C", "opt-level=1", "--crate-type=cdylib",
         "--emit=llvm-ir", "--out-dir", "targets", src_path],
        capture_output=True, text=True,
    )
    # rustc names the .ll after the crate (source stem), not the -o flag
    src_stem = os.path.splitext(os.path.basename(src_path))[0]
    produced = f"targets/{src_stem}.ll"
    if res.returncode == 0 and os.path.exists(produced):
        os.rename(produced, ir_path)
        return True, ""
    return False, res.stderr


def run_verifier(cpp_ir: str, rust_ir: str, func: str) -> dict | None:
    """
    Run equiv_check.py for one function.
    Returns:
      {'status': 'equiv'}
      {'status': 'diverge', 'inputs': {...}, 'cpp': int, 'rust': int}
      {'status': 'error', 'msg': str}
    """
    res = subprocess.run(
        [sys.executable, "equiv_check.py", cpp_ir, rust_ir, func],
        capture_output=True, text=True,
    )
    out = res.stdout + res.stderr
    if "EQUIV" in out:
        return {"status": "equiv"}
    if "DIVERGE" in out:
        inputs = {}
        for m in re.finditer(r'input\s+(\S+)\s*=\s*(-?\d+)\s*\(0x([0-9a-f]+)\)', out):
            inputs[m.group(1)] = {"signed": int(m.group(2)), "hex": m.group(3)}
        m_cpp  = re.search(r'C\+\+ returns\s*:\s*(-?\d+)', out)
        m_rust = re.search(r'Rust returns\s*:\s*(-?\d+)', out)
        return {
            "status": "diverge",
            "inputs": inputs,
            "cpp":  int(m_cpp.group(1))  if m_cpp  else 0,
            "rust": int(m_rust.group(1)) if m_rust else 0,
        }
    return {"status": "error", "msg": out.strip()[-300:]}


def extract_cpp_function(cpp_src: str, func_name: str) -> str:
    """Pull the C++ source of a single extern "C" function."""
    # Match from 'extern "C"' before func_name to the closing brace
    pattern = rf'(extern\s+"C"\s+\S+\s+{re.escape(func_name)}\s*\([^{{]*\)\s*\{{[^}}]*\}})'
    m = re.search(pattern, cpp_src, re.DOTALL)
    return m.group(1).strip() if m else f"// {func_name} (source not found)"


def extract_rust_function(rust_src: str, func_name: str) -> str:
    """Pull one #[no_mangle] pub extern function from a Rust source string."""
    pattern = (
        rf'(#\[no_mangle\]\s*pub\s+extern\s+"C"\s+fn\s+{re.escape(func_name)}'
        r'\s*\([^{]*\)\s*->\s*\S+\s*\{[^}]*(?:\{[^}]*\}[^}]*)?\})'
    )
    m = re.search(pattern, rust_src, re.DOTALL)
    return m.group(1).strip() if m else ""


def replace_rust_function(rust_src: str, func_name: str, new_impl: str) -> str:
    """Swap out the named function in a Rust source string."""
    # Find the function and replace it; use a simple brace-counting extractor
    # to avoid regex issues with nested braces
    start_pat = re.compile(
        rf'#\[no_mangle\]\s*\npub\s+extern\s+"C"\s+fn\s+{re.escape(func_name)}\b'
    )
    m = start_pat.search(rust_src)
    if not m:
        return rust_src + "\n" + new_impl + "\n"

    # Walk forward from the opening brace to find the matching close
    start = m.start()
    brace_start = rust_src.index('{', m.end())
    depth, i = 0, brace_start
    while i < len(rust_src):
        if rust_src[i] == '{': depth += 1
        elif rust_src[i] == '}':
            depth -= 1
            if depth == 0:
                return rust_src[:start] + new_impl + "\n" + rust_src[i+1:]
        i += 1
    return rust_src  # shouldn't reach here


def build_repair_prompt(func_name: str, cpp_fn: str, rust_fn: str, ce: dict) -> str:
    input_lines = "\n".join(
        f"  {name} = {v['signed']} (0x{v['hex']})"
        for name, v in ce["inputs"].items()
    )
    return textwrap.dedent(f"""\
        Your Rust implementation of `{func_name}` failed formal equivalence verification.
        The verifier found an input where your Rust code returns a different value than the original C++.

        ── C++ source (ground truth) ──────────────────────────────────────────
        {cpp_fn}

        ── Your current Rust implementation ───────────────────────────────────
        {rust_fn}

        ── Failing counterexample ─────────────────────────────────────────────
        Inputs:
        {input_lines}

          C++ returns  : {ce['cpp']}
          Rust returns : {ce['rust']}

        ── Task ───────────────────────────────────────────────────────────────
        Rewrite the Rust function so it matches the C++ return value for ALL
        possible 32-bit inputs, including edge cases like the one above.

        Rules:
        - Keep `#[no_mangle] pub extern "C"` and the same argument/return types.
        - Do NOT add `fn main()` or any other functions.
        - Do NOT use Rust standard library methods that might behave differently
          than the raw arithmetic in the C++ (e.g. avoid `wrapping_sub` if it
          changes edge-case semantics).
        - Output ONLY the fixed Rust function. No explanation, no markdown.
    """)


# ── main CEGIS loop ──────────────────────────────────────────────────────────

def cegis_loop(func_name: str, rust_src: str, cpp_src: str) -> tuple[str, bool]:
    """
    Run the CEGIS loop for one function.
    Returns (updated_rust_src, proven_equivalent).
    """
    print(f"\n{'━'*60}")
    print(f"  CEGIS: {func_name}")
    print(f"{'━'*60}")

    for iteration in range(1, MAX_ITER + 1):
        print(f"\n  [iter {iteration}] verifying...")

        # Write current src to disk and compile
        with open(RUST_SRC, "w") as f:
            f.write(rust_src)
        ok, err = compile_rust_to_ir(RUST_SRC, RUST_IR)
        if not ok:
            print(f"  [iter {iteration}] compile FAILED:\n{err[:400]}")
            # Feed compile error back to DeepSeek
            cpp_fn  = extract_cpp_function(cpp_src, func_name)
            rust_fn = extract_rust_function(rust_src, func_name)
            prompt  = (
                f"Your Rust function `{func_name}` has a compile error:\n\n"
                f"{err[:600]}\n\n"
                f"C++ original:\n{cpp_fn}\n\n"
                f"Current (broken) Rust:\n{rust_fn}\n\n"
                f"Output only the fixed Rust function with "
                f"`#[no_mangle] pub extern \"C\"` — no explanation."
            )
            fixed_fn = ask_deepseek(prompt)
            rust_src = replace_rust_function(rust_src, func_name, fixed_fn)
            continue

        # Run verifier
        result = run_verifier(CPP_IR, RUST_IR, func_name)

        if result["status"] == "equiv":
            print(f"  [iter {iteration}] ✓ PROVEN EQUIVALENT (UNSAT)")
            return rust_src, True

        if result["status"] == "error":
            print(f"  [iter {iteration}] verifier error: {result['msg'][:200]}")
            return rust_src, False

        # Divergence — build repair prompt
        ce = result
        print(f"  [iter {iteration}] divergence found:")
        for name, v in ce["inputs"].items():
            print(f"    {name} = {v['signed']} (0x{v['hex']})")
        print(f"    C++ → {ce['cpp']},  Rust → {ce['rust']}")
        print(f"  [iter {iteration}] asking DeepSeek to fix...")

        cpp_fn  = extract_cpp_function(cpp_src, func_name)
        rust_fn = extract_rust_function(rust_src, func_name)
        prompt  = build_repair_prompt(func_name, cpp_fn, rust_fn, ce)
        fixed_fn = ask_deepseek(prompt)

        print(f"  [iter {iteration}] DeepSeek fix:")
        for line in fixed_fn.splitlines():
            print(f"    {line}")

        rust_src = replace_rust_function(rust_src, func_name, fixed_fn)

    print(f"  [!] max iterations ({MAX_ITER}) reached without convergence")
    return rust_src, False


def main():
    # Start from the loose port as our initial Rust source
    with open("targets/jsmn_targets_loose.rs") as f:
        rust_src = f.read()
    with open(CPP_SRC) as f:
        cpp_src = f.read()

    print("Running initial verification pass on all functions...")
    print()

    # Quick initial pass to see what's diverging
    with open(RUST_SRC, "w") as f:
        f.write(rust_src)
    ok, err = compile_rust_to_ir(RUST_SRC, RUST_IR)
    if not ok:
        print(f"Initial compile failed:\n{err}")
        sys.exit(1)

    diverging = []
    for fn in FUNCS:
        r = run_verifier(CPP_IR, RUST_IR, fn)
        status = r.get("status", "error")
        mark = "✓" if status == "equiv" else ("✗" if status == "diverge" else "?")
        print(f"  {mark} {fn}")
        if status == "diverge":
            diverging.append(fn)

    if not diverging:
        print("\nAll functions already proven equivalent — nothing to fix!")
        return

    print(f"\nFound {len(diverging)} diverging function(s): {diverging}")
    print("Starting CEGIS repair loop...\n")

    final_proven = []
    final_failed = []

    for fn in diverging:
        rust_src, proved = cegis_loop(fn, rust_src, cpp_src)
        (final_proven if proved else final_failed).append(fn)

    # Write final repaired source
    with open("targets/jsmn_targets_repaired.rs", "w") as f:
        f.write(rust_src)
    print(f"\n{'━'*60}")
    print(f"  CEGIS complete")
    print(f"  Repaired source written to targets/jsmn_targets_repaired.rs")
    print(f"  Proven equivalent : {final_proven or '(none)'}")
    print(f"  Still diverging   : {final_failed or '(none)'}")
    print(f"{'━'*60}")


if __name__ == "__main__":
    main()
