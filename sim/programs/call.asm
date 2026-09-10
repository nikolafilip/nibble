; Nested CALL: the return register holds one address, so a subroutine that calls another returns to the wrong place.
; This program shows the documented failure, so the machine gate proves the hardware fails exactly as the ISA says:
; sub1 calls sub2; sub2 returns into sub1 correctly; sub1's own RET then goes back to the word after "CALL sub2"
; (RA was overwritten by the inner call) instead of to main. Slot 0 counts arrivals at that word; the second arrival
; shows 14 and halts. A machine with a return stack would show 15 instead.
; needs: datamem
; expect: 1 2 14
; expect-halt: wrong
        LDI 0
        STORE 0
        CALL sub1
        LDI 15          ; only a machine with a stack gets here
        OUT
right:  HLT
sub1:   CALL sub2
        LOAD 0          ; arrivals here: 1 the first time, 2 after the misrouted RET
        INC
        STORE 0
        OUT
        MOV B,A
        LDI 2
        SUB             ; zero on the second arrival
        JZ  twice
        RET             ; RA points at the LOAD above, not at main
twice:  LDI 14
        OUT
wrong:  HLT
sub2:   RET
