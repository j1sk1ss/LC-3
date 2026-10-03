from __future__ import annotations

from enum import Enum

class LC3Opcodes(Enum):
    # NOP  = 0b0000
    BR   = 0b0000
    BRZ  = 999998 # sets z
    BRP  = 999997 # sets p
    BRN  = 999996 # sets n
    ADD  = 0b0001
    AND  = 0b0101
    JMP  = 0b1100
    JSR  = 0b0100
    JSRR = 0b0100
    LD   = 0b0010
    LDI  = 0b1010
    LDR  = 0b0110
    LEA  = 0b1110
    NOT  = 0b1001
    RET  = 999995
    RTI  = 0b1000
    ST   = 0b0011
    STI  = 0b1011
    STR  = 0b0111
    TRAP = 0b1111
    LB   = 999999

    ORIG = 100000
    FILL = 100001
    BLKW = 100002
    STRZ = 100003
    END  = 100004

    def to_string(self) -> str:
        return f"{self.value:04b}"

    @staticmethod
    def from_string(opcode: str) -> LC3Opcodes:
        match opcode.upper():
            case ".ORIG":
                return LC3Opcodes.ORIG
            case ".FILL":
                return LC3Opcodes.FILL
            case ".BLKW":
                return LC3Opcodes.BLKW
            case ".STRZ":
                return LC3Opcodes.STRZ
            case ".END":
                return LC3Opcodes.END
            case "NOP":
                return LC3Opcodes.NOP
            case "BR":
                return LC3Opcodes.BR
            case "BRZ":
                return LC3Opcodes.BRZ
            case "BRN":
                return LC3Opcodes.BRN
            case "BRP":
                return LC3Opcodes.BRP
            case "ADD":
                return LC3Opcodes.ADD
            case "AND":
                return LC3Opcodes.AND
            case "JMP":
                return LC3Opcodes.JMP
            case "JSR":
                return LC3Opcodes.JSR
            case "JSRR":
                return LC3Opcodes.JSRR
            case "LD":
                return LC3Opcodes.LD
            case "LDI":
                return LC3Opcodes.LDI
            case "LDR":
                return LC3Opcodes.LDR
            case "LEA":
                return LC3Opcodes.LEA
            case "NOT":
                return LC3Opcodes.NOT
            case "RET":
                return LC3Opcodes.RET
            case "RTI":
                return LC3Opcodes.RTI
            case "ST":
                return LC3Opcodes.ST
            case "STI":
                return LC3Opcodes.STI
            case "STR":
                return LC3Opcodes.STR
            case "TRAP":
                return LC3Opcodes.TRAP
            case _:
                return LC3Opcodes.LB

class LC3Registers(Enum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7
    NOT_A_REGISTER = 999

    @staticmethod
    def from_string(register: str) -> LC3Registers:
        match register.upper():
            case "R0":
                return LC3Registers.R0
            case "R1":
                return LC3Registers.R1
            case "R2":
                return LC3Registers.R2
            case "R3":
                return LC3Registers.R3
            case "R4":
                return LC3Registers.R4
            case "R5":
                return LC3Registers.R5
            case "R6":
                return LC3Registers.R6
            case "R7":
                return LC3Registers.R7
            case _:
                return LC3Registers.NOT_A_REGISTER

class LC3Tokenizer:
    """ Tokenizer for LC3 assembly language
    """
    def __init__(self, code: list[str]) -> None:
        self.counter: int    = 0
        self.code: list[str] = code
        if not self.code:
            raise Exception("Code is NULL!")

    def get_next_line(self) -> None:
        """ Get the current counter, get a line from the code by this
            counter, than increment the counter.

            P.S.: Will throw an exception when encounter situation
                  where counter larger than code size
        """
        if self.counter >= len(self.code):
            raise Exception("EOF")
        
        self.counter += 1

    def get_tokens(self) -> list[str]:
        """ Split the input line by comma and space character.
            This is essential considering a possible input: add r0,r1,r2 where
            opcode is separated from the 'body' via space, and the body
            consists from parts that are separated by comma.
        """
        import re
        line = self.code[self.counter].strip()
        return re.findall(r'"(?:\\.|[^"\\])*"|[^,\s]+', line)

    @staticmethod
    def read_lc3_file(path: str) -> list[str]:
        """ Read a file by @path variable and
            strip comments from him.
        """
        data: list[str] = []
        with open(path, 'r') as f:
            for line in f:
                if line.startswith(';'):
                    continue

                line = line.split(" ;")[0]
                if line.strip() != "":
                    data.append(line)

        return data
