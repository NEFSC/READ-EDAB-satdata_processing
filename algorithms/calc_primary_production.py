def vgpm_models(chl,sst,par,day_length):
    """
    Calculate Primary Productivity using the Behrenfeld-Falkowski VGPM Model (1997) and a modified Eppley-based formulation.

    INPUTS:
        chl         : float or np.ndarray — Satellite chlorophyll (mg m⁻³)
        sst         : float or np.ndarray — Sea surface temperature (°C)
        par         : float or np.ndarray — Surface PAR (Einstein m⁻² d⁻¹)
        day_length  : float or np.ndarray — Day length (hours)

    RETURNS:
        pp_eppley        : Daily PP using Eppley-based Pb_opt (gC m⁻² d⁻¹)
        pp_vgpm          : Daily PP using VGPM Pb_opt (gC m⁻² d⁻¹)
        kdpar            : Diffuse attenuation coefficient for PAR (m⁻¹)
        chl_euphotic     : Areal chlorophyll within euphotic layer (mg m⁻²)
        euphotic_depth   : Euphotic depth (m)
    
    REFERENCES:
        VGPM Reference:
        Behrenfeld, M.J. and P.G. Falkowski. 1997. Photosynthetic Rates Derived from Satellite-based Chlorophyll Concentration. Limnol. Oceanogr., 42[1]:1-20.

        Pbopt/temperature Reference:
        Antoine, D., J.-M. Andre, and A. Morel. 1996. Oceanic primary production. 2. Estimation at global
           scale from satellite (coastal zone color scanner) chlorophyll. Global Biogeochem. Cycles 10:57- 69.

    COPYRIGHT: 
        Copyright (C) 2025, Department of Commerce, National Oceanic and Atmospheric Administration, National Marine Fisheries Service,
        Northeast Fisheries Science Center, Narragansett Laboratory.
        This software may be used, copied, or redistributed as long as it is not sold and this copyright notice is reproduced on each copy made.
        This routine is provided AS IS without any express or implied warranties whatsoever.

    AUTHOR:
      This program was written on June 02, 2025 by Kimberly J. W. Hyde, Northeast Fisheries Science Center | NOAA Fisheries | U.S. Department of Commerce, 28 Tarzwell Dr, Narragansett, RI 02882
  
    MODIFICATION HISTORY:
        June 02, 2025 - KJWH: Initial code written and adapted from John E. O'Reilly's PP_VGPM2.pro (IDL) code
        June 23, 2025 - KJWH: Modified to return both VGPM and Eppley
    
    """

    # Convert inputs to arrays if they're scalars
    if np.isscalar(chl):
        chl = np.asarray(chl)
    if np.isscalar(sst):
        sst = np.asarray(sst)
    if np.isscalar(par):
        par = np.asarray(par)
    if np.isscalar(day_length):
        day_length = np.asarray(day_length)

    # Ensure arrays and mask invalid inputs
    chl = np.where((chl > 0) & ~np.isnan(chl), chl, np.nan)
    
    # Calculate total chlorophyll within the euphotic zone (mg m⁻²)
    chl_euphotic = np.where(
        chl < 1.0,
        38.0 * chl**0.425,
        40.2 * chl**0.507
    )  
    
    # Calculate depth of euphotic layer (m)
    zeu = np.where(
        chl_euphotic <= 10.0,
        200.0 * chl_euphotic**-0.293,
        568.2 * chl_euphotic**-0.746
    )

    # Calculate Kd_PAR (m⁻¹)
    #kdpar = -np.log(0.01) / zeu
    #kdpar = xr.where(zeu > 0, -np.log(0.01) / zeu, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        kdpar = xr.where(zeu > 0, -np.log(0.01) / zeu, np.nan)

    
    # Eppley formulation for Pb_opt (gC gChl⁻¹ h⁻¹)
    Pb_opt_eppley = 1.54 * 10.0**(0.0275 * sst - 0.07)

    # Behrenfeld VGPM polynomial formulation for Pb_opt
    sst_valid = np.where(sst > 1.e-5, sst, np.nan)
    coeffs = [1.2956, 2.749e-1, 6.17e-2, -2.05e-2, 2.462e-3, -1.348e-4, 3.4132e-6, -3.27e-8]
    sst_poly = sum(c * sst_valid**i for i, c in enumerate(coeffs))

    Pb_opt_vgpm = np.where(
        sst > 28.5, 4.0,
        np.where(sst < -1.0, 1.13, sst_poly)
    )
    
    # Light limitation factor
    light_lim = par / (par + 4.1)
    scalar = 0.66125 * 0.001 # (gC m⁻² d⁻¹) and unit conversion

    # Final primary production cac;iatopm (gC m⁻² d⁻¹)
    pp_eppley = scalar * Pb_opt_eppley * light_lim * chl * zeu * day_length
    pp_vgpm   = scalar * Pb_opt_vgpm   * light_lim * chl * zeu * day_length
        
    return pp_eppley, pp_vgpm, kdpar, chl_euphotic, zeu

