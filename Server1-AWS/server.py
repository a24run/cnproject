import socket,os,sys,json,base64,threading,requests,threading,time,ssl
from threading import Thread
from PIL import Image
from priceinfo import ServerPrices
import arun_pb2
import cStringIO
s=socket.socket();
port = 21610
host = socket.gethostname();                       
print host;
# sys.argv[1] == List of server , sys.argv[2]= Encrypted communication ,, sys.argv[3]="protobuf or json " sys.arg[4]="precompute" or dynamic 
#Thread Kill
dead=False
#download speeds
low=20
low_resize_width=0.5
medium=40
medium_resize_width=0.7
#creating Folder
cwd=os.getcwd();
filesFolder=cwd+"/files"
if (os.path.isdir(filesFolder) is False):
    os.mkdir("files")


# send data to each server 
def sendToIndividualserver(host,port,JsonOfFile):
    try:
        new_socket=socket.socket();
        new_socket.connect((host,int(port)))
        JsonOfFile['isdist']=False
        #{"sz": 10,"isdist": true,"filecontent": "c2FtcGxlZmlsZQ==","filename": "sample.txt"}
        if(sys.argv[3]=="json"):
            serverCommunication={"isdist":JsonOfFile['isdist'],"filename":JsonOfFile['filename'],"sz":JsonOfFile['sz'],"filecontent":JsonOfFile['filecontent']}
            jsonServerhead=json.dumps(serverCommunication);
            new_socket.send(jsonServerhead)
        elif(sys.argv[3]=="protobuf"):
            print("in protobuf")
            protobufData=arun_pb2.clientUpload()
            protobufData.sz=JsonOfFile['sz']
            protobufData.isdist=False
            print("in protobuf")
            protobufData.filename=JsonOfFile['filename']
            protobufData.filecontent=JsonOfFile['filecontent']
            print("in protobuf")
            #print(protobufData.SerializeToString())
            new_socket.send(protobufData.SerializeToString())
        print "Done Sending"
        new_socket.close();
    except Exception:
        print("Other Servers",host, port ,"Down")
# Send to ALL servers 
def sendToAllServers(JsonOfFile):
    list_ofServers=sys.argv[1];
    with open(sys.argv[1]) as i:
        data=json.load(i)
    for x in range(0,len(data['AllAddresses'])):
        sendToIndividualserver(data['AllAddresses'][x]['host'],data['AllAddresses'][x]['port'],JsonOfFile);
# Creating Server Objects And Storing in array 
def CreateServerObjects():
    ServerArray=[]
    with open(sys.argv[1]) as i:
        data_price=json.load(i)
    presentServer=ServerPrices('18.221.59.87',port,"AWS");               #Present Server
    for x in range(0,len(data_price['AllAddresses'])):
        print(data_price['AllAddresses'][x]['provider'])
        temp=ServerPrices(data_price['AllAddresses'][x]['host'],data_price['AllAddresses'][x]['port'],data_price['AllAddresses'][x]['provider']);
        ServerArray.append(temp)
    ServerArray.append(presentServer);
    return ServerArray
def heartBeat(heartStop):
    if not heartStop.is_set():
        #heartBeat();
        #threading.Timer(3.0, heartBeat).start()
        for each in list_of_servers_with_price:
            if(each.port!=port):
                heartBeat_socket=socket.socket();
                try:
                    heartBeat_socket.connect((each.host,int(each.port)))
                    heartBeat_socket.send(json.dumps({"ServerCommunication":"heartBeat","heartBeat":"alive","host":"18.221.59.87","port":str(port)}));        #Present Server
                    heartBeat_socket.close();
                except:
                    #print("server down",each.port)
                    each.alive=False
        threading.Timer(3, heartBeat, [heartStop]).start()

def VerifyingHeartBeats(verifystop):
    #threading.Timer(5.0, VerifyingHeartBeats).start()
    if not verifystop.is_set():
        for each in list_of_servers_with_price:
            if(each.port!=port):
                #print(time.time()-each.time);
                each.alive=True;
                if(time.time()-each.time>3):
                    each.alive=False;
                print("Alive--",each.alive,each.host,each.port)
        threading.Timer(5, VerifyingHeartBeats, [verifystop]).start()


def returnNotMatches(a, b):
    return [x for x in a if x not in b]
