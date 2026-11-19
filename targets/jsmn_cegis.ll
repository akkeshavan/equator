; ModuleID = 'jsmn_targets_cegis.27d41c1f10fd16a7-cgu.0'
source_filename = "jsmn_targets_cegis.27d41c1f10fd16a7-cgu.0"
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64-apple-macosx11.0.0"

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, 2) i32 @bit_parity(i32 noundef %0) unnamed_addr #0 {
start:
  %_2 = lshr i32 %0, 16
  %1 = xor i32 %_2, %0
  %_4 = lshr i32 %1, 8
  %2 = xor i32 %_4, %1
  %_6 = lshr i32 %2, 4
  %3 = xor i32 %_6, %2
  %4 = and i32 %3, 15
  %_9 = lshr i32 27030, %4
  %_8 = and i32 %_9, 1
  ret i32 %_8
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef i32 @extend_sign(i32 noundef %x, i32 noundef %bits) unnamed_addr #0 personality ptr @rust_eh_personality {
start:
  %_0.i1 = sub i32 0, %bits
  %rhs1.i = and i32 %_0.i1, 31
  %_0.i = shl i32 %x, %rhs1.i
  %_0 = ashr exact i32 %_0.i, %rhs1.i
  ret i32 %_0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef i32 @jsmn_alloc_check(i32 noundef %toknext, i32 noundef %num_tokens) unnamed_addr #0 {
start:
  %_3.not = icmp ult i32 %toknext, %num_tokens
  %toknext. = select i1 %_3.not, i32 %toknext, i32 -1
  ret i32 %toknext.
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, 2) i32 @jsmn_escape_valid(i32 noundef %c) unnamed_addr #0 {
start:
  switch i32 %c, label %bb3 [
    i32 34, label %bb2
    i32 47, label %bb2
    i32 92, label %bb2
    i32 98, label %bb2
    i32 102, label %bb2
    i32 114, label %bb2
    i32 110, label %bb2
    i32 116, label %bb2
  ]

bb2:                                              ; preds = %start, %start, %start, %start, %start, %start, %start, %start
  br label %bb3

bb3:                                              ; preds = %start, %bb2
  %_0.sroa.0.0 = phi i32 [ 1, %bb2 ], [ 0, %start ]
  ret i32 %_0.sroa.0.0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, 2) i32 @jsmn_is_delimiter(i32 noundef %c) unnamed_addr #0 {
start:
  switch i32 %c, label %bb3 [
    i32 58, label %bb2
    i32 9, label %bb2
    i32 13, label %bb2
    i32 10, label %bb2
    i32 32, label %bb2
    i32 44, label %bb2
    i32 93, label %bb2
    i32 125, label %bb2
  ]

bb2:                                              ; preds = %start, %start, %start, %start, %start, %start, %start, %start
  br label %bb3

bb3:                                              ; preds = %start, %bb2
  %_0.sroa.0.0 = phi i32 [ 1, %bb2 ], [ 0, %start ]
  ret i32 %_0.sroa.0.0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, 2) i32 @jsmn_is_hex_digit(i32 noundef %0) unnamed_addr #0 personality ptr @rust_eh_personality {
start:
  %1 = add i32 %0, -48
  %spec.select15 = icmp ult i32 %1, 10
  %2 = and i32 %0, -33
  %3 = add i32 %2, -65
  %4 = icmp ult i32 %3, 6
  %narrow = or i1 %spec.select15, %4
  %_0.sroa.0.0 = zext i1 %narrow to i32
  ret i32 %_0.sroa.0.0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, 2) i32 @jsmn_is_valid_char(i32 noundef %c) unnamed_addr #0 {
start:
  %0 = add i32 %c, -32
  %or.cond = icmp ult i32 %0, 95
  %. = zext i1 %or.cond to i32
  ret i32 %.
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, 2) i32 @jsmn_safe_next(i32 noundef %pos, i32 noundef %len) unnamed_addr #0 personality ptr @rust_eh_personality {
start:
  %_0.i = add i32 %pos, 1
  %_3 = icmp ult i32 %_0.i, %len
  %. = zext i1 %_3 to i32
  ret i32 %.
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 0, -2147483648) i32 @saturating_shl(i32 noundef %x, i32 noundef %n) unnamed_addr #0 {
start:
  %_3 = icmp ugt i32 %n, 31
  br i1 %_3, label %bb10, label %bb2

bb2:                                              ; preds = %start
  %shifted = shl i32 %x, %n
  %_5.not = icmp eq i32 %n, 0
  %_7 = lshr exact i32 %shifted, %n
  %_6.not = icmp eq i32 %_7, %x
  %or.cond = select i1 %_5.not, i1 true, i1 %_6.not
  %spec.store.select = tail call i32 @llvm.umin.i32(i32 %shifted, i32 2147483647)
  %spec.select = select i1 %or.cond, i32 %spec.store.select, i32 2147483647
  br label %bb10

bb10:                                             ; preds = %bb2, %start
  %result.sroa.0.0 = phi i32 [ %spec.select, %bb2 ], [ 2147483647, %start ]
  ret i32 %result.sroa.0.0
}

; Function Attrs: nounwind uwtable
declare noundef range(i32 0, 10) i32 @rust_eh_personality(i32 noundef, i32 noundef, i64 noundef, ptr noundef, ptr noundef) unnamed_addr #1

; Function Attrs: nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none)
declare i32 @llvm.umin.i32(i32, i32) #2

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable "frame-pointer"="non-leaf" "probe-stack"="inline-asm" "target-cpu"="apple-m1" }
attributes #1 = { nounwind uwtable "frame-pointer"="non-leaf" "probe-stack"="inline-asm" "target-cpu"="apple-m1" }
attributes #2 = { nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.95.0 (59807616e 2026-04-14)"}
