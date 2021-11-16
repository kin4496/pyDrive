from utils import *

if __name__=='__main__':
    
    service=get_access_drive('credentials.json')
    set_file_path(r'C:\Users\aa823\Desktop\FIle')
    sync_with_drive(service,'GoodNotes')
