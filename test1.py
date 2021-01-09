from scapy.all import Packet
from scapy.fields import ByteField, XByteField

import libscrc
import sys
import serial
import time
import threading

import serial.tools.list_ports
from datetime import datetime




class Mavlink:
    name = "Mavlink "
    fields_desc = [
        XByteField("STX", 0xFE),
        ByteField("LEN", 255),
        ByteField("SEQ", 255),
        ByteField("SYS", 255),
        ByteField("COMP", 255),
        ByteField("MSG", 255),
        ByteField("PAYLOAD", 255),
        ByteField("CKA", 255),
        ByteField("CKB", 255)]
    seq = 1

    # def __init__(self):
    #     self.name = "Mavlink"

    def setMsg(self, msg):
        self.fields_desc[5] = msg.encode()


    def getMsg(self,data):
        print("提取"+data+"类型的数据包，演示使用请求数据流消息包的结构")

    def setStx(self, stx):
        self.fields_desc[0] = stx.encode()
        print(" 设定版本号，目前版本是1.0", stx)

    def setLen(self, len):
        self.fields_desc[1] = len.encode()
        print("设定该消息类型的预留长度", len)

    def setSys(self, sys):
        self.fields_desc[3] = sys.encode()
        print("系统中提取sys，这里按照模拟数据填入", sys)

    def setCom(self, com):
        self.fields_desc[4] = com.encode()
        print("系统中提取com，这里按模拟试数据填入", com)

    def setPayload(self, payload):
        p = ""
        for i in payload:
            p = p + i
        self.fields_desc[6] = p.encode()
        print(" 填充消息包，这里按照模拟数据填入", p)

    def setMavlinkCk(self, ck):
        self.fields_desc[7] = str(hex(ck[0]))[2:4].encode()
        self.fields_desc[8] = str(hex(ck[1]))[2:4].encode()
        print("1.8.1 填充cka，计算结果填入", ck[0])
        print("1.8.2 填充ckb，计算结果填入", ck[1])

    def setMavlinkSeq(self, seq):
        if seq < 16:
            r = str(hex(seq)).encode()[2:]
            r = b'0' + r
        else:
            r = str(hex(seq)).encode()[2:]
        self.fields_desc[2] = r
        print("填充seq，计算结果填入", r)

    def computeCk(self, data):
        print("计算校验值，使用有效负载，以及心跳包的额外值进行计算")
        data1 = ''
        for i in data:
            data1 = data1 + i
        data1 = data1.encode()
        print(data1)
        result = libscrc.xmodem(data1)
        print("计算校验值高8位")
        cka = int(bin(result)[2:10], 2)
        print("计算校验值低8位")
        ckb = int(bin(result)[11:18], 2)
        return [cka, ckb]

    def computeSeq(self):
        print(" 计算seq")
        if Mavlink.seq >= 255:
            Mavlink.seq = 0
        else:
            Mavlink.seq = Mavlink.seq + 1
            print("小于255，加1")
        return Mavlink.seq

port_list = list(serial.tools.list_ports.comports())
port_list_name = []

class SerialPort:
    def __init__(self, port, buand):
        self.port = serial.Serial(port, buand)
        self.port.close()
        if not self.port.isOpen():
            self.port.open()

    def port_open(self):
        if not self.port.isOpen():
            self.port.open()

    def port_close(self):
        self.port.close()

    def send_data(self, data):
        # while True:
        #    self.port.write(data)
        #    print("发送",data)
        #    time.sleep(1)
        self.port.write(data)
        print("发送", data)
        time.sleep(1)



def makeMessage(data):
    p1 = Mavlink()
    p1.setMsg(data[5])
    p1.setStx(data[0])
    p1.setLen(data[1])
    p1.setSys(data[3])
    p1.setCom(data[4])
    p1.setPayload(data[6:15])
    ck = p1.computeCk(data[6:15])
    p1.setMavlinkCk(ck)
    p1.setMavlinkSeq(p1.seq)
    return p1


def show_all_com():
    if len(port_list) <= 0:
        print("the serial port can't find!")
    else:
        for itms in port_list:
            port_list_name.append(itms.device)


class myThreadwrite(threading.Thread):
    def __init__(self, data, ser):
        threading.Thread.__init__(self)
        self.data = data
        self.ser = ser

    def run(self):
        self.ser.send_data(self.data)


if __name__ == "__main__":
    baunRate = 115200

    print("1.显示所有端口")
    show_all_com()
    print(port_list_name)

    print("2.打开写入消息的端口 ", port_list_name[0])
    serialPort_w = port_list_name[0]
    mSerial_w = SerialPort(serialPort_w, baunRate)

    print("3.构建数据包")
    test1 = 'FE 06 70 FF BE 42 02 00 01 01 02 01 28 C1'

    test = test1.split(" ")
    data = makeMessage(test)
    d = b''
    for i in data.fields_desc:
        d = d + i

    print(d)
    print("4.启动写入消息的进程")
    t1 = myThreadwrite(d, mSerial_w)
    t1.setDaemon(True)
    t1.start()
