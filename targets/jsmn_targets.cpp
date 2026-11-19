#include <stdint.h>

// ---------------------------------------------------------------------------
// All functions extracted from jsmn's core logic and exposed with a flat
// C ABI so clang++ and rustc produce matching symbol names for the verifier.
// ---------------------------------------------------------------------------

// Function 1 ----------------------------------------------------------------
// Valid character for a JSON primitive token body.
// jsmn rejects control chars (< 32) and DEL / non-ASCII (>= 127).
// Key subtlety: C's plain `char` is signed on ARM/x86, so a byte like 0xFF
// arrives as -1 — the `< 32` branch catches it.  Rust's u8 is always
// unsigned, so an LLM naively typing `c < 32u8` will never see the negative
// bytes and the two sides diverge on inputs 128..255.
extern "C" int32_t jsmn_is_valid_char(int32_t c) {
    if (c < 32 || c >= 127) {
        return 0;
    }
    return 1;
}

// Function 2 ----------------------------------------------------------------
// Whitespace / structural delimiter that ends a primitive token.
// Taken verbatim from the switch in jsmn_parse_primitive (non-strict mode,
// which also includes ':').
// LLM bug: forgetting ':' in the non-strict case, or using a Rust `matches!`
// macro that leaves out one arm.
extern "C" int32_t jsmn_is_delimiter(int32_t c) {
    switch (c) {
    case ':':
    case '\t':
    case '\r':
    case '\n':
    case ' ':
    case ',':
    case ']':
    case '}':
        return 1;
    default:
        return 0;
    }
}

// Function 3 ----------------------------------------------------------------
// Hex digit validator used inside the \uXXXX escape handler in
// jsmn_parse_string.  Checks three ASCII ranges: 0-9, A-F, a-f.
// LLM bug: using Rust's char::is_ascii_hexdigit() looks right, but that
// method also accepts 'g'-'f' (it doesn't — but LLM may flip && to || in
// the range checks, or swap inclusive/exclusive bounds by one).
// Another common bug: using `c >= b'0' && c <= b'9'` in Rust where c is i32
// — the byte literal is u8 so the comparison triggers a type mismatch the
// LLM patches by casting, sometimes wrongly.
extern "C" int32_t jsmn_is_hex_digit(int32_t c) {
    return ((c >= 48 && c <= 57) ||   // '0'..'9'
            (c >= 65 && c <= 70) ||   // 'A'..'F'
            (c >= 97 && c <= 102));   // 'a'..'f'
}

// Function 4 ----------------------------------------------------------------
// Valid character immediately after a backslash in a JSON string.
// jsmn allows exactly: " / \ b f r n t  (and 'u' handled separately).
// LLM bug: Rust `match` arm — forgetting '/' (JSON allows \/ as an escape),
// or adding extra arms, or returning a bool that gets widened differently.
extern "C" int32_t jsmn_escape_valid(int32_t c) {
    switch (c) {
    case '\"':
    case '/':
    case '\\':
    case 'b':
    case 'f':
    case 'r':
    case 'n':
    case 't':
        return 1;
    default:
        return 0;
    }
}

// Function 5 ----------------------------------------------------------------
// Bounds check before allocating a token from the pool.
// Returns the current index (toknext) if allocation is possible, -1 if full.
// LLM bug: both args are uint32_t in C.  LLM might cast them to i32 to do
// the comparison "safely" — but when toknext == 2147483648u the signed cast
// produces -2147483648, flipping the >= comparison result.
extern "C" int32_t jsmn_alloc_check(uint32_t toknext, uint32_t num_tokens) {
    if (toknext >= num_tokens) {
        return -1;
    }
    return (int32_t)toknext;
}

// Function 6 ----------------------------------------------------------------
// Safe-advance guard: can we look one character ahead without reading past
// the end of the buffer?
// jsmn writes this as `parser->pos + 1 < len`.
// LLM bug: rewrites as `pos < len - 1`.  When len == 0 that becomes
// `pos < 4294967295` (unsigned underflow), which is always true — a classic
// buffer-overread gate that Z3 immediately finds as a counterexample at
// pos=0, len=0.
extern "C" int32_t jsmn_safe_next(uint32_t pos, uint32_t len) {
    return (pos + 1 < len) ? 1 : 0;
}

// ---------------------------------------------------------------------------
// Trap functions — designed to expose classic C++ → Rust translation bugs.
// ---------------------------------------------------------------------------

// Trap 1 --------------------------------------------------------------------
// Sign-extension via shift pair: left-shift a value up to bit 31, then
// arithmetic-right-shift back down to sign-extend it.
//
// C++: `(int32_t)(x << shift) >> shift`
//   Step 1: x << shift  is uint32_t → maps to `shl i32` (unsigned, no UB)
//   Step 2: cast to int32_t         → reinterpret (no-op at IR level)
//   Step 3: >> shift on int32_t     → `ashr i32` (fills with sign bit)
//
// LLM bug: keeps x as u32 for both shifts →
//   `(x << shift >> shift) as i32`
//   Step 3 becomes `lshr i32` (fills with 0s, NOT sign bit).
//   For x=0x80, bits=8: C++ gives -128; buggy Rust gives +128.
extern "C" int32_t extend_sign(uint32_t x, uint32_t bits) {
    uint32_t shift = 32u - bits;
    return (int32_t)((int32_t)(x << shift) >> shift);
}

// Trap 2 --------------------------------------------------------------------
// Bit-reversal parity via XOR folding then lookup.
// All shifts are on uint32_t so they must compile to `lshr`, not `ashr`.
//
// LLM bug: works in i32 throughout, turning `>>` into `ashr`. For inputs
// with the high bit set (x >= 0x80000000 as uint32_t, i.e. negative i32),
// `ashr` fills with 1s instead of 0s, corrupting the XOR fold.
// e.g., x=0x80000000: lshr gives 0x00008000; ashr gives 0xFFFF8000.
extern "C" int32_t bit_parity(uint32_t x) {
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x &= 0xf;
    return (int32_t)((0x6996u >> x) & 1u);
}

// Trap 3 --------------------------------------------------------------------
// Saturating left shift: shift x left by n bits but cap at INT32_MAX.
// Uses unsigned arithmetic for the shift to avoid C++ UB on signed overflow,
// then compares against the threshold with a signed comparison.
//
// LLM bug: does the shift in i32 directly → rustc adds `nsw` flag →
// for large x the shift overflows and the `nsw` flag lets LLVM assume it
// didn't, breaking the overflow check.  Z3 finds this via the range where
// the signed result wraps negative but the threshold check says "no overflow".
extern "C" int32_t saturating_shl(uint32_t x, uint32_t n) {
    if (n >= 32u) return INT32_MAX;
    uint32_t shifted = x << n;
    // If any high bits were lost, saturate
    if (n > 0u && (shifted >> n) != x) return INT32_MAX;
    int32_t result = (int32_t)shifted;
    return (result < 0) ? INT32_MAX : result;
}
