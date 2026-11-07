"""Editable draw.io sequence diagrams and SVG previews from the same geometry."""
from __future__ import annotations
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import ImageFont

FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
STEP = 335
COLORS = {'actor': '#FFF4D8', 'boundary': '#EAF2F8',
          'control': '#E5F3F0', 'entity': '#F1F4F7', 'external': '#F4ECF7'}


def M(a, b, text, reply=False):
    return {'type': 'message', 'a': a, 'b': b, 'text': text, 'reply': reply}


def R(a, b, text):
    return M(a, b, text, True)


def C(a, b, text, result):
    return {'type': 'call', 'a': a, 'b': b, 'text': text, 'result': result}


def F(kind, *operands):
    return {'type': 'fragment', 'kind': kind, 'operands': list(operands)}


def O(guard, *body):
    return F('opt', (guard, list(body)))


def L(guard, *body):
    return F('loop', (guard, list(body)))


def A(*operands):
    return F('alt', *operands)


def flatten(items):
    for item in items:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


def normalize(items):
    """Nest a callee's following database work before returning to its caller."""
    source = list(flatten(items))
    result = []
    i = 0
    while i < len(source):
        item = source[i]
        if item['type'] == 'call':
            inner = []
            j = i + 1
            while j < len(source):
                nxt = source[j]
                if nxt['type'] not in ('call', 'message') or nxt.get('reply') or nxt['a'] != item['b']:
                    break
                inner.append(nxt)
                j += 1
            result.append(M(item['a'], item['b'], item['text']))
            result.extend(normalize(inner))
            result.append(R(item['b'], item['a'], item['result']))
            i = j
            continue
        if item['type'] == 'fragment':
            item = dict(item, operands=[(guard, normalize(body)) for guard,body in item['operands']])
        result.append(item)
        i += 1
    return result


def wrap(value, width):
    lines = []
    for paragraph in value.split('\n'):
        remaining = paragraph.strip()
        while remaining and FONT.getlength(remaining) > width:
            end = 1
            while end < len(remaining) and FONT.getlength(remaining[:end+1]) <= width:
                end += 1
            space = remaining.rfind(' ', 0, end+1)
            if space >= end*0.4:
                cut = space
            else:
                positions = [remaining.rfind(c, 0, end) for c in ('_', ',', '/', '.', ')')]
                candidate = max(positions)
                cut = candidate+1 if candidate >= end*0.4 else end
            lines.append(remaining[:cut].rstrip())
            remaining = remaining[cut:].lstrip()
        lines.append(remaining)
    return lines