def StartupCalls():
    index_of_least_price=0;
    for x in range (0,len(list_of_servers_with_price)):
        if(list_of_servers_with_price[x].port!=port and list_of_servers_with_price[x].alive==True):
            #min=list_of_servers_with_price[x].price
            index_of_least_price=x;
            try:
                if(sys.argv[2]=="encrypt"):
                    socketStartupRequest=socket.socket()
                    ssl_sock = ssl.wrap_socket(socketStartupRequest,ca_certs="selfsigned.crt",cert_reqs=ssl.CERT_REQUIRED,ssl_version=ssl.PROTOCOL_TLSv1)
                    #print("least price is ",list_of_servers_with_price[index_of_least_price].port,list_of_servers_with_price[index_of_least_price].price);
                    ssl_sock.connect((list_of_servers_with_price[index_of_least_price].host,6666))
                    variable=""
                    variable=json.dumps({"ServerCommunication":"ServerStartupRequest"})
                    ssl_sock.send(variable);
                    ssl_sock.send("\n\n")
                    dataReceived=""
                    while True:
                        data=ssl_sock.recv(1024)
                        #print(str(data));
                        if(data!=""):
                            print('data being received',data);
                            dataReceived+=data;
                            if("\n\n" in dataReceived):
                                dataReceived.replace("\n\n","")
                                break;
                        else:
                            break;
                    print(dataReceived)
                    dataInJsonFormat=json.loads(dataReceived)
                    print(dataInJsonFormat)
                    files_to_get=returnNotMatches(dataInJsonFormat['listOfFiles'],os.listdir(filesFolder))
                    print("files to get ",files_to_get);
                    socketFilesRequest=socket.socket()
                    ssl_sock_Files = ssl.wrap_socket(socketFilesRequest,ca_certs="selfsigned.crt",cert_reqs=ssl.CERT_REQUIRED,ssl_version=ssl.PROTOCOL_TLSv1)
                    ssl_sock_Files.connect((list_of_servers_with_price[index_of_least_price].host,6666))
                    ssl_sock_Files.send(json.dumps({"ServerCommunication":"ServerStartup/files","listOfFiles":files_to_get}))
                    #socketStartupRequest.send(json.dumps({"listOfFiles":files_to_get}))
                    ssl_sock_Files.send("\n\n")
                    FilesdataReceived="";
                    while True:
                        filesData=ssl_sock_Files.recv(1024)
                        #print(str(data));
                        #print('each',filesData)
                        if(filesData!=""):
                            FilesdataReceived+=filesData;
                            #print("in if ",FilesdataReceived)
                            if("\n\n" in FilesdataReceived):
                                FilesdataReceived.replace("\n\n","");
                                break;
                        else:
                            #print("in else ",FilesdataReceived)
                            break;
                    print("FilesdataReceived",FilesdataReceived)
                    FilesDataJson=json.loads(FilesdataReceived)
                    #print(FilesDataJson)
                    for x in range(0,len(FilesDataJson['Files'])):
                        JsonData=FilesDataJson['Files'][x]
                        f = open(JsonData['Name'],'wb')
                        f.write(base64.b64decode(JsonData['data']))
                        f.close()
                        if(sys.argv[4]=="precompute"):
                            fileName=JsonData['Name']
                            img = Image.open(fileName)
                            lowHeight = int((float(img.size[1])*float(low_resize_width)))
                            img = img.resize((int(img.size[0]*0.3),lowHeight), Image.ANTIALIAS)
                            lowFile='low'+fileName;
                            img.save(lowFile)
                            medumHeight=int((float(img.size[1])*float(medium_resize_width)))
                            img = img.resize((int(img.size[0]*0.5),medumHeight), Image.ANTIALIAS)
                            mediumFile=('medium'+fileName)
                            img.save(mediumFile)
                            os.rename(cwd+"/"+lowFile, filesFolder+"/"+lowFile)
                            os.rename(cwd+"/"+mediumFile, filesFolder+"/"+mediumFile)
                        os.rename(cwd+"/"+JsonData['Name'], filesFolder+"/"+JsonData['Name'])
                elif(sys.argv[2]=="nonencrypt"):
                    socketStartupRequest=socket.socket()
                    #print("least price is ",list_of_servers_with_price[index_of_least_price].port,list_of_servers_with_price[index_of_least_price].price);
                    socketStartupRequest.connect((list_of_servers_with_price[index_of_least_price].host,int((list_of_servers_with_price[index_of_least_price].port))))
                    variable=""
                    variable=json.dumps({"ServerCommunication":"ServerStartupRequest"})
                    socketStartupRequest.send(variable);
                    socketStartupRequest.send("\n\n")
                    dataReceived=""
                    while True:
                        data=socketStartupRequest.recv(1024)
                        #print(str(data));
                        if(data!=""):
                            print('data being received',data);
                            dataReceived+=data;
                            if("\n\n" in dataReceived):
                                dataReceived.replace("\n\n","")
                                break;
                        else:
                            break;
                    print(dataReceived)
                    dataInJsonFormat=json.loads(dataReceived)
                    print(dataInJsonFormat)
                    files_to_get=returnNotMatches(dataInJsonFormat['listOfFiles'],os.listdir(filesFolder))
                    print("files to get ",files_to_get);
                    socketFilesRequest=socket.socket()
                    socketFilesRequest.connect((list_of_servers_with_price[index_of_least_price].host,int((list_of_servers_with_price[index_of_least_price].port))))
                    socketFilesRequest.send(json.dumps({"ServerCommunication":"ServerStartup/files","listOfFiles":files_to_get}))
                    #socketStartupRequest.send(json.dumps({"listOfFiles":files_to_get}))
                    socketFilesRequest.send("\n\n")
                    FilesdataReceived="";
                    while True:
                        filesData=socketFilesRequest.recv(1024)
                        #print(str(data));
                        #print('each',filesData)
                        if(filesData!=""):
                            FilesdataReceived+=filesData;
                            #print("in if ",FilesdataReceived)
                            if("\n\n" in FilesdataReceived):
                                FilesdataReceived.replace("\n\n","");
                                break;
                        else:
                            #print("in else ",FilesdataReceived)
                            break;
                    print("FilesdataReceived",FilesdataReceived)
                    FilesDataJson=json.loads(FilesdataReceived)
                    #print(FilesDataJson)
                    for x in range(0,len(FilesDataJson['Files'])):
                        JsonData=FilesDataJson['Files'][x]
                        f = open(JsonData['Name'],'wb')
                        f.write(base64.b64decode(JsonData['data']))
                        f.close()
                        if(sys.argv[4]=="precompute"):
                            fileName=JsonData['Name']
                            img = Image.open(fileName)
                            lowHeight = int((float(img.size[1])*float(low_resize_width)))
                            img = img.resize((int(img.size[0]*0.3),lowHeight), Image.ANTIALIAS)
                            lowFile='low'+fileName;
                            img.save(lowFile)
                            medumHeight=int((float(img.size[1])*float(medium_resize_width)))
                            img = img.resize((int(img.size[0]*0.5),medumHeight), Image.ANTIALIAS)
                            mediumFile=('medium'+fileName)
                            img.save(mediumFile)
                            os.rename(cwd+"/"+lowFile, filesFolder+"/"+lowFile)
                            os.rename(cwd+"/"+mediumFile, filesFolder+"/"+mediumFile)
                        os.rename(cwd+"/"+JsonData['Name'], filesFolder+"/"+JsonData['Name'])
            except socket.error,msg:
                print("Server Down",msg[0]);
