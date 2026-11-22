#[no_mangle]
pub extern "C" fn jsmn_is_valid_char(c: i32) -> i32 {
    if c < 32 || c >= 127 {
        0
    } else {
        1
    }
}

#[no_mangle]
pub extern "C" fn jsmn_is_delimiter(c: i32) -> i32 {
    match c {
        58 | 9 | 13 | 10 | 32
        | 44 | 93 | 125 => 1,
        _ => 0,
    }
}

#[no_mangle]
pub extern "C" fn jsmn_is_hex_digit(c: i32) -> i32 {
    if (48..=57).contains(&c) || (65..=70).contains(&c) || (97..=102).contains(&c) {
        1
    } else {
        0
    }
}

#[no_mangle]
pub extern "C" fn jsmn_escape_valid(c: i32) -> i32 {
    match c {
        34 | 47 | 92 | 98 | 102
        | 114 | 110 | 116 => 1,
        _ => 0,
    }
}

#[no_mangle]
pub extern "C" fn jsmn_alloc_check(toknext: u32, num_tokens: u32) -> i32 {
    if toknext >= num_tokens {
        -1
    } else {
        toknext as i32
    }
}

#[no_mangle]
pub extern "C" fn jsmn_safe_next(pos: u32, len: u32) -> i32 {
    if pos.wrapping_add(1) < len { 1 } else { 0 }
}

#[no_mangle]
pub extern "C" fn extend_sign(x: u32, bits: u32) -> i32 {
    let shift = 32u32.wrapping_sub(bits);
    if shift >= 32 {
        return 0;
    }
    let shifted = x.wrapping_shl(shift);
    (shifted as i32) >> shift
}








#[no_mangle]
pub extern "C" fn bit_parity(x: u32) -> i32 {
    let mut x = x;
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x &= 0xf;
    ((0x6996u32 >> x) & 1u32) as i32
}

#[no_mangle]
pub extern "C" fn saturating_shl(x: u32, n: u32) -> i32 {
    if n >= 32 {
        return i32::MAX;
    }
    let shifted = x << n;
    if n > 0 && (shifted >> n) != x {
        return i32::MAX;
    }
    let result = shifted as i32;
    if result < 0 { i32::MAX } else { result }
}
