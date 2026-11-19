#[no_mangle]
pub extern "C" fn jsmn_is_valid_char(c: i32) -> i32 {
    if c < 32 || c >= 127 {
        return 0;
    }
    return 1;
}

#[no_mangle]
pub extern "C" fn jsmn_is_delimiter(c: i32) -> i32 {
    match c {
        58 | 9 | 13 | 10 | 32 | 44 | 93 | 125 => 1,
        _ => 0,
    }
}

#[no_mangle]
pub extern "C" fn jsmn_is_hex_digit(c: i32) -> i32 {
    if (c >= 48 && c <= 57) || (c >= 65 && c <= 70) || (c >= 97 && c <= 102) {
        1
    } else {
        0
    }
}

#[no_mangle]
pub extern "C" fn jsmn_escape_valid(c: i32) -> i32 {
    match c {
        34 | 47 | 92 | 98 | 102 | 114 | 110 | 116 => 1,
        _ => 0,
    }
}

#[no_mangle]
pub extern "C" fn jsmn_alloc_check(toknext: u32, num_tokens: u32) -> i32 {
    if toknext >= num_tokens {
        return -1;
    }
    toknext as i32
}

#[no_mangle]
pub extern "C" fn jsmn_safe_next(pos: u32, len: u32) -> i32 {
    if pos.wrapping_add(1) < len { 1 } else { 0 }
}
