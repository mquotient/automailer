import smtplib
from email.mime.text import MIMEText
import subprocess
import os
import pdb
from settings import *


class GTPPNotRunningError(Exception):
    
    def __init__(self):
        self.message = "Stack stopeed running in the system"

        
class AppNotRunningError(Exception):
    
    def __init__(self, msg=""):
        self.message = "Application stopped running in the system. " + msg


class PCPNotRunningError(Exception):
    
    def __init__(self, msg=""):
        self.message = "Partial CDR processing is not working properly. " + msg
        
        
class FileCollectionError(Exception):
    
    def __init__(self, msg=""):
        self.message = "Files are not getting collected. " + msg


class OutOfSpace(Exception):
    def __init__(self, msg=""):
        self.message = "File system is running out of space. " + msg


class FileSystemError(Exception):
    pass
        
        
def sendmail(to_address,
             message,
             host='localhost',
             from_address="CGWatcher@alcatelcg1",
             subject="CG Status",
             ):
    """
    Sends a single mail to the given mail id
    """
    msg = MIMEText(message)
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    try:
        s = smtplib.SMTP(host)
        s.sendmail(from_address, to_address, msg.as_string() + "\n\n---" + mail_foot_note)
        s.quit()
    except Exception as e:
        print e
            
            
def check_gtpp_running():
    if not process_running("gtpp"):
        raise GTPPNotRunningError()


def check_app_running():
    if not process_running("GTPInit2"):
        raise AppNotRunningError()


def process_running(process_name):
    """
    Checks if the process is running
    """
    p = subprocess.Popen(["pgrep", process_name], stdout=subprocess.PIPE)
    procees_id, error = p.communicate()
    return not error and procees_id


def check_collection(sgsn_path):
    """
    Checks the status of tmp, swp and dat files
    Raise alarm if
    1. There are too many tmp files
    2. If there are too many swp files
    3. If there are too many dat files
    """
    min_tmp = minimum_temp_files
    max_swp = maximum_swp_files  # Maximum number of swp files
    max_dat = maximum_dat_files  # Maximum number of data files
    file_count = lambda files, ext: len([f for f in files if os.path.splitext(f)[1] == ext])
    
    if os.path.exists(sgsn_path):
        files = [
                 f for f in os.listdir(sgsn_path) 
                 if os.path.isfile(os.path.join(sgsn_path, f))
                 ]
        tmp_count = file_count(files, '.tmp')
        swp_count = file_count(files, '.swp')
        dat_count = file_count(files, '.dat')
    
    if tmp_count < min_tmp:
        # App is not running
        raise AppNotRunningError("Number of tmp files are less than {}".format(min_tmp))
    
    if swp_count > max_swp:
        # PCP is not running properly
        raise PCPNotRunningError("Number of swp files are more than {}".format(max_swp))
    
    if dat_count > max_dat:
        raise FileCollectionError("Number of data files are more than {}".format(max_dat))


def check_space(root_dir, min_size=2):
    """
    Checks if there is enough space in the root directory
    The minimum size is 5 GB
    """
    fs = os.statvfs(root_dir)
    size_in_gb = fs.f_bavail * fs.f_frsize / 1024 / 1024
    if size_in_gb < min_size:
        raise OutOfSpace("{} has only {} GB left".format(root_dir, size_in_gb))


if __name__ == "__main__":

    try:
        # First check if the processes are running
        check_gtpp_running()
        check_app_running()
        
        # Now check if the files are gettign generated properly
        check_collection(sgsn_path)
        
        # Now check if there is enough space in the root dir
        check_space(root_dir)
    except (GTPPNotRunningError, AppNotRunningError, FileCollectionError, OutOfSpace, PCPNotRunningError) as e:
        for recepient in error_mailing_list:
            print "Mailing {}".format(recepient)
            sendmail(recepient, e.message, subject="CG Error")
    else:
        print "Everything is normal"
        for recepient in normal_mailing_list:
            print "Mailing {}".format(recepient)
            sendmail(recepient, "", subject="CG Running Normally")
