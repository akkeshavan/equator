#!/usr/bin/env python3
"""
equiv_check.py — Prove C++ ↔ Rust function equivalence via LLVM IR + Z3.

Symbolically executes both LLVM IR functions into Z3 BitVec formulas and asks:
  ∃ input . cpp_return(input) ≠ rust_return(input)

UNSAT → proven equivalent for all inputs.
SAT   → Z3 produces the exact input that exposes the divergence.

Usage:
    # single function
    .venv/bin/python3 equiv_check.py targets/jsmn_cpp.ll targets/jsmn_rust.ll jsmn_is_valid_char

    # all 6 jsmn functions at once
    .venv/bin/python3 equiv_check.py --all targets/jsmn_cpp.ll targets/jsmn_rust.ll
"""

import re
import sys
import llvmlite.binding as llvm
import z3

KNOWN_FUNCS = [
    "jsmn_is_valid_char",
    "jsmn_is_delimiter",
    "jsmn_is_hex_digit",
    "jsmn_escape_valid",
    "jsmn_alloc_check",
    "jsmn_safe_next",
    # Trap functions designed to expose classic C++ → Rust translation bugs
    "extend_sign",
    "bit_parity",
    "saturating_shl",
]

# ---------------------------------------------------------------------------
# IR loading
# ---------------------------------------------------------------------------

def load_function(ir_path, func_name):
    with open(ir_path) as f:
        ir = f.read()
    mod = llvm.parse_assembly(ir)
    mod.verify()
    return mod.get_function(func_name)


def make_sym_args(func):
    """Create Z3 symbolic BitVec args sized to match the function's argument types."""
    args = []
    # Parse widths from the function signature text (first line)
    sig = str(func).split('\n')[0]
    widths = [int(m.group(1)) for m in re.finditer(r'\bi(\d+)\s+(?:noundef\s+)?%', sig)]
    if not widths:
        widths = [32] * len(list(func.arguments))
    for i, (arg, w) in enumerate(zip(func.arguments, widths)):
        args.append(z3.BitVec(f'arg_{i}', w))
    return args


# ---------------------------------------------------------------------------
# Symbolic executor
# ---------------------------------------------------------------------------

