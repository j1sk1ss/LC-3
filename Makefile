CPL       ?= cplc
PY        ?= python3
LC3       ?= compiler/main.py

CPL_FLAGS ?= -O3 --linker gcc
SRC       ?= main.cpl src/*.cpl


all: build-vm compile-code

build-vm:
	$(CPL) $(SRC) $(CPL_FLAGS)

compile-code:
	$(PY) $(LC3) main.s lib.s

run: build-vm compile-code
	./a.out output.o
	$(MAKE) clean

clean:
	rm -f a.out output.o


.PHONY: all build-vm compile-code run clean