import json
import importlib.metadata
import subprocess
import sys

from fastchunk import RecursiveCharacterTextSplitter as FastSplitter

def get_rust_chunks(text, chunk_size, chunk_overlap, keep_sep, strip_ws, separators):
    kwargs = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "strip_whitespace": strip_ws,
    }
    if separators is not None:
        kwargs["separators"] = separators

    if keep_sep == "true":
        kwargs["keep_separator"] = True
    elif keep_sep == "false":
        kwargs["keep_separator"] = False
    elif keep_sep == "start":
        kwargs["keep_separator"] = "start"
    elif keep_sep == "end":
        kwargs["keep_separator"] = "end"

    fs = FastSplitter(**kwargs)
    return fs.split_text(text)

try:
    import langchain_text_splitters as ts
    LANGCHAIN_INSTALLED = True
    version = importlib.metadata.version('langchain-text-splitters')
    print(f"LangChain Reference Version: {version}")
except Exception as e:
    LANGCHAIN_INSTALLED = False
    print(f"Error: {e}")
    sys.exit(1)

def run_test(name, text, chunk_size=4000, chunk_overlap=200, keep_separator=True, strip_whitespace=True, separators=None):
    keep_sep_map = {
        True: "true",
        False: "false",
        "start": "start",
        "end": "end"
    }

    # Langchain splits
    kwargs = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "keep_separator": keep_separator,
        "strip_whitespace": strip_whitespace,
    }
    if separators is not None:
        kwargs["separators"] = separators

    lc_splitter = ts.RecursiveCharacterTextSplitter(**kwargs)
    lc_chunks = lc_splitter.split_text(text)

    # Rust splits
    rs_chunks = get_rust_chunks(text, chunk_size, chunk_overlap, keep_sep_map[keep_separator], strip_whitespace, separators)

    if lc_chunks == rs_chunks:
        print(f"[PASS] {name}")
        return True
    else:
        print(f"[FAIL] {name}")
        print(f"LangChain: {lc_chunks}")
        print(f"Rust     : {rs_chunks}")
        return False

tests = [
    ("Empty String", ""),
    ("Whitespace-only", "     "),
    ("Text shorter than chunk_size", "Hello world", 50, 0),
    ("Text exactly equal to chunk_size", "abc", 3, 0),
    ("Text one character larger than chunk_size", "abcd", 3, 0),
    ("Multiple paragraphs", "P1\n\nP2\n\nP3", 10, 0),
    ("Multiple newlines", "\n\n\n\n", 2, 0),
    ("Repeated separators", "a b  c   d", 3, 0),
    ("Leading separators", "  hello", 3, 0),
    ("Trailing separators", "hello  ", 3, 0),
    ("Custom separator hierarchy", "a|b|c,d,e", 3, 0, True, True, ["|", ","]),
    ("Default separators", "a b c d e f", 3, 0, False, False),
    ("Empty-string fallback", "abcdefg", 3, 0),
    ("No empty separator", "aaaaabbbbb", 3, 0, True, True, ["\n"]),
    ("Long single word", "supercalifragilisticexpialidocious", 5, 0),
    ("chunk_overlap = 0", "a b c d e f", 3, 0),
    ("chunk_overlap > 0", "a b c d e f", 5, 2),
    ("overlap close to chunk_size", "a b c d e f", 5, 4),
    ("keep_separator = true", "a b c d e f", 3, 0, True, False),
    ("keep_separator = false", "a b c d e f", 3, 0, False, False),
    ("keep_separator = start", "a b c d e f", 3, 0, "start", False),
    ("keep_separator = end", "a b c d e f", 3, 0, "end", False),
    ("strip_whitespace = true", " a b c ", 3, 0, False, True),
    ("strip_whitespace = false", " a b c ", 3, 0, False, False),
    ("Unicode", "こんにちは世界", 3, 0),
    ("Emoji", "👨‍👩‍👧‍👦", 3, 0), # This might panic or behave differently!
    ("CJK text", "測試", 1, 0),
    ("Mixed ASCII and Unicode", "Hello 世界", 4, 0),
    ("Regression Test 98 (Empty Sep whitespace strip bypass)", "H3S\nWWAq9漢Hn  z\n0R jRA rfmmJdXTu2YLx34CVis xJOSCF UYOX80H 4 L2uvJKVpcN0rO", 1, 0, "end", True),
]

passed = 0
for test in tests:
    if len(test) == 2:
        if run_test(test[0], test[1]): passed += 1
    elif len(test) == 4:
        if run_test(test[0], test[1], chunk_size=test[2], chunk_overlap=test[3]): passed += 1
    elif len(test) == 6:
        if run_test(test[0], test[1], chunk_size=test[2], chunk_overlap=test[3], keep_separator=test[4], strip_whitespace=test[5]): passed += 1
    elif len(test) == 7:
        if run_test(test[0], test[1], chunk_size=test[2], chunk_overlap=test[3], keep_separator=test[4], strip_whitespace=test[5], separators=test[6]): passed += 1

print(f"\nDeterministic Tests: {passed}/{len(tests)} passed")

# Randomized testing
import random
import string

def generate_random_string(length):
    chars = string.ascii_letters + string.digits + " \n\n \t 漢字 😊 "
    return "".join(random.choice(chars) for _ in range(length))

def run_random_tests(num_tests=1000, seed=42):
    random.seed(seed)
    passed = 0
    failures = []
    for i in range(num_tests):
        text = generate_random_string(random.randint(0, 500))
        chunk_size = random.randint(1, 100)
        chunk_overlap = random.randint(0, chunk_size - 1) if chunk_size > 1 else 0
        keep_sep = random.choice([True, False, "start", "end"])
        strip_ws = random.choice([True, False])

        res = run_test(f"Random Test {i}", text, chunk_size, chunk_overlap, keep_sep, strip_ws)
        if res:
            passed += 1
        else:
            failures.append((i, text, chunk_size, chunk_overlap, keep_sep, strip_ws))

    print(f"\nRandomized Tests: {passed}/{num_tests} passed")
    if failures:
        print("\nFailures:")
        for f in failures[:5]: # Print first 5
            print(f"Seed {seed}, test {f[0]}")
            print(f"Config: chunk_size={f[2]}, chunk_overlap={f[3]}, keep_separator={f[4]}, strip_whitespace={f[5]}")
            print(f"Text: {repr(f[1])}")

run_random_tests(1000)
