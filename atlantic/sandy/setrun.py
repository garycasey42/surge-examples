#!/usr/bin/python3
from __future__ import absolute_import
from __future__ import print_function

#ensure# encoding: utf-8
"""
Module to set up run time parameters for Clawpack.

The values set in the function setrun are then written out to data files
that will be read in by the Fortran code.

"""

import os
# to exract all the fine grid topography data from /bathy
import glob
import sys
import datetime
import shutil
import gzip

import numpy as np

from clawpack.geoclaw.surge.storm import Storm
import clawpack.clawutil as clawutil


# Time Conversions
def days2seconds(days):
    return days * 60.0**2 * 24.0


#------------------------------
def setrun(claw_pkg='geoclaw'):
#------------------------------
    """
    Define the parameters used for running Clawpack.

    INPUT:
    claw_pkg expected to be "geoclaw" for this setrun.

    OUTPUT:
    rundata - object of class ClawRunData

    """

    from clawpack.clawutil import data as clawdata

    assert claw_pkg.lower() == 'geoclaw',  "Expected claw_pkg = 'geoclaw'"

    num_dim = 2
    rundata = clawdata.ClawRunData(claw_pkg, num_dim)

    #------------------------------------------------------------------
    # Problem-specific parameters to be written to setprob.data:
    #------------------------------------------------------------------
    
    #probdata = rundata.new_UserData(name='probdata',fname='setprob.data')

    #------------------------------------------------------------------
    # Standard Clawpack parameters to be written to claw.data:
    #   (or to amr2ez.data for AMR)
    #------------------------------------------------------------------
    clawdata = rundata.clawdata  # initialized when rundata instantiated


    # Set single grid parameters first.
    # See below for AMR parameters.


    # ---------------
    # Spatial domain:
    # ---------------

    # Number of space dimensions:
    clawdata.num_dim = num_dim

    # Lower and upper edge of computational domain:
    # clawdata.lower[0] = -85.0      # west longitude
    # clawdata.upper[0] = -55.0      # east longitude

    # clawdata.lower[1] = 13.0       # south latitude
    # clawdata.upper[1] = 45.0      # north latitude

    clawdata.lower[0] = -88.0      # west longitude
    clawdata.upper[0] = -55.0      # east longitude

    clawdata.lower[1] = 15.0       # south latitude
    clawdata.upper[1] = 45.0      # north latitude


    # Number of grid cells:
    degree_factor = 4
    clawdata.num_cells[0] = int(clawdata.upper[0] - clawdata.lower[0]) * degree_factor
    clawdata.num_cells[1] = int(clawdata.upper[1] - clawdata.lower[1]) * degree_factor

    # ---------------
    # Size of system:
    # ---------------

    # Number of equations in the system:
    clawdata.num_eqn = 3

    # Number of auxiliary variables in the aux array (initialized in setaux)
    clawdata.num_aux = 3 + 1 + 3

    # Index of aux array corresponding to capacity function, if there is one:
    clawdata.capa_index = 2

    
    
    # -------------
    # Initial time:
    # -------------

    clawdata.t0 = days2seconds(-2.0)


    # Restart from checkpoint file of a previous run?
    # Note: If restarting, you must also change the Makefile to set:
    #    RESTART = False
    # If restarting, t0 above should be from original run, and the
    # restart_file 'fort.chkNNNNN' specified below should be in 
    # the OUTDIR indicated in Makefile.

    clawdata.restart = False               # True to restart from prior results
    clawdata.restart_file = 'fort.chk00043'  # File to use for restart data

    # -------------
    # Output times:
    #--------------

    # Specify at what times the results should be written to fort.q files.
    # Note that the time integration stops after the final output time.
    # The solution at initial time t0 is always written in addition.

    clawdata.output_style = 1

    if clawdata.output_style==1:
        # Output nout frames at equally spaced times up to tfinal:
        #                 day     s/hour  hours/day
        
        clawdata.tfinal = days2seconds(1.0)

        # Output occurrence per day, 24 = every hour, 4 = every 6 hours
        recurrence = 24
        clawdata.num_output_times = int((clawdata.tfinal - clawdata.t0) 
                                            * recurrence / (60**2 * 24))

        clawdata.output_t0 = True  # output at initial (or restart) time?
        

    elif clawdata.output_style == 2:
        # Specify a list of output times.
        clawdata.output_times = [0.5, 1.0]

    elif clawdata.output_style == 3:
        # Output every iout timesteps with a total of ntot time steps:
        clawdata.output_step_interval = 1
        clawdata.total_steps = 1
        clawdata.output_t0 = True
        

    clawdata.output_format = 'ascii'      # 'ascii' or 'netcdf' 

    clawdata.output_q_components = 'all'   # could be list such as [True,True]
    clawdata.output_aux_components = 'all'
    clawdata.output_aux_onlyonce = False    # output aux arrays only at t0



    # ---------------------------------------------------
    # Verbosity of messages to screen during integration:
    # ---------------------------------------------------

    # The current t, dt, and cfl will be printed every time step
    # at AMR levels <= verbosity.  Set verbosity = 0 for no printing.
    #   (E.g. verbosity == 2 means print only on levels 1 and 2.)
    clawdata.verbosity = 4



    # --------------
    # Time stepping:
    # --------------

    # if dt_variable==1: variable time steps used based on cfl_desired,
    # if dt_variable==0: fixed time steps dt = dt_initial will always be used.
    clawdata.dt_variable = True

    # Initial time step for variable dt.
    # If dt_variable==0 then dt=dt_initial for all steps:
    clawdata.dt_initial = 0.016

    # Max time step to be allowed if variable dt used:
    clawdata.dt_max = 1e+99

    # Desired Courant number if variable dt used, and max to allow without
    # retaking step with a smaller dt:
    # clawdata.cfl_desired = 0.75
    clawdata.cfl_desired = 0.75
    clawdata.cfl_max = 1.0

    # Maximum number of time steps to allow between output times:
    clawdata.steps_max = 2**16




    # ------------------
    # Method to be used:
    # ------------------

    # Order of accuracy:  1 => Godunov,  2 => Lax-Wendroff plus limiters
    clawdata.order = 1
    
    # Use dimensional splitting? (not yet available for AMR)
    clawdata.dimensional_split = 'unsplit'
    
    # For unsplit method, transverse_waves can be 
    #  0 or 'none'      ==> donor cell (only normal solver used)
    #  1 or 'increment' ==> corner transport of waves
    #  2 or 'all'       ==> corner transport of 2nd order corrections too
    clawdata.transverse_waves = 2

    # Number of waves in the Riemann solution:
    clawdata.num_waves = 3
    
    # List of limiters to use for each wave family:  
    # Required:  len(limiter) == num_waves
    # Some options:
    #   0 or 'none'     ==> no limiter (Lax-Wendroff)
    #   1 or 'minmod'   ==> minmod
    #   2 or 'superbee' ==> superbee
    #   3 or 'mc'       ==> MC limiter
    #   4 or 'vanleer'  ==> van Leer
    clawdata.limiter = ['mc', 'mc', 'mc']

    clawdata.use_fwaves = True    # True ==> use f-wave version of algorithms
    
    # Source terms splitting:
    #   src_split == 0 or 'none'    ==> no source term (src routine never called)
    #   src_split == 1 or 'godunov' ==> Godunov (1st order) splitting used, 
    #   src_split == 2 or 'strang'  ==> Strang (2nd order) splitting used,  not recommended.
    clawdata.source_split = 'godunov'


    # --------------------
    # Boundary conditions:
    # --------------------

    # Number of ghost cells (usually 2)
    clawdata.num_ghost = 2

    # Choice of BCs at xlower and xupper:
    #   0 => user specified (must modify bcN.f to use this option)
    #   1 => extrapolation (non-reflecting outflow)
    #   2 => periodic (must specify this at both boundaries)
    #   3 => solid wall for systems where q(2) is normal velocity

    clawdata.bc_lower[0] = 'extrap'
    clawdata.bc_upper[0] = 'extrap'

    clawdata.bc_lower[1] = 'extrap'
    clawdata.bc_upper[1] = 'extrap'

    # Specify when checkpoint files should be created that can be
    # used to restart a computation.

    clawdata.checkpt_style = 0

    if clawdata.checkpt_style == 0:
        # Do not checkpoint at all
        pass

    elif clawdata.checkpt_style == 1:
        # Checkpoint only at tfinal.
        pass

    elif clawdata.checkpt_style == 2:
        # Specify a list of checkpoint times.  
        clawdata.checkpt_times = [0.1,0.15]

    elif clawdata.checkpt_style == 3:
        # Checkpoint every checkpt_interval timesteps (on Level 1)
        # and at the final time.
        clawdata.checkpt_interval = 5


    # ---------------
    # AMR parameters:
    # ---------------
    amrdata = rundata.amrdata


    # max number of refinement levels:
    amrdata.amr_levels_max = 6

    # List of refinement ratios at each level (length at least mxnest-1)
    # amrdata.refinement_ratios_x = [2, 2, 2, 6, 16]
    # amrdata.refinement_ratios_y = [2, 2, 2, 6, 16]
    # amrdata.refinement_ratios_t = [2, 2, 2, 6, 16]

    amrdata.refinement_ratios_x = [2, 2, 2, 6, 8]
    amrdata.refinement_ratios_y = [2, 2, 2, 6, 8]
    amrdata.refinement_ratios_t = [2, 2, 2, 6, 8]


    # Specify type of each aux variable in amrdata.auxtype.
    # This must be a list of length maux, each element of which is one of:
    #   'center',  'capacity', 'xleft', or 'yleft'  (see documentation).

    amrdata.aux_type = ['center','capacity','yleft','center','center','center',
                         'center', 'center', 'center']



    # Flag using refinement routine flag2refine rather than richardson error
    amrdata.flag_richardson = False    # use Richardson?
    amrdata.flag2refine = True

    # steps to take on each level L between regriddings of level L+1:
    amrdata.regrid_interval = 4

    # width of buffer zone around flagged points:
    # (typically the same as regrid_interval so waves don't escape):
    amrdata.regrid_buffer_width  = 2

    # clustering alg. cutoff for (# flagged pts) / (total # of cells refined)
    # (closer to 1.0 => more small grids may be needed to cover flagged cells)
    amrdata.clustering_cutoff = 0.700000

    # print info about each regridding up to this level:
    amrdata.verbosity_regrid = 0  


    #  ----- For developers ----- 
    # Toggle debugging print statements:
    amrdata.dprint = False      # print domain flags
    amrdata.eprint = False      # print err est flags
    amrdata.edebug = False      # even more err est flags
    amrdata.gprint = False      # grid bisection/clustering
    amrdata.nprint = False      # proper nesting output
    amrdata.pprint = False      # proj. of tagged points
    amrdata.rprint = False      # print regridding summary
    amrdata.sprint = False      # space/memory output
    amrdata.tprint = False      # time step reporting each level
    amrdata.uprint = False      # update/upbnd reporting
    
    # More AMR parameters can be set -- see the defaults in pyclaw/data.py

    # == setregions.data values ==
    regions = rundata.regiondata.regions
    # to specify regions of refinement append lines of the form
    #  [minlevel,maxlevel,t1,t2,x1,x2,y1,y2]
    regions.append([1,6,days2seconds(-0.45),days2seconds(0.10),-74.1,-73.7,40.55,48.5])
    regions.append([1,5,days2seconds(0.10),days2seconds(1),-74.2,-73.7,40.55,48.5])

    
    # == setgauges.data values ==
    # for gauges append lines of the form  [gaugeno, x, y, t1, t2]
    # battery gauge
    rundata.gaugedata.gauges.append([1,-74.013,40.7,clawdata.t0,clawdata.tfinal])
    # Kings point gauge
    rundata.gaugedata.gauges.append([2,-73.77,40.81,clawdata.t0,clawdata.tfinal])
    # Sandy Hook gauge
   # rundata.gaugedata.gauges.append([3,-74.01,40.47,clawdata.t0,clawdata.tfinal])
    # Bergen Point West Reach
    rundata.gaugedata.gauges.append([3,-74.14166,40.6367,clawdata.t0,clawdata.tfinal])
   # Narrows
   # rundata.gaugedata.gauges.append([4,-74.038,40.605,clawdata.t0,clawdata.tfinal])

    #------------------------------------------------------------------
    # GeoClaw specific parameters:
    #------------------------------------------------------------------
    rundata = setgeo(rundata)

    return rundata
    # end of function setrun
    # ----------------------


