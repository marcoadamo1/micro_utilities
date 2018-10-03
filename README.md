# micro_utilities

Python 3.6-3.7 scripts to deal with micro-SANS.
In detail:

- SLDcalculator.py calculates the density and SLD from the volume % of D2O
- getPeak_improved.py finds a peak and fits its neighborhood to overcome detector finite resolution
- surface.py takes a folder with several I(q) and clusters them to be plotted in Origin. It also shows the data in an interactive 3D graph 
- redPumps folder: program to run binary and ternary phase diagrams with red pumps AND solCalc to calculate the scanned concentrations
- blackPumps folder: program to run push/pull on black pumps
- RTD.py  calculates the RTD for a given flowrate and D in the Dolomite chip
- RTD_overillumination.py calculates the RTD around a point, in order to keep in account the beam footprint