class SymExec:
    """
    Walks the CFG of an LLVM function, translating each instruction into a
    Z3 expression.  Branches fork the symbolic state; the result is a list of
    (path_condition, return_value) pairs — one per execution path.
    """

    def __init__(self, func, sym_args):
        self.func = func
        all_blocks = list(func.blocks)

        if any(b.name for b in all_blocks):
            # Rust IR: blocks have explicit string labels ('start', 'bb2', …)
            self.blocks = {b.name: b for b in all_blocks}
            self._entry_name = all_blocks[0].name
        else:
            # C++ IR: all blocks are unnamed (llvmlite returns '').
            # LLVM's value-slot numbering assigns:
            #   slots 0..n_args-1  → function arguments (%0, %1, …)
            #   slot  n_args       → entry block (implicit label)
            #   slots n_args+1..   → explicit block labels (2:, 3:, …)
            # Parse explicit labels from the function IR text so we can map
            # label strings to Block objects.
            n_args = len(list(func.arguments))
            self._entry_name = str(n_args)
            func_ir = str(func)
            labels = re.findall(
                r'^([A-Za-z0-9_.]+):\s*(?:;.*)?$', func_ir, re.MULTILINE)
            self.blocks = {self._entry_name: all_blocks[0]}
            for i, label in enumerate(labels):
                if i + 1 < len(all_blocks):
                    self.blocks[label] = all_blocks[i + 1]

        # Seed env with symbolic arguments.
        # C++ args are unnamed (%0, %1 …) → arg.name == ''; use index string.
        # Rust args are named (%c, %pos …) → arg.name is the string directly.
        self._base_env = {}
        for i, (arg, expr) in enumerate(zip(func.arguments, sym_args)):
            name = arg.name if arg.name else str(i)
            self._base_env[name] = expr

    # ------------------------------------------------------------------
    def run(self):
        return self._exec_block(
            self._entry_name, z3.BoolVal(True), dict(self._base_env), predecessor=None
        )

    # ------------------------------------------------------------------
    def _exec_block(self, bname, pc, env, predecessor):
        """Execute one basic block; return list of (path_cond, return_expr)."""
        if z3.is_false(pc):
            return []
        env = dict(env)
        for inst in self.blocks[bname].instructions:
            result = self._inst(inst.opcode, str(inst).strip(), bname, env, pc, predecessor)
            if result is not None:          # terminal instruction
                return result
        return []                           # should not be reached in valid IR

    # ------------------------------------------------------------------
    def _inst(self, op, line, bname, env, pc, pred):
        """
        Process one instruction.
        Returns None to keep going, or [(pc, z3_expr)] for terminal instructions.
        Modifies env in-place for assignment instructions.
        """

        # ── Binary arithmetic (i32 or i1) ──────────────────────────────
        if op in ('add', 'sub', 'mul', 'and', 'or', 'xor', 'shl', 'ashr', 'lshr'):
            m = re.match(
                r'%([A-Za-z0-9_.]+)\s*=\s*\S+'
                r'(?:\s+(?:nsw|nuw|exact))*\s+i(\d+)\s+'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+),\s*'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+)',
                line)
            if m:
                dest, w = m.group(1), int(m.group(2))
                ls, rs = m.group(3), m.group(4)
                if w == 1:          # boolean ops on i1
                    lb, rb = self._bool(ls, env), self._bool(rs, env)
                    env[dest] = {'or': z3.Or, 'and': z3.And, 'xor': z3.Xor}[op](lb, rb)
                else:
                    l, r = self._bv(ls, w, env), self._bv(rs, w, env)
                    env[dest] = {
                        'add': l + r, 'sub': l - r, 'mul': l * r,
                        'and': l & r, 'or':  l | r, 'xor': l ^ r,
                        'shl': l << r, 'ashr': l >> r, 'lshr': z3.LShR(l, r),
                    }[op]
            return None

        # ── icmp ────────────────────────────────────────────────────────
        elif op == 'icmp':
            m = re.match(
                r'%([A-Za-z0-9_.]+)\s*=\s*icmp\s+(\w+)\s+i(\d+)\s+'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+),\s*'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+)',
                line)
            if m:
                dest, prd, w = m.group(1), m.group(2), int(m.group(3))
                l, r = self._bv(m.group(4), w, env), self._bv(m.group(5), w, env)
                env[dest] = {
                    'eq': l == r,  'ne': l != r,
                    'slt': l < r,  'sle': l <= r,  'sgt': l > r,  'sge': l >= r,
                    'ult': z3.ULT(l, r), 'ule': z3.ULE(l, r),
                    'ugt': z3.UGT(l, r), 'uge': z3.UGE(l, r),
                }[prd]            # result is z3.Bool
            return None

        # ── Type conversion: zext / sext / trunc ────────────────────────
        elif op in ('zext', 'sext', 'trunc'):
            m = re.match(
                r'%([A-Za-z0-9_.]+)\s*=\s*\S+\s+i(\d+)\s+'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+)\s+to\s+i(\d+)',
                line)
            if m:
                dest, sw, src_s, dw = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
                if sw == 1:         # i1 → iN
                    b = self._bool(src_s, env)
                    env[dest] = z3.If(b, z3.BitVecVal(1, dw), z3.BitVecVal(0, dw))
                else:
                    src = self._bv(src_s, sw, env)
                    env[dest] = {
                        'zext':  z3.ZeroExt(dw - sw, src),
                        'sext':  z3.SignExt(dw - sw, src),
                        'trunc': z3.Extract(dw - 1, 0, src),
                    }[op]
            return None

        # ── select ──────────────────────────────────────────────────────
        elif op == 'select':
            m = re.match(
                r'%([A-Za-z0-9_.]+)\s*=\s*select\s+i1\s+'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+|true|false),\s*i(\d+)\s+'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+|true|false),\s*i\d+\s+'
                r'(%[A-Za-z0-9_.]+|-?[0-9]+|true|false)',
                line)
            if m:
                dest, cond_s, w, t_s, f_s = (
                    m.group(1), m.group(2), int(m.group(3)), m.group(4), m.group(5))
                cond = self._bool(cond_s, env)
                if w == 1:
                    # select i1 cond, i1 tv, i1 fv  → Bool result
                    env[dest] = z3.If(cond, self._bool(t_s, env), self._bool(f_s, env))
                else:
                    env[dest] = z3.If(cond, self._bv(t_s, w, env), self._bv(f_s, w, env))
            return None

        # ── call (LLVM intrinsics only) ─────────────────────────────────
        elif op == 'call':
            m = re.match(
                r'%([A-Za-z0-9_.]+)\s*=\s*(?:tail\s+)?call\s+i(\d+)\s+'
                r'@(llvm\.[a-z0-9._]+)\((.+)\)',
                line)
            if m:
                dest, w, intr, args_s = (
                    m.group(1), int(m.group(2)), m.group(3), m.group(4))
                # Parse "iN %reg" or "iN literal" argument list
                arg_vals = [self._bv(a.strip().split()[-1], w, env)
                            for a in args_s.split(',')]
                a, b = arg_vals[0], arg_vals[1] if len(arg_vals) > 1 else arg_vals[0]
                intrinsic_map = {
                    'llvm.umin.i32': z3.If(z3.ULT(a, b), a, b),
                    'llvm.umax.i32': z3.If(z3.UGT(a, b), a, b),
                    'llvm.smin.i32': z3.If(a < b, a, b),
                    'llvm.smax.i32': z3.If(a > b, a, b),
                    'llvm.umin.i64': z3.If(z3.ULT(a, b), a, b),
                    'llvm.umax.i64': z3.If(z3.UGT(a, b), a, b),
                }
                if intr in intrinsic_map:
                    env[dest] = intrinsic_map[intr]
            return None

        # ── phi ─────────────────────────────────────────────────────────
        elif op == 'phi':
            m = re.match(
                r'%([A-Za-z0-9_.]+)\s*=\s*phi\s+i(\d+)\s+(.+)',
                line)
            if m:
                dest, w, rest = m.group(1), int(m.group(2)), m.group(3)
                pairs = re.findall(
                    r'\[\s*(%[A-Za-z0-9_.]+|-?[0-9]+),\s*%([A-Za-z0-9_.]+)\s*\]',
                    rest)
                # Select the value whose predecessor label matches where we came from
                val = None
                for val_s, blk in pairs:
                    if blk == pred:
                        val = self._bv(val_s, w, env)
                        break
                if val is None and pairs:
                    val = self._bv(pairs[0][0], w, env)   # fallback
                if val is not None:
                    env[dest] = val
            return None

        # ── ret ─────────────────────────────────────────────────────────
        elif op == 'ret':
            m = re.match(
                r'ret\s+i(\d+)\s+(%[A-Za-z0-9_.]+|-?[0-9]+)',
                line)
            if m:
                return [(pc, self._bv(m.group(2), int(m.group(1)), env))]
            return []           # ret void

        # ── br ──────────────────────────────────────────────────────────
        elif op == 'br':
            # Conditional branch
            m = re.match(
                r'br\s+i1\s+(%[A-Za-z0-9_.]+|-?[0-9]+),\s*'
                r'label\s*%([A-Za-z0-9_.]+),\s*'
                r'label\s*%([A-Za-z0-9_.]+)',
                line)
            if m:
                cond = self._bool(m.group(1), env)
                t_bb, f_bb = m.group(2), m.group(3)
                return (
                    self._exec_block(t_bb, z3.And(pc, cond),        env, bname) +
                    self._exec_block(f_bb, z3.And(pc, z3.Not(cond)), env, bname)
                )
            # Unconditional branch
            m = re.match(r'br\s+label\s*%([A-Za-z0-9_.]+)', line)
            if m:
                return self._exec_block(m.group(1), pc, env, bname)
            return []

        # ── switch ──────────────────────────────────────────────────────
        elif op == 'switch':
            return self._exec_switch(line, bname, env, pc)

        # ── everything else (function attrs, metadata, etc.) ────────────
        return None

    # ------------------------------------------------------------------
    def _exec_switch(self, line, bname, env, pc):
        """
        Fork symbolic execution for a switch instruction.
        Groups cases by destination label — all cases going to the same block
        become a single Or-condition path.
        """
        m = re.match(
            r'switch\s+i(\d+)\s+'
            r'(%[A-Za-z0-9_.]+|-?[0-9]+),\s*'
            r'label\s*%([A-Za-z0-9_.]+)',
            line)
        if not m:
            return []
        w, val_s, default_bb = int(m.group(1)), m.group(2), m.group(3)
        val = self._bv(val_s, w, env)

        # All case entries: (numeric_value, destination_label)
        cases = [(int(v), lbl)
                 for v, lbl in re.findall(r'i\d+\s+(-?[0-9]+),\s*label\s*%([A-Za-z0-9_.]+)', line)]

        # Group by destination label
        label_vals: dict = {}
        for cv, lbl in cases:
            label_vals.setdefault(lbl, []).append(cv)

        all_case_vals = [cv for cv, _ in cases]
        results = []

        # One fork per unique case destination
        for lbl, vals in label_vals.items():
            match_cond = z3.Or([val == z3.BitVecVal(v, w) for v in vals])
            results += self._exec_block(lbl, z3.And(pc, match_cond), env, bname)

        # Default fork: none of the case values matched
        no_match = z3.And([val != z3.BitVecVal(v, w) for v in all_case_vals]) \
                   if all_case_vals else z3.BoolVal(True)
        results += self._exec_block(default_bb, z3.And(pc, no_match), env, bname)

        return results

    # ------------------------------------------------------------------
    # Operand helpers
    # ------------------------------------------------------------------

    def _bv(self, operand, width, env):
        """Resolve an operand to a BitVec(width) Z3 expression."""
        operand = operand.strip()
        if operand == 'true':  return z3.BitVecVal(1, width)
        if operand == 'false': return z3.BitVecVal(0, width)
        if operand.startswith('%'):
            v = env[operand[1:]]
            if z3.is_bool(v):
                return z3.If(v, z3.BitVecVal(1, width), z3.BitVecVal(0, width))
            if v.size() != width:
                diff = width - v.size()
                return z3.ZeroExt(diff, v) if diff > 0 else z3.Extract(width - 1, 0, v)
            return v
        return z3.BitVecVal(int(operand), width)

    def _bool(self, operand, env):
        """Resolve an operand to a Z3 Bool."""
        operand = operand.strip()
        if operand.startswith('%'):
            v = env[operand[1:]]
            return v if z3.is_bool(v) else v != z3.BitVecVal(0, v.size())
        if operand == 'true':  return z3.BoolVal(True)
        if operand == 'false': return z3.BoolVal(False)
        return z3.BoolVal(int(operand) != 0)


