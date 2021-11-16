from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from unicodedata import normalize
import os
import datetime
import io


def get_access_drive(creds_name):
    creds=None
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    try:
        if(os.path.isfile('token.json')):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_name, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        service = build('drive', 'v3', credentials=creds)
        print('Success on access drive')
        return service;
    except:
        print('Error in credentials.json')
        return None;

def write_sync_time(utc_time,root):
    with open(root+'/time.txt',mode='w') as f:
        f.write(str(utc_time.timestamp()))
        f.close()

def get_latest_synctime(root):
    if os.path.isfile(root+'/time.txt'):
        with open(root+'/time.txt',mode='r') as f:
            time=f.read();
            time=float(time);
            f.close()
            return datetime.datetime.fromtimestamp(time);
    return datetime.datetime.fromtimestamp(0);

def sync_with_drive(service,root):
    if not service:
        print("Access Denied!")
        return;

    time=get_latest_synctime(root)
    utc_time=time.replace(tzinfo=datetime.timezone.utc)
    utc_time=utc_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    root_folder=find_root_folder(service,root)
    sync_under_the_folder(service,utc_time,root_folder)
    
    sync_time=datetime.datetime.now()
    write_sync_time(sync_time.replace(tzinfo=datetime.timezone.utc),root)
    print('sync with drive at '+sync_time.strftime('%Y-%m-%dT%H:%M:%S'))

def find_root_folder(service,root):
    response=service.files().list(
    q=f"mimeType = 'application/vnd.google-apps.folder' and name='{root}' ",
    pageSize=1).execute()
    
    root_folder=response.get('files',[])[0]
    
    return root_folder;
    
def sync_under_the_folder(service,utc_time,folder):
    
    path=os.getcwd()
    if not os.path.isdir(folder['name']):
        os.mkdir(folder['name'])
    os.chdir(path+"/"+folder['name'])
    
    query="parents in '"+folder['id']+"' and (mimeType = 'application/vnd.google-apps.folder' or modifiedTime > '"+utc_time+"' )"
    page_token=None
    
    while True:
        response=service.files().list(q=query,pageSize=40,pageToken=page_token).execute()
        files=response.get('files',[])
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                sync_under_the_folder(service,utc_time,file)
            else:
                download_file(service,file)
        page_token=response.get('nextPageToken',None)
        if page_token is None:
            break
    os.chdir('..')

def set_file_path(path):
        os.chdir(path)

def correct_file_name(dirname,filename):
    before_filename = os.path.join(dirname, filename)
    after_filename = normalize('NFC', before_filename)
    os.rename(before_filename, after_filename)

def download_file(service,file):
    request=service.files().get_media(fileId=file['id'])
    fh=io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done=False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    with open(file['name'],mode='wb') as f:
        f.write(fh.read())
        f.close()
    correct_file_name(os.getcwd(),file['name'])
    print('download '+file['name'])