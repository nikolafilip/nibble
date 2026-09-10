; Largest of four numbers held in data memory slots 0..3 (3, 9, 4, 7). Slot 4 holds the running maximum.
; needs: datamem
; expect: 9
; expect-halt: end
        LDI 3
        STORE 0
        LDI 9
        STORE 1
        LDI 4
        STORE 2
        LDI 7
        STORE 3
        LOAD 0
        STORE 4
        LOAD 1
        MOV B,A
        LOAD 4
        SUB             ; max - x: C = 1 means max >= x
        JC  k1
        LOAD 1
        STORE 4
k1:     LOAD 2
        MOV B,A
        LOAD 4
        SUB
        JC  k2
        LOAD 2
        STORE 4
k2:     LOAD 3
        MOV B,A
        LOAD 4
        SUB
        JC  k3
        LOAD 3
        STORE 4
k3:     LOAD 4
        OUT
end:    HLT
