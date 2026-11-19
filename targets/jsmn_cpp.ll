; ModuleID = 'jsmn_targets.cpp'
source_filename = "jsmn_targets.cpp"
target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64-apple-macosx15.0.0"

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define range(i32 0, 2) i32 @jsmn_is_valid_char(i32 noundef %0) local_unnamed_addr #0 {
  %2 = add i32 %0, -32
  %3 = icmp ult i32 %2, 95
  %4 = zext i1 %3 to i32
  ret i32 %4
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define range(i32 0, 2) i32 @jsmn_is_delimiter(i32 noundef %0) local_unnamed_addr #0 {
  switch i32 %0, label %2 [
    i32 58, label %3
    i32 9, label %3
    i32 13, label %3
    i32 10, label %3
    i32 32, label %3
    i32 44, label %3
    i32 93, label %3
    i32 125, label %3
  ]

2:                                                ; preds = %1
  br label %3

3:                                                ; preds = %1, %1, %1, %1, %1, %1, %1, %1, %2
  %4 = phi i32 [ 0, %2 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ]
  ret i32 %4
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define range(i32 0, 2) i32 @jsmn_is_hex_digit(i32 noundef %0) local_unnamed_addr #0 {
  %2 = add i32 %0, -48
  %3 = icmp ult i32 %2, 10
  %4 = and i32 %0, -33
  %5 = add i32 %4, -65
  %6 = icmp ult i32 %5, 6
  %7 = or i1 %3, %6
  %8 = zext i1 %7 to i32
  ret i32 %8
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define range(i32 0, 2) i32 @jsmn_escape_valid(i32 noundef %0) local_unnamed_addr #0 {
  switch i32 %0, label %2 [
    i32 34, label %3
    i32 47, label %3
    i32 92, label %3
    i32 98, label %3
    i32 102, label %3
    i32 114, label %3
    i32 110, label %3
    i32 116, label %3
  ]

2:                                                ; preds = %1
  br label %3

3:                                                ; preds = %1, %1, %1, %1, %1, %1, %1, %1, %2
  %4 = phi i32 [ 0, %2 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ], [ 1, %1 ]
  ret i32 %4
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define noundef i32 @jsmn_alloc_check(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = icmp ult i32 %0, %1
  %4 = select i1 %3, i32 %0, i32 -1
  ret i32 %4
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define range(i32 0, 2) i32 @jsmn_safe_next(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = add i32 %0, 1
  %4 = icmp ult i32 %3, %1
  %5 = zext i1 %4 to i32
  ret i32 %5
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define i32 @extend_sign(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = sub i32 32, %1
  %4 = shl i32 %0, %3
  %5 = ashr exact i32 %4, %3
  ret i32 %5
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define range(i32 0, 2) i32 @bit_parity(i32 noundef %0) local_unnamed_addr #0 {
  %2 = lshr i32 %0, 16
  %3 = xor i32 %2, %0
  %4 = lshr i32 %3, 8
  %5 = xor i32 %4, %3
  %6 = lshr i32 %5, 4
  %7 = xor i32 %6, %5
  %8 = and i32 %7, 15
  %9 = lshr i32 27030, %8
  %10 = and i32 %9, 1
  ret i32 %10
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync)
define i32 @saturating_shl(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = icmp ugt i32 %1, 31
  br i1 %3, label %12, label %4

4:                                                ; preds = %2
  %5 = shl i32 %0, %1
  %6 = icmp eq i32 %1, 0
  %7 = lshr exact i32 %5, %1
  %8 = icmp eq i32 %7, %0
  %9 = select i1 %6, i1 true, i1 %8
  %10 = tail call i32 @llvm.umin.i32(i32 %5, i32 2147483647)
  %11 = select i1 %9, i32 %10, i32 2147483647
  br label %12

12:                                               ; preds = %2, %4
  %13 = phi i32 [ %11, %4 ], [ 2147483647, %2 ]
  ret i32 %13
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i32 @llvm.umin.i32(i32, i32) #1

attributes #0 = { mustprogress nofree norecurse nosync nounwind ssp willreturn memory(none) uwtable(sync) "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #1 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 2, !"SDK Version", [2 x i32] [i32 15, i32 5]}
!1 = !{i32 1, !"wchar_size", i32 4}
!2 = !{i32 8, !"PIC Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 1}
!4 = !{i32 7, !"frame-pointer", i32 1}
!5 = !{!"Apple clang version 17.0.0 (clang-1700.0.13.5)"}
