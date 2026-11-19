; ModuleID = 'jsmn_targets.fd8cb436b4ff23ca-cgu.0'
source_filename = "jsmn_targets.fd8cb436b4ff23ca-cgu.0"
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64-apple-macosx11.0.0"

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
define noundef range(i32 0, 2) i32 @jsmn_is_hex_digit(i32 noundef %c) unnamed_addr #0 {
start:
  %0 = add i32 %c, -48
  %or.cond = icmp ult i32 %0, 10
  %1 = and i32 %c, -33
  %2 = add i32 %1, -65
  %3 = icmp ult i32 %2, 6
  %or.cond4 = or i1 %or.cond, %3
  %_0.sroa.0.0 = zext i1 %or.cond4 to i32
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

; Function Attrs: nounwind uwtable
declare noundef range(i32 0, 10) i32 @rust_eh_personality(i32 noundef, i32 noundef, i64 noundef, ptr noundef, ptr noundef) unnamed_addr #1

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable "frame-pointer"="non-leaf" "probe-stack"="inline-asm" "target-cpu"="apple-m1" }
attributes #1 = { nounwind uwtable "frame-pointer"="non-leaf" "probe-stack"="inline-asm" "target-cpu"="apple-m1" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.95.0 (59807616e 2026-04-14)"}
