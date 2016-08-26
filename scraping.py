from __future__ import print_function
import httplib2
import os
import base64
import email
from apiclient import errors

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import sqlite3
try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()

    print ('Message snippet' + message['snippet'])

    return message
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)


def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    #print ('Message snippet: %s' % message['snippet'])

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mime_msg = email.message_from_string(msg_str)

    return mime_msg
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)

def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])
    
    return messages
  except errors.HttpError, error:
    print('An error occurred: %s' % error)

def parse_content(content):
    print(content['Subject'])
    print(content['From'])
    print(content['Date'])
    

def find_email_body(content):
    pass

def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    # if not labels:
    #     print('No labels found.')
    # else:
    #   print('Labels:')
    #   for label in labels:
    #     print(label['name'])
    messages = ListMessagesMatchingQuery(service, 'dj724530@gmail.com',query='')
    print(len(messages))
    conn = sqlite3.connect('congress_email.db')
    conn.text_factory = str
    c = conn.cursor()
    c.execute('''DROP TABLE emails''')
    # Create table
    c.execute('''CREATE TABLE emails
           (msg_id text, msg_from_name text, msg_from_email text, msg_subject text, msg_date text, msg_body text)''')

    f1 = open('./changgmail.txt','w+')
    count = 0
    for message in messages:
      #f1.write(message['id'] + '\n')
      count = count+1
      if (count % 100 ==0 ):
        print(count)
      
      #content = GetMimeMessage(service,'eeliuchang@gmail.com',message['id'])
      content = GetMimeMessage(service,'dj724530@gmail.com',message['id'])

      body = ""
      b = content

      if b.is_multipart():

      	for part in b.walk():
	        ctype = part.get_content_type()
	        cdispo = str(part.get('Content-Disposition'))

	        # skip any text/plain (txt) attachments
	        if ctype == 'text/plain' and 'attachment' not in cdispo:
	            body = part.get_payload(decode=True)  # decode
	            
	            break
      else:
	    body = b.get_payload(decode=True)

      # f1.write('Subject: ' + str(content['Subject'])+ '\n')
      # f1.write('From:name ' + str(email.utils.parseaddr(content['From'])[0])+ '\n')
      # f1.write('From:email ' + str(email.utils.parseaddr(content['From'])[1])+ '\n')
      # f1.write('Time: ' + str(content['Date'])+ '\n')	  
      # f1.write('Body: \n' + body)
      c.execute("INSERT INTO emails VALUES (?,?,?,?,?,?)",(message['id'],email.utils.parseaddr(content['From'])[0],email.utils.parseaddr(content['From'])[1],content['Subject'],content['Date'], body),)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()