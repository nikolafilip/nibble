; NOP: the empty instruction steps the sequencer and changes nothing else; no other program executes it.
; expect: 7 10
; expect-halt: end
        LDI 7
        NOP
        NOP
        OUT             ; 7, untouched by the NOPs
        MOV B,A
        NOP
        LDI 3
        ADD             ; 3 + 7
        NOP
        OUT             ; 10
end:    HLT
