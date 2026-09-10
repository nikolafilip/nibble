; Greatest common divisor of two numbers from the switches, by repeated subtraction (Euclid).
; input: 12 9
; expect: 3
; expect-halt: end
        IN
        STORE 0         ; x
        IN
        STORE 1         ; y
loop:   LOAD 1
        MOV B,A         ; B = y
        LOAD 0
        SUB             ; x - y
        JZ  done        ; equal: that is the answer
        JC  xbig        ; x > y
        LOAD 0          ; x < y: y = y - x
        MOV B,A
        LOAD 1
        SUB
        STORE 1
        JMP loop
xbig:   STORE 0         ; x = x - y
        JMP loop
done:   LOAD 0
        OUT
end:    HLT
