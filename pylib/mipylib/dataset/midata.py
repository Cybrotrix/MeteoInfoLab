#-----------------------------------------------------
# Author: Yaqiang Wang
# Date: 2014-12-27
# Purpose: MeteoInfo data module
# Note: Jython
#-----------------------------------------------------

import os
import datetime

from org.meteoinfo.data.meteodata import MeteoDataInfo, Dimension, DimensionType
from org.meteoinfo.data.meteodata.arl import ARLDataInfo
from org.meteoinfo.data.meteodata.bufr import BufrDataInfo
from org.meteoinfo.data.meteodata.netcdf import NetCDFDataInfo
from org.meteoinfo.data import ArrayUtil
from ucar.nc2 import NetcdfFileWriter

import mipylib.numeric.minum as minum
import mipylib.miutil as miutil
from mipylib.numeric.miarray import MIArray
from mipylib.numeric.dimarray import DimArray
import dimdatafile
from dimdatafile import DimDataFile, DimDataFiles

currentfolder = None

__all__ = [
    'addfile','addfiles','addfile_arl','addfile_ascii_grid','addfile_awx','addfile_geotiff',
    'addfile_grads','addfile_hyconc','addfile_hytraj','addfile_lonlat','addfile_micaps',
    'addfile_mm5','addfile_nc','addfile_surfer',
    'addtimedim','joinncfile','asciiread','binread','binwrite',
    'convert2nc','dimension','grads2nc','ncwrite'
    ]

def isgriddata(gdata):
    return isinstance(gdata, PyGridData)
    
def isstationdata(sdata):
    return isinstance(sdata, PyStationData)
    
def __getfilename(fname):
    s5 = fname[0:5]
    isweb = False
    if s5 == 'http:' or s5 == 'https' or s5 == 'dods:' or s5 == 'dap4:':
        isweb = True
        return fname, isweb
    if os.path.exists(fname):
        if os.path.isabs(fname):
            return fname, isweb
        else:
            return os.path.join(currentfolder, fname), isweb
    else:
        if currentfolder != None:
            fname = os.path.join(currentfolder, fname)
            if os.path.isfile(fname):
                return fname, isweb
            else:
                print 'File not exist: ' + fname
                return None, isweb
        else:
            print 'File not exist: ' + fname
            return None, isweb
            
def addfiles(fnames):
    '''
    Open multiple data files.
    
    :param fnames: (*list of string*) Data file names to be opened.
    
    :returns: (*DimDataFiles*) DimDataFiles object.
    '''
    dfs = []
    for fname in fnames:
        dfs.append(addfile(fname))
    return DimDataFiles(dfs)
          
def addfile(fname, access='r', dtype='netcdf', keepopen=False, **kwargs):
    """
    Opens a data file that is written in a supported file format.
    
    :param fname: (*string*) The full or relative path of the data file to load.
    :param access: (*string*) The access right setting to the data file. Default is ``r``.
    :param dtype: (*string*) The data type of the data file. Default is ``netcdf``.
    :param keepopen: (*boolean*) If the file keep open after this function. Default is ``False``. The
        file need to be closed later if ``keepopen`` is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    """
    if access == 'r':
        fname = fname.strip()
        fname, isweb = __getfilename(fname)
        if fname is None:
            return None

        if isweb:
            return addfile_nc(fname, False)
        
        if not os.path.exists(fname):
            print 'File not exist: ' + fname
            return None
        
        fsufix = os.path.splitext(fname)[1].lower()
        if fsufix == '.ctl':
            return addfile_grads(fname, False)
        elif fsufix == '.tif':
            return addfile_geotiff(fname, False)
        elif fsufix == '.awx':
            return addfile_awx(fname, False)
        
        meteodata = MeteoDataInfo()
        meteodata.openData(fname, keepopen)
        datafile = DimDataFile(meteodata)
        return datafile
    elif access == 'c':
        if dtype == 'arl':
            arldata = ARLDataInfo()
            arldata.createDataFile(fname)
            datafile = DimDataFile(arldata=arldata)
        elif dtype == 'bufr':
            bufrdata = BufrDataInfo()
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except:   
                    info=sys.exc_info()   
                    print info[0],":",info[1]
            bufrdata.createDataFile(fname)
            datafile = DimDataFile(bufrdata=bufrdata)
        else:
            version = kwargs.pop('version', 'netcdf3')
            if version == 'netcdf3':
                version = NetcdfFileWriter.Version.netcdf3
            else:
                version = NetcdfFileWriter.Version.netcdf4
            ncfile = NetcdfFileWriter.createNew(version, fname)
            datafile = DimDataFile(ncfile=ncfile)
        return datafile
    else:
        return None
    
