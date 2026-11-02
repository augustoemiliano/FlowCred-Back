"""Validação de CPF e CNPJ (dígitos verificadores)."""


def digits_only(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def _all_same(digits: str) -> bool:
    return len(set(digits)) == 1


def is_valid_cpf(cpf: str) -> bool:
    if len(cpf) != 11 or not cpf.isdigit() or _all_same(cpf):
        return False
    for size in (9, 10):
        total = sum(int(cpf[i]) * (size + 1 - i) for i in range(size))
        check = (total * 10) % 11 % 10
        if check != int(cpf[size]):
            return False
    return True


def is_valid_cnpj(cnpj: str) -> bool:
    if len(cnpj) != 14 or not cnpj.isdigit() or _all_same(cnpj):
        return False
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_2 = [6, *weights_1]
    for weights in (weights_1, weights_2):
        size = len(weights)
        total = sum(int(cnpj[i]) * weights[i] for i in range(size))
        rest = total % 11
        check = 0 if rest < 2 else 11 - rest
        if check != int(cnpj[size]):
            return False
    return True
