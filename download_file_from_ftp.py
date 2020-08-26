# Author : Doug Cameron
# Last Date Modified : May 27, 2015
#This script downloads the latest ICIS_Cadastre.shp.zip from the ICIS FTP site.
#The file will be downloaded only if the file on the FTP is newer than the one on the L: drive 

import fme,fmeobjects
import os, ftplib, sys, datetime, calendar, cx_Oracle, traceback

#--------------------------------------------------------------------------------------------------------------------------
def set_sql_err_message():

    """Create a error message if there are problems connecting to Oracle"""
    etype = sys.exc_info()[0]
    evalue = sys.exc_info()[1]
    etb = traceback.extract_tb(sys.exc_info()[2])

    sql_err_message_new = 'Error in the GIS update routine.\n'
    sql_err_message_new += 'Error Type: ' + str(etype) + '\n'
    sql_err_message_new += 'Error Value: ' + str(evalue) + '\n'
    sql_err_message_new += 'Traceback: ' + str(etb) + '\n\n'

    return sql_err_message_new 
#--------------------------------------------------------------------------------------------------------------------------

# Template Class Interface:
class FeatureProcessor(object):
    def __init__(self):
       pass    
    def input(self,feature):
            
        reports_dir = "//engfps/cadd/landbase/GIS/Projects/Base Data/Landbase/Parcel/Spatial_Load/BC/ICIS/QC/"#Error reports in this directory
        download_directory = '//engfps/groups-extension/Mapping_Services/SourceData_GIS/BC/ICIS_Cadastres/'#zip file will go here

        logger = fmeobjects.FMELogFile()# intialize new fme logger
        sql_err_message_new = ""#set blank error messages
        err_message = ""
        ftplib_err_message = ""
        Error_message = ""


        db_input = feature.getAttribute('PATH_MOD_DATE')#get the date when the file was last downloaded which is saved in META_PARCEL_T table 
        db_input_obj = datetime.datetime.strptime(db_input, "%Y%m%d%H%M%S")#convert the mod date into an python object
        db_local_time_converted_UTC_seconds = int(calendar.timegm(db_input_obj.utctimetuple()))#convert the date object into UTC seconds

        #db_local_time_converted_UTC_seconds = 957529034

        server = 'geoshare.icisociety.ca'#the is the ICIS FTP server name
        username = '********' 
        password = '********'


        directory = '/Cadastre/'# Directory where the file is located on FTP
        file_to_download = 'ICIS_Cadastre.shp.zip'#filename to download

        filename_full_path = download_directory+file_to_download#set filename with full path of where it will be stored on L:


        if os.path.exists(download_directory):#if the path exists

            try:
                
                ftpconnection = ftplib.FTP(server)# Establish the connection
                ftpconnection.login(username, password)#login to server
                ftpconnection.cwd(directory)# Change to the proper directory on FTP
           
                for filename in ftpconnection.nlst(file_to_download):#match the filename we need to the filename on the server

                    try:
                        connection = cx_Oracle.connect('BOUNDARYUPDATE_APP_ACCESS/bu5acc@PRDFDBSL')# Establish the Oracle connection
                        cursor = connection.cursor() #set a cursor connection

                        if cursor: #if there is a cursor connection

                            try:
                                
                                ftp_file_modified_time_raw = ftpconnection.sendcmd('MDTM ' + filename)#find the modified date of the file in UTC server time
                                ftp_file_modified_time_stripped = ftp_file_modified_time_raw[4:]#strip off the first 4 characters of the time. Just junk. Not sure what it is for.
                                ftp_file_modified_time_obj = datetime.datetime.strptime(ftp_file_modified_time_stripped, "%Y%m%d%H%M%S")# convert the time string into date object
                                ftp_local_time_converted_UTC_seconds = int(calendar.timegm(ftp_file_modified_time_obj.utctimetuple()))#convert date object to UTC seconds
                                ftp_file_modified_time_converted_str = str(ftp_file_modified_time_obj)#convert the local time H:M:S into string for insert into Meta_Parcel_T table
                                

                                if ftp_local_time_converted_UTC_seconds > db_local_time_converted_UTC_seconds: #compare the zip file datetime to the file's datetime stored in the PARCEL_MO
                                                                                                               #if the file is newer on the server then download it 

                                    try:
                                        #file_new = open(filename_full_path, 'wb')#open new file for writing
                                        log_string1 = 'Getting ' + filename#create a log string
                                        print log_string1  
                                        logger.logMessageString(log_string1)#log the message
                                        #ftpconnection.retrbinary('RETR ' + filename, file_new.write)#copy file from server to new file
                                        #file_new.close()
                                        
                                        try:# update the time record in the PARCEL_MOD_LOG table
                                            sqlstr = "UPDATE GIS_STAGING.META_PARCEL_T SET PATH_MOD_DAT = TO_DATE('"+ ftp_file_modified_time_converted_str +"','YYYY-MM-DD HH24:MI:SS') where PATH_FILENAME = '"+ filename +"'"
                                            sqlstr_1 = str(sqlstr)

                                            #cursor.execute(sqlstr_1)#excute the update statment
                                            #connection.commit()

                                        except cx_Oracle.DatabaseError:#if the sql statement didn't work, create an error message

                                            sql_err_message_new += set_sql_err_message()


                                    except (IOError,WindowsError) ,e :#if the file didn't write 

                                        err_message += "Error: Couldn't write zip file to L: drive" + str(e) + '\n'
                                                                       

                            
                            
                            except ftplib.all_errors as e: #if there was a problem connecting to the ICIS site

                                ftplib_err_message += 'Error with URL open. File is not on server: '+ '\n' + filename + '\n' + str(e) + '\n' 
                                
                        else:

                            err_message += "Error: Couldn't file directory on L: drive" +download_directory+ str(e) + '\n'
                            ftpconnection.quit()#close the ftp connection

                    except cx_Oracle.DatabaseError: #if there is problem connecting to Oracle
                    
                        sql_err_message_new += set_sql_err_message()

            except ftplib.all_errors, e: #if there was a problem connecting to the ICIS site

                ftplib_err_message = 'Error connecting to ICIS site: ' + str(e) + '\n' 

        else:
            err_message += "Error: Couldn't file directory on L: drive" +download_directory + '\n'

        #-----------------------------------------------------------------------------------
        #This section check if there is an existing error report. If there is then deletes it.

        f = "ICIS_Parcel_1_download_files_Error_Report.txt"#error report file name

        error_report_full_path = os.path.join(reports_dir, f)#full file name for error report including full path

        if os.path.exists(error_report_full_path):#if there is an existing error report

            try:
                
                os.unlink(error_report_full_path)#delete the file 

            except (IOError,WindowsError) ,e :#if the file didn't write 

                log_string = 'Could not delete the old report file ' + error_report_full_path
                
                logger.logMessageString(log_string)

        #-----------------------------------------------------------------------------------
        if sql_err_message_new != "" or err_message != "" or ftplib_err_message != "":

            try:#open and write the report file 
                new_line = sql_err_message_new + '\n' + ftplib_err_message + '\n' + err_message + '\n'#set the new line for the report
                updated_files_file = str(error_report_full_path)#set the file with full path as a string
                updated_files_file_csv = open(updated_files_file, "a")#open the output file for writing
                updated_files_file_csv.writelines(new_line)#write the new line to the report
                updated_files_file_csv.close()#close the report file
                
                Status = 'Process Error'
                feature.setAttribute('Status', Status)#give the object an attribute
                self.pyoutput(feature)#this outputs the FME object back to workspace
                
            except (IOError,WindowsError) ,e :#if the file didn't write 

                log_string = 'Could create new report file ' + error_report_full_path
                
                logger.logMessageString(log_string)
    
        else:
            Status = 'Success'
            feature.setAttribute('Status', Status)#give the object an attribute
            self.pyoutput(feature)#this outputs the FME object back to workspace
         
    
    def close(self):
        pass
