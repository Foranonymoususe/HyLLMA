import os
import json
import io
import random
import sys
import traceback
import argparse
from urllib.parse import urlparse
from scapy.all import *
from scapy.utils import PcapWriter

try:
    import pybase64 as base64
except:
    print("couldn't import pybase64 falling back to normal base64")
    import base64


def build_handshake(pktdump, src, dst, sport, dport):
    client_isn = random.randint(1024, 10000)
    server_isn = random.randint(1024, 10000)
    syn = IP(src=src, dst=dst) / TCP(flags="S", sport=sport, dport=dport, seq=client_isn)
    synack = IP(src=dst, dst=src) / TCP(flags="SA", sport=dport, dport=sport, seq=server_isn, ack=syn.seq + 1)
    ack = IP(src=src, dst=dst) / TCP(flags="A", sport=sport, dport=dport, seq=syn.seq + 1, ack=synack.seq + 1)
    pktdump.write(syn)
    pktdump.write(synack)
    pktdump.write(ack)
    return (ack.seq, ack.ack)


def build_finshake(pktdump, src, dst, sport, dport, seq, ack):
    finAck = IP(src=src, dst=dst) / TCP(flags="FA", sport=sport, dport=dport, seq=seq, ack=ack)
    finalAck = IP(src=dst, dst=src) / TCP(flags="A", sport=dport, dport=sport, seq=finAck.ack, ack=finAck.seq + 1)
    pktdump.write(finAck)
    pktdump.write(finalAck)


def chunkstring(string, length):
    return (string[0 + i: length + i] for i in range(0, len(string), length))


def make_poop(pktdump, src, dst, sport, dport, seq, ack, payload):
    segments = []
    if len(payload) > 1460:
        segments = chunkstring(payload, 1460)
    else:
        segments.append(payload)
    for segment in segments:
        p = IP(src=src, dst=dst) / TCP(flags="PA", sport=sport, dport=dport, seq=seq, ack=ack) / segment
        returnAck = IP(src=dst, dst=src) / TCP(flags="A", sport=dport, dport=sport, seq=p.ack, ack=(p.seq + len(p[Raw])))
        seq = returnAck.ack
        ack = returnAck.seq
        pktdump.write(p)
        pktdump.write(returnAck)
    return (returnAck.seq, returnAck.ack)