#-------------------
def setgeo(rundata):
#-------------------
    """
    Set GeoClaw specific runtime parameters.
    For documentation see ....
    """

    try:
        geo_data = rundata.geo_data
    except:
        print("*** Error, this rundata has no geodata attribute")
        raise AttributeError("Missing geodata attribute")
       
    # == Physics ==
    geo_data.gravity = 9.81
    geo_data.coordinate_system = 2
    geo_data.earth_radius = 6367.5e3
    geo_data.rho = 1025.0
    geo_data.rho_air = 1.15
    geo_data.ambient_pressure = 101.3e3

    # == Forcing Options
    geo_data.coriolis_forcing = True
    geo_data.friction_forcing = True
    geo_data.friction_depth = 1e10

    # == Algorithm and Initial Conditions ==
    geo_data.sea_level = 0.33
    geo_data.dry_tolerance = 1.e-2

    # Refinement Criteria
    refine_data = rundata.refinement_data
    refine_data.wave_tolerance = 1.0
    refine_data.speed_tolerance = [1.0, 2.0, 3.0, 4.0]
    refine_data.deep_depth = 300.0
    refine_data.max_level_deep = 4
    refine_data.variable_dt_refinement_ratios = True

    # == settopo.data values ==
    topo_data = rundata.topo_data
    topo_data.topofiles = []
    # for topography, append lines of the form
    #   [topotype, minlevel, maxlevel, t1, t2, fname]
    topo_path = '../bathy'

    topo_data.topofiles.append([3, 1, 3, days2seconds(-2), days2seconds(1), os.path.join(topo_path,'atlantic_1min.tt3')])
    topo_data.topofiles.append([3, 1, 3, days2seconds(-2), days2seconds(1), os.path.join(topo_path,'newyork_3s.tt3')])
    # restrict these make max lower and for all time
   # for file in glob.glob("../bathy/*.nc"):
    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x00_74x00.nc')])
    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc40x75_74x00.nc')])
   
    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc40x50_74x00.nc')])
    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc40x75_73x75.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc40x75_73x50.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x00_73x25.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'montauk_13.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc40x75_73x25.nc')])
    
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x25_74x00.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x25_73x75.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x25_73x50.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x25_73x25.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x00_73x75.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x00_73x50.nc')])
    
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc40x75_73x00.nc')])
#    topo_data.topofiles.append([4, 1, 6, days2seconds(-0.45),days2seconds(0.46),os.path.join(topo_path,'nc41x00_73x00.nc')])
 
    #print(topo_data.topofiles)

    
    # == setqinit.data values ==
    rundata.qinit_data.qinit_type = 0
    rundata.qinit_data.qinitfiles = []
    # for qinit perturbations, append lines of the form: (<= 1 allowed for now!)
    #   [minlev, maxlev, fname]

    # == setfixedgrids.data values ==
    rundata.fixed_grid_data.fixedgrids = []
    # for fixed grids append lines of the form
    # [t1,t2,noutput,x1,x2,y1,y2,xpoints,ypoints,\
    #  ioutarrivaltimes,ioutsurfacemax]

    # ================
    #  Set Surge Data
    # ================
    data = rundata.surge_data

    # Source term controls
    data.wind_forcing = True
    data.drag_law = 1
    data.pressure_forcing = True

    data.display_landfall_time = True

    # AMR parameters
    data.wind_refine = [20.0,40.0,60.0] # m/s
    data.R_refine = [60.0e3,40e3,20e3]  # m
    
    # Storm parameters
    data.storm_specification_type = "holland80" # Set type of storm field
    data.storm_file = os.path.expandvars(os.path.join(os.getcwd(),
                                                      'sandy.storm'))

    # Convert ATCF data to GeoClaw format
    clawutil.data.get_remote_file(
                   "http://ftp.nhc.noaa.gov/atcf/archive/2012/bal182012.dat.gz",
                   output_dir=os.getcwd())
    atcf_path = os.path.join(os.getcwd(), "bal182012.dat")
    # Note that the get_remote_file function does not support gzip files which
    # are not also tar files.  The following code handles this
    with gzip.open(".".join((atcf_path, 'gz')), 'rb') as atcf_file:
        with open(atcf_path, 'w') as atcf_unzipped_file:
            atcf_unzipped_file.write(atcf_file.read().decode('ascii'))

    sandy = Storm(path=atcf_path, file_format="ATCF")

    # Calculate landfall time - Need to specify as the file above does not
    # include this info (9/13/2008 ~ 7 UTC)
    sandy.time_offset = datetime.datetime(2012,10,30,0,0)

    sandy.write(data.storm_file, file_format='geoclaw')
    
    # =======================
    #  Set Variable Friction
    # =======================
    data = rundata.friction_data

    # Variable friction
    data.variable_friction = True

    # Region based friction
    # Entire domain - seems high on land...
    data.friction_regions.append([rundata.clawdata.lower, 
                                  rundata.clawdata.upper,
                                  [np.infty,0.0,-np.infty],
                                  [0.050, 0.025]])

    
    return rundata
    # end of function setgeo
    # ----------------------


if __name__ == '__main__':
    # Set up run-time parameters and write all data files.
    import sys
    if len(sys.argv) == 2:
        rundata = setrun(sys.argv[1])
    else:
        rundata = setrun()

    rundata.write()
