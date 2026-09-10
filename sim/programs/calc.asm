; Interactive multiply: read two numbers from the panel switches, show the 8-bit product, high nibble then low.
; The multiply is a subroutine called with X in slot 0 and Y (>= 1) in slot 1; result in slots 2 (low) and 3 (high).
; input: 13 11
; expect: 8 15
; expect-halt: end
        IN
        STORE 0         ; X = 13
        IN
        STORE 1         ; Y = 11
        CALL mul
        LOAD 3
        OUT             ; 143 = 0x8F: high nibble 8
        LOAD 2
        OUT             ; low nibble 15
end:    HLT
mul:    LDI 0
        STORE 2
        STORE 3
mloop:  LOAD 0
        MOV B,A
        LOAD 2
        ADD
        STORE 2
        JC  mcarry
mback:  LOAD 1
        DEC
        STORE 1
        JZ  mdone
        JMP mloop
mcarry: LOAD 3
        INC
        STORE 3
        JMP mback
mdone:  RET
