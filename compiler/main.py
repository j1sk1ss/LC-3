from coder import LC3Coder
from tokenizer import LC3Tokenizer

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process a simple file input.")
    parser.add_argument("filename", help="The name of the file to process")

    args = parser.parse_args()

    try:
        tokenizer: LC3Tokenizer = LC3Tokenizer(LC3Tokenizer.read_lc3_file(args.filename))
        coder: LC3Coder = LC3Coder(tokenizer)
        print(coder.get_next_word())
    except Exception as ex:
        raise KeyboardInterrupt() from ex
