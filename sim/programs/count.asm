; Count 0..15 on the LEDs, wrap (ADD sets C), then count 15..0 down with SUB and JZ.
; expect: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1 0
; expect-halt: end
        LDI 1
        MOV B,A         ; B = 1
        LDI 0
up:     OUT
        ADD             ; A = A + 1
        JC  top         ; 15 + 1 wraps to 0 with carry
        JMP up
top:    LDI 15
down:   OUT
        SUB             ; A = A - 1
        JZ  last
        JMP down
last:   OUT             ; show the final 0
end:    HLT