def CreateResizedFiles(fileName,fileContent):
    #basewidth = 500
    img = Image.open(fileName)
    # with open('bigFile.jpg', "rb") as imageFile:
    #     print(imageFile.read()==Image.ANTIALIAS)
    #     imageFile.close()
    #print(Image.ANTIALIAS)
    #wpercent = (basewidth/float(img.size[0]))
    lowHeight = int((float(img.size[1])*float(low_resize_width)))
    img = img.resize((float(img.size[0])*0.5,lowHeight), Image.ANTIALIAS)
    lowFile='low'+fileName;
    img.save(lowFile)
    medumHeight=int((float(img.size[1])*float(low_resize_width)))
    img = img.resize((float(img.size[0])*0.7,medumHeight), Image.ANTIALIAS)
    mediumFile=('medium'+fileName)
    img.save(mediumFile)
    os.rename(cwd+"/"+lowFile, filesFolder+"/"+lowFile)
    os.rename(cwd+"/"+mediumFile, filesFolder+"/"+mediumFile)
try:
    s.bind((host, port))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    #print("exiting Appliaction")
    sys.exit()
s.listen(8)

# Creating server Objects and assigning the Prices to server Obects 
list_of_servers_with_price=CreateServerObjects();
if(sys.argv[2]=="encrypt"):
    print("encrpyted")
# getting Data from server with least price 
StartupCalls();
heartStop=threading.Event()
verifystop=threading.Event()
heartBeat(heartStop)
VerifyingHeartBeats(verifystop)

