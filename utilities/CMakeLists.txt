INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR} )
INCLUDE_DIRECTORIES(/usr/include/hdf5/serial/)
FIND_PACKAGE(HDF5 REQUIRED)
INCLUDE_DIRECTORIES(${HDF5_INCLUDE_DIRS})
########### next target ###############

SET(csv2antenna_SRCS
   csv2antenna.c
   )

ADD_EXECUTABLE(csv2antenna ${csv2antenna_SRCS})

SET(cluttergen_SRCS
   cluttergen.cpp
   )

ADD_EXECUTABLE(cluttergen ${cluttergen_SRCS})

SET(cluttergen2d_SRCS
   cluttergen2d.cpp
   )

ADD_EXECUTABLE(cluttergen2d ${cluttergen2d_SRCS})

SET(h52raw_SRCS
   h52raw.cpp
   )

#Link to the HDF5 libraries
#FIND_LIBRARY(FERS_LIB_HDF5 NAMES hdf5 )
SET(FERS_LIB_HDF5 /usr/lib/x86_64-linux-gnu/hdf5/serial/libhdf5.so)

ADD_EXECUTABLE(h52raw ${h52raw_SRCS})

#FIND_LIBRARY(FERS_LIB_HDF5 NAMES hdf5 )
SET(FERS_LIB_HDF5 /usr/lib/x86_64-linux-gnu/hdf5/serial/libhdf5.so)
IF (FERS_LIB_HDF5)
   TARGET_LINK_LIBRARIES(h52raw ${FERS_LIB_HDF5})
ENDIF (FERS_LIB_HDF5)

#FIND_LIBRARY(FERS_LIB_HDF5_HL NAMES hdf5_hl )
SET(FERS_LIB_HDF5_HL /usr/lib/x86_64-linux-gnu/hdf5/serial/libhdf5_hl.so)
IF (FERS_LIB_HDF5_HL)
   TARGET_LINK_LIBRARIES(h52raw ${FERS_LIB_HDF5_HL})
ENDIF (FERS_LIB_HDF5_HL)

########### install files ###############

#original Makefile.am contents follow:

#
#bin_PROGRAMS = csv2antenna
#csv2antenna_SOURCES = csv2antenna.c
