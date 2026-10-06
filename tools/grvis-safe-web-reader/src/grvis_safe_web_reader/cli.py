"""CLI with legacy single-URL invocation support."""
import sys
from .core import main as reader_main

def main():
    if len(sys.argv)>1 and not any(x in {'fetch','batch','capabilities'} for x in sys.argv[1:]):
        sys.argv.insert(1,'fetch')
    return reader_main()

if __name__=='__main__':
    raise SystemExit(main())
