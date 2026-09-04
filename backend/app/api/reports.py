import os
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, Event, Camera
import json
import uuid
import qrcode
from app.services.blockchain import blockchain_service
import asyncio

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
except ImportError:
    pass

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def generate_pdf_sync(event_id: int, db: Session):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise Exception("Event not found")
        
    camera = db.query(Camera).filter(Camera.id == event.camera_id).first()
    cam_name = camera.name if camera else f"Camera {event.camera_id}"
    cam_loc = camera.location if camera else "Unknown Location"
    
    details = json.loads(event.details) if event.details else {}
    track_id = details.get("id", "").split("_")[-1] if details.get("id") else "Unknown"
    
    # Calculate SHA256 of image
    file_path = None
    file_hash = "No Evidence Attached"
    if event.thumbnail_path:
        file_name = event.thumbnail_path.split('/')[-1]
        file_path = os.path.join("data", "evidence", file_name)
        if os.path.exists(file_path):
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for block in iter(lambda: f.read(4096), b""):
                    sha256.update(block)
            file_hash = sha256.hexdigest()
        else:
            file_path = None

    # Generate PDF
    os.makedirs("data/reports", exist_ok=True)
    pdf_filename = f"DRISHTI_Incident_{event.id}_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = os.path.join("data", "reports", pdf_filename)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], textColor=colors.HexColor('#06b6d4'), alignment=1)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], alignment=1, textColor=colors.gray)
    normal_style = styles['Normal']
    
    story = []
    
    story.append(Paragraph("DRISHTI - SECURITY INCIDENT REPORT", title_style))
    story.append(Paragraph("Advanced Border & Surveillance Platform", subtitle_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Data Table
    data = [
        ["Incident ID:", str(event.id), "Date/Time:", event.created_at.strftime("%Y-%m-%d %H:%M:%S")],
        ["Severity:", event.severity.upper(), "Event Type:", event.event_type.replace('_', ' ').upper()],
        ["Camera Name:", cam_name, "Location:", cam_loc],
        ["Detected Obj:", event.object_class.upper(), "Track ID:", f"#{track_id}"],
    ]
    
    t = Table(data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#333333')),
        ('TEXTCOLOR', (2,0), (2,-1), colors.HexColor('#333333')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))
    
    # Explanation
    story.append(Paragraph("<b>AI Detection Summary:</b>", styles['Heading3']))
    story.append(Paragraph(details.get('title', 'Unknown Alert'), normal_style))
    story.append(Paragraph(details.get('detail', ''), normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    legal_disclaimer = "<i>Note: Normal person or vehicle detection does not itself generate a critical alert. This particular incident was triggered strictly because a configured security rule (e.g., Restricted Tripwire Crossing, Suspicious Dwelling, or Watchlist Match) was violated.</i>"
    story.append(Paragraph(legal_disclaimer, normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Image
    # Fetch Blockchain Ledger Data
    block = blockchain_service.get_block_by_event(event.id)
    block_status = "VERIFIED IMMUTABLE" if block else "PENDING MINING"
    
    if block:
        # Create QR Code for verification
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr_data = f"DRISHTI_VERIFY:{block['hash']}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join("data", "reports", f"qr_{event.id}.png")
        qr_img.save(qr_path)
    
    if file_path:
        story.append(Paragraph("<b>Evidence Snapshot:</b>", styles['Heading3']))
        try:
            img = Image(file_path, width=6*inch, height=3.375*inch) # 16:9 ratio
            story.append(img)
        except Exception:
            story.append(Paragraph("[Error embedding image]", normal_style))
        story.append(Spacer(1, 0.1 * inch))
    else:
        story.append(Paragraph("<b>Evidence Snapshot:</b> None Captured.", styles['Heading3']))
        story.append(Spacer(1, 0.1 * inch))

    # Blockchain Cryptographic Ledger Table
    ledger_elements = []
    ledger_elements.append(Paragraph("<b>Immutable Cryptographic Ledger (Blockchain):</b>", styles['Heading3']))
    
    if block:
        ledger_data = [
            ["Verification Status:", block_status],
            ["Block Number:", f"#{block['index']}"],
            ["Block Hash:", Paragraph(f"<font size=7>{block['hash']}</font>", normal_style)],
            ["Previous Block Hash:", Paragraph(f"<font size=7>{block['previous_hash']}</font>", normal_style)],
            ["Evidence SHA-256:", Paragraph(f"<font size=7>{block['evidence_hash']}</font>", normal_style)],
            ["Event Hash:", Paragraph(f"<font size=7>{block['event_hash']}</font>", normal_style)],
        ]
        
        lt = Table(ledger_data, colWidths=[1.8*inch, 4.2*inch])
        lt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdfa')), # Teal tint
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#004d40')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#14b8a6')),
        ]))
        ledger_elements.append(lt)
        
        # Add QR Code next to text
        ledger_elements.append(Spacer(1, 0.1 * inch))
        ledger_elements.append(Paragraph("<i>Scan QR code to verify cryptographic signature on the DRISHTI Network.</i>", subtitle_style))
        try:
            qr_pdf_img = Image(qr_path, width=1*inch, height=1*inch)
            ledger_elements.append(qr_pdf_img)
        except:
            pass
    else:
        ledger_elements.append(Paragraph("<i>Ledger transaction pending... (Mining in progress)</i>", normal_style))
        
    story.append(KeepTogether(ledger_elements))
        
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"<i>Report generated securely by DRISHTI Engine on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", subtitle_style))
    
    doc.build(story)
    return pdf_path


@router.get("/{event_id}/download")
async def download_report(event_id: int, db: Session = Depends(get_db)):
    try:
        # Offload CPU-bound PDF generation to thread pool
        pdf_path = await asyncio.to_thread(generate_pdf_sync, event_id, db)
        
        return FileResponse(
            path=pdf_path, 
            filename=f"DRISHTI_Incident_Report_{event_id}.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=DRISHTI_Incident_Report_{event_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
