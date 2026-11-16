"""
RR EDGE - Word Document Generator (.docx)
Replicates the PDF presentation styling with Poppins typography, RR theme (Pink, White, Midnight Blue, Charcoal),
A4 grid background, logo, graphics, cards, and complete canonical submission text.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# ---------------------------------------------------------
# PALETTE DEFINITION (Rajasthan Royals Theme)
# ---------------------------------------------------------
COLOR_RR_PINK = RGBColor(217, 26, 91)       # #D91A5B (Primary Brand Pink)
COLOR_RR_VIVID_PINK = RGBColor(230, 0, 126) # #E6007E (Accent Pink)
COLOR_RR_DEEP_BLUE = RGBColor(0, 29, 74)    # #001D4A (Midnight Navy)
COLOR_RR_DARK_TEXT = RGBColor(31, 41, 55)   # #1F2937 (Charcoal Dark Text)
COLOR_RR_MUTED = RGBColor(107, 114, 128)    # #6B7280 (Muted Secondary)
COLOR_RR_LIGHT_BG = RGBColor(253, 242, 248) # #FDF2F8 (Soft Pink Fill)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_EMERALD = RGBColor(16, 149, 106)
COLOR_AMBER = RGBColor(217, 119, 6)

HEX_RR_PINK = "D91A5B"
HEX_RR_DEEP_BLUE = "001D4A"
HEX_RR_SOFT_PINK = "FFF5F8"
HEX_RR_LIGHT_GRAY = "F9FAFB"
HEX_RR_BORDER = "E5E7EB"
HEX_RR_BORDER_PINK = "F3D5E4"
HEX_EMERALD_BG = "ECFDF5"
HEX_EMERALD_TEXT = "065F46"
HEX_AMBER_BG = "FFFBEB"
HEX_AMBER_TEXT = "92400E"

BASE_DIR = r"c:\HACKATHONS\77. RR SELECTOR - RAJASTHAN ROYALS\APP\rr-edge"
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ASSETS_DIR = os.path.join(DOCS_DIR, "extracted_assets")
PLAYERS_DIR = os.path.join(BASE_DIR, "frontend", "public", "players")
LOGO_PATH = os.path.join(BASE_DIR, "frontend", "public", "logo.png")
EMBLEM_PATH = os.path.join(BASE_DIR, "frontend", "public", "rr_emblem.png")
BG_A4_PATH = os.path.join(DOCS_DIR, "rr_grid_bg_a4.png")
BALL_GRAPHIC_PATH = os.path.join(ASSETS_DIR, "p1_img6_840x824.png")

# ---------------------------------------------------------
# XML HELPER FUNCTIONS
# ---------------------------------------------------------
def set_cell_background(cell, hex_color):
    """Sets background shading of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    """Sets internal cell margins in twips (1 pt = 20 twips)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    """Configures individual cell borders."""
    tcPr = cell._tc.get_or_add_tcPr()
    borders_elm = OxmlElement('w:tcBorders')
    
    border_specs = {'top': top, 'bottom': bottom, 'left': left, 'right': right}
    for b_name, b_val in border_specs.items():
        if b_val:
            sz = b_val.get('sz', '4')
            val = b_val.get('val', 'single')
            color = b_val.get('color', HEX_RR_BORDER)
            tag = f'<w:{b_name} {nsdecls("w")} w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            borders_elm.append(parse_xml(tag))
        else:
            tag = f'<w:{b_name} {nsdecls("w")} w:val="none"/>'
            borders_elm.append(parse_xml(tag))
    tcPr.append(borders_elm)

def format_run(run, font_name="Poppins", size_pt=10.5, bold=False, italic=False, color_rgb=COLOR_RR_DARK_TEXT):
    """Applies clean typography to a text run."""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb

def add_callout_card(doc, title, body_text, icon_text=None, border_color=HEX_RR_PINK, bg_color=HEX_RR_SOFT_PINK):
    """Creates a modern rounded card container with colored border and soft background."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Mm(170)
    
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=160, bottom=160, left=240, right=200)
    set_cell_borders(cell,
        left={'val': 'single', 'sz': '24', 'color': border_color},
        top={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        right={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        bottom={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK}
    )
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    
    if icon_text:
        r_ico = p.add_run(f"{icon_text} ")
        format_run(r_ico, "Poppins", 11, bold=True, color_rgb=COLOR_RR_PINK)
    
    r_title = p.add_run(title)
    format_run(r_title, "Poppins", 11.5, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
    
    if body_text:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.2
        r_body = p2.add_run(body_text)
        format_run(r_body, "Poppins", 10, bold=False, color_rgb=COLOR_RR_DARK_TEXT)
    
    # Add trailing space after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def add_kpi_card_row(doc, kpi_list):
    """Creates a horizontal row of statistical metric cards."""
    cols_count = len(kpi_list)
    tbl = doc.add_table(rows=1, cols=cols_count)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    col_width = Mm(170 / cols_count)
    for i, (val, label, sub) in enumerate(kpi_list):
        cell = tbl.cell(0, i)
        cell.width = col_width
        set_cell_background(cell, "FFFFFF")
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        set_cell_borders(cell,
            top={'val': 'single', 'sz': '6', 'color': HEX_RR_BORDER},
            bottom={'val': 'single', 'sz': '6', 'color': HEX_RR_BORDER},
            left={'val': 'single', 'sz': '6', 'color': HEX_RR_BORDER},
            right={'val': 'single', 'sz': '6', 'color': HEX_RR_BORDER}
        )
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r_val = p.add_run(val)
        format_run(r_val, "Poppins", 16, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
        
        p2 = cell.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(1)
        r_lbl = p2.add_run(label)
        format_run(r_lbl, "Poppins", 9.5, bold=True, color_rgb=COLOR_RR_PINK)
        
        if sub:
            p3 = cell.add_paragraph()
            p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p3.paragraph_format.space_before = Pt(0)
            p3.paragraph_format.space_after = Pt(0)
            r_sub = p3.add_run(sub)
            format_run(r_sub, "Poppins", 8, bold=False, color_rgb=COLOR_RR_MUTED)
            
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def add_comparison_box(doc, left_title, left_points, right_title, right_points, footer_note=None):
    """Side-by-side comparison container (Batting Pressure vs. Bowling Pressure, RAE vs RCAE)."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Mm(83)
    tbl.columns[1].width = Mm(83)
    
    # Left Cell
    c_left = tbl.cell(0, 0)
    set_cell_background(c_left, HEX_RR_SOFT_PINK)
    set_cell_margins(c_left, top=140, bottom=140, left=160, right=160)
    set_cell_borders(c_left,
        top={'val': 'single', 'sz': '16', 'color': HEX_RR_PINK},
        bottom={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        left={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        right={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK}
    )
    p_l = c_left.paragraphs[0]
    p_l.paragraph_format.space_after = Pt(4)
    r_lt = p_l.add_run(left_title)
    format_run(r_lt, "Poppins", 11, bold=True, color_rgb=COLOR_RR_PINK)
    for pt in left_points:
        p_pt = c_left.add_paragraph()
        p_pt.paragraph_format.space_before = Pt(1)
        p_pt.paragraph_format.space_after = Pt(2)
        p_pt.paragraph_format.line_spacing = 1.15
        r_b = p_pt.add_run("• ")
        format_run(r_b, "Poppins", 9.5, bold=True, color_rgb=COLOR_RR_PINK)
        r_txt = p_pt.add_run(pt)
        format_run(r_txt, "Poppins", 9, bold=False, color_rgb=COLOR_RR_DARK_TEXT)
        
    # Right Cell
    c_right = tbl.cell(0, 1)
    set_cell_background(c_right, "F0F4F8")
    set_cell_margins(c_right, top=140, bottom=140, left=160, right=160)
    set_cell_borders(c_right,
        top={'val': 'single', 'sz': '16', 'color': HEX_RR_DEEP_BLUE},
        bottom={'val': 'single', 'sz': '4', 'color': "CBD5E1"},
        left={'val': 'single', 'sz': '4', 'color': "CBD5E1"},
        right={'val': 'single', 'sz': '4', 'color': "CBD5E1"}
    )
    p_r = c_right.paragraphs[0]
    p_r.paragraph_format.space_after = Pt(4)
    r_rt = p_r.add_run(right_title)
    format_run(r_rt, "Poppins", 11, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
    for pt in right_points:
        p_pt = c_right.add_paragraph()
        p_pt.paragraph_format.space_before = Pt(1)
        p_pt.paragraph_format.space_after = Pt(2)
        p_pt.paragraph_format.line_spacing = 1.15
        r_b = p_pt.add_run("• ")
        format_run(r_b, "Poppins", 9.5, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
        r_txt = p_pt.add_run(pt)
        format_run(r_txt, "Poppins", 9, bold=False, color_rgb=COLOR_RR_DARK_TEXT)
        
    if footer_note:
        sp_f = doc.add_paragraph()
        sp_f.paragraph_format.space_before = Pt(4)
        sp_f.paragraph_format.space_after = Pt(6)
        r_fn = sp_f.add_run(footer_note)
        format_run(r_fn, "Poppins", 8.5, italic=True, color_rgb=COLOR_RR_MUTED)
    else:
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)

def add_full_page_background(header, img_path):
    """Embeds an anchored full-page background watermark in the header behind text."""
    p = header.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    pic = run.add_picture(img_path, width=Mm(210), height=Mm(297))
    drawing = pic._inline
    cx = drawing.extent.cx
    cy = drawing.extent.cy
    graphic = drawing.graphic

    anchor_xml = f'''
    <wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
               distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0"
               behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1">
        <wp:simplePos x="0" y="0"/>
        <wp:positionH relativeFrom="page">
            <wp:posOffset>0</wp:posOffset>
        </wp:positionH>
        <wp:positionV relativeFrom="page">
            <wp:posOffset>0</wp:posOffset>
        </wp:positionV>
        <wp:extent cx="{cx}" cy="{cy}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:wrapNone/>
        <wp:docPr id="101" name="PageWatermark"/>
        <wp:cNvGraphicFramePr/>
    </wp:anchor>
    '''
    anchor = parse_xml(anchor_xml)
    anchor.append(graphic)
    drawing.getparent().replace(drawing, anchor)

def add_section_header(doc, section_num_text, title_text):
    """Adds a stylish section header matching the PDF layout."""
    p_tag = doc.add_paragraph()
    p_tag.paragraph_format.space_before = Pt(16)
    p_tag.paragraph_format.space_after = Pt(2)
    p_tag.paragraph_format.keep_with_next = True
    
    r_tag = p_tag.add_run(section_num_text.upper())
    format_run(r_tag, "Poppins", 9, bold=True, color_rgb=COLOR_RR_PINK)
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(6)
    p_title.paragraph_format.keep_with_next = True
    
    r_title = p_title.add_run(title_text)
    format_run(r_title, "Poppins", 20, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)

def add_styled_table(doc, headers, rows_data, col_widths=None, align_right_cols=None):
    """Renders a beautifully styled RR theme table."""
    align_right_cols = align_right_cols or []
    tbl = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    # Header Row
    hdr_cells = tbl.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = ""
        set_cell_background(hdr_cells[i], HEX_RR_DEEP_BLUE)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=120, right=120)
        set_cell_borders(hdr_cells[i],
            bottom={'val': 'single', 'sz': '12', 'color': HEX_RR_PINK},
            top={'val': 'none'}, left={'val': 'none'}, right={'val': 'none'}
        )
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if i in align_right_cols else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(title)
        format_run(r, "Poppins", 8.5, bold=True, color_rgb=COLOR_WHITE)
        
    # Data Rows
    for r_idx, row in enumerate(rows_data):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_hex = "FFFFFF" if r_idx % 2 == 0 else HEX_RR_LIGHT_GRAY
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = ""
            set_cell_background(row_cells[c_idx], bg_hex)
            set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=120, right=120)
            set_cell_borders(row_cells[c_idx],
                bottom={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER},
                top={'val': 'none'}, left={'val': 'none'}, right={'val': 'none'}
            )
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx in align_right_cols else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            
            # Format text: highlight ranks, bold names
            r = p.add_run(str(val))
            if c_idx == 0 and str(val).startswith("#"):
                format_run(r, "Poppins", 9, bold=True, color_rgb=COLOR_RR_PINK)
            elif c_idx == 1:
                format_run(r, "Poppins", 9, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
            else:
                format_run(r, "Poppins", 8.5, bold=False, color_rgb=COLOR_RR_DARK_TEXT)
                
    if col_widths:
        for row in tbl.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Mm(w)
                
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)
    return tbl

def add_player_card(doc, rank, name, player_id, role, archetype, photo_filename, ipl_stats, t20i_stats, combined_stats, scout_notes):
    """Renders a comprehensive candidate dossier card with photo and stats."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Mm(32)
    tbl.columns[1].width = Mm(138)
    
    cell_photo = tbl.cell(0, 0)
    cell_info = tbl.cell(0, 1)
    
    set_cell_background(cell_photo, HEX_RR_SOFT_PINK)
    set_cell_margins(cell_photo, top=140, bottom=140, left=100, right=100)
    set_cell_borders(cell_photo,
        left={'val': 'single', 'sz': '16', 'color': HEX_RR_PINK},
        top={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        bottom={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        right={'val': 'none'}
    )
    
    set_cell_background(cell_info, "FFFFFF")
    set_cell_margins(cell_info, top=140, bottom=140, left=140, right=140)
    set_cell_borders(cell_info,
        top={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        bottom={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        right={'val': 'single', 'sz': '4', 'color': HEX_RR_BORDER_PINK},
        left={'val': 'none'}
    )
    
    # Photo cell
    p_ph = cell_photo.paragraphs[0]
    p_ph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ph.paragraph_format.space_before = Pt(2)
    p_ph.paragraph_format.space_after = Pt(2)
    
    photo_path = os.path.join(PLAYERS_DIR, photo_filename)
    if os.path.exists(photo_path):
        try:
            p_ph.add_run().add_picture(photo_path, width=Mm(24))
        except Exception:
            pass
            
    p_rk = cell_photo.add_paragraph()
    p_rk.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rk.paragraph_format.space_before = Pt(4)
    p_rk.paragraph_format.space_after = Pt(0)
    r_rk = p_rk.add_run(f"RANK #{rank}")
    format_run(r_rk, "Poppins", 9.5, bold=True, color_rgb=COLOR_RR_PINK)
    
    p_id = cell_photo.add_paragraph()
    p_id.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_id.paragraph_format.space_before = Pt(0)
    p_id.paragraph_format.space_after = Pt(0)
    r_id = p_id.add_run(f"ID: {player_id}")
    format_run(r_id, "Poppins", 8, color_rgb=COLOR_RR_MUTED)
    
    # Info cell
    p_nm = cell_info.paragraphs[0]
    p_nm.paragraph_format.space_before = Pt(0)
    p_nm.paragraph_format.space_after = Pt(2)
    r_nm = p_nm.add_run(name)
    format_run(r_nm, "Poppins", 13, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
    
    r_sep = p_nm.add_run("  |  ")
    format_run(r_sep, "Poppins", 10, color_rgb=COLOR_RR_MUTED)
    
    r_rl = p_nm.add_run(role)
    format_run(r_rl, "Poppins", 10, bold=True, color_rgb=COLOR_RR_PINK)
    
    r_sep2 = p_nm.add_run("  •  ")
    format_run(r_sep2, "Poppins", 10, color_rgb=COLOR_RR_MUTED)
    
    r_arc = p_nm.add_run(f"Archetype: {archetype}")
    format_run(r_arc, "Poppins", 9.5, italic=True, color_rgb=COLOR_EMERALD)
    
    # Stats Breakdown
    p_st = cell_info.add_paragraph()
    p_st.paragraph_format.space_before = Pt(4)
    p_st.paragraph_format.space_after = Pt(2)
    p_st.paragraph_format.line_spacing = 1.15
    
    # IPL
    r_ipl_tag = p_st.add_run("IPL Pressure: ")
    format_run(r_ipl_tag, "Poppins", 8.5, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
    r_ipl_val = p_st.add_run(ipl_stats + "\n")
    format_run(r_ipl_val, "Poppins", 8.5, color_rgb=COLOR_RR_DARK_TEXT)
    
    # T20I
    r_t20_tag = p_st.add_run("T20I Pressure: ")
    format_run(r_t20_tag, "Poppins", 8.5, bold=True, color_rgb=COLOR_RR_PINK)
    r_t20_val = p_st.add_run(t20i_stats + "\n")
    format_run(r_t20_val, "Poppins", 8.5, color_rgb=COLOR_RR_DARK_TEXT)
    
    # Combined
    r_cb_tag = p_st.add_run("Combined Portfolio: ")
    format_run(r_cb_tag, "Poppins", 8.5, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
    r_cb_val = p_st.add_run(combined_stats)
    format_run(r_cb_val, "Poppins", 8.5, color_rgb=COLOR_RR_DARK_TEXT)
    
    # Scout notes
    p_sn = cell_info.add_paragraph()
    p_sn.paragraph_format.space_before = Pt(4)
    p_sn.paragraph_format.space_after = Pt(0)
    p_sn.paragraph_format.line_spacing = 1.15
    r_snt = p_sn.add_run("Tactical Fit & Scout Evaluation: ")
    format_run(r_snt, "Poppins", 8.5, bold=True, color_rgb=COLOR_RR_DEEP_BLUE)
    r_snv = p_sn.add_run(scout_notes)
    format_run(r_snv, "Poppins", 8.5, italic=True, color_rgb=COLOR_RR_DARK_TEXT)
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

print("Helper definitions loaded successfully.")
