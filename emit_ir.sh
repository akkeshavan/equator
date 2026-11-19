#!/usr/bin/env bash
# Usage: ./emit_ir.sh <name>.cpp <name>.rs
# Outputs: <name>_cpp.ll and <name>_rust.ll in the current directory
set -e

CPP_SRC="$1"
RS_SRC="$2"
BASE="${CPP_SRC%.cpp}"

clang++ -O1 -S -emit-llvm "$CPP_SRC" -o "${BASE}_cpp.ll"
rustc -C opt-level=1 --crate-type=cdylib --emit=llvm-ir --out-dir . "$RS_SRC"
# rustc names output after the crate; rename to match convention
RS_CRATE=$(basename "${RS_SRC%.rs}")
mv "${RS_CRATE}.ll" "${BASE}_rust.ll" 2>/dev/null || true

echo "C++ IR  → ${BASE}_cpp.ll"
echo "Rust IR → ${BASE}_rust.ll"
