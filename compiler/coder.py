from __future__ import annotations

from dataclasses import dataclass

from tokenizer import LC3Tokenizer, LC3Registers, LC3Opcodes
from smt import (
    LC3Word, LC3Reg, LC3Padd, 
    LC3Imm, LC3Symtable, LC3PaddBody, 
    LC3Lb, LC3String
)

@dataclass
class LC3CoderState:
    raw_encoded: bool
    linked: bool

class LC3Coder:
    def __init__(self, tokenizer: LC3Tokenizer, baddr: int = 0x00) -> None:
        self.tokenizer: LC3Tokenizer = tokenizer
        self.smt: LC3Symtable        = LC3Symtable()
        self.words: list[LC3Word]    = []
        self.baddr: int              = baddr
        self.size: int               = 0
        self.state: LC3CoderState    = LC3CoderState(False, False)

    def encode_next_word(self) -> None:
        """ Get a line from a tokenizer, tokenize it, and
            convert it to a LC3Word raw object.

            P.S.: Will throw an exception when encounter EOF
                  from the tokenizer
        """
        if self.state.raw_encoded:
            raise Exception("Already encoded!") from ex

        word: LC3Word | None = None

        try:
            tokens: list[str] = self.tokenizer.get_tokens()
            op: LC3Opcodes = LC3Opcodes.from_string(tokens[0])
            self.tokenizer.get_next_line()
        except Exception as ex:
            self.state.raw_encoded = True
            raise Exception("EOF") from ex

        try:
            match op:
                case LC3Opcodes.EXRN:
                    word = LC3Word(op, [ self.smt.get_or_create_label(tokens[1], 16) ])
                case LC3Opcodes.ORIG:
                    self.baddr = int(tokens[1], 0)
                    return
                case LC3Opcodes.ADD | LC3Opcodes.AND:
                    dr, sr1, data = LC3Registers.from_string(tokens[1]), LC3Registers.from_string(tokens[2]), LC3Registers.from_string(tokens[3])
                    if data is LC3Registers.NOT_A_REGISTER:
                        word = LC3Word(op, [ LC3Reg(dr), LC3Reg(sr1), LC3Padd(size=1, value=1), LC3Imm(int(tokens[3])) ])
                    else:
                        word = LC3Word(op, [ LC3Reg(dr), LC3Reg(sr1), LC3Padd(size=3), LC3Reg(data) ])
                case LC3Opcodes.BR | LC3Opcodes.BRP | LC3Opcodes.BRN | LC3Opcodes.BRZ:
                    word = LC3Word(
                        LC3Opcodes.BR,
                        [ 
                            LC3Padd(size=1, value=1 if op in (LC3Opcodes.BRN, LC3Opcodes.BR) else 0), 
                            LC3Padd(size=1, value=1 if op in (LC3Opcodes.BRZ, LC3Opcodes.BR) else 0),
                            LC3Padd(size=1, value=1 if op in (LC3Opcodes.BRP, LC3Opcodes.BR) else 0),
                            self.smt.get_or_create_label(tokens[1], 9)
                        ]
                    )
                case LC3Opcodes.JMP:
                    word = LC3Word(op, [ LC3Padd(size=3), LC3Reg(LC3Registers.from_string(tokens[1])), LC3Padd(size=6) ])
                case LC3Opcodes.JSR:
                    word = LC3Word(op, [ LC3Padd(size=1, value=1), self.smt.get_or_create_label(tokens[1], 11) ])
                case LC3Opcodes.JSRR:
                    word = LC3Word(op, [ LC3Padd(size=3), LC3Reg(LC3Registers.from_string(tokens[1])), LC3Padd(size=6) ])
                case LC3Opcodes.LD | LC3Opcodes.LDI | LC3Opcodes.ST | LC3Opcodes.STI | LC3Opcodes.LEA:
                    word = LC3Word(op, [ LC3Reg(LC3Registers.from_string(tokens[1])), self.smt.get_or_create_label(tokens[2], 9) ])
                case LC3Opcodes.LDR | LC3Opcodes.STR:
                    word = LC3Word(
                        op, [ 
                            LC3Reg(LC3Registers.from_string(tokens[1])), 
                            LC3Reg(LC3Registers.from_string(tokens[2])), 
                            LC3Imm(int(tokens[3]), 6)
                        ]
                    )
                case LC3Opcodes.NOT:
                    word = LC3Word(op, [ LC3Reg(LC3Registers.from_string(tokens[1])), LC3Reg(LC3Registers.from_string(tokens[2])), LC3Padd(1, 6) ])
                case LC3Opcodes.RET:
                    word = LC3Word(LC3Opcodes.JMP, [ LC3Padd(0, 3), LC3Padd(1, 3), LC3Padd(0, 6) ])
                case LC3Opcodes.RTI:
                    word = LC3Word(op, [LC3Padd(0, 12) ])
                case LC3Opcodes.TRAP:
                    word = LC3Word(op, [ LC3Padd(0, 4), LC3Imm(value=int(tokens[1], 0), size=8) ])
                case _:
                    if tokens[0].split()[-1][-1] == ':':
                        word = LC3Word(LC3Opcodes.LB, [ self.smt.get_or_create_label(tokens[0][:-1], 16) ])
                    else:
                        if LC3Opcodes.from_string(tokens[0]) == LC3Opcodes.END:
                            return
                        
                        match LC3Opcodes.from_string(tokens[1]):
                            case LC3Opcodes.FILL:
                                word = LC3Word(LC3Opcodes.FILL, [ self.smt.get_or_create_label(tokens[0], 16), LC3Imm(int(tokens[2], 0), 16) ])
                            case LC3Opcodes.BLKW:
                                defset: LC3Imm = LC3Imm(0, 16)
                                if len(tokens) >= 4:
                                    defset = LC3Imm(int(tokens[3], 0), 16)

                                word = LC3Word(LC3Opcodes.BLKW, [ self.smt.get_or_create_label(tokens[0], 16), LC3Imm(int(tokens[2], 0)), defset ])
                            case LC3Opcodes.STRZ:
                                word = LC3Word(LC3Opcodes.STRZ, [ self.smt.get_or_create_label(tokens[0], 16), LC3String(tokens[2]) ])
        except Exception as ex:
            raise EncodingWarning("Label encode error!") from ex

        if not word:
            raise EncodingWarning(f"Operation {op.name} can't be handled!")

        self.words.append(word)

    def link_labels(self) -> None:
        """ !! Invoke this function after encoding !!
            Will link labels and allocate addresses for them.

            P.S.: Can't be invoked twice! Will throw an exception!
        """
        if not self.state.raw_encoded:
            raise Exception("There is now raw encoding yet!")

        if self.state.linked:
            raise Exception("Already linked!")

        self.smt.set_baddr(self.baddr)

        for word in self.words:
            if (
                word.op in (LC3Opcodes.LB, LC3Opcodes.FILL, LC3Opcodes.BLKW, LC3Opcodes.STRZ) and 
                isinstance(word.body[0], LC3PaddBody) and 
                isinstance(word.body[0].cont, LC3Lb)
            ):
                word.body[0].cont.set_addr(self.size)

            match word.op:
                case LC3Opcodes.LB | LC3Opcodes.EXRN:
                    continue
                case LC3Opcodes.BLKW if isinstance(word.body[1], LC3Imm):
                    self.size += word.body[1].value
                case LC3Opcodes.STRZ if isinstance(word.body[1], LC3String):
                    self.size += len(word.body[1].string) + 1
                case _:
                    self.size += 1 # 16 bits for a word -> LC-3 base counter

        self.state.linked = True

    def encode(self) -> list[str]:
        """ Get the final encoded sequence of
            instructions
        """
        if not self.state.linked:
            raise Exception("There is now link for the raw encoding!")

        pc: int = 0
        body: list[str] = []

        for word in self.words:
            if word.op in (LC3Opcodes.LB, LC3Opcodes.EXRN):
                continue

            try:
                match word.op:
                    case LC3Opcodes.FILL:
                        body.append(word.body[1].encode())
                        pc += 1
                    case LC3Opcodes.BLKW if isinstance(word.body[1], LC3Imm) and isinstance(word.body[2], LC3Imm):
                        for _ in range(word.body[1].value):
                            body.append(word.body[2].encode())
                            pc += 1
                    case LC3Opcodes.STRZ if isinstance(word.body[1], LC3String):
                        for block in word.body[1].blocks:
                            body.append(block)
                            pc += 1
                    case _:
                        pc += 1
                        word.relink(self.baddr + pc)
                        body.append(word.encode())
            except Exception as ex:
                raise EncodingWarning(f"Can't encode {word}!") from ex

        return body