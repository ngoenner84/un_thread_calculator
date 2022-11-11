from fractions import Fraction
import os
os.system('mode con: cols=135 lines=40')

# This program calculates UN threads per ASME B1.1 formulaicly and adjusts machining dimensions 
# for plating thickness as needed.

# This file can be exported to a windows executable by running "python -m auto_py_to_exe" in the terminal.

def main():
    print(f"UN Thread Plating Adjuster - Version 1.00\nReport any bugs or errors to Nick Goenner\nCompiled: 11/11/2022\n")
    print(f"*** IMPORTANT NOTES ***:")
    print("\nThis program formulaicly calculates UN thread dimensions per ASME B1.1 and calculates adjustment to machine dimensions to accomodate plating thickness.\n")
    print(f"1. Pre-plate thread adjustments from this program conform to ASME B1.1 - 2003 recommendations.")
    print(f"2. This calculator is only valid for Class 2 threads with a 60° flank angle.")
    print(f"\n**********************************************************************************************\nPrior to creating or updating any drawing requiring pre-plate dimensions, check the gauge list in Thrive to \nverify that no gauge or suitable alternative exists. If a gauge exists, its dimensions should be adopted on\nthe drawing whenever possible to avoid uneccessary duplication.\n**********************************************************************************************\n")

    # Collect thread size from user, verify postive fractional or numerical value.
    while True:
        md_b_frac = input("Enter basic major Ø of thread (i.e. enter '.3125' or '5/16' for 5/16-18 UNC thread): ")
        if md_b_frac == '':
            print("Entry must not be blank.")
        else:
            try:
                if float(Fraction(md_b_frac)) > 0: 
                    md_b = float(Fraction(md_b_frac))           
                    break
                else:
                    print("Negative values are not allowed.")
            except:
                print("Please read the instructions and double-check your entry.")

    # Collect TPI from user, verify positive numerical value.
    while True:
        tpi = (input("Enter threads per inch (i.e. enter '13' for a 1/2-13 UNC thread): "))
        if tpi == '':
            print("Entry must not be blank.")
        else:
            try:
                if float(tpi) > 0:
                    p = round(1 / float(tpi), 6)          
                    break
                else:
                    print("Negative values are not allowed.")
            except:
                print("Please read the instructions and double-check your entry.")
    
    # Collect thread series from user, verify that it is one of the accepted types.
    while True:
        series = input("Enter thread series (ONLY: 'UN' 'UNC' 'UNF' 'UNS' 'UNEF': ").upper()
        if series in ['UN', 'UNC', 'UNF', 'UNS', 'UNEF']:
            break
        else:
            print("Please select a valid thread series.")

    # Collect min plating thickness from user, verify it is a positive numerical value.
    while True:
        try:
            t_min = float(input("Enter MIN plating thickness in inches (i.e. '.0002'): "))
            if t_min >= 0:
                break
            else:
                print("Please enter a positive number.")
        except:
            print("Please read the instruction and try again. ")

    # Collect max plating thickness from user, verify it is positive numerical value in excess of minimum value.
    while True:
        try:
            t_max = float(input("Enter MAX plating thickness in inches (i.e. '.0004'): "))
            if t_max >= t_min:
                break
            else:
                print("Please enter a plating thickness greater than 'MIN.'")
        except:
            print("Please read the instruction and try again. ")

    # Collect thread gender from user, verify that it is one of the two accepted types.
    while True:
        type = input("Enter 'E' for external thread or 'I' for internal: ").upper()
        if type in ['E', 'I']:
            break
        else:
            print("Please select either 'E' or 'I' only.")

    # thd_class = 2

    lower = ['4', '6', '8']
    upper = ['12', '16', '20', '28', '32']

    # Calculates LE for "pd_tol" formula
    if((series == 'UNC') or (series == 'UNF')):
        LE = md_b
    elif((series == 'UN') and (tpi in lower)):
        LE = md_b
    elif((series == 'UN') and (tpi in upper)):
        LE = 9 * p
    elif((series == 'UNEF') or (series == 'UNS')):
        LE = 9 * p
    else:
        print(f"\n***NON-STANDARD THREAD SERIES ENTRY. Output is a suggestion only.***\n")
        LE = 9 * p

    # Compute nominal as-machined dimensions for the entered thread
    pd_tol = round((.0015 * ((md_b) ** (1.0/3.0))) + (.0015 * ((LE) ** (1.0/2.0))) + (.015 * ((p ** 2) ** (1.0/3.0))), 6)
    allowance = round(0.3 * pd_tol, 4)
    pd_bsc = round((md_b - .32475953 * p * 2), 4)

    # Executes appropriate thread dimension function depending on internal/external per users input
    if type == 'I':
        maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min = internal(md_b, p, pd_tol, pd_bsc)
    elif type == 'E':
        maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min = external(md_b, p, allowance, pd_bsc, pd_tol)
    else:
        print("Invalid entry for internal/external thread")
        exit()

    # Adjusts the calculated thread dimensions for plating
    p_maj_max, p_maj_min, p_pd_max, p_pd_min, p_mnr_max, p_mnr_min = plt_adj(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min, t_max, t_min, type)

    print(f"\n------------------------------------------------------------------------------------------------------------------------------------")
    print(f"| ASME B1.1:  |    Major Ø, Max/Min: {maj_max:.4f} / {maj_min:.4f}  |   Pitch Ø, Max/Min: {pd_max:.4f} / {pd_min:.4f}  |   Minor Ø, Max/Min: {mnr_max:.4f} / {mnr_min:.4f} |")
    print(f"------------------------------------------------------------------------------------------------------------------------------------")
    print(f"| Pre-plate:  |    Major Ø, Max/Min: {p_maj_max:.4f} / {p_maj_min:.4f}  |   Pitch Ø, Max/Min: {p_pd_max:.4f} / {p_pd_min:.4f}  |   Minor Ø, Max/Min: {p_mnr_max:.4f} / {p_mnr_min:.4f} |")
    print(f"------------------------------------------------------------------------------------------------------------------------------------")

    # Ensures console window remains open until user hits 'enter'
    finish = input("\nPress 'Enter' to close this window.")