def process_har_file(input_file, output_pcap):
    with io.open(input_file, encoding="utf-8") as fh:
        try:
            har_data = json.load(fh)
            json_str = json.dumps(har_data)
            json_str.encode("utf-8")
        except Exception as e:
            print("failed to jsonload the HAR file {0}".format(e))
            sys.exit(1)

    pktdump = PcapWriter(output_pcap, sync=True)
    pages = har_data.get("log", {}).get("entries", [])
    for entry in pages:
        try:
            sport = random.randint(1024, 65535)
            parts = None
            dport = 80
            path = "/"
            src = "192.168.1.100"
            dst = entry.get("serverIPAddress", "192.0.2.1")
            url = entry.get("request", {}).get("url", "")
            reqmethod = entry.get("request", {}).get("method", "GET")
            if reqmethod == "CONNECT":
                continue
            reqversion = entry.get("request", {}).get("httpVersion", "HTTP/1.1")
            if reqversion in ["h2", "h2c"]:
                reqversion = "HTTP/1.1"
            reqbody = entry.get("request", {}).get("postData", {}).get("text", "")
            if not reqbody:
                reqbody = entry.get("request", {}).get("PostData", {}).get("text", "")
            stat_code = entry.get("response", {}).get("status", -1)
            if url:
                try:
                    parts = urlparse(url)
                    if parts:
                        port = parts.port
                        if not port:
                            scheme = parts.scheme
                            if scheme == "http":
                                dport = 80
                            elif scheme == "https":
                                dport = 443
                        if parts.path:
                            path = parts.path

                        if parts.query:
                            path = path + "?" + parts.query

                except Exception as e:
                    print("failed to parse url {0}".format(e))
                    pass
            req = b""
            resp = b""
            req = "{0} {1} {2}\r\n".format(reqmethod, path, reqversion)
            headers_arr = entry.get("request", {}).get("headers")
            if headers_arr:
                for header in headers_arr:
                    hname = header.get("name", "")
                    if hname and hname not in [":method", ":scheme", ":path", ":authority"]:
                        req = req + hname
                        value = header.get("value", "")
                        if value:
                            if hname.lower() == "content-length":
                                if reqbody:
                                    value = len(reqbody)
                            req = req + ": {0}".format(value)
                        req = req + "\r\n"
                req = req + "\r\n"
            else:
                req = req + "\r\n\r\n"
            if reqbody:
                req = req + reqbody
            req = req.encode("utf-8")
            if entry.get("response", {}):
                body = ""
                respversion = entry.get("response", {}).get("httpVersion", "HTTP/1.1")
                if respversion in ["h2", "h2c"]:
                    respversion = "HTTP/1.1"
                respstatus = entry.get("response", {}).get("status", None)
                respstattxt = entry.get("response", {}).get("statusText", "")
                if entry.get("response", {}).get("content", {}).get("encoding", "") == "base64":
                    body = base64.b64decode(entry.get("response", {}).get("content", {}).get("text", ""))
                else:
                    body = entry.get("response", {}).get("content", {}).get("text", "")
                if not isinstance(body, bytes):
                    body = body.encode("utf-8")
                if respversion and respstatus:
                    resp = "{0} {1} {2}\r\n".format(respversion, respstatus, respstattxt)
                    headers_arr = entry.get("response", {}).get("headers")
                    if headers_arr:
                        for header in headers_arr:
                            hname = header.get("name", "")
                            if hname:
                                if hname.lower() == "x-twinwave-remote-server-ip":
                                    if header.get("value", ""):
                                        dst = header.get("value")
                                if hname.lower() == "x-twinwave-remote-server-port":
                                    if header.get("value", ""):
                                        dport = int(header.get("value"))
                                if hname.lower() == "transfer-encoding" and body:
                                    if body:
                                        resp = resp + "Content-Length"
                                        value = len(body)
                                        resp = resp + ": {0}".format(value)
                                elif hname.lower() not in ["content-encoding", ":status"]:
                                    resp = resp + hname
                                    value = header.get("value", "")
                                    if value:
                                        if hname.lower() == "content-length":
                                            if body:
                                                value = len(body)
                                        resp = resp + ": {0}".format(value)
                                resp = resp + "\r\n"
                    resp = resp + "\r\n"
                    resp = resp.encode("utf-8")
                    resp = resp + body
            (seq, ack) = build_handshake(pktdump, src, dst, sport, dport)
            if req:
                (seq, ack) = make_poop(pktdump, src, dst, sport, dport, seq, ack, req)
            if resp:
                (seq, ack) = make_poop(pktdump, dst, src, dport, sport, seq, ack, resp)
            build_finshake(pktdump, src, dst, sport, dport, seq, ack)
        except Exception as e:
            print("Failed to handle session skipping {0}".format(e))
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)
    pktdump.close()


def main(input_folder, output_folder_base):
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.har'):
                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, input_folder)
                output_folder = os.path.join(output_folder_base, relative_path)
                
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                
                output_pcap = os.path.join(output_folder, file.replace('.har', '.pcap'))
                process_har_file(input_file, output_pcap)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="har2pcap batch processing")
    parser.add_argument("input_folder", help="Path to the folder containing HAR files")
    parser.add_argument("output_folder_base", help="Base path for the output PCAP files")
    args = parser.parse_args()

    if not os.path.exists(args.input_folder):
        print(f"Folder {args.input_folder} does not exist")
        sys.exit(1)

    main(args.input_folder, args.output_folder_base)