from pudb.lowlevel import detect_encoding, decode_lines


def test_detect_encoding_nocookie():
    lines = ["Test Проверка"]
    lines = [line.encode("utf-8") for line in lines]
    encoding, _ = detect_encoding(iter(lines))
    assert encoding == "utf-8"


def test_detect_encoding_cookie():
    lines = [
        "# coding=utf-8",
        "Test",
        "Проверка"
    ]
    lines = [line.encode("utf-8") for line in lines]
    encoding, _ = detect_encoding(iter(lines))
    assert encoding == "utf-8"


def test_decode_lines():
    unicode_lines = [
        "# coding=utf-8",
        "Test",
        "Проверка",
    ]
    lines = [line.encode("utf-8") for line in unicode_lines]
    assert unicode_lines == list(decode_lines(iter(lines)))


# {{{ remove common indentation

def _remove_common_indentation(code, require_leading_newline=True):
    if "\n" not in code:
        return code

    if require_leading_newline and not code.startswith("\n"):
        return code

    lines = code.split("\n")
    while lines[0].strip() == "":
        lines.pop(0)
    while lines[-1].strip() == "":
        lines.pop(-1)

    if lines:
        base_indent = 0
        while lines[0][base_indent] in " \t":
            base_indent += 1

        for line in lines[1:]:
            if line[:base_indent].strip():
                raise ValueError("inconsistent indentation")

    return "\n".join(line[base_indent:] for line in lines)

# }}}


def test_executable_lines():
    def get_exec_lines(src):
        code = compile(
                    _remove_common_indentation(test_code),
                    "<tmp>", "exec")
        from pudb.lowlevel import get_executable_lines_for_codes_recursive
        return get_executable_lines_for_codes_recursive([code])

    test_code = """
        def main():
            import pudb; pu.db
            conf = ''. \\
                replace('', '')

            conf_tpl = ''  # <-- imposible to set breakpoint here

        main()
        """

    assert get_exec_lines(test_code) == {1, 2, 3, 4, 6, 8}

    test_code = "a = 3*5\n" + 333 * "\n" + "b = 15"
    assert get_exec_lines(test_code) == {
        1,
        128,  # bogus,
        255,  # bogus,
        335
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main
        main([__file__])