# ---------------------------------------------------------------------------
# Fold list of paths into one Z3 ITE expression
# ---------------------------------------------------------------------------

def paths_to_z3(paths):
    """Fold [(cond1,val1), (cond2,val2), ...] into a single ITE Z3 expression."""
    if not paths:
        raise ValueError("No return paths — function may have unsupported opcodes")
    # Build ITE tree: If(cond1, val1, If(cond2, val2, ... last_val))
    expr = paths[-1][1]
    for pc, val in reversed(paths[:-1]):
        expr = z3.If(pc, val, expr)
    return expr


# ---------------------------------------------------------------------------
# Main verification entry point
# ---------------------------------------------------------------------------

def verify(cpp_ir, rust_ir, func_name):
    try:
        f_cpp  = load_function(cpp_ir,  func_name)
        f_rust = load_function(rust_ir, func_name)
    except Exception as e:
        print(f"  [SKIP  ] {func_name}: {e}")
        return None

    sym_args = make_sym_args(f_cpp)

    try:
        cpp_paths  = SymExec(f_cpp,  sym_args).run()
        rust_paths = SymExec(f_rust, sym_args).run()
        cpp_expr   = paths_to_z3(cpp_paths)
        rust_expr  = paths_to_z3(rust_paths)
    except Exception as e:
        print(f"  [ERROR ] {func_name}: symbolic execution failed — {e}")
        return None

    s = z3.Solver()
    s.add(cpp_expr != rust_expr)

    result = s.check()

    if result == z3.sat:
        m = s.model()
        inputs = {}
        for a in sym_args:
            raw = m.eval(a)
            # show both signed and hex for readability
            inputs[str(a)] = f"{raw.as_signed_long()} (0x{raw.as_long():08x})"
        cpp_val  = m.eval(cpp_expr).as_signed_long()
        rust_val = m.eval(rust_expr).as_signed_long()
        print(f"  [DIVERGE] {func_name}")
        for k, v in inputs.items():
            print(f"    input  {k} = {v}")
        print(f"    C++ returns  : {cpp_val}")
        print(f"    Rust returns : {rust_val}")
        return False

    elif result == z3.unsat:
        print(f"  [EQUIV  ] {func_name}  — proven equivalent (UNSAT)")
        return True

    else:
        print(f"  [UNKNOWN] {func_name}  — Z3 timed out or returned unknown")
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    args = sys.argv[1:]

    if '--all' in args:
        args.remove('--all')
        if len(args) < 2:
            sys.exit("Usage: equiv_check.py --all <cpp.ll> <rust.ll>")
        cpp_ir, rust_ir = args[0], args[1]
        funcs = KNOWN_FUNCS
    elif len(args) == 3:
        cpp_ir, rust_ir, func = args
        funcs = [func]
    else:
        sys.exit(
            "Usage:\n"
            "  equiv_check.py <cpp.ll> <rust.ll> <func_name>\n"
            "  equiv_check.py --all <cpp.ll> <rust.ll>"
        )

    print(f"Checking {len(funcs)} function(s)...\n")
    passed = failed = skipped = 0
    for fn in funcs:
        r = verify(cpp_ir, rust_ir, fn)
        if r is True:  passed  += 1
        elif r is False: failed += 1
        else:            skipped += 1

    if len(funcs) > 1:
        print(f"\n{'─'*50}")
        print(f"  {passed} equivalent   {failed} diverging   {skipped} skipped/error")
