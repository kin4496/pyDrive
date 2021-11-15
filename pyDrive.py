from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
import queue
import datetime
import os
import io

class pyDirve:
    
    def __init__(self):
        self.creds=None
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.service=None
        self.canAccess=False
        self.get_access_drive()

    def get_access_drive(self):
        try:
            if(os.path.isfile('token.json')):
                self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            self.service = build('drive', 'v3', credentials=self.creds)
            self.canAccess=True
            print('Success on access drive')
        except:
            print('Error in credentials.json')
        
    def sync_with_drive(self):
        if not self.canAccess:
            print('Get access first!')
            return;

        time=self.get_latest_synctime()
        if not time:
            time=datetime.datetime.fromtimestamp(0)
        utc_time=time.replace(tzinfo=datetime.timezone.utc)

        files=self.get_file_id(utc_time)
        self.download_files(files)

        time=datetime.datetime.now()
        self.write_sync_time(time.replace(tzinfo=datetime.timezone.utc))
        print('sync with drive at '+time.strftime('%Y-%m-%dT%H:%M:%S'))

    def get_latest_synctime(self):
        if os.path.isfile('time.txt'):
            with open('time.txt',mode='r') as f:
                time=f.read();
                time=float(time);
                f.close()
                return datetime.datetime.fromtimestamp(time);
        return None;

    def write_sync_time(self,utc_time):
        with open('time.txt',mode='w') as f:
            f.write(str(utc_time.timestamp()))
            f.close()
    def get_file_id(self,utc_time):
        response = self.service.files().list(
        q="mimeType = 'application/vnd.google-apps.folder' and name='GoodNotes' ",
        pageSize=1).execute()
        
        goodNotes=response.get('files',[])[0]
        files=[]
        
        q=queue.Queue()
        q.put(goodNotes)

        time=utc_time.strftime('%Y-%m-%dT%H:%M:%S')

        while not q.empty():
            front=q.get()
            id=front['id']
            nextPageToken=True
            
            query="parents in '"+id+"' and (mimeType = 'application/vnd.google-apps.folder' or modifiedTime > '"+time+"' )"
            while nextPageToken:
                response=self.service.files().list(q=query).execute()
                arr=response.get('files',[])
                for ele in arr:
                    if ele['mimeType'] == 'application/vnd.google-apps.folder':
                        q.put(ele)
                    else:
                        files.append(ele)
                        
                nextPageToken=response.get('nextPageToken')
        return files;
    
    def download_files(self,files):
        if not os.path.isdir('GoodNotes'):
            os.mkdir('GoodNotes')
        for file in files:
            request=self.service.files().get_media(fileId=file['id'])
            fh=io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            fh.seek(0)
            done=False
            while done is False:
                status, done = downloader.next_chunk()
                with open('GoodNotes/'+file['name'],mode='wb') as f:
                    f.write(fh.read())
                    f.close()
            print('download '+file['name'])

        




    
