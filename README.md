# un_thread_calculator
This program calculates Major Diameter, Pitch Diameter, and Minor diameter for ANSI/ASME/UN-series threads according to ASME B1.1 thread standard.

The program currently only works for Unified National thread series, Class 2, with 60° flank angle.

The program runs in a console window and prompts the user for the following information:  

  Basic thread size (nominal major diameter of male thread, for example, 1/2")  
  Thread pitch (TPI)  
  Thread series (for example UN, UNC, UNF, etc.)  
  Plating thickness to adjust machine dimensions for, if desired  
  Internal or External Thread  
  
The program will output the "Textbook" machining dimensions as well as a modified set of dimensions that account for plating thickness according to the ASME B1.1 standard.

The program has been audited against a cross-section of threads specified in the ASME B1.1 standard and has been verified to output correct values. If you use this program, I would appreciate feedback on any additional verification that is performed.

The source code is provided in Python but a Windows Executable is provided as well for non-programmers.

# Desired future improvements:

  Add functionality for metric threads  
  Improver user experience with a GUI  
  Create executable versions for Mac and Linux   
