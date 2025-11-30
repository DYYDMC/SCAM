# SCAM
## SCAN
Upon using a new spectrometer, you need to register the idVendor and idProduct in a rules file. In linux, this file can be put somewhere under "/etc/udev/rules.d" etc

## CAM-correct-spherical-abberation
checkboard should be fully visible, but NOT overexposed. Orientation stay unchanged throughout photo-shooting.This requires a proper laser intensity (80,100,100) and exposuretime (800ms for UV,100mv for green) and no analog gian etc, gain will blur the sharp edges and impedes the corner detection

## CAM-vignette-effect
use a lens paper to wrap around the light guid to create a (suboptimal) homogenous light source. The lens paper is thin enough as the UV is at 80%, the light can still penetrate the lens paper and be captured by the camera. However the analoggain need to be adjusted here for the uv-cam for the exposure time at 1s is not enough for it.