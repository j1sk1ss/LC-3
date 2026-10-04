from __future__ import annotations

from tokenizer import LC3Registers, LC3Opcodes

__unique_id_counter: int = 0

def get_unique_id() -> int:
    """ Get a totaly unique ID for a compiler entry
    """
    global __unique_id_counter
    val: int = __unique_id_counter
    __unique_id_counter += 1
    return val

class LC3Body:
    def __init__(self) -> None:
        pass

    def encode(self) -> str:
        """ Return a sequence of 1 and 0 in string
            representation
        """
        pass

class LC3Lb(LC3Body):
    def __init__(self, addr: int | None = None):
        self.id: int          = get_unique_id()
        self.addr: int | None = addr

    def set_addr(self, addr: int) -> None:
        self.addr = addr

    def get_addr(self) -> int:
        return self.addr

    def get_related_off(self, pc: int) -> LC3Lb:
        """ Get related addr to the current program counter.
            @pc - Current program counter.
        """
        return LC3Lb(self.addr - pc) # By two given the size of single instruction (16bits)

    def encode(self) -> str:
        if not self.addr:
            raise Exception("Not allocated label was attempted to encode!")
        
        return f"{self.addr:012b}"

    def __repr__(self) -> str:
        return f"{self.id}<{self.addr}>"

class LC3Imm(LC3Body):
    def __init__(self, value: int, size: int = 5) -> None:
        self.value = value
        self.size = size

    def encode(self) -> str:
        value = self.value & ((1 << self.size) - 1)
        return f"{value:0{self.size}b}"

    def __repr__(self) -> str:
        return f"imm<{self.value}>"

class LC3String(LC3Body):
    def __init__(self, string: str, term: bool = True) -> None:
        self.string: str = string
        self.blocks: list[str] = [ f'{b:016b}' for b in self.string.encode() ]
        if term:
            self.blocks.append(f'{0b0:016b}')

    def encode(self) -> str:
        return ''.join(f'{b:08b}' for b in self.string.encode())

    def __repr__(self) -> str:
        return f"str<{self.string}>"

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
        return "".join(str(self.value) for _ in range(self.size))

class LC3PaddBody(LC3Body):
    def __init__(self, cont: LC3Body, value: int = 0, size: int = 1):
        self.value: int    = value
        self.size: int     = size
        self.cont: LC3Body = cont
    
    def encode(self) -> str:
        encoded = self.cont.encode()
        return encoded.zfill(self.size)[-self.size:]

class LC3Word:
    def __init__(self, op: LC3Opcodes, body: list[LC3Body]) -> None:
        self.op: LC3Opcodes     = op
        self.body: list[LC3Body] = body

    def relink(self, pc: int) -> None:
        for el in self.body:
            if isinstance(el, LC3PaddBody) and isinstance(el.cont, LC3Lb):
                el.cont = el.cont.get_related_off(pc)

    def encode(self) -> str:
        """ Return a sequence of 1 and 0 in string
            representation.

            Will encode first the opcode (4bits), then will
            encode the body.
        """
        return "".join([f"{self.op.to_string()}", *[x.encode() for x in self.body]])

    def __str__(self) -> str:
        return "".join([str(self.op), *[str(x) for x in self.body]])

class LC3Symtable:
    def __init__(self) -> None:
        self.labels: dict[str, LC3Lb] = {}

    def get_or_create_label(self, name: str, padd: KeyboardInterrupt) -> LC3PaddBody:
        if name in self.labels:
            return LC3PaddBody(self.labels[name], 0, padd)

        lb: LC3Lb = LC3Lb()
        self.labels[name] = lb
        return LC3PaddBody(lb, 0, padd)

    def __repr__(self) -> str:
        return f"labels: {self.labels}"
