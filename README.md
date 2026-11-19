# equator

**Blog post**: [Can You Trust an AI to Rewrite Your Code?](https://akkeshavan.github.io/equator)

Semantic equivalence checker for LLM-ported C++ → Rust code, using LLVM IR and Z3.

Compiles both the original C++ and the AI-generated Rust to LLVM IR, symbolically executes each function into Z3 bit-vector formulas, and asks Z3 whether the two can ever disagree. UNSAT = proven equivalent over all 32-bit inputs. SAT = concrete counterexample.

Includes a CEGIS repair loop that feeds counterexamples back to DeepSeek for automatic repair.

---

## Setup

### 1. Clone the jsmn target (not tracked in this repo)

```bash
git clone https://github.com/zserge/jsmn.git jsmn
```

### 2. Create a Python virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install z3-solver llvmlite requests
```

### 3. Add your DeepSeek API key

```bash
echo "DEEPSEEK_API_KEY=your_key_here" > .env
```

### 4. Install compiler toolchains

- **clang++** (for C++ → LLVM IR): install via Xcode Command Line Tools on macOS, or `apt install clang` on Linux
- **rustc** (for Rust → LLVM IR): install via [rustup.rs](https://rustup.rs)

---

## Usage

### Emit LLVM IR for both sources

```bash
./emit_ir.sh targets/jsmn_targets.cpp targets/jsmn_targets.rs
# produces targets/jsmn_cpp.ll and targets/jsmn_rust.ll
```

### Run the equivalence checker

```bash
# Check all known functions
.venv/bin/python3 equiv_check.py targets/jsmn_cpp.ll targets/jsmn_rust.ll

# Check a single function
.venv/bin/python3 equiv_check.py targets/jsmn_cpp.ll targets/jsmn_rust.ll extend_sign
```

### Port functions using DeepSeek (strict translation)

```bash
.venv/bin/python3 port_with_deepseek.py
```

### Port functions using DeepSeek (idiomatic Rust, finds real bugs)

```bash
.venv/bin/python3 port_loose.py
```

### Run the CEGIS repair loop

```bash
.venv/bin/python3 cegis.py
```

---

## Project structure

```
equiv_check.py          # Core verifier: LLVM IR → Z3 → UNSAT/SAT
cegis.py                # CEGIS loop: verify → counterexample → LLM repair → repeat
port_with_deepseek.py   # Strict literal port via DeepSeek API
port_loose.py           # Idiomatic Rust port via DeepSeek API
emit_ir.sh              # Convenience wrapper around clang++ and rustc
targets/
  jsmn_targets.cpp      # Nine C++ functions extracted from jsmn
  jsmn_targets.rs       # Strict DeepSeek port
  jsmn_targets_loose.rs # Idiomatic DeepSeek port (contains deliberate trap bugs)
  jsmn_cpp.ll           # Compiled LLVM IR (C++)
  jsmn_rust.ll          # Compiled LLVM IR (Rust)
jsmn/                   # Upstream jsmn source — clone separately (see above)
```

---

## How it works

See the blog post for a full walkthrough: [Can You Trust an AI to Rewrite Your Code?](https://akkeshavan.github.io/equator)

---

## GitHub Pages (blog)

The `docs/` folder contains the Jekyll site that powers the blog.

To enable it on your fork:
1. Push to GitHub.
2. Go to **Settings → Pages → Source**: Deploy from branch → Branch: `main`, Folder: `/docs`.
3. The site will be live at `https://<your-username>.github.io/equator/`.

To preview locally:
```bash
cd docs
bundle install
bundle exec jekyll serve
# open http://localhost:4000/equator/
```
