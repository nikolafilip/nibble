; Pseudo-random numbers: a 4-bit linear feedback shift register (taps at bits 3 and 2) shown on the LEDs.
; Shift left is ADD with B = A; the carry catches the bit that falls out. The new low bit is bit3 xor bit2 of the old value.
; Fifteen steps visit every value 1..15 once, then the sequence repeats. Slots: 0 = state.
; needs: datamem
; expect: 1 2 4 9 3 6 13 10 5 11 7 15 14 12 8 1
; expect-halt: end
        LDI 1
        STORE 0
        LDI 15
        STORE 1         ; 16 outputs
loop:   LOAD 0
        OUT
        MOV B,A
        ADD             ; A = 2 * state, carry = old bit 3
        STORE 2         ; shifted value, low bit 0
        LDI 0
        JC  b3one
        JMP b2
b3one:  LDI 1
b2:     STORE 3         ; slot 3 = old bit 3
        LOAD 0
        MOV B,A
        LDI 4
        AND             ; isolate old bit 2
        JZ  b2zero
        LDI 1
        JMP fb
b2zero: LDI 0
fb:     MOV B,A
        LOAD 3
        XOR             ; feedback bit = bit3 xor bit2
        MOV B,A
        LOAD 2
        OR              ; new state = shifted | feedback
        STORE 0
        LOAD 1
        DEC
        STORE 1
        JC  loop        ; carry clear once the counter passes 0
end:    HLT
