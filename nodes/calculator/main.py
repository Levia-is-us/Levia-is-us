def calculate(expression: str) -> float:
    """
    Evaluates a mathematical expression string and returns the calculated result.

    Args:
        expression (str): A string containing a valid mathematical expression
                         e.g. "2 + 3 * 4", "10 / 2", etc.

    Returns:
        float: The calculated result of evaluating the expression

    Warning:
        This function uses eval() which can be unsafe if the input is not properly sanitized.
        Only use with trusted input expressions.
    """
    return eval(
        expression
    ) 
