import numpy as np
def day_length_calculation(latitude,doy):
    
    # Check that the input data are np arrays
    if not isinstance(doy,np.ndarray):
        doy = np.array(doy,dtype=float)

    if not isinstance(latitude,np.ndarray):
        latitude = np.array(latitude,dtype=float)

    # Check the input array sizes
    if doy.size > 1 and latitude.size > 1 and doy.size != latitude.size:
        print("Error: Input latitude and DOY arrays have different lengths")

    # Check bounds of the input data and replace with NA if invalid
    doy = np.where((doy < 1) | (doy > 366), np.nan, doy)
    latitude = np.where((latitude < -90.0) | (latitude > 90.0), np.nan, latitude)
        
    
    dtor = np.pi/180.0 # Convert degrees to radians
    angle = dtor * 360.0 * (doy-1)/365
    
    declination = (0.39637 - 22.9133*np.cos(angle)
                   + 4.02543*np.sin(angle)
                   -0.3872*np.cos(2*angle)
                   +0.052*np.sin(2*angle))

    radians = -1.0 * np.tan(latitude * dtor) * np.tan(declination * dtor)
    radians = radians.clip(min=-1.0, max=1.0)  # Ensure radians is at least -1.0 and most 1.0
    
    factor = 0.133333
    day_length = factor * np.arccos(radians) / dtor
    
    return day_length