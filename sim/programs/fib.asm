; Fibonacci on the LEDs: 0 1 1 2 3 5 8, then 8+13 overflows, C sets, JC halts.
; Exercises LDI, MOV, XCH, ADD, OUT, JC, JMP, HLT and the two-word jump.
; expect: 0 1 1 2 3 5 8
; expect-halt: end
        LDI 1
        MOV B,A
        LDI 0
loop:   OUT
        ADD
        XCH
        JC  end
        JMP loop
end:    HLT
