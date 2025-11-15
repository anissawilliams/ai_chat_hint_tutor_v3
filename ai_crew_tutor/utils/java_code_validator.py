# Java validator helpers
import re

def _normalize_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def signature_check(student_code: str, method_name: str = None,
                    return_type: str = None, param_types: list = None) -> bool:
    """
    Regex-based method signature check.
    - method_name: optional exact method name to look for
    - return_type: optional expected return type substring (e.g., 'List<Integer>')
    - param_types: optional list of expected parameter type substrings (order-insensitive)
    """
    code = _normalize_whitespace(student_code)
    # rough capture of a Java method signature header (modifiers optional)
    sig_re = r'(public|protected|private|static|\s)*\s*([\w\<\>\[\]\s,]+)\s+(\w+)\s*\(([^)]*)\)'
    m = re.search(sig_re, code)
    if not m:
        return False

    found_return = _normalize_whitespace(m.group(2))
    found_name = m.group(3)
    found_params = m.group(4).strip()
    # check name
    if method_name and found_name != method_name:
        return False
    # check return type substring
    if return_type and return_type not in found_return:
        return False
    # check param types presence
    if param_types:
        # split params and look for each type token
        param_tokens = [p.strip() for p in found_params.split(',') if p.strip()]
        types_found = []
        for p in param_tokens:
            # take the first token as type (handles final/annotations poorly but works for simple cases)
            t = p.split()[:-1]  # all but last are type tokens; last is name
            if not t:
                continue
            types_found.append(' '.join(t))
        # make them comparable by ignoring var names, check each expected type occurs in at least one
        for expected in param_types:
            if not any(expected in tf for tf in types_found):
                return False
    return True


def content_check(student_code: str, required_tokens: list = None, forbidden_tokens: list = None) -> bool:
    """
    Check for presence or absence of simple code tokens/phrases.
    required_tokens: all must appear (case-insensitive)
    forbidden_tokens: none must appear
    """
    code_lower = student_code.lower()
    if required_tokens:
        for tok in required_tokens:
            if tok.lower() not in code_lower:
                return False
    if forbidden_tokens:
        for tok in forbidden_tokens:
            if tok.lower() in code_lower:
                return False
    return True


def ast_check_using_javalang(student_code: str, expected_method_name: str = None) -> bool:
    """
    Optional stronger check using javalang parser. Returns False if javalang not installed.
    pip install javalang
    """
    try:
        import javalang
    except Exception:
        return False

    try:
        tree = javalang.parse.parse(student_code)
    except Exception:
        return False

    # walk type_declarations -> methods; check for method name
    for path, node in tree:
        # node may be MethodDeclaration
        if getattr(node, 'name', None) == expected_method_name:
            return True
    return False


def java_validator_factory(method_name: str = None, return_type: str = None,
                           param_types: list = None, required_tokens: list = None,
                           forbidden_tokens: list = None, use_ast_check: bool = False):
    """
    Returns a callable validator(student_answer: str) -> bool.
    Configure the expected signature and content tokens per exercise.
    """
    def validator(student_answer: str) -> bool:
        code = student_answer or ""
        # quick signature + content checks
        if method_name or return_type or param_types:
            if not signature_check(code, method_name=method_name,
                                   return_type=return_type, param_types=param_types):
                return False

        if required_tokens or forbidden_tokens:
            if not content_check(code, required_tokens, forbidden_tokens):
                return False

        if use_ast_check and method_name:
            # try AST-level check; if javalang unavailable, skip AST and rely on regex checks
            ast_ok = ast_check_using_javalang(code, expected_method_name=method_name)
            if not ast_ok:
                return False

        return True

    return validator