#----------------------------------------------------------------------------------------------------------
def daily_vgpm(date, chl, sst, par, lat, lon, output_dir,input_dirs):
    """
    Generates daily VGPM estimates and writes them to a NetCDF file.

    Parameters:
        date (str or datetime): Date to process.
        chl, sst, par (xarray.Dataset): Input datasets containing daily values.
        lat, lon (np.ndarray or xarray): Latitude and longitude grids.
        output_dir (str): Directory to write the output NetCDF file.
        input_dirs (list of str): Directories of input data, used to determine freshness.

    Returns:
        None
    """
    
    # Define the output file and check if exists and is up to date
    output_file = os.path.join(output_dir, f"D_{date}-OCCCI-V6.0-GLOBAL_MAPPED-PPD.nc")
    should_process = True
    
    
    if os.path.exists(output_file):
    #    if not any_input_newer(input_dirs, date, output_file):
    #        expected = chl.sel(time=str(date)).time.dt.floor("D").values
    #    if not missing_dates(output_file, expected):
        print(f"✓ Skipping {date} — output file exists.")
        return
    #        should_process = False
    #if not should_process:

    print(f"The output file is: {output_file}")
    
    # Subset dataset to the specified date
    date_str = str(date)
    chl_day = chl.sel(time=date_str)
    sst_day = sst.sel(time=date_str)
    par_day = par.sel(time=date_str)

    # Broadcast DOY and LAT for day length calculation
    doy = chl_day['time'].dt.dayofyear
    doy_3d, lat_3d = xr.broadcast(doy, lat)

    # Calculate the day length
    daylength = day_length_calculation(lat_3d.values, doy_3d.values)
    
    # Convert day_length to 2D array
    daylength = np.tile(daylength.reshape(-1, 1), (1, len(lon)))
    
    # Convert day_length to dataset
    day_length = xr.DataArray(
        data=daylength,
        dims=chl_day.dims,
        coords=chl_day.coords,
        name="day_length"
    )
    
    # Change variables to float32
    chl_day = chl_day.astype("float32")
    sst_day = sst_day.astype("float32")
    par_day = par_day.astype("float32")
    day_length = day_length.astype("float32")
   
    print("Running vgpm_models...")
    pp_eppley, pp_vgpm, kdpar, chl_eu, zeu =vgpm_models(chl_day,sst_day,par_day,day_length)
    
    
    #Create data arrays for each variable
    xa_pp_eppley = xr.DataArray(pp_eppley,dims=chl_day.dims,coords=chl_day.coords,name="pp_eppley")
    xa_pp_vgpm = xr.DataArray(pp_vgpm,dims=chl_day.dims,coords=chl_day.coords,name="pp_vgpm")
    xa_kdpar = xr.DataArray(kdpar,dims=chl_day.dims,coords=chl_day.coords,name="pp_kdpar")
    xa_chl_euphotic = xr.DataArray(chl_eu,dims=chl_day.dims,coords=chl_day.coords,name="chl_euphotic")
    xa_zeu = xr.DataArray(zeu,dims=chl_day.dims,coords=chl_day.coords,name="zeu")
    
    
    # Create a dataset
    pp_dataset = xr.Dataset({
        "pp_eppley": xa_pp_eppley,
        "pp_vgpm": xa_pp_vgpm,
        "kdpar": xa_kdpar,
        "chl_euphotic": xa_chl_euphotic,
        "zeu": xa_zeu
    })
    

    pp_dataset = pp_dataset.expand_dims({"time":[date]})
    
    print(f"✓ Writing {output_file}")
    pp_dataset.to_netcdf(output_file)