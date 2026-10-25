arch spc700
output "emu.bin", create
origin $400
base $400
adc8:
clc
lda #$7f
adc #$01
stp
origin $440
base $440
adcc:
sec
lda #$ff
adc #$00
stp
origin $480
base $480
sbc8:
sec
lda #$10
sbc #$20
stp
origin $4c0
base $4c0
sbcbor:
clc
lda #$50
sbc #$10
stp
origin $500
base $500
cmpimm:
lda #$40
cmp #$41
stp
origin $540
base $540
movw:
ldw $10
stp
origin $580
base $580
addw:
ldw $10
adw $12
stp
origin $5c0
base $5c0
subw:
ldw $10
sbw $12
stp
origin $600
base $600
cmpw:
ldw $10
cpw $12
stp
origin $640
base $640
incw:
inw $10
stp
origin $680
base $680
mul:
lda #$12
ldy #$34
mul
stp
origin $6c0
base $6c0
div:
lda #$23
ldy #$01
ldx #$10
div
stp
origin $700
base $700
divovf:
lda #$00
ldy #$20
ldx #$10
div
stp
origin $740
base $740
daa:
clc
lda #$19
adc #$28
daa
stp
origin $780
base $780
das:
sec
lda #$42
sbc #$15
das
stp
origin $7c0
base $7c0
call:
jsr call_sub
bra call_end
call_sub:
lda #$42
rts
call_end:
nop
stp
origin $800
base $800
pcall:
jsp $80
stp
origin $840
base $840
tcall:
jst 0
stp
origin $880
base $880
brkreti:
sec
brk
lda #$01
stp
origin $8c0
base $8c0
dbnzy:
lda #$00
ldy #$05
dbnzy_l:
inc
bne --y=dbnzy_l
stp
origin $900
base $900
dbnzdp:
ldx #$00
dbnzdp_l:
inx
bne --$20=dbnzdp_l
stp
origin $940
base $940
cbne:
lda #$07
ldy #$00
bne $30=cbne_n
ldy #$01
cbne_n:
nop
stp
origin $980
base $980
bbs:
ldy #$00
bbs $30:5=bbs_t
ldy #$01
bbs_t:
nop
stp
origin $9c0
base $9c0
set1clr1:
set $31:7
clr $31:0
stp
origin $a00
base $a00
membit:
clc
orc $0123:6
stc $0124:0
not $0125:1
stp
origin $a40
base $a40
membitn:
sec
and !$0123:6
stp
origin $a80
base $a80
tsb:
lda #$0f
tsb $0200
stp
origin $ac0
base $ac0
trb:
lda #$0f
trb $0200
stp
origin $b00
base $b00
pushpop:
lda #$12
pha
lda #$00
pla
stp
origin $b40
base $b40
pushpsw:
sec
php
clc
plp
stp
origin $b80
base $b80
xcn:
lda #$3c
xcn
stp
origin $bc0
base $bc0
dppage1:
sep
lda $12
clp
ldx $12
stp
origin $c00
base $c00
staxinc:
ldx #$40
lda #$aa
sta (x++)
sta (x++)
stp
origin $c40
base $c40
ldaidx:
ldx #$02
lda ($10,x)
stp
origin $c80
base $c80
ldaidy:
ldy #$03
lda ($10),y
stp
origin $cc0
base $cc0
jmpidx:
ldx #$02
jmp ($0280,x)
lda #$01
stp
origin $d00
base $d00
strdp:
str $41=$40
stp
origin $d40
base $d40
adcxy:
clc
ldx #$50
ldy #$51
adc (x)=(y)
stp
origin $d80
base $d80
dpxwrap:
ldx #$10
lda $f8,x
stp
origin $dc0
base $dc0
incx:
ldx #$ff
inx
stp
origin $e00
base $e00
dexneg:
ldx #$00
dex
stp
origin $e40
base $e40
incy:
ldy #$7f
iny
stp
origin $e80
base $e80
deca:
lda #$01
dec
stp
origin $ec0
base $ec0
incdp:
inc $20
stp
origin $f00
base $f00
decabs:
dec $0234
stp
origin $f40
base $f40
incxloop:
ldx #$00
ldy #$00
inx
bne incxloop_t
ldy #$01
incxloop_t:
nop
stp
origin $f80
base $f80
jmpidx4:
ldx #$04
jmp ($0280,x)
lda #$01
stp
origin $fc0
base $fc0
jmpidx_t:
lda #$00
stp
