; Loops on the inverted conditions (D044): JNZ counts down, JNC adds until the carry.
; expect: 5 4 3 2 1 0 3 6 9 12 15
; expect-halt: end
        LDI 5
down:   OUT             ; 5 4 3 2 1
        DEC
        JNZ down        ; falls through when A reaches 0
        LDI 3
        MOV B,A
        LDI 0
up:     OUT             ; 0 3 6 9 12 15
        ADD
        JNC up          ; 15 + 3 carries: done
end:    HLT
