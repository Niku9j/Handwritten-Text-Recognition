#!/usr/bin/env python
# coding: utf-8

# In[5]:


import pymysql
import os
import io
import google.cloud
from google.cloud import vision
import pandas as pd
import logging
import boto3
from botocore.exceptions import ClientError
from fuzzywuzzy import fuzz


# In[6]:


s3=boto3.resource('s3')


# In[7]:


jsonBucket='ocrevs'
jsonKEY='OCRMailRoom-b3cfc7245bdd.json'

try:
    s3.Bucket(jsonBucket).download_file(jsonKEY, '/home/ec2-user/ocr/json/OCRMailRoomCred.json')
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise


# In[8]:


connection = pymysql.connect(host='ocrresearch.ckfhbvjrt7zo.us-west-2.rds.amazonaws.com',
                             user='root',
                             password='evs$1234',
                             db='ocr')


# In[9]:


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/ec2-user/ocr/json/OCRMailRoomCred.json'
os.environ['GOOGLE_CLOUD_PROJECT']='ocrmailroom-231609'


# In[28]:


text=[]


# ### Text Recognition

# In[11]:


def detect_document(path):
    """Detects document features in an image."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            #print('\nBlock confidence: {}\n'.format(block.confidence))
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    text.append(word_text.encode('utf-8'))
                    #print(word_text)


# In[12]:

emp_data = pd.read_sql('Select * from Employee_Information',con=connection)


# In[34]:


flist=os.listdir('/home/ec2-user/ocr/images/')

print(flist)

# In[36]:


def print_table(elements):
    table=""""""
    table+="""<table>\n<tr>\n<th width="30%">Name</th>\n<th width="70%">Email ID</th>\n</tr>"""
    for s in elements:
        table+="\n<tr>"
        for e in s:
            table+="\n<td>" + str(e) + "</td>"
        table+="\n</tr>"
    table+="\n</table>"
    return table


# In[27]:


def sendMails(RECIPIENT,BODY_TEXT,BODY_HTML):
    
    SENDER = "nikunj.jain@evalueserve.com"
    SUBJECT = "OCR Testing"
    AWS_REGION = "us-west-2"
    CHARSET = "UTF-8"
    
    client = boto3.client('ses',region_name=AWS_REGION)
        
    #Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                    'ToAddresses': [
                        RECIPIENT,
                        ],
                        },
            Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                    },
            Source=SENDER)
        #If you are not using a configuration set, comment or delete the
        #following line
        #ConfigurationSetName=CONFIGURATION_SET
        #Display an error if something goes wrong.
    
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:")
        print(response['MessageId'])
        #row+=1
        
#Initialize logger and set log level

logger = logging.getLogger()
logger.setLevel(logging.INFO)           


# In[15]:


def rec_details(eids):
        #print("In Rec_det")
        ADMIN = "nikunj.jain@evalueserve.com"
        mailList=[]
        b=[1,4]
        for row in emp_data.loc[emp_data['ID'].isin(eids)].iterrows():
            index, data = row
            mailList.append([list(data)[i] for i in b])
            
        if(len(mailList)==1):
            RECIPIENT = ADMIN
            BODY_TEXT = str('Hi ' + mailList[0][0] + "!\r\n" + " You've Got Mail")
            BODY_HTML = str("""<html>
            <head></head>
            <body>
              <p>Hi """ + mailList[0][0] + '!'"""</p>
              <p>You've Got Mail """ + mailList[0][1] + """</p>
            </body>
            </html>""")          
            sendMails(RECIPIENT,BODY_TEXT,BODY_HTML)
        elif(len(mailList)>1):
            RECIPIENT = ADMIN
            BODY_TEXT = str('Hi, ' "!\r\n" + "There are multiple recepients with same name.")
            BODY_HTML = str("""<html>
            <head>
            <style>
            table {
            font-family: arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
            }

            td, th {
            border: 1px solid #dddddd;
              text-align: left;
              padding: 8px;
            }

            tr:nth-child(even) {
              background-color: #dddddd;
            } 
            </style>
            </head>
            <body>
              <p>Hi, \nThere are multiple recepients with same name.""" + print_table(mailList) + """</p>
            </body>
            </html>""")          
            sendMails(RECIPIENT,BODY_TEXT,BODY_HTML)
        else:
            #print("Inside else")
            RECIPIENT = ADMIN
            BODY_TEXT = str('Hi,' +"!\r\n" + " No match found for the recepient.")
            BODY_HTML = str("""<html>
            <head></head>
            <body>
              <p>Hi,\nNo match found for the recepient.</p>
            </body>
            </html>""")          
            sendMails(RECIPIENT,BODY_TEXT,BODY_HTML)
        # Create a new SES resource and specify a region.
        


# In[23]:


def parse_text():
    flag=0
    names={}
    eids=[]
    for phn,eid in zip(emp_data['PHONE'],emp_data['ID']):
        if(flag!=0):
            break
        for p in text:
            if(str(phn).lower()==str(p).lower()):                          #Phone no is matched and no ambiguity
                eids.append(eid)
                flag=1

    if flag==0:
        for fname,lname,eid in zip(emp_data['FIRST_NAME'],emp_data['LAST_NAME'],emp_data['ID']):
            for f in text:
                if(str(fname).lower()==str(f).lower()):
                    names[eid]=0
                    for l in text:
                        if(str(lname).lower()==str(l).lower()):
                            names[eid]=1
                            break
    if len(names)==0 and flag==0:
        for fname,lname,eid in zip(emp_data['FIRST_NAME'],emp_data['LAST_NAME'],emp_data['ID']):
            for f in text:
                if(fuzz.ratio(str(fname).lower(),str(f).lower())>=80):
                #if(str(fname).lower()==str(f).lower()):
                    names[eid]=0
                    for l in text:
                        if(str(lname).lower()==str(l).lower()):
                            names[eid]=1
                            break

    if len(names)>0 and flag==0:
        if sum(names.values())==0 and len(names)==1: #Only First Name matched and no ambiguity
            eids=list(names.keys())
        elif sum(names.values())==1:                 #Both last name and first name matched and no ambiguity
            for ids,fg in names.items():
                if fg==1:
                    eids=list(names.keys())
                    break
        else:                                        #Multiple matches but not sure if first name/last name/both are matched
            eids=list(names.keys())
    del text[:]

    rec_details(eids)

for img in flist:
    detect_document('/home/ec2-user/ocr/images/'+img)
    print(text)
    for i in text:
        if len(i)==1:
            text.remove(i)
    parse_text()

