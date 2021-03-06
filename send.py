from scapy.all import Packet
from scapy.fields import ByteField, XByteField

import libscrc
import sys
import serial
import time
import threading

import serial.tools.list_ports
from datetime import datetime


port_list = list(serial.tools.list_ports.comports())
port_list_name = []

class Mavlink:
    name = "Mavlink "
    fields_desc=[
        XByteField("STX",0xFE),
        ByteField("LEN", 255),
        ByteField("SEQ", 255),
        ByteField("SYS", 255),
        ByteField("COMP", 255),
        ByteField("MSG", 255),
        ByteField("PAYLOAD", 255),
        ByteField("CKA", 255),
        ByteField("CKB", 255)]
    seq = 0

    def __init__(self):
        self.name = "Mavlink"

    def setMsg(self,msg):
        self.fields_desc[5] = msg.encode()
        print("1.1 设定数据包的MSG",msg)

    def getMsg(self,data):
        print("1.2 提取"+data+"类型的数据包，演示使用心跳包的结构")

    def setStx(self,stx):
        self.fields_desc[0] = stx.encode()
        print("1.3 设定版本号，目前版本是1.0",stx)

    def setLen(self,len):
        self.fields_desc[1] = len.encode()
        print("1.4.1 设定该消息类型的预留长度，心跳包是9",len)
        print("1.4.2 写入数据类型的长度")

    def setSys(self,sys):
        self.fields_desc[3] = sys.encode()
        print("1.5 系统中提取sys，这里按照测试数据填入",sys)

    def setCom(self,com):
        self.fields_desc[4] = com.encode()
        print("1.6 系统中提取com，这里按照测试数据填入",com)

    def setPayload(self,payload):
        p = ""
        for i in payload:
            p = p+i
        self.fields_desc[6] = p.encode()
        print("1.7 填充消息包，这里按照测试数据填入",p)

    def setMavlinkCk(self,ck):
        self.fields_desc[7] = str(hex(ck[0]))[2:4].encode()
        self.fields_desc[8] = str(hex(ck[1]))[2:4].encode()
        print("1.8.1 填充cka，计算结果填入",ck[0])
        print("1.8.2 填充ckb，计算结果填入",ck[1])

    def setMavlinkSeq(self,seq):
        if seq<16:
            r = str(hex(seq)).encode()[2:]
            r = b'0'+r
        else:
        	r = str(hex(seq)).encode()[2:]
        self.fields_desc[2] = r
        print("填充seq，计算结果填入",r)

    def computeCk(self,data):
        print("计算校验值，使用有效负载，以及心跳包的额外值进行计算")
        data1 = ''
        for i in data:
        	data1 = data1+i
        data1 = data1.encode()
        print(data1)
        result = libscrc.xmodem(data1)
        print("计算校验值高8位",result)
        cka = int(bin(result)[2:10],2)
        #cka = hex(int(bin(result)[2:10],2))
        print("计算校验值低8位")
        #ckb = hex(int(bin(result)[11:18], 2))
        ckb = int(bin(result)[11:18], 2)
        return [cka,ckb]

    def computeSeq(self):
        print("1.9 计算seq")
        if Mavlink.seq >= 255:
            Mavlink.seq = 0
            print("大于等于255，从0计算")
        else:
            Mavlink.seq = Mavlink.seq+1
            print("小于255，加1")
        return Mavlink.seq

    def getStx(self,stx):
        print("检查协议版本")

    def getCk(self,ck,data):
        result = libscrc.xmodem(data)
        print("计算校验值高8位")
        cka = hex(int(bin(result)[2:10], 2))
        print("计算校验值低8位")
        ckb = hex(int(bin(result)[11:18], 2))
        print("校验结果，高8位，低8为分别为：",cka,"",ckb)

    def getLen(self,len):
        print("消息长度",len)

    def getLen(self,sys,com):
        print("系统编号", sys)
        print("组件编号", com)

    def getMsg(self,msg):
        print("message编号", msg)

    def getPlayload(self,payload):
        print("消息负载为",p.encode())

    def getcrc(self,cka,ckb):
        print("检查crc16校验值,高8位，低8位分别是",cka," ",ckb)

    def computeRight(self):
        print("检查结果是否正确")

    def send(self):
        print("发送完成")

    def receive(self):
        print("接受完成")



class SerialPort:
    def __init__(self,port,buand):
        self.port = serial.Serial(port,buand)
        self.port.close()
        if not self.port.isOpen():
            self.port.open()

    def port_open(self):
        if not self.port.isOpen():
            self.port.open()

    def port_close(self):
        self.port.close()

    def send_data(self,data):
        #while True:
        #    self.port.write(data)
        #    print("发送",data)
        #    time.sleep(1)
        self.port.write(data)
        print("发送",data)
        time.sleep(1)


    def read_data(self):
        while True:
            count = self.port.inWaiting()
            if count > 0:
                rec_str = self.port.read(count)
                print("receive:",rec_str.decode())



def makeMessage(data):

    p1 = Mavlink()
    #构建数据包
    #1.1设定msg
    p1.setMsg(data[5])
    p1.getMsg(data[5])
    p1.setStx(data[0])
    p1.setLen(data[1])
    p1.setSys(data[3])
    p1.setCom(data[4])
    p1.setPayload(data[6:15])
    ck = p1.computeCk(data[6:15])
    p1.setMavlinkCk(ck)
    seq = p1.computeSeq()
    p1.setMavlinkSeq(p1.seq)

    return p1


def show_all_com():
    if len(port_list) <= 0:
        print("the serial port can't find!")
    else:
        for itms in port_list:
            port_list_name.append(itms.device)


 
class myThreadwrite(threading.Thread):
    def __init__(self,data,ser):
        threading.Thread.__init__(self)
        self.data = data
        self.ser  = ser
    def run(self):                
        self.ser.send_data(self.data)
        


class myThreadread(threading.Thread):
    def __init__(self,ser):
        threading.Thread.__init__(self)
        self.ser  = ser
    def run(self):              
        self.ser.read_data()

if __name__ == "__main__":
    baunRate = 115200

    print("1.显示所有端口")
    show_all_com()
    print(port_list_name)

    print("2.打开写入消息的端口 ",port_list_name[2])
    serialPort_w = port_list_name[2]
    mSerial_w = SerialPort(serialPort_w,baunRate)


    print("3.构建数据包")
    test0 ='FE 09 18 01 01 00 00 00 00 00 02 03 51 03 03 CC 68'
    'FE09 10 10100000000000203510303228106'
    test = test0.split(" ")
    data = makeMessage(test)
    d = b''
    for i in data.fields_desc:
        d = d+i

    print(d)
    print("4.启动写入消息的进程")
    t1 = myThreadwrite(d,mSerial_w)
    t1.setDaemon(True)
    t1.start()

    #print("5.打开读取消息的端口",port_list_name[2])
    #serialPort_r = port_list_name[2]
    #mSerial_r = SerialPort(serialPort_r,baunRate)

    #print("6.启动读取消息的进程")
    #t2 = threading.Thread(target=mSerial_r.read_data)
    #t2 = myThreadread(mSerial_w)
    #t2.setDaemon(True)
    #t2.start()

    #do something else, make main thread alive there