# heart = Thread(target=heartBeat)
# heart.start();
# verifyHeart=Thread(target=VerifyingHeartBeats)
# verifyHeart.start()


while True:
    try:
        filename=""
        c, addr = s.accept()     # Establish connection with client.
        #print 'Got connection from', addr
        #print ("c is ",c)
        total_data=""
        while True:
            try:
                data=c.recv(1024)
                #print("yoyoyoyoyoyoy",data);
                if(data!=""):
                    total_data+=data;
                    if("\n\n" in data  or "\r\n\r\n" in data):
                        #print("in here ",total_data)
                        #print("\n\n" in total_data)
                        #print("\r\n\r\n" in total_data)
                        total_data.replace("\n\n","")
                        break;
                else:
                    break;
            except KeyboardInterrupt:
                print("exiting from Receiving Part");
                s.close();
                verifystop.set()
                heartStop.set()
                sys.exit();
        #print('HTTP' in total_data)
        total_data_json=""
        protobufData=""
        #print(total_data)
        if('HTTP/1.1' in total_data):
            total_data_json=""
            curlRequest=total_data.split('\n')
            print(curlRequest)
            typeAndUrl=curlRequest[0]
            valueOfUrl=curlRequest[len(curlRequest)-1]
            methodAndUrl=typeAndUrl.split(' ')
            TypeOfRequest=methodAndUrl[0]
            #print(total_data)
            Url=str(methodAndUrl[1])[1:]
            print(Url)
        else:
            Url=""
            if(sys.argv[3]=="json"):
                total_data_json=json.loads(total_data)
                #print(total_data_json)
            elif(sys.argv[3]=="protobuf"):
                try:
                    #print("total data is ",total_data)
                    protobufData=arun_pb2.clientUpload()
                    protobufData.ParseFromString(total_data)
                    total_data_json={"sz": protobufData.sz, "filecontent":protobufData.filecontent, "isdist": protobufData.isdist, "filename": protobufData.filename}
                    #print("protos",total_data_json);
                except:
                    #print("total data is ",total_data)
                    total_data_json=json.loads(total_data)
            else:
                print("not a proper input for type of serialization ")
                s.close();
                verifystop.set()
                heartStop.set()
                sys.exit();
            #print("data is ",total_data);
            
            #print('inital data is ',total_data_json);
        # GET and Set Server List
        if(Url=="getServerList"):
            c.send("HTTP/1.1 200 OK\nContent-Type: text/html\n\n");
            list_ofServers=sys.argv[1];
            with open(sys.argv[1]) as i:
                data=json.load(i)
            tempVariable=data['AllAddresses']
            Value_to_Send=''
            for x in range(0,len(tempVariable)):
                Value_to_Send+=("Host"+" :"+tempVariable[x]['host']+ "Port is  "+" :"+tempVariable[x]['port']+"\n");
            c.send(json.dumps(data));
            c.shutdown(socket.SHUT_RDWR);
            print("connection closed");
            c.close();
        elif(Url=="setServerList"):
            print valueOfUrl;
            file=open(sys.argv[1], "w")
            file.write(valueOfUrl)
            file.close();
            c.send("'HTTP/1.1 200 OK\nContent-Type: text/html\n\n'");
            c.send(valueOfUrl);
            c.shutdown(socket.SHUT_RDWR);
            print("connection closed");
            c.close();
            list_of_servers_with_price=CreateServerObjects();
        # Download Content
        elif("get/download" in Url):
            #print Url;
            UrlRequested=Url.split('/')
            if(len(UrlRequested)==4):
                fileRequested=UrlRequested[(len(UrlRequested)-2)]
                downloadSpeed=int(UrlRequested[(len(UrlRequested)-1)])
            else:
                fileRequested=UrlRequested[(len(UrlRequested)-1)]
                downloadSpeed=""
            print("speed is ",downloadSpeed)
            #print("folder structure",filesFolder)
            listOfFiles=os.listdir(filesFolder)
            #print("listOfFiles",listOfFiles)
            #print("file is ",fileRequested)
            #print(fileRequested in listOfFiles)
            if(fileRequested in listOfFiles):
                try:
                    print("downlaod speed is ",downloadSpeed)
                    if(downloadSpeed!="" and downloadSpeed<=low):
                        if(sys.argv[4]=="precompute"):
                            with open(filesFolder+'/'+"low"+fileRequested, "rb") as imageFile:
                                b64Data = base64.b64encode(imageFile.read())
                                c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                                c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                                c.send("Content-Type: image/png"+"\n")
                                fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                                c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                                c.send(fileJsonObject)
                                c.close();
                        elif(sys.argv[4]=="dynamic"):
                            img = Image.open(filesFolder+'/'+fileRequested)
                            lowHeight = int((float(img.size[1])*float(low_resize_width)))
                            img = img.resize((int((img.size[0])*0.5),lowHeight), Image.ANTIALIAS)
                            buffer = cStringIO.StringIO()
                            img.save(buffer, format="JPEG")
                            #print("image vlaue ",buffer.getvalue())
                            b64Data = base64.b64encode(buffer.getvalue())
                            c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                            c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                            c.send("Content-Type: image/png"+"\n")
                            fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                            c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                            c.send(fileJsonObject)
                            c.close();

                    elif(downloadSpeed!="" and downloadSpeed>low and downloadSpeed<=medium):
                        if(sys.argv[4]=="precompute"):
                            with open(filesFolder+'/'+"medium"+fileRequested, "rb") as imageFile:
                                b64Data = base64.b64encode(imageFile.read())
                                c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                                c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                                c.send("Content-Type: image/png"+"\n")
                                fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                                c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                                c.send(fileJsonObject)
                                c.close();
                        elif(sys.argv[4]=="dynamic"):
                            img = Image.open(filesFolder+'/'+fileRequested)
                            mediumHeight = int((float(img.size[1])*float(medium_resize_width)))
                            img = img.resize((int((img.size[0])*0.7),mediumHeight), Image.ANTIALIAS)
                            buffer = cStringIO.StringIO()
                            img.save(buffer, format="JPEG")
                            #print("image vlaue ",buffer.getvalue())
                            b64Data = base64.b64encode(buffer.getvalue())
                            c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                            c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                            c.send("Content-Type: image/png"+"\n")
                            fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                            c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                            c.send(fileJsonObject)
                            c.close();
                    elif(downloadSpeed!="" and downloadSpeed>medium):
                        if(sys.argv[4]=="precompute"):
                            with open(filesFolder+'/'+fileRequested, "rb") as imageFile:
                                b64Data = base64.b64encode(imageFile.read())
                                c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                                c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                                c.send("Content-Type: image/png"+"\n")
                                fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                                c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                                c.send(fileJsonObject)
                                c.close();
                        else:
                            with open(filesFolder+'/'+fileRequested, "rb") as imageFile:
                                b64Data = base64.b64encode(imageFile.read())
                                c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                                c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                                c.send("Content-Type: image/png"+"\n")
                                fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                                c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                                c.send(fileJsonObject)
                                c.close();
                    else:
                        with open(filesFolder+'/'+fileRequested, "rb") as imageFile:
                            b64Data = base64.b64encode(imageFile.read())
                            c.send('HTTP/1.1 '+str(200)+' OK '+'\n')
                            c.send("Accept-Ranges"+":"+ "bytes" +'\n')
                            c.send("Content-Type: image/png"+"\n")
                            fileJsonObject= json.dumps({"sz": len(b64Data),"filecontent": b64Data,"filename": fileRequested}) #base64.b64decode(b64Data)            
                            c.send("Content-Length:"+str(len(fileJsonObject))+'\n\n')
                            c.send(fileJsonObject)
                            c.close();
                except socket.error,msg:
                    print("Issue in file fetch"+ ' Message ' + msg[1])
                    c.send('HTTP/1.1 '+str(404)+' Not Found '+'\n\n')
                    c.send('BAD URL')
                    #print("Bad Request");
                    c.shutdown(socket.SHUT_RDWR);
                    c.close();
            else:
                c.send('HTTP/1.1 '+str(404)+' Not Found '+'\n\n')
                c.send('BAD URL')
                print("Bad Request");
                c.shutdown(socket.SHUT_RDWR);
                c.close();

        # Client Upload
        elif('isdist' in total_data_json):
            if(total_data_json['isdist']==True):
                print ("request from the client");
                f = open(total_data_json['filename'],'wb')
                f.write(base64.b64decode(total_data_json['filecontent']))
                f.close()
                print "Done Receiving"
                c.send('Thank you for connecting')
                c.close()
                sendToAllServers(total_data_json);
                #CreateResizedFiles(total_data_json['filename'],total_data_json['filecontent']);
                if(sys.argv[4]=="precompute"):
                    fileName=total_data_json['filename']
                    img = Image.open(fileName)
                    lowHeight = int((float(img.size[1])*float(low_resize_width)))
                    img = img.resize((int(img.size[0]*0.3),lowHeight), Image.ANTIALIAS)
                    lowFile='low'+fileName;
                    img.save(lowFile)
                    medumHeight=int((float(img.size[1])*float(medium_resize_width)))
                    img = img.resize((int(img.size[0]*0.5),medumHeight), Image.ANTIALIAS)
                    mediumFile=('medium'+fileName)
                    img.save(mediumFile)
                    os.rename(cwd+"/"+lowFile, filesFolder+"/"+lowFile)
                    os.rename(cwd+"/"+mediumFile, filesFolder+"/"+mediumFile)
                os.rename(cwd+"/"+total_data_json['filename'], filesFolder+"/"+total_data_json['filename'])
            elif(total_data_json['isdist']==False):
                print ("request from the Server");
                f = open(total_data_json['filename'],'wb')
                f.write(base64.b64decode(total_data_json['filecontent']))
                f.close()
                print "Done Receiving"
                c.send('Thank you for connecting')
                c.close()
                if(sys.argv[4]=="precompute"):
                    fileName=total_data_json['filename']
                    img = Image.open(fileName)
                    lowHeight = int((float(img.size[1])*float(low_resize_width)))
                    img = img.resize((int(img.size[0]*0.3),lowHeight), Image.ANTIALIAS)
                    lowFile='low'+fileName;
                    img.save(lowFile)
                    medumHeight=int((float(img.size[1])*float(medium_resize_width)))
                    img = img.resize((int(img.size[0]*0.5),medumHeight), Image.ANTIALIAS)
                    mediumFile=('medium'+fileName)
                    img.save(mediumFile)
                    os.rename(cwd+"/"+lowFile, filesFolder+"/"+lowFile)
                    os.rename(cwd+"/"+mediumFile, filesFolder+"/"+mediumFile)
                os.rename(cwd+"/"+total_data_json['filename'], filesFolder+"/"+total_data_json['filename'])
            else:
                c.close()
        elif('ServerCommunication' in total_data_json ):
            if(total_data_json['ServerCommunication']=='ServerStartupRequest'):
                objToSend=json.dumps({"listOfFiles":os.listdir(filesFolder)});
                #print("obj to send ",objToSend);
                #print("obj to send ",objToSend)
                c.send(objToSend);
                c.send("\n\n")
                c.close();
            elif(total_data_json['ServerCommunication']=='ServerStartup/files'):
                #print("value of url is",valueOfUrl);
                #postRequestInput=json.loads(valueOfUrl);
                #print(postRequestInput['listOfFiles'][0],postRequestInput['listOfFiles'][1])
                #c.send("HTTP/1.1 200 OK\nContent-Type: text/html\n\n");
                SendingDataArray=[]
                #print(len(total_data_json['listOfFiles']))
                for x in range(0,len(total_data_json['listOfFiles'])):
                    with open(filesFolder+'/'+total_data_json['listOfFiles'][x], "rb") as imageFile:
                        b64Data = base64.b64encode(imageFile.read())
                        SendingDataArray.append({"Type":"StartupFileSave","Name":total_data_json['listOfFiles'][x],"data":b64Data})
                #print(json.dumps({"Files":SendingDataArray}))
                c.send(json.dumps({"Files":SendingDataArray})) 
                c.send("\n\n") 
                #c.shutdown(socket.SHUT_RDWR);
                c.close()
                print("data Sent");
            elif(total_data_json['ServerCommunication']=="heartBeat"):
                #print(HeartBeatJson['host'],HeartBeatJson['port']);
                for each in list_of_servers_with_price:
                    #print("each",each.host,each.port,HeartBeatJson['port'])
                    if(each.host==total_data_json['host'] and each.port==total_data_json['port']):
                        each.time=time.time();
                        #print("update time is ",each.time)
                        c.close()
        elif("Type" in total_data_json):
            print("iin RTTTT")
            if(total_data_json["Type"]=="RoundTrip"):
                #print("RTT request")
                c.send(total_data)
                c.send("\n\n")
                #print("data sent")
                c.close();
                #print("connection closed");
        else:
            c.send('HTTP/1.1 '+str(404)+' Not Found'+'\n\n')
            c.send('BAD URL')
            print("Bad Request");
            c.shutdown(socket.SHUT_RDWR);
            c.close();
    except KeyboardInterrupt:
        print("exiting");
        s.close();
        verifystop.set()
        heartStop.set()
        sys.exit();
