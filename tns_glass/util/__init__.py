
def to_base_36(number):
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')

    if number < 0:
        raise ValueError('number must be positive')

    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36

    return base36 or alphabet[0]

def to_base_33(number):
    """
    Base 33 is here so we can avoid I, L, and O which
    can be confusing when mixing with numbers
    """
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')

    if number < 0:
        raise ValueError('number must be positive')

    alphabet = '0123456789ABCDEFGHJKMNPQRSTUVWXYZ'

    base33 = ''
    while number:
        number, i = divmod(number, 33)
        base33 = alphabet[i] + base33

    return base33 or alphabet[0]