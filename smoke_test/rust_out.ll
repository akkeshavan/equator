; ModuleID = 'target.50f4bdc50489af64-cgu.0'
source_filename = "target.50f4bdc50489af64-cgu.0"
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64-apple-macosx11.0.0"

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable
define noundef range(i32 -1, 1073741824) i32 @compute_offset(i32 noundef %base, i32 noundef %delta, i32 noundef %mask) unnamed_addr #0 personality ptr @rust_eh_personality {
start:
  %_0.i = add i32 %delta, %base
  %_6 = lshr i32 %_0.i, 2
  %0 = and i32 %_6, %mask
  %_4.inv = icmp sgt i32 %delta, -1
  %_0.sroa.0.0 = select i1 %_4.inv, i32 %0, i32 -1
  ret i32 %_0.sroa.0.0
}

; Function Attrs: nounwind uwtable
declare noundef range(i32 0, 10) i32 @rust_eh_personality(i32 noundef, i32 noundef, i64 noundef, ptr noundef, ptr noundef) unnamed_addr #1

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable "frame-pointer"="non-leaf" "probe-stack"="inline-asm" "target-cpu"="apple-m1" }
attributes #1 = { nounwind uwtable "frame-pointer"="non-leaf" "probe-stack"="inline-asm" "target-cpu"="apple-m1" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.95.0 (59807616e 2026-04-14)"}