def external(md_b, p, allowance, pd_bsc, pd_tol):
    # Computations for external threads
    maj_max = round(md_b - allowance, 6) # because MD on ext thread follows PD allowance offset
    maj_min = round(md_b - allowance - (.060 * (p**2)**(1/3)), 6) # Per 5.8.1-b-2

    pd_max = round(pd_bsc - allowance, 6) # Per ASME B1.1 p.4 sketch
    pd_min = round(pd_max - pd_tol, 6)

    mnr_max = md_b - (2 * .54126588 * p) - allowance
    mnr_min = md_b - (2 * .54126588 * p) - (2 * .10825318 * p)

    return(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min)

def internal(md_b, p, pd_tol, pd_bsc):
    # Computations for internal threads
    maj_min = md_b
    maj_max = round(md_b + (.14433757 * p) + round((1.3 * pd_tol), 6), 6)

    pd_min = pd_bsc
    pd_max = round(pd_min + round((1.3 * pd_tol), 6), 6)

    if (md_b < .25):
        mnr_tol = round((.0500 * (p ** 2) ** (1.0 / 3.0)) + .03 * (p / md_b), 6) - .002
        if mnr_tol > (.394 * p):
                mnr_tol = (.394 * p)
        elif mnr_tol < (.25 * p):
                mnr_tol = (.25 * p)
    elif (md_b >= 0.25):
        mnr_tol = round((0.25 * p) - (0.4 * p ** 2), 6)
    else:
        print("No tolerance adjustment.")

    mnr_min = round(md_b - (2 * .54126588 * p), 6)
    mnr_max = round(mnr_min + mnr_tol, 6)

    return(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min)

def plt_adj(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min, t_max, t_min, type):
    # Adjusts thread dimensions to add allowance for plating thickness, per section 7 of ASME B1.1-2003

    if type == 'E':
        maj_max = maj_max - 2 * t_max
        maj_min = maj_min - 2 * t_min
        pd_max = pd_max - (4 * t_max)
        pd_min = pd_min - (4 * t_min)
        mnr_max = mnr_max - 2 * t_max
        mnr_min = mnr_min - 2 * t_min
        return(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min)
    elif type == 'I':
        maj_max = maj_max + 2 * t_min
        maj_min = maj_min + 2 * t_max
        pd_max = pd_max + (4 * t_min)
        pd_min = pd_min + (4 * t_max)
        mnr_max = mnr_max + 2 * t_min
        mnr_min = mnr_min + 2 * t_max
        return(maj_max, maj_min, pd_max, pd_min, mnr_max, mnr_min)
    else:
        print("Error in plating adjustment function.")

if __name__ == "__main__":
    main()