def addfile_grads(fname, getfn=True):
    '''
    Add a GrADS data file. use this function is GrADS control file has no ``.ctl`` suffix, otherwise use
    ``addfile`` function.
    
    :param fname: (*string*) GrADS control file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openGrADSData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_nc(fname, getfn=True):
    '''
    Add a netCDF data file.
    
    :param fname: (*string*) The netCDF file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openNetCDFData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_arl(fname, getfn=True):
    '''
    Add a ARL data file.
    
    :param fname: (*string*) The ARL file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openARLData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_surfer(fname, getfn=True):
    '''
    Add a Surfer ASCII grid data file.
    
    :param fname: (*string*) The Surfer ASCII grid file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openSurferGridData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_mm5(fname, getfn=True):
    '''
    Add a MM5 data file.
    
    :param fname: (*string*) The MM5 file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openMM5Data(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_lonlat(fname, getfn=True, missingv=-9999.0):
    '''
    Add a Lon/Lat ASCII data file.
    
    :param fname: (*string*) The Lon/Lat ASCII file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openLonLatData(fname)
    meteodata.getDataInfo().setMissingValue(missingv)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_micaps(fname, getfn=True):
    '''
    Add a MICAPS data file (Data formats from CMA).
    
    :param fname: (*string*) The MICAPS file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openMICAPSData(fname)
    datafile = DimDataFile(meteodata)
    return datafile

def addfile_hytraj(fname, getfn=True):
    '''
    Add a HYSPLIT trajectory endpoint data file.
    
    :param fname: (*string*) The HYSPLIT trajectory endpoint file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if isinstance(fname, basestring):
        if getfn:
            fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openHYSPLITTrajData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_hyconc(fname, getfn=True):
    '''
    Add a HYSPLIT concentration data file.
    
    :param fname: (*string*) The HYSPLIT concentration file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openHYSPLITConcData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_geotiff(fname, getfn=True):
    '''
    Add a GeoTiff data file.
    
    :param fname: (*string*) The GeoTiff file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openGeoTiffData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_awx(fname, getfn=True):
    '''
    Add a AWX data file (Satellite data file format from CMA). use this function is the file has no ``.awx`` 
    suffix, otherwise use ``addfile`` function.
    
    :param fname: (*string*) The AWX file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    meteodata = MeteoDataInfo()
    meteodata.openAWXData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addfile_ascii_grid(fname, getfn=True):
    '''
    Add a ESRI ASCII grid data file.
    
    :param fname: (*string*) The ESRI ASCII grid file name.
    :param getfn: (*string*) If run ``__getfilename`` function or not. Default is ``True``.
    
    :returns: (*DimDataFile*) Opened file object.
    '''
    if getfn:
        fname, isweb = __getfilename(fname)
    if not os.path.exists(fname):
        print 'File not exist: ' + fname
        return None
    meteodata = MeteoDataInfo()
    meteodata.openASCIIGridData(fname)
    datafile = DimDataFile(meteodata)
    return datafile
    
def addtimedim(infn, outfn, t, tunit='hours'):
    '''
    Add a time dimension to a netCDF data file.
    
    :param infn: (*string*) Input netCDF file name.
    :param outfn: (*string*) Output netCDF file name.
    :param t: (*datetime*) A time value.
    :param tunit: (*string*) Time unite, Default is ``hours``.
    
    :returns: The new netCDF with time dimension.
    '''
    NetCDFDataInfo.addTimeDimension(infn, outfn, miutil.jdate(t), tunit)
        
def joinncfile(infns, outfn, tdimname):
    '''
    Join several netCDF files to one netCDF file.
    
    :param infns: (*list*) Input netCDF file name list.
    :param outfn: (*string*) Output netCDF file name.
    :param tdimname: (*string*) Time dimension name.
    
    :returns: Joined netCDF file.
    '''
    NetCDFDataInfo.joinDataFiles(infns, outfn, tdimname)
    
def asciiread(filename, **kwargs):
    '''
    Read data from an ASCII file.
    
    :param filename: (*string*) The ASCII file name.
    :param delimiter: (*string*) Field delimiter character. Default is ``None``, means space or tab 
        delimiter.
    :param headerlines: (*int*) Lines to skip at beginning of the file. Default is ``0``.
    :param shape: (*string*) Data array dimension shape. Default is ``None``, the file content will
        be readed as one dimension array.
    :param readfirstcol: (*boolean*) Read first column data or not. Default is ``True``.
    
    :returns: (*MIArray*) The data array.
    '''
    delimiter = kwargs.pop('delimiter', None)
    datatype = kwargs.pop('datatype', None)
    headerlines = kwargs.pop('headerlines', 0)
    shape = kwargs.pop('shape', None)
    rfirstcol = kwargs.pop('readfirstcol', True)
    a = ArrayUtil.readASCIIFile(filename, delimiter, headerlines, datatype, shape, rfirstcol)
    return MIArray(a)
    
def binread(fn, dim, datatype=None, skip=0, byteorder='little_endian'):
    """
    Read data array from a binary file.
    
    :param fn: (*string*) The binary file name for data reading. 
    :param dim: (*list*) Dimensions.
    :param datatype: (*string*) Data type string.
    :param skip: (*int*) Skip bytes number.
    :param byteorder: (*string*) Byte order. ``little_endian`` or ``big_endian``.
    
    :returns: (*MIArray*) Data array
    """
    r = ArrayUtil.readBinFile(fn, dim, datatype, skip, byteorder);
    return MIArray(r)
        
def binwrite(fn, data, byteorder='little_endian', append=False):
    """
    Create a binary data file from an array variable.
    
    :param fn: (*string*) Path needed to locate binary file.
    :param data: (*array_like*) A numeric array variable of any dimensionality.
    :param byteorder: (*string*) Byte order. ``little_endian`` or ``big_endian``.
    :param append: (*boolean*) Append to an existing file or not.
    """
    ArrayUtil.saveBinFile(fn, data.asarray(), byteorder, append)  
    
def convert2nc(infn, outfn, version='netcdf3'):
    """
    Convert data file (Grib, HDF...) to netCDF data file.
    
    :param infn: (*string*) Input data file name.
    :param outfn: (*string*) Output netCDF data file name.
    """
    #Open input data file
    f = addfile(infn)
    #New netCDF file
    ncfile = addfile(outfn, 'c', version=version)
    #Add dimensions
    dims = []
    for dim in f.dimensions():
        dims.append(ncfile.adddim(dim.getShortName(), dim.getLength()))
    #Add global attributes
    for attr in f.attributes():
        ncfile.addgroupattr(attr.getName(), attr.getValues())
    #Add variables
    variables = []
    for var in f.variables():    
        #print 'Variable: ' + var.getShortName()
        if var.hasNullDimension():
            continue
        vdims = []
        missdim = False
        for vdim in var.getDimensions():
            isvalid = False
            for dim in dims:
                if dim.getShortName() == vdim.getShortName():
                    vdims.append(dim)
                    isvalid = True
                    break
            if not isvalid:
                missdim = True
                break
        if missdim:
            continue
        nvar = ncfile.addvar(var.getShortName(), var.getDataType(), vdims)
        for attr in var.getAttributes():
            nvar.addattr(attr.getName(), attr.getValues())
        variables.append(nvar)
    #Create netCDF file
    ncfile.create()
    #Write data
    for var in variables:
        print 'Variable: ' + var.name
        data = f[str(var.name)].read()
        ncfile.write(var, data)
    #Close netCDF file
    ncfile.close()
    print 'Convert finished!'
    
def grads2nc(infn, outfn, big_endian=None):
    """
    Convert GrADS data file to netCDF data file.
    
    :param infn: (*string*) Input GrADS data file name.
    :param outfn: (*string*) Output netCDF data file name.
    :param big_endian: (*boolean*) Is GrADS data big_endian or not.
    """
    #Open GrADS file
    f = addfile_grads(infn)
    if not big_endian is None:
        f.bigendian(big_endian)

    #New netCDF file
    ncfile = addfile(outfn, 'c')

    #Add dimensions
    dims = []
    for dim in f.dimensions():
        dims.append(ncfile.adddim(dim.getShortName(), dim.getLength()))
    xdim = f.finddim('X')
    ydim = f.finddim('Y')
    tdim = f.finddim('T')
    xnum = xdim.getLength()
    ynum = ydim.getLength()
    tnum = tdim.getLength()

    #Add global attributes
    ncfile.addgroupattr('Conventions', 'CF-1.6')
    for attr in f.attributes():
        ncfile.addgroupattr(attr.getName(), attr.getValues())

    #Add dimension variables
    dimvars = []
    for dim in dims:
        dname = dim.getShortName()
        if dname == 'T':
            var = ncfile.addvar('time', 'int', [dim])
            var.addattr('units', 'hours since 1900-01-01 00:00:0.0')
            var.addattr('long_name', 'Time')
            var.addattr('standard_name', 'time')
            var.addattr('axis', dname)
            tvar = var
        elif dname == 'Z':
            var = ncfile.addvar('level', 'float', [dim])
            var.addattr('axis', dname)
        else:
            var = ncfile.addvar(dim.getShortName(), 'float', [dim])
            if 'Z' in dname:
                var.addattr('axis', 'Z')
            else:
                var.addattr('axis', dname)
        dimvars.append(var)

    #Add variables
    variables = []
    for var in f.variables():    
        print 'Variable: ' + var.getShortName()
        vdims = []
        for vdim in var.getDimensions():
            for dim in dims:
                if vdim.getShortName() == dim.getShortName():
                    vdims.append(dim)
        #print vdims
        nvar = ncfile.addvar(var.getShortName(), var.getDataType(), vdims)
        nvar.addattr('fill_value', -9999.0)
        for attr in var.getAttributes():
            nvar.addattr(attr.getName(), attr.getValues())
        variables.append(nvar)

    #Create netCDF file
    ncfile.create()

    #Write variable data
    for dimvar, dim in zip(dimvars, f.dimensions()):
        if dim.getShortName() != 'T':
            ncfile.write(dimvar, minum.array(dim.getDimValue()))

    sst = datetime.datetime(1900,1,1)
    for t in range(0, tnum):
        st = f.gettime(t)
        print st.strftime('%Y-%m-%d %H:00')
        hours = (st - sst).total_seconds() // 3600
        origin = [t]
        ncfile.write(tvar, minum.array([hours]), origin=origin)
        for var in variables:
            print 'Variable: ' + var.name
            if var.ndim == 3:
                data = f[str(var.name)][t,:,:]    
                data[data==minum.nan] = -9999.0        
                origin = [t, 0, 0]
                shape = [1, ynum, xnum]
                data = data.reshape(shape)
                ncfile.write(var, data, origin=origin)
            else:
                znum = var.dims[1].getLength()
                for z in range(0, znum):
                    data = f[str(var.name)][t,z,:,:]
                    data[data==minum.nan] = -9999.0
                    origin = [t, z, 0, 0]
                    shape = [1, 1, ynum, xnum]
                    data = data.reshape(shape)
                    ncfile.write(var, data, origin=origin)

    #Close netCDF file
    ncfile.close()
    print 'Convert finished!'
    
def dimension(dimvalue, dimname='null', dimtype=None):
    """
    Create a new Dimension.
    
    :param dimvalue: (*array_like*) Dimension value.
    :param dimname: (*string*) Dimension name.
    :param dimtype: (*DimensionType*) Dimension type.
    """
    if isinstance(dimvalue, (MIArray, DimArray)):
        dimvalue = dimvalue.aslist()
    dtype = DimensionType.Other
    if not dimtype is None:
        if dimtype.upper() == 'X':
            dtype = DimensionType.X
        elif dimtype.upper() == 'Y':
            dtype = DimensionType.Y
        elif dimtype.upper() == 'Z':
            dtype = DimensionType.Z
        elif dimtype.upper() == 'T':
            dtype = DimensionType.T
    dim = Dimension(dtype)
    dim.setDimValues(dimvalue)
    dim.setShortName(dimname)
    return dim
    
def ncwrite(fn, data, varname, dims=None, attrs=None):
    """
    Write a netCDF data file from an array.
    
    :param: fn: (*string*) netCDF data file path.
    :param data: (*array_like*) A numeric array variable of any dimensionality.
    :param varname: (*string*) Variable name.
    :param dims: (*list of dimensions*) Dimension list.
    :param attrs: (*list of attributes*) Attributes list.
    """
    if dims is None:
        if isinstance(data, MIArray):
            dims = []
            for s in data.shape:
                dimvalue = minum.arange(s)
                dimname = 'dim' + str(len(dims))
                dims.append(dimension(dimvalue, dimname))
        else:
            dims = data.dims
    #New netCDF file
    ncfile = addfile(fn, 'c')
    #Add dimensions
    ncdims = []
    for dim in dims:    
        ncdims.append(ncfile.adddim(dim.getShortName(), dim.getLength()))
    #Add global attributes
    ncfile.addgroupattr('Conventions', 'CF-1.6')
    ncfile.addgroupattr('Tools', 'Created using MeteoInfo')
    #Add dimension variables
    dimvars = []
    for dim,midim in zip(ncdims,dims):
        dimtype = midim.getDimType()
        dimname = dim.getShortName()
        if dimtype == DimensionType.T:
            var = ncfile.addvar(dimname, 'int', [dim])
            var.addattr('units', 'hours since 1900-01-01 00:00:0.0')
            var.addattr('long_name', 'Time')
            var.addattr('standard_name', 'time')
            var.addattr('axis', 'T')
            tvar = var
        elif dimtype == DimensionType.Z:
            var = ncfile.addvar(dimname, 'float', [dim])
            var.addattr('axis', 'Z')
        elif dimtype == DimensionType.Y:
            var = ncfile.addvar(dimname, 'float', [dim])
            var.addattr('axis', 'Y')
        elif dimtype == DimensionType.X:
            var = ncfile.addvar(dimname, 'float', [dim])
            var.addattr('axis', 'X')
        else:
            var = ncfile.addvar(dim.getShortName(), 'float', [dim])
            var.addattr('axis', 'null')
        dimvars.append(var)
    #Add variable
    var = ncfile.addvar(varname, data.dtype, ncdims)
    if attrs is None:    
        var.addattr('name', varname)
    else:
        for key in attrs:
            var.addattr(key, attr[key])
    #Create netCDF file
    ncfile.create()
    #Write variable data
    for dimvar, dim in zip(dimvars, dims):
        if dim.getDimType() == DimensionType.T:
            sst = datetime.datetime(1900,1,1)
            tt = miutil.nums2dates(dim.getDimValue())
            hours = []
            for t in tt:
                hours.append((t - sst).total_seconds() // 3600)
            ncfile.write(dimvar, minum.array(hours))
        else:
            ncfile.write(dimvar, minum.array(dim.getDimValue()))
    ncfile.write(var, data)
    #Close netCDF file
    ncfile.close()