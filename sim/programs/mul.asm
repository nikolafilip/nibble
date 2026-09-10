; 7 x 6 = 42 as an 8-bit product, by repeated addition through data memory.
; Slots: 0 = X, 1 = Y (count, must be >= 1), 2 = product low nibble, 3 = product high nibble.
; Only ADD and SUB set the flags, so the loop adds first and tests Y after the decrement.
; needs: datamem
; expect: 10 2
; expect-halt: end
        LDI 7
        STORE 0
        LDI 6
        STORE 1
        LDI 0
        STORE 2
        STORE 3
loop:   LOAD 0
        MOV B,A         ; B = X
        LOAD 2
        ADD
        STORE 2         ; low += X
        JC  carry
back:   LDI 1
        MOV B,A         ; B = 1
        LOAD 1
        SUB
        STORE 1         ; Y = Y - 1
        JZ  done
        JMP loop
carry:  LDI 1
        MOV B,A
        LOAD 3
        ADD
        STORE 3         ; high += 1
        JMP back
done:   LOAD 2
        OUT             ; 42 = 0x2A: low nibble 10
        LOAD 3
        OUT             ; high nibble 2
end:    HLT
