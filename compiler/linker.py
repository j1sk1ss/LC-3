from coder import LC3Coder
from tokenizer import LC3Opcodes
from smt import LC3Lb, LC3PaddBody, LC3Imm, LC3String

from dataclasses import dataclass

@dataclass
class LC3LbAddr:
    base: int
    offt: int

class LC3LinkerSymtable:
    def __init__(self) -> None:
        self.externs: dict[str, LC3LbAddr]   = {}
        self.used_names: dict[LC3Coder, set] = {}

    def add_used_name(self, coder: LC3Coder, name: str) -> None:
        if coder in self.used_names:
            self.used_names[coder].add(name)
        else:
            names: set = set()
            names.add(name)
            self.used_names[coder] = names

    def is_used_name(self, coder: LC3Coder, name: str) -> bool:
        return coder in self.used_names and name in self.used_names[coder]

    def get_or_create_label(self, name: str, baddr: int | None = None, addr: int | None = None) -> LC3LbAddr | None:
        if name in self.externs and not baddr and not addr:
            return self.externs[name]

        if baddr is None or addr is None:
            raise Exception(f"Address is None and {name} is not found!")

        lb_addr: LC3LbAddr = LC3LbAddr(baddr, addr)
        self.externs[name] = lb_addr
        return lb_addr

    def __repr__(self) -> str:
        return f"labels: {self.externs}"

class LC3Linker:
    def __init__(self, coders: list[LC3Coder], baddr: int | None):
        """ The Linker part is the last part of compilation.
            We take coders of each object file, traverse their words,
            register labels and update addresses.
            @coders - Object files.
            @baddr - Entry base address.
        """
        self.baddr: int | None      = baddr
        self.coders: list[LC3Coder] = coders
        self.smt: LC3LinkerSymtable = LC3LinkerSymtable()
        if not self.coders:
            raise Exception("There is no coders to link!")

        for coder in coders:
            if not coder.state.linked:
                raise Exception("There is object file with unlinked labels!")

    def allocate_baddrs(self) -> None:
        """ Allocate base addresses for every
            coder instance.
        """
        baddr: int | None = self.baddr
        if not baddr:
            for coder in self.coders:
                if coder.baddr != 0:
                    baddr = coder.baddr

        if not baddr:
            baddr = 0
        
        for coder in self.coders:
            if not coder.baddr:
                coder.baddr = baddr

                # Update base addresses of all used labels
                for word in coder.words:
                    for el in word.body:
                        if isinstance(el, LC3PaddBody) and isinstance(el.cont, LC3Lb):
                            el.cont.baddr = coder.baddr
                
            baddr += coder.size

    def sort_coders(self) -> None:
        """ Sort coders by ascending order of their
            base addresses
        """
        self.coders.sort(key=lambda x: x.baddr)

    def register_labels(self) -> None:
        for coder in self.coders:
            for word in coder.words:
                if word.op == LC3Opcodes.EXRN and isinstance(word.body[0], LC3PaddBody) and isinstance(word.body[0].cont, LC3Lb):
                    self.smt.add_used_name(coder, word.body[0].cont.name)

        for coder in self.coders:
            for word in coder.words:
                if word.op in (
                    LC3Opcodes.LB, LC3Opcodes.BLKW, 
                    LC3Opcodes.STRZ, LC3Opcodes.FILL
                ) and isinstance(word.body[0], LC3PaddBody) and isinstance(word.body[0].cont, LC3Lb):
                    self.smt.get_or_create_label(word.body[0].cont.name, word.body[0].cont.get_baddr(), word.body[0].cont.get_addr())

    def resolve_labels(self) -> None:
        """ Get label in a coder, and if it is from another source (its base address isn't
            equals to the base address of the coder) find it by name and set addresses and PC.
        """
        for coder in self.coders:
            local_pc: int = 0
            for word in coder.words:
                if (
                    word.op in (
                        LC3Opcodes.LB, LC3Opcodes.BLKW, LC3Opcodes.STRZ, LC3Opcodes.FILL, LC3Opcodes.EXRN
                    ) and isinstance(word.body[0], LC3PaddBody) and isinstance(word.body[0].cont, LC3Lb)
                ):
                    match word.op:
                        case LC3Opcodes.BLKW if isinstance(word.body[1], LC3Imm) and isinstance(word.body[2], LC3Imm):
                            local_pc += word.body[1].value
                        case LC3Opcodes.STRZ if isinstance(word.body[1], LC3String):
                            local_pc += len(word.body[1].blocks)
                        case LC3Opcodes.FILL:
                            local_pc += 1
                    continue

                local_pc += 1
                for el in word.body:
                    if isinstance(el, LC3PaddBody) and isinstance(el.cont, LC3Lb) and self.smt.is_used_name(coder, el.cont.name):
                        lb_addr: LC3LbAddr = self.smt.get_or_create_label(el.cont.name)
                        if el.cont.baddr is None or el.cont.addr is None or el.cont.pc is None:
                            el.cont = el.cont.get_related_off(coder.baddr + local_pc, lb_addr.base, lb_addr.offt)

    def encode(self) -> list[str]:
        result: list[str] = []
        for coder in self.coders:
            result.extend(coder.encode())

        return result
