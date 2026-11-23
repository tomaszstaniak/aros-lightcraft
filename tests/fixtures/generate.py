#!/usr/bin/env python3
"""Generate original CC0 small RGB and CFA RAW fixtures; no downloaded media."""
import struct
import zlib
from pathlib import Path
import sys

def chunk(name, data):
    return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)

def png(w=320,h=240):
    rows=b''.join(b'\0'+bytes(c for x in range(w) for c in (20+x*180//w,30+y*170//h,70+(x+y)*100//(w+h))) for y in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,9))+chunk(b'IEND',b'')

def dng(w=64,h=48):
    """Uncompressed 16-bit RGGB mosaic, DNG 1.4, 12-bit white point."""
    tags={}
    def add(tag,kind,values):
        data=values if isinstance(values,bytes) else struct.pack('<'+{3:'H',4:'I'}[kind]*len(values),*values)
        unit={1:1,2:1,3:2,4:4,5:8,10:8}[kind]
        tags[tag]=(kind,len(data)//unit,data)
    add(254,4,[0]);add(256,4,[w]);add(257,4,[h]);add(258,3,[16]);add(259,3,[1]);add(262,3,[32803]);add(273,4,[0]);add(277,3,[1]);add(278,4,[h]);add(279,4,[w*h*2]);add(284,3,[1]);add(33421,3,[2,2]);add(33422,1,bytes([0,1,1,2]));add(50706,1,bytes([1,4,0,0]));add(50707,1,bytes([1,1,0,0]));add(50708,2,b'LightCraft Synthetic CC0\0');add(50714,4,[64]);add(50717,4,[4095]);add(50721,10,b''.join(struct.pack('<ii',int(i%4==0),1) for i in range(9)));add(50728,5,struct.pack('<IIIIII',1,1,1,1,1,1));add(50778,3,[21])
    offset=8+2+len(tags)*12+4;entries=[];extras=bytearray()
    for tag,(kind,count,data) in sorted(tags.items()):
        if tag==273:
            entries.append((tag,kind,count,None));continue
        if len(data)<=4:value=data.ljust(4,b'\0')
        else:
            value=struct.pack('<I',offset+len(extras));extras+=data
            if len(extras)%2:extras+=b'\0'
        entries.append((tag,kind,count,value))
    pixels=offset+len(extras)
    table=b''.join(struct.pack('<HHI',tag,kind,count)+(struct.pack('<I',pixels) if val is None else val) for tag,kind,count,val in entries)
    mosaic=bytearray()
    for y in range(h):
        for x in range(w):
            channel=((0,1),(1,2))[y%2][x%2]
            value=(300+x*2200//w,400+y*2000//h,700+(x+y)*1000//(w+h))[channel]
            mosaic+=struct.pack('<H',value)
    return b'II*\0'+struct.pack('<I',8)+struct.pack('<H',len(tags))+table+b'\0'*4+extras+mosaic

if __name__=='__main__':
    dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=True)
    for name in ['sample.png','My Photo.png','zażółć.png']:(dest/name).write_bytes(png())
    (dest/'synthetic.dng').write_bytes(dng())
    (dest/'bad.jpg').write_bytes(b'Not an image\n')
    (dest/'LICENSE.txt').write_text('These procedural image fixtures and their generator are original work dedicated to the public domain under CC0 1.0 Universal. No camera or third-party image data is included.\nhttps://creativecommons.org/publicdomain/zero/1.0/\n')
