from coder import LC3Coder
from tokenizer import LC3Tokenizer
from linker import LC3Linker

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process a simple file input.")
    parser.add_argument("filenames", nargs="+", help="The names of the files to process")
    parser.add_argument("--output", required=False, default="output.o", help="Where to save output")

    args = parser.parse_args()

    try:
        coders: list[LC3Coder] = []
        for filename in args.filenames:
            tokenizer: LC3Tokenizer = LC3Tokenizer(LC3Tokenizer.read_lc3_file(filename))
            coder: LC3Coder = LC3Coder(tokenizer)

            while True:
                try:
                    coder.encode_next_word()
                except EncodingWarning as ex:
                    raise Exception("Raw encoding error!") from ex
                except Exception as _:
                    break

            coder.link_labels()
            coders.append(coder)

        linker: LC3Linker = LC3Linker(coders, 0x0)
        linker.allocate_baddrs()
        linker.sort_coders()
        linker.register_labels()
        linker.resolve_labels()

        with open(args.output, "wb") as f:
            for word in linker.encode():
                f.write(int(word, 2).to_bytes(2, byteorder="little"))
    except Exception as ex:
        raise KeyboardInterrupt() from ex
