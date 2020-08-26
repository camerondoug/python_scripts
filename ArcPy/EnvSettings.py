import arcpy

arcpy.env.overwriteOutput = True

arcpy.env.workspace = r"C:\LPA\Data\test.gdb"
##if arcpy.Exists(r"C:\LPA\Data\test.gdb"):
##
##    arcpy.Delete_management(r"C:\LPA\Data\test.gdb")

arcpy.CreateFileGDB_management(r"C:\LPA\Data", "test")

arcpy.FeatureClassToFeatureClass_conversion(
    r"C:\LPA\Data\ne_10m_admin_0_countries.shp",
    r"C:\LPA\Data\test.gdb", "Countries")

print(arcpy.Exists(r"C:\LPA\Data\test.gdb\Countries"))

arcpy.Select_analysis(
    "Countries", "TrinidadTobago","NAME = 'Trinidad and Tobago'")

print(arcpy.Exists(r"C:\LPA\Data\test.gdb\TrinidadTobago"))

arcpy.Buffer_analysis("TrinidadTobago","TrinidadTobago_EEZ",
                      "200 NauticalMiles", method = "GEODESIC")

print(arcpy.Exists(r"C:\LPA\Data\test.gdb\TrinidadTobago_EEZ"))

arcpy.FeatureClassToFeatureClass_conversion(
    r"C:\LPA\Data\ne_10m_admin_0_countries.shp",
    r"C:\LPA\Data\test.gdb", "Countries")


print ("\nScript Completed!")
