from fractions import Fraction

# Reference thread sizes
REF_TO_MD = {
    '#0': .060,
    '#1': .073,
    '#2': .086,
    '#3': .099,
    '#4': .112,
    '#5': .125,
    '#6': .138,
    '#8': .164,
    '#10': .190,
    '#12': .216,
}


def parse_diameter(input_str):
    """Parse diameter input: '#10', '.3125', '1-5/16', etc."""
    input_str = input_str.strip()

    if input_str[0] == '#':
        if input_str in REF_TO_MD:
            return REF_TO_MD[input_str]
        raise ValueError('Invalid numbered thread size')

    parts = input_str.split('-')
    if len(parts) == 2:
        return float(parts[0]) + float(Fraction(parts[1]))
    if len(parts) == 1:
        return float(Fraction(input_str))
    raise ValueError('Could not parse diameter')


def external(md_b, p, allowance, pd_bsc, pd_tol):
    maj_max = round(md_b - allowance, 6)
    maj_min = round(md_b - allowance - (.060 * (p ** 2) ** (1 / 3)), 6)

    pd_max = round(pd_bsc - allowance, 6)
    pd_min = round(pd_max - pd_tol, 6)

    mnr_max = md_b - (2 * .54126588 * p) - allowance
    mnr_min = md_b - (2 * .54126588 * p) - (2 * .10825318 * p)

    return maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min


def internal(md_b, p, pd_tol, pd_bsc):
    maj_min = md_b
    maj_max = round(md_b + (.14433757 * p) + round((1.3 * pd_tol), 6), 6)

    pd_min = pd_bsc
    pd_max = round(pd_min + round((1.3 * pd_tol), 6), 6)

    if md_b < .25:
        mnr_tol = round((.0500 * (p ** 2) ** (1.0 / 3.0)) + .03 * (p / md_b), 6) - .002
        if mnr_tol > (.394 * p):
            mnr_tol = (.394 * p)
        elif mnr_tol < (.25 * p):
            mnr_tol = (.25 * p)
    else:
        mnr_tol = round((0.25 * p) - (0.4 * p ** 2), 6)

    mnr_min = round(md_b - (2 * .54126588 * p), 6)
    mnr_max = round(mnr_min + mnr_tol, 6)

    return maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min


def plt_adj(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min, t_max, t_min, thread_type):
    if thread_type == 'E':
        maj_max = maj_max - 2 * t_max
        maj_min = maj_min - 2 * t_min
        pd_max = pd_max - (4 * t_max)
        pd_min = pd_min - (4 * t_min)
        mnr_max = mnr_max - 2 * t_max
        mnr_min = mnr_min - 2 * t_min
    else:
        maj_max = maj_max + 2 * t_min
        maj_min = maj_min + 2 * t_max
        pd_max = pd_max + (4 * t_min)
        pd_min = pd_min + (4 * t_max)
        mnr_max = mnr_max + 2 * t_min
        mnr_min = mnr_min + 2 * t_max

    return maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min


def calculate_thread_dimensions(data):
    md_basic_input = data['majorDiameter'].strip()
    md_b = parse_diameter(md_basic_input)

    tpi = float(data['tpi'])
    if tpi <= 0:
        raise ValueError('TPI must be positive')
    p = round(1 / tpi, 6)

    series = data['series'].upper()
    if series not in ['UN', 'UNC', 'UNF', 'UNS', 'UNEF']:
        raise ValueError('Invalid thread series')

    t_min = float(data['minPlating'])
    t_max = float(data['maxPlating'])
    if t_min < 0 or t_max < 0:
        raise ValueError('Plating thickness must be non-negative')
    if t_max < t_min:
        raise ValueError('Max plating must be >= Min plating')

    thread_type = data['threadType'].upper()
    if thread_type not in ['E', 'I']:
        raise ValueError('Invalid thread type')

    lower = ['4', '6', '8']
    upper = ['12', '16', '20', '28', '32']

    if (series == 'UNC') or (series == 'UNF'):
        le = md_b
    elif (series == 'UN') and (str(tpi) in lower):
        le = md_b
    elif (series == 'UN') and (str(tpi) in upper):
        le = 9 * p
    elif (series == 'UNEF') or (series == 'UNS'):
        le = 9 * p
    else:
        le = 9 * p

    pd_tol = round((.0015 * ((md_b) ** (1.0 / 3.0))) + (.0015 * ((le) ** (1.0 / 2.0))) + (.015 * ((p ** 2) ** (1.0 / 3.0))), 6)
    allowance = round(0.3 * pd_tol, 4)
    pd_bsc = round((md_b - .32475953 * p * 2), 4)

    if thread_type == 'I':
        maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min = internal(md_b, p, pd_tol, pd_bsc)
        if md_b > .125:
            mnr_max = round(mnr_max, 3)
            mnr_min = round(mnr_min, 3)
    else:
        maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min = external(md_b, p, allowance, pd_bsc, pd_tol)

    p_maj_max, p_maj_min, p_pd_max, p_pd_min, p_mnr_max, p_mnr_min = plt_adj(
        maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min, t_max, t_min, thread_type
    )

    return {
        'success': True,
        'asme': {
            'majorMax': round(maj_max, 4),
            'majorMin': round(maj_min, 4),
            'pitchMax': round(pd_max, 4),
            'pitchMin': round(pd_min, 4),
            'minorMax': round(mnr_max, 4),
            'minorMin': round(mnr_min, 4),
        },
        'prePlate': {
            'majorMax': round(p_maj_max, 4),
            'majorMin': round(p_maj_min, 4),
            'pitchMax': round(p_pd_max, 4),
            'pitchMin': round(p_pd_min, 4),
            'minorMax': round(p_mnr_max, 4),
            'minorMin': round(p_mnr_min, 4),
        },
    }
