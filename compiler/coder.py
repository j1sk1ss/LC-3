from __future__ import annotations

from tokenizer import LC3Tokenizer, LC3Registers, LC3Opcodes

class LC3Body:
    def __init__(self) -> None:
        pass

    def encode(self) -> str:
        pass

class LC3Imm(LC3Body):
    def __init__(self, value: int) -> None:
        self.value: int = value

    def encode(self) -> str:
        return f"{self.value:03b}"

class LC3Reg(LC3Body):
    def __init__(self, value: LC3Registers) -> None:
        self.value: LC3Registers = value

    def encode(self) -> str:
        return f"{self.value.value:03b}"

class LC3Padd(LC3Body):
    def __init__(self, value: int = 0, size: int = 1):
        self.value: int = value
        self.size: int = size

    def encode(self) -> str:
        return f"{self.value:0{self.size}b}"

class LC3Word:
    def __init__(self, op: LC3Opcodes, body: list[LC3Body]) -> None:
        self.op: LC3Opcodes     = op
        self.body: list[LC3Body] = body

    def encode(self) -> str:
        return "".join([f"{self.op.to_string()}", *[x.encode() for x in self.body]])

class LC3Coder:
    def __init__(self, tokenizer: LC3Tokenizer) -> None:
        self.tokenizer: LC3Tokenizer = tokenizer

    def get_next_word(self) -> str:
        word: LC3Word | None = None

        self.tokenizer.get_next_line()
        tokens: list[str] = self.tokenizer.get_tokens()

        op: LC3Opcodes = LC3Opcodes.from_string(tokens[0])
        match op:
            case LC3Opcodes.ADD, LC3Opcodes.AND:
                dr, sr1, data = LC3Registers.from_string(tokens[1]), LC3Registers.from_string(tokens[2]), LC3Registers.from_string(tokens[3])
                if data is LC3Registers.NOT_A_REGISTER:
                    word = LC3Word(op, [ LC3Reg(dr), LC3Reg(sr1), LC3Padd(size=1), LC3Imm(int(tokens[3])) ])
                else:
                    word = LC3Word(op, [ LC3Reg(dr), LC3Reg(sr1), LC3Padd(size=3), LC3Reg(data) ])

        return word.encode() if word else ""


