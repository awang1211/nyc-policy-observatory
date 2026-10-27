"""Render the two-page readiness brief; never insert synthetic findings."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

ROOT=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BriefTitle',fontName='Helvetica-Bold',fontSize=24,leading=29,textColor=colors.HexColor('#172f38'),spaceAfter=14))
styles.add(ParagraphStyle(name='BriefDeck',fontSize=10,leading=15,textColor=colors.HexColor('#596e76'),spaceAfter=18))
styles.add(ParagraphStyle(name='BriefHeading',fontName='Helvetica-Bold',fontSize=13,leading=18,textColor=colors.HexColor('#007b73'),spaceBefore=13,spaceAfter=8))
styles.add(ParagraphStyle(name='BriefBody',fontSize=10.3,leading=15,spaceAfter=12,textColor=colors.HexColor('#172f38')))
story=[]
for block in (ROOT/'docs/executive-brief.md').read_text().split('\n\n'):
 block=block.strip()
 if block=='---':story.append(PageBreak());continue
 if not block:continue
 # A heading may share a block with the following heading; preserve each line.
 if block.startswith('#'):
  for line in block.splitlines():
   level=len(line)-len(line.lstrip('#'))
   style={1:'BriefTitle',2:'BriefDeck',3:'BriefHeading'}.get(level,'BriefBody')
   story.append(Paragraph(escape(line.lstrip('#').strip()),styles[style]))
 else:story.append(Paragraph(escape(block),styles['BriefBody']))
def footer(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#d7dfda'));canvas.line(45,42,A4[0]-45,42)
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#596e76'))
 canvas.drawString(45,28,'NYC Policy Implementation Observatory · Readiness, not research findings')
 canvas.drawRightString(A4[0]-45,28,str(doc.page))
out=ROOT/'reports/executive-brief.pdf';out.parent.mkdir(exist_ok=True)
SimpleDocTemplate(str(out),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=44,bottomMargin=55).build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
