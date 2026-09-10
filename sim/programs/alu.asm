; Every flag pattern: ADD with carry, SUB with and without borrow, zero result, JC/JZ taken and not taken.
; expect: 1 10 15 0 10
; expect-halt: end
        LDI 9
        MOV B,A         ; B = 9
        LDI 8
        ADD             ; 8 + 9 = 17 -> A = 1, C = 1, Z = 0
        OUT             ; 1
        JC  c1
        HLT             ; wrong: carry not set
c1:     LDI 3
        SUB             ; 3 - 9 = -6 -> A = 10, C = 0 (borrow)
        OUT             ; 10
        JC  bad
        XCH             ; A = 9, B = 10
        SUB             ; 9 - 10 -> A = 15, C = 0
        OUT             ; 15
        LDI 10
        SUB             ; 10 - 10 = 0 -> C = 1 (no borrow), Z = 1
        OUT             ; 0
        JZ  z1
bad:    HLT             ; wrong
z1:     JC  c2
        HLT             ; wrong: C should be set after 10 - 10
c2:     ADD             ; 0 + 10 -> A = 10, C = 0, Z = 0
        OUT             ; 10
        JZ  bad
        JC  bad
end:    HLT