class Diagram:
    def __init__(self, code, title, participants, body, sources):
        self.code, self.title = code, title
        self.participants, self.body, self.sources = participants, body, sources
        self.x = {p[0]: 150 + i * STEP for i, p in enumerate(participants)}
        self.width = 300 + (len(participants)-1)*STEP
        self.events, self.frames = [], []
        self.cursor, self.number = 240, 0
        self.plan(normalize(body), 0)
        self.height = self.cursor + 70
        self.cells, self.svg = [], []
        self.counter = 0
        self.mxroot = ET.Element('root')
        ET.SubElement(self.mxroot, 'mxCell', id='0')
        ET.SubElement(self.mxroot, 'mxCell', id='1', parent='0')

    def plan(self, items, depth):
        for item in flatten(items):
            if item['type'] == 'message':
                assert item['a'] in self.x and item['b'] in self.x
                self.number += 1
                a, b = self.x[item['a']], self.x[item['b']]
                width = min(660, abs(b-a)-42) if a != b else 290
                text = f"{self.number}: {item['text']}"
                lines = wrap(text, width)
                h = max(23, len(lines)*23)
                self.events.append(dict(item, number=self.number, lines=lines,
                                        y=self.cursor+h+8, label_h=h, label_w=width))
                self.cursor += h + (66 if a == b else 42)
            else:
                assert item['kind'] in ('alt', 'opt', 'loop')
                assert item['kind'] != 'alt' or len(item['operands']) >= 2
                y = self.cursor
                first_event = len(self.events)
                self.cursor += 61
                guards = []
                for index, (guard, body) in enumerate(item['operands']):
                    assert guard
                    if index:
                        self.cursor += 15
                        guards.append((self.cursor, guard, False))
                        self.cursor += 50
                    else:
                        guards.append((y, guard, True))
                    self.plan(body, depth+1)
                self.cursor += 23
                self.frames.append({'kind': item['kind'], 'y': y,
                                    'h': self.cursor-y, 'depth': depth, 'guards': guards,
                                    'event_range': [first_event,len(self.events)],
                                    'participants': sorted({p for e in self.events[first_event:] for p in (e['a'],e['b'])})})
                self.cursor += 22

    def cell(self, **attrs):
        self.counter += 1
        attrs = {k: str(v) for k, v in attrs.items()}
        attrs.setdefault('id', f'{self.code}_{self.counter}')
        attrs.setdefault('parent', '1')
        return ET.SubElement(self.mxroot, 'mxCell', attrs)

    def box(self, x, y, w, h, fill='none', stroke='#52606B', label='',
            font=17, align='center', bold=False, style=''):
        base = f'rect;rounded=0;html=0;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};fontFamily=Arial;fontSize={font};fontColor=#202B33;align={align};verticalAlign=middle;spacing=5;fontStyle={1 if bold else 0};'
        cell = self.cell(value=label, vertex=1, style=base+style)
        ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
        if fill != 'none' or stroke != 'none':
            self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
        return cell

    def text(self, x, y, w, h, lines, font=17, align='center', bold=False):
        label = '\n'.join(lines)
        self.box(x, y, w, h, stroke='none', label=label, font=font, align=align, bold=bold)
        self.svg_text(x, y, w, h, lines, font, align, bold)

    def svg_text(self, x, y, w, h, lines, font=17, align='center', bold=False):
        from html import escape
        line_h = font+6
        tx = x+w/2 if align == 'center' else x+5
        top = y+(h-line_h*len(lines))/2+font+1
        spans = ''.join(f'<tspan x="{tx}" y="{top+i*line_h}">{escape(line)}</tspan>' for i,line in enumerate(lines))
        self.svg.append(f'<text font-family="Arial" font-size="{font}" font-weight="{700 if bold else 400}" text-anchor="{"middle" if align=="center" else "start"}" fill="#202B33">{spans}</text>')

    def line(self, points, dashed=False, arrow=False, reply=False, stroke='#53616A'):
        style = f'edgeStyle=none;html=0;rounded=0;strokeColor={stroke};strokeWidth=1.3;endArrow={"open" if reply else "block" if arrow else "none"};endFill={0 if reply else 1};endSize=10;dashed={1 if dashed else 0};'
        edge = self.cell(edge=1, style=style, value='')
        geo = ET.SubElement(edge,'mxGeometry',relative='1',**{'as':'geometry'})
        ET.SubElement(geo,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'})
        ET.SubElement(geo,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),**{'as':'targetPoint'})
        if len(points)>2:
            arr=ET.SubElement(geo,'Array',**{'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
        coords=' '.join(f'{x},{y}' for x,y in points)
        self.svg.append(f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="1.3"'+(' stroke-dasharray="7 5"' if dashed else '')+(f' marker-end="url(#{ "reply" if reply else "call"})"' if arrow or reply else '')+'/>')
        return edge

    def render(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.box(12,12,self.width-24,self.height-24,stroke='#303B44')
        self.text(24,18,min(self.width-50,1200),40,
                  [f'sd {self.code} — {self.title}'],21,'left',True)
        for pid, label, kind in self.participants:
            x = self.x[pid]
            if kind == 'actor':
                self.box(x-13,76,26,26,fill=COLORS[kind],style='ellipse;')
                # SVG uses the same simple actor geometry.
                self.svg.pop()
                self.svg.append(f'<ellipse cx="{x}" cy="89" rx="13" ry="13" fill="{COLORS[kind]}" stroke="#52606B"/>')
                for pts in [[(x,102),(x,138)],[(x-23,117),(x+23,117)],[(x,138),(x-21,159)],[(x,138),(x+21,159)]]:
                    self.line(pts)
                self.text(x-145,164,290,56,wrap(label,280),17)
            else:
                stereotype = {'boundary':'boundary','control':'control','entity':'entity','external':'external'}[kind]
                lines = [f'«{stereotype}»'] + wrap(label,287)
                self.box(x-151,84,302,108,fill=COLORS[kind])
                self.text(x-146,89,292,98,lines,17)
            self.line([(x,220),(x,self.height-45)],dashed=True,stroke='#87939B')
        guard_labels=[]
        frame_tabs=[]
        for frame in sorted(self.frames,key=lambda f:(f['depth'],f['y'])):
            left = frame.get('left',28+frame['depth']*17)
            width = frame.get('width',self.width-left-28-frame['depth']*17)
            self.box(left,frame['y'],width,frame['h'],stroke='#4F5E69')
            frame_tabs.append((left,frame['y'],frame['kind']))
            for gy,guard,first in frame['guards']:
                if not first:self.line([(left,gy),(left+width,gy)],dashed=True,stroke='#87939B')
                guard_labels.append((left+80 if first else left+12,gy+4,width-100,guard))
        executions = {}
        kinds = {p[0]: p[2] for p in self.participants}
        for i,event in enumerate(self.events):
            if event['reply'] or event['a']==event['b'] or kinds[event['b']]=='actor':
                continue
            end = event['y']+22
            for nxt in self.events[i+1:]:
                if not nxt['reply'] and nxt['a']==event['a'] and nxt['b']==event['b']:
                    break
                if nxt['reply'] and nxt['a']==event['b'] and nxt['b']==event['a']:
                    end = nxt['y']
            executions.setdefault(event['b'],[]).append((event['y']-7,end+7))
        for pid,intervals in executions.items():
            merged=[]
            for start,end in sorted(intervals):
                if merged and start<=merged[-1][1]:
                    merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
                else:merged.append((start,end))
            for start,end in merged:
                self.box(self.x[pid]-6,start,12,end-start,fill='#D9EEEA',stroke='#5E7A75')
        for left,y,kind in frame_tabs:
            self.box(left,y,68,33,fill='#FFFFFF',label=kind,bold=True)
            self.svg_text(left,y,68,33,[kind],17,'center',True)
        for x,y,available,guard in guard_labels:
            label=f'[{guard}]'
            self.box(x,y,min(available,FONT.getlength(label)+14),37,fill='#FFFFFF',stroke='none')
            self.text(x,y,available,37,[label],17,'left')
        for event in self.events:
            x1,x2=self.x[event['a']],self.x[event['b']]
            y=event['y']
            points=[(x1,y),(x2,y)]
            if x1==x2:points=[(x1,y),(x1+115,y),(x1+115,y+26),(x1,y+26)]
            edge=self.line(points,dashed=event['reply'],arrow=not event['reply'],reply=event['reply'])
            w,h=event['label_w'],event['label_h']
            lx=(x1+x2-w)/2 if x1!=x2 else x1+20
            ly=y-h-8
            # Native edge label: remains attached when its message is moved.
            label=self.cell(parent=edge.attrib['id'],vertex=1,connectable=0,value='\n'.join(event['lines']),
                            style='edgeLabel;html=0;whiteSpace=wrap;fontFamily=Arial;fontSize=17;fontColor=#202B33;align=center;verticalAlign=middle;fillColor=#FFFFFF;strokeColor=none;spacing=0;')
            geo=ET.SubElement(label,'mxGeometry',x='0',y='0',width=str(w),height=str(h),relative='1',**{'as':'geometry'})
            if x1==x2:
                ox=20-115;oy=-h-21
            else:ox=-w/2;oy=-h-8
            ET.SubElement(geo,'mxPoint',x=str(ox),y=str(oy),**{'as':'offset'})
            self.svg.append(f'<rect x="{lx}" y="{ly}" width="{w}" height="{h}" fill="#FFFFFF"/>')
            self.svg_text(lx,ly,w,h,event['lines'])
        mx=ET.Element('mxfile',host='app.diagrams.net',version='26.0.0',type='device')
        page=ET.SubElement(mx,'diagram',id=self.code,name=f'{self.code} - Secuencia')
        model=ET.SubElement(page,'mxGraphModel',dx=str(self.width),dy=str(self.height),grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='0',pageScale='1',pageWidth=str(self.width),pageHeight=str(self.height),math='0',shadow='0')
        model.append(self.mxroot)
        stem=f'{self.code}_Diagrama_Secuencia'
        path=directory/(stem+'.drawio')
        ET.ElementTree(mx).write(path,encoding='utf-8',xml_declaration=True)
        defs='<defs><marker id="call" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#53616A"/></marker><marker id="reply" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#53616A" stroke-width="1.3"/></marker></defs>'
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}"><rect width="100%" height="100%" fill="white"/>{defs}'+''.join(self.svg)+'</svg>'
        (directory/(stem+'.svg')).write_text(svg,encoding='utf-8')
        return {'cu':self.code,'archivo':path.name,'participantes':len(self.participants),
                'mensajes':len(self.events),'fragmentos':dict((k,sum(f['kind']==k for f in self.frames)) for k in ('alt','opt','loop')),
                'ancho':self.width,'alto':self.height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'fuentes':self.sources}
