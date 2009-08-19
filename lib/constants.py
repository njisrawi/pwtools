# vim:ts=4:sw=4:et

#-----------------------------------------------------------------------------
# Atomic units and constants
#-----------------------------------------------------------------------------
#
# All constants taken from CODATA: 
#   http://physics.nist.gov/cuu/Constants/index.html
#   
# See also:  
#   http://en.wikipedia.org/wiki/Atomic_units
#   http://en.wikipedia.org/wiki/Natural_units
#
# hbar  = h/(2*pi)
# h     = Planck constant          
# m0    = electron mass            
# e0    = (electron) unit charge  
# mu0   = magnetic constant = 4*pi * 1e-7 (exact)
# c0    = speed of light (exact)
# eps0  = electric field constant (exact)
#
# Bohr radius (also "Bohr" as length unit):
#   a0 = 4*pi*eps0*hbar**2/(m0*e0**2)
# 
# fine structute constant:
#   alpha = e0**2 / (4*pi*eps0*hbar*c0)
#
# Hartree units:
# --------------
#
# hbar = m0 = e0 = 1
# 4*pi*eps0 = 1
# 
# length:
#     a0      
# energy:
#     Eh = e0**2 / (4*pi**eps0*a0) = alpha**2*m0*c0**2
# time: ("atomic time unit")
#     th = hbar/Eh # J*s/J = s
# 
# =>
# unit of mass   = m0 = 1
# unit of charge = e0 = 1
# 
# Rydberg units: 
# --------------
#
# hbar = 2*m0 = e0**2/2 = 1
# 4*pi*eps0 = 1
#    
# =>
# unit of mass   = 2*m0       = 1
# unit of charge = e0/sqrt(2) = 1
# 
# In all Hartree-definitions, replace:
#   e0**2 -> e0**2/2
#   m0    -> 2*m0
#
# length:
#     a0 (the same, b/c in a0 formula: m0*e0**2 -> 2*m0*e0**2/2)     
# energy:
#     Eryd = e0**2/2 / (4*pi**eps0*a0) = 1/4*alpha**2*2*m0*c0**2
#            ^^^^^^^                     ^^^          ^^^^
# time:
#     tryd = hbar/Eryd
# 
# m0(Rydberg) = 1/2*m0(Hartree)
# Eryd        = 1/2*Eh
# tryd = hbar/Eryd = 2*th     
#


#-----------------------------------------------------------------------------
# Useful conversions
#-----------------------------------------------------------------------------
# 
# pressure
#
# dyn / cm**2 = 0.1 Pa
# 1 Mbar      = 100 GPa
# 1 kbar      = 0.1 GPa
#
# energy/frequency
#
# 1 cm^-1     = 2.998e10 Hz = 0.02998 THz





__all__ = ['pi', 'h', 'hbar', 'm0', 'e0', 'mu0', 'c0', 'eps0', 'a0', 'a0_A',\
           'Eh', 'th', 'kb', 'avo', 'Eryd', 'tryd', 'dyn']

from math import pi
h = 6.62606896e-34          # J*s
hbar = 1.054571628e-34      # J*s
m0 = 9.10938215e-31         # kg
e0 = 1.602176487e-19        # C = A*s
mu0 = 4e-7 * pi             # N / A**2
c0 = 299792458.0            # m/s  
eps0 = 1.0 / (mu0*c0**2)    # F/m = C / (V*m)
a0 = 0.52917720859e-10      # m
a0_A = 0.52917720859        # Angstrom
Eh = 4.35974394e-18         # J
th = 2.418884326505e-17     # s
kb = 1.3806504e-23          # J/K
avo = 6.02214179e23         # 1/mol

Eryd = 0.5*Eh
tryd = 2.0*th

dyn = 1e-5                  # N

#-----------------------------------------------------------------------------

