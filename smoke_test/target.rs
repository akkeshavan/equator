#[no_mangle]
pub extern "C" fn compute_offset(base: i32, delta: i32, mask: u32) -> i32 {
    if delta < 0 {
        return -1;
    }
    // Intentional LLM-style bug: casts to u32 before shifting → lshr instead of ashr
    let shifted = ((base.wrapping_add(delta)) as u32 >> 2) as i32;
    shifted & ((mask & 0x7FFF_FFFF) as i32)
}
