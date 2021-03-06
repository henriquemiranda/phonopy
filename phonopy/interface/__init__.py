# Copyright (C) 2014 Atsushi Togo
# All rights reserved.
#
# This file is part of phonopy.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name of the phonopy project nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
from phonopy.file_IO import parse_disp_yaml, write_FORCE_SETS

def read_crystal_structure(filename=None,
                           interface_mode='vasp',
                           chemical_symbols=None,
                           yaml_mode=False):
    if filename is None:
        unitcell_filename = get_default_cell_filename(interface_mode, yaml_mode)
    else:
        unitcell_filename = filename

    if not os.path.exists(unitcell_filename):
        if filename is None:
            return None, (unitcell_filename + " (default file name)",)
        else:
            return None, (unitcell_filename,)
    
    if yaml_mode:
        from phonopy.interface.phonopy_yaml import phonopyYaml
        unitcell = phonopyYaml(unitcell_filename).get_atoms()
        return unitcell, (unitcell_filename,)
        
    if interface_mode == 'vasp':
        from phonopy.interface.vasp import read_vasp
        if chemical_symbols is None:
            unitcell = read_vasp(unitcell_filename)
        else:
            unitcell = read_vasp(unitcell_filename, symbols=chemical_symbols)
        return unitcell, (unitcell_filename,)
        
    if interface_mode == 'abinit':
        from phonopy.interface.abinit import read_abinit
        unitcell = read_abinit(unitcell_filename)
        return unitcell, (unitcell_filename,)
        
    if interface_mode == 'pwscf':
        from phonopy.interface.pwscf import read_pwscf
        unitcell, pp_filenames = read_pwscf(unitcell_filename)
        return unitcell, (unitcell_filename, pp_filenames)
        
    if interface_mode == 'wien2k':
        from phonopy.interface.wien2k import parse_wien2k_struct
        unitcell, npts, r0s, rmts = parse_wien2k_struct(unitcell_filename)
        return unitcell, (unitcell_filename, npts, r0s, rmts)

    if interface_mode == 'elk':
        from phonopy.interface.elk import read_elk
        unitcell, sp_filenames = read_elk(unitcell_filename)
        return unitcell, (unitcell_filename, sp_filenames)


def get_default_cell_filename(interface_mode, yaml_mode):
    if yaml_mode:
        return "POSCAR.yaml"
    if interface_mode == 'vasp':
        return "POSCAR"
    if interface_mode == 'abinit':
        return "unitcell.in"
    if interface_mode == 'pwscf':
        return "unitcell.in"
    if interface_mode == 'wien2k':
        return "case.struct"
    if interface_mode == 'elk':
        return "elk.in"
        
def create_FORCE_SETS(interface_mode,
                      force_filenames,
                      options,
                      log_level):
    if interface_mode == 'vasp':
        displacements = parse_disp_yaml(filename='disp.yaml')
    if (interface_mode == 'wien2k' or
        interface_mode == 'abinit' or
        interface_mode == 'elk' or
        interface_mode == 'pwscf'):
        displacements, supercell = parse_disp_yaml(filename='disp.yaml',
                                                   return_cell=True)
            
    num_disp_files = len(force_filenames)
    if options.force_sets_zero_mode:
        num_disp_files -= 1
    if len(displacements['first_atoms']) != num_disp_files:
        print
        print ("Number of files to be read don't match "
               "to number of displacements in disp.yaml.")
        return 1

    if interface_mode == 'vasp':
        from phonopy.interface.vasp import parse_set_of_forces
        is_parsed = parse_set_of_forces(
            displacements,
            force_filenames,
            is_zero_point=options.force_sets_zero_mode)

    if interface_mode == 'abinit':
        from phonopy.interface.abinit import parse_set_of_forces
        print "**********************************************************"
        print "****    Abinit FORCE_SETS support is experimental.    ****"
        print "****        Your feedback would be appreciated.       ****"
        print "**********************************************************"
        is_parsed = parse_set_of_forces(
            displacements,
            force_filenames,
            supercell.get_number_of_atoms())
        
    if interface_mode == 'pwscf':
        from phonopy.interface.pwscf import parse_set_of_forces
        print "**********************************************************"
        print "****     Pwscf FORCE_SETS support is experimental.    ****"
        print "****        Your feedback would be appreciated.       ****"
        print "**********************************************************"
        is_parsed = parse_set_of_forces(
            displacements,
            force_filenames,
            supercell.get_number_of_atoms())
        
    if interface_mode == 'wien2k':
        from phonopy.interface.wien2k import parse_set_of_forces
        print "**********************************************************"
        print "****    Wien2k FORCE_SETS support is experimental.    ****"
        print "****        Your feedback would be appreciated.       ****"
        print "**********************************************************"
        is_parsed = parse_set_of_forces(
            displacements,
            force_filenames,
            supercell,
            is_distribute=(not options.is_wien2k_p1),
            symprec=options.symprec)

    if interface_mode == 'elk':
        from phonopy.interface.elk import parse_set_of_forces
        print "**********************************************************"
        print "****      Elk FORCE_SETS support is experimental.     ****"
        print "****        Your feedback would be appreciated.       ****"
        print "**********************************************************"
        is_parsed = parse_set_of_forces(
            displacements,
            force_filenames,
            supercell.get_number_of_atoms())

    if is_parsed:
        write_FORCE_SETS(displacements, filename='FORCE_SETS')
        
    if log_level > 0:
        if is_parsed:
            print "FORCE_SETS has been created."
        else:
            print "FORCE_SETS could not be created."

    return 0
            
