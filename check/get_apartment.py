import re

def apartment_validity(apartment_num):
    # Регулярное выражение для проверки формата
    pattern = r'^[1-9][0-9]?[a-zA-Z]$'
    if re.match(pattern, apartment_num):
        return True
    else:
        return False