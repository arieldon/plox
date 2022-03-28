import sys

from plox import lox


def main() -> None:
    argc = len(sys.argv)
    if argc > 2:
        print(f"usage: {sys.argv[0]} [script]")
        sys.exit(1)
    elif argc == 2:
        lox.run_file(sys.argv[1])
    else:
        lox.run_prompt()


if __name__ == "__main__":
    main()
