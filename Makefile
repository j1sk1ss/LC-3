CPL       ?= cplc
CPL_FLAGS ?= -O3
SRC       ?= main.cpl src/*.cpl

build:
	$(CPL) $(SRC) $(CPL_FLAGS)

run:
	make build && ./a.out && make clean

clean:
	rm a.out

.PHONY: all build run clean
