; Logic stress: AND, OR and XOR of the sixteen operand pairs (i, i+3) for i = 15 down to 0, shown in that order.
; lfsr.asm uses each logic function once, on one operand pair, so a wrong F0/F1 decode could hide behind a lucky
; operand. Here every bit of both operands is 0 and 1 across the pairs, and on every pair the three results differ
; from each other and from the sum; the emulator compares A and the flags every tick. Slot 0 = i.
; needs: datamem
; expect: 2 15 13 0 15 15 0 13 13 12 15 3 10 15 5 8 15 7 8 13 5 8 11 3 2 15 13 0 15 15 0 13 13 4 7 3 2 7 5 0 7 7 0 5 5 0 3 3
; expect-halt: end
        LDI 15
        STORE 0
loop:   LOAD 0          ; i
        MOV B,A
        LDI 3
        ADD
        MOV B,A         ; B = i + 3
        LOAD 0
        AND
        OUT
        LOAD 0
        OR
        OUT
        LOAD 0
        XOR
        OUT
        LOAD 0
        DEC
        STORE 0
        JC  loop        ; carry clear once i passes 0
end:    HLT
