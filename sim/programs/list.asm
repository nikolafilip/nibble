; Largest of the numbers in data memory slots 0..3 (3, 9, 4, 7), walking the list with B as the pointer.
; Slot 4 holds the running maximum.
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
        STORE 4         ; max = list[0]
        LDI 3
        MOV B,A         ; B = 3, the last index
loop:   LOAD [B]        ; A = list[B]
        XCH             ; A = index, B = element
        STORE 5         ; save the index
        LOAD 4
        SUB             ; max - element: carry set means max >= element
        JC  keep
        XCH             ; A = element (B = old max, unused)
        STORE 4         ; new max
keep:   LOAD 5
        DEC             ; next index down; carry clear when it was 0
        MOV B,A
        JC  loop
        LOAD 4
        OUT
end:    HLT
