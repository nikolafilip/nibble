; Sort four numbers from the panel switches into data memory slots 0..3, smallest first, then show them.
; Bubble sort with B as the pointer: compare slot B with slot B+1, swap if out of order, repeat four passes.
; Slots: 0..3 = the list, 4 = pass counter, 5 = index, 6 = list[i], 7 = list[i+1].
; input: 9 2 14 5
; expect: 2 5 9 14
; expect-halt: end
        LDI 0
        MOV B,A
        IN
        STORE [B]       ; slot 0
        LDI 1
        MOV B,A
        IN
        STORE [B]       ; slot 1
        LDI 2
        MOV B,A
        IN
        STORE [B]       ; slot 2
        LDI 3
        MOV B,A
        IN
        STORE [B]       ; slot 3
        LDI 3
        STORE 4         ; three passes
pass:   LDI 0
        STORE 5         ; i = 0
step:   LOAD 5
        MOV B,A
        LOAD [B]
        STORE 6         ; list[i]
        LOAD 5
        INC
        MOV B,A
        LOAD [B]
        STORE 7         ; list[i+1]
        MOV B,A         ; B = list[i+1]
        LOAD 6
        SUB             ; list[i] - list[i+1]: carry set means list[i] >= list[i+1]
        JZ  next        ; equal: nothing to do
        JC  swap
next:   LOAD 5
        INC
        STORE 5
        MOV B,A         ; B = i + 1
        LDI 3
        SUB             ; 3 - (i+1): zero when i+1 = 3, i.e. the pass is over
        JZ  endpass
        JMP step
swap:   LOAD 5
        MOV B,A
        LOAD 7
        STORE [B]       ; list[i] = old list[i+1]
        LOAD 5
        INC
        MOV B,A
        LOAD 6
        STORE [B]       ; list[i+1] = old list[i]
        JMP next
endpass: LOAD 4
        DEC
        STORE 4
        JZ  show
        JMP pass
show:   LOAD 0
        OUT
        LOAD 1
        OUT
        LOAD 2
        OUT
        LOAD 3
        OUT
end:    HLT
