"""
Data Export Service for HNC Legal Questionnaire System
Provides functionality to export client data to PDF and Excel formats
"""

import io
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import xlsxwriter

from jinja2 import Template


class ExportService:
    """Service for exporting client data to various formats"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.exports_dir = self.data_dir / "exports"
        self.templates_dir = self.data_dir / "templates"
        
        # Create directories if they don't exist
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup styles
        self.setup_pdf_styles()
    
    def setup_pdf_styles(self):
        """Setup PDF styles for consistent formatting"""
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.darkblue
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.darkgreen
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
    
    async def export_client_to_pdf(self, client_data: Dict[str, Any], include_ai_proposal: bool = True) -> bytes:
        """Export single client data to PDF format"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Build the PDF content
        story = []
        
        # Title
        story.append(Paragraph("HNC LEGAL QUESTIONNAIRE REPORT", self.title_style))
        story.append(Spacer(1, 12))
        
        # Client Information Header
        client_info_data = [
            ['Client Name:', client_data.get('bioData', {}).get('fullName', 'N/A')],
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Client ID:', client_data.get('clientId', 'N/A')],
        ]
        
        client_info_table = Table(client_info_data, colWidths=[2*inch, 4*inch])
        client_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(client_info_table)
        story.append(Spacer(1, 20))
        
        # Bio Data Section
        story.append(Paragraph("PERSONAL INFORMATION", self.heading_style))
        
        bio_data = client_data.get('bioData', {})
        bio_data_content = [
            ['Full Name:', bio_data.get('fullName', 'N/A')],
            ['Marital Status:', bio_data.get('maritalStatus', 'N/A')],
            ['Spouse Name:', bio_data.get('spouseName', 'N/A')],
            ['Spouse ID:', bio_data.get('spouseId', 'N/A')],
            ['Children:', bio_data.get('children', 'N/A')],
        ]
        
        bio_table = Table(bio_data_content, colWidths=[2*inch, 4*inch])
        bio_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(bio_table)
        story.append(Spacer(1, 20))
        
        # Financial Information Section
        story.append(Paragraph("FINANCIAL INFORMATION", self.heading_style))
        
        financial_data = client_data.get('financialData', {})
        
        # Assets table
        story.append(Paragraph("Assets", self.subheading_style))
        assets = financial_data.get('assets', [])
        
        if assets:
            assets_data = [['Type', 'Description', 'Value (KES)']]
            total_value = 0
            
            for asset in assets:
                value = asset.get('value', 0)
                assets_data.append([
                    asset.get('type', 'N/A'),
                    asset.get('description', 'N/A'),
                    f"{value:,.2f}"
                ])
                total_value += value
            
            assets_data.append(['TOTAL', '', f"{total_value:,.2f}"])
            
            assets_table = Table(assets_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
            assets_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(assets_table)
        else:
            story.append(Paragraph("No assets recorded", self.body_style))
        
        story.append(Spacer(1, 12))
        
        # Other financial info
        other_financial = [
            ['Liabilities:', financial_data.get('liabilities', 'N/A')],
            ['Income Sources:', financial_data.get('incomeSources', 'N/A')],
        ]
        
        other_financial_table = Table(other_financial, colWidths=[2*inch, 4*inch])
        other_financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(other_financial_table)
        story.append(Spacer(1, 20))
        
        # Economic Context Section
        story.append(Paragraph("ECONOMIC CONTEXT", self.heading_style))
        
        economic_data = client_data.get('economicContext', {})
        economic_content = [
            ['Economic Standing:', economic_data.get('economicStanding', 'N/A')],
            ['Distribution Preferences:', economic_data.get('distributionPrefs', 'N/A')],
        ]
        
        economic_table = Table(economic_content, colWidths=[2*inch, 4*inch])
        economic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(economic_table)
        story.append(Spacer(1, 20))
        
        # Objectives Section
        story.append(Paragraph("CLIENT OBJECTIVES", self.heading_style))
        
        objectives_data = client_data.get('objectives', {})
        objectives_content = [
            ['Objective:', objectives_data.get('objective', 'N/A')],
            ['Details:', objectives_data.get('details', 'N/A')],
        ]
        
        objectives_table = Table(objectives_content, colWidths=[2*inch, 4*inch])
        objectives_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(objectives_table)
        story.append(Spacer(1, 20))
        
        # Lawyer Notes
        lawyer_notes = client_data.get('lawyerNotes', '')
        if lawyer_notes:
            story.append(Paragraph("LAWYER NOTES", self.heading_style))
            story.append(Paragraph(lawyer_notes, self.body_style))
            story.append(Spacer(1, 20))
        
        # AI Proposal Section (if included)
        if include_ai_proposal and 'aiProposal' in client_data:
            story.append(PageBreak())
            story.append(Paragraph("AI LEGAL PROPOSAL", self.title_style))
            story.append(Spacer(1, 12))
            
            ai_proposal = client_data['aiProposal']
            
            # Suggestion
            story.append(Paragraph("RECOMMENDATION", self.heading_style))
            story.append(Paragraph(ai_proposal.get('suggestion', 'N/A'), self.body_style))
            story.append(Spacer(1, 12))
            
            # Legal References
            legal_refs = ai_proposal.get('legalReferences', [])
            if legal_refs:
                story.append(Paragraph("LEGAL REFERENCES", self.heading_style))
                for ref in legal_refs:
                    story.append(Paragraph(f"• {ref}", self.body_style))
                story.append(Spacer(1, 12))
            
            # Consequences
            consequences = ai_proposal.get('consequences', [])
            if consequences:
                story.append(Paragraph("POTENTIAL CONSEQUENCES", self.heading_style))
                for consequence in consequences:
                    story.append(Paragraph(f"• {consequence}", self.body_style))
                story.append(Spacer(1, 12))
            
            # Next Steps
            next_steps = ai_proposal.get('nextSteps', [])
            if next_steps:
                story.append(Paragraph("RECOMMENDED NEXT STEPS", self.heading_style))
                for step in next_steps:
                    story.append(Paragraph(f"• {step}", self.body_style))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("--- End of Report ---", self.title_style))
        
        # Build PDF
        doc.build(story)
        
        # Get the value of the BytesIO buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    async def export_clients_to_excel(self, clients_data: List[Dict[str, Any]], 
                                    include_summary: bool = True) -> bytes:
        """Export multiple clients data to Excel format"""
        
        buffer = io.BytesIO()
        
        with xlsxwriter.Workbook(buffer, {'in_memory': True}) as workbook:
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#366092',
                'border': 1
            })
            
            subheader_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BD',
                'border': 1
            })
            
            data_format = workbook.add_format({
                'border': 1,
                'text_wrap': True
            })
            
            currency_format = workbook.add_format({
                'num_format': '#,##0.00',
                'border': 1
            })
            
            # Summary Sheet
            if include_summary:
                summary_sheet = workbook.add_worksheet('Summary')
                self._create_summary_sheet(summary_sheet, clients_data, header_format, data_format, currency_format)
            
            # Individual client sheets
            for i, client in enumerate(clients_data[:10]):  # Limit to 10 sheets for performance
                sheet_name = f"Client_{i+1}"
                if len(client.get('bioData', {}).get('fullName', '')) > 0:
                    # Use client name but sanitize for sheet name
                    name = client['bioData']['fullName'][:20]  # Limit length
                    name = ''.join(c for c in name if c.isalnum() or c in (' ', '_')).strip()
                    sheet_name = name if name else sheet_name
                
                client_sheet = workbook.add_worksheet(sheet_name)
                self._create_client_sheet(client_sheet, client, header_format, subheader_format, 
                                        data_format, currency_format)
            
            # Assets Overview Sheet
            assets_sheet = workbook.add_worksheet('Assets_Overview')
            self._create_assets_overview_sheet(assets_sheet, clients_data, header_format, 
                                             data_format, currency_format)
        
        excel_data = buffer.getvalue()
        buffer.close()
        
        return excel_data
    
    def _create_summary_sheet(self, worksheet, clients_data, header_format, data_format, currency_format):
        """Create summary sheet with overview of all clients"""
        
        # Headers
        headers = ['Client Name', 'Marital Status', 'Objective', 'Total Assets (KES)', 
                  'Economic Standing', 'Date Created']
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data rows
        for row, client in enumerate(clients_data, 1):
            bio_data = client.get('bioData', {})
            financial_data = client.get('financialData', {})
            economic_context = client.get('economicContext', {})
            objectives = client.get('objectives', {})
            
            # Calculate total assets
            total_assets = sum(asset.get('value', 0) for asset in financial_data.get('assets', []))
            
            worksheet.write(row, 0, bio_data.get('fullName', 'N/A'), data_format)
            worksheet.write(row, 1, bio_data.get('maritalStatus', 'N/A'), data_format)
            worksheet.write(row, 2, objectives.get('objective', 'N/A'), data_format)
            worksheet.write(row, 3, total_assets, currency_format)
            worksheet.write(row, 4, economic_context.get('economicStanding', 'N/A'), data_format)
            worksheet.write(row, 5, client.get('savedAt', 'N/A'), data_format)
        
        # Auto-adjust column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 20)
    
    def _create_client_sheet(self, worksheet, client_data, header_format, subheader_format, 
                           data_format, currency_format):
        """Create detailed sheet for individual client"""
        
        row = 0
        
        # Client Name Header
        bio_data = client_data.get('bioData', {})
        worksheet.write(row, 0, 'CLIENT INFORMATION', header_format)
        worksheet.write(row, 1, bio_data.get('fullName', 'N/A'), data_format)
        row += 2
        
        # Bio Data Section
        worksheet.write(row, 0, 'PERSONAL INFORMATION', subheader_format)
        row += 1
        
        bio_fields = [
            ('Full Name', bio_data.get('fullName', 'N/A')),
            ('Marital Status', bio_data.get('maritalStatus', 'N/A')),
            ('Spouse Name', bio_data.get('spouseName', 'N/A')),
            ('Spouse ID', bio_data.get('spouseId', 'N/A')),
            ('Children', bio_data.get('children', 'N/A')),
        ]
        
        for field, value in bio_fields:
            worksheet.write(row, 0, field, data_format)
            worksheet.write(row, 1, value, data_format)
            row += 1
        
        row += 1
        
        # Financial Data Section
        financial_data = client_data.get('financialData', {})
        worksheet.write(row, 0, 'FINANCIAL INFORMATION', subheader_format)
        row += 1
        
        # Assets
        worksheet.write(row, 0, 'Assets', data_format)
        row += 1
        
        assets = financial_data.get('assets', [])
        if assets:
            # Asset headers
            worksheet.write(row, 0, 'Type', header_format)
            worksheet.write(row, 1, 'Description', header_format)
            worksheet.write(row, 2, 'Value (KES)', header_format)
            row += 1
            
            total_assets = 0
            for asset in assets:
                value = asset.get('value', 0)
                worksheet.write(row, 0, asset.get('type', 'N/A'), data_format)
                worksheet.write(row, 1, asset.get('description', 'N/A'), data_format)
                worksheet.write(row, 2, value, currency_format)
                total_assets += value
                row += 1
            
            # Total row
            worksheet.write(row, 0, 'TOTAL', subheader_format)
            worksheet.write(row, 1, '', subheader_format)
            worksheet.write(row, 2, total_assets, currency_format)
            row += 1
        
        row += 1
        
        # Other financial info
        financial_fields = [
            ('Liabilities', financial_data.get('liabilities', 'N/A')),
            ('Income Sources', financial_data.get('incomeSources', 'N/A')),
        ]
        
        for field, value in financial_fields:
            worksheet.write(row, 0, field, data_format)
            worksheet.write(row, 1, value, data_format)
            row += 1
        
        row += 1
        
        # Economic Context
        economic_context = client_data.get('economicContext', {})
        worksheet.write(row, 0, 'ECONOMIC CONTEXT', subheader_format)
        row += 1
        
        economic_fields = [
            ('Economic Standing', economic_context.get('economicStanding', 'N/A')),
            ('Distribution Preferences', economic_context.get('distributionPrefs', 'N/A')),
        ]
        
        for field, value in economic_fields:
            worksheet.write(row, 0, field, data_format)
            worksheet.write(row, 1, value, data_format)
            row += 1
        
        row += 1
        
        # Objectives
        objectives = client_data.get('objectives', {})
        worksheet.write(row, 0, 'CLIENT OBJECTIVES', subheader_format)
        row += 1
        
        objectives_fields = [
            ('Objective', objectives.get('objective', 'N/A')),
            ('Details', objectives.get('details', 'N/A')),
        ]
        
        for field, value in objectives_fields:
            worksheet.write(row, 0, field, data_format)
            worksheet.write(row, 1, value, data_format)
            row += 1
        
        # Lawyer Notes
        lawyer_notes = client_data.get('lawyerNotes', '')
        if lawyer_notes:
            row += 1
            worksheet.write(row, 0, 'LAWYER NOTES', subheader_format)
            row += 1
            worksheet.write(row, 0, lawyer_notes, data_format)
        
        # Auto-adjust column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 15)
    
    def _create_assets_overview_sheet(self, worksheet, clients_data, header_format, data_format, currency_format):
        """Create assets overview sheet"""
        
        # Headers
        headers = ['Client Name', 'Asset Type', 'Description', 'Value (KES)']
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        row = 1
        total_value = 0
        
        for client in clients_data:
            client_name = client.get('bioData', {}).get('fullName', 'N/A')
            financial_data = client.get('financialData', {})
            assets = financial_data.get('assets', [])
            
            for asset in assets:
                value = asset.get('value', 0)
                worksheet.write(row, 0, client_name, data_format)
                worksheet.write(row, 1, asset.get('type', 'N/A'), data_format)
                worksheet.write(row, 2, asset.get('description', 'N/A'), data_format)
                worksheet.write(row, 3, value, currency_format)
                total_value += value
                row += 1
        
        # Total row
        if row > 1:
            row += 1
            worksheet.write(row, 0, 'GRAND TOTAL', header_format)
            worksheet.write(row, 1, '', header_format)
            worksheet.write(row, 2, '', header_format)
            worksheet.write(row, 3, total_value, currency_format)
        
        # Auto-adjust column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 15)
    
    async def save_export_file(self, file_data: bytes, filename: str) -> str:
        """Save export file to disk and return file path"""
        
        file_path = self.exports_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return str(file_path)
    
    def get_export_filename(self, client_name: str, export_type: str, timestamp: Optional[datetime] = None) -> str:
        """Generate standardized export filename"""
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Sanitize client name for filename
        safe_name = ''.join(c for c in client_name if c.isalnum() or c in (' ', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        if export_type.lower() == 'pdf':
            return f"{safe_name}_{timestamp_str}.pdf"
        elif export_type.lower() in ['excel', 'xlsx']:
            return f"{safe_name}_{timestamp_str}.xlsx"
        else:
            return f"{safe_name}_{timestamp_str}.{export_type}"