from openpyxl.styles import Alignment, Font, PatternFill, Border, Side, borders

def highlight_percent_gte50(val):
    color = 'green' if val >= 50 else ''
    return 'background-color: %s' % color

def highlight_percent_lte5(val):
    color = 'green' if abs(val) >= 5 else ''
    return 'background-color: %s' % color

def bold_total(data):
    attr = 'font-weight:bold'
    return attr

def color_negative_red( val):
    color = '#940000' if val < 0 else 'black'
    return 'color: %s' % color

def big_total(data):
    attr = 'font-size:14px'
    return attr

def global_hover( hover_color="#d6d6d6"):
    return dict(selector="td:hover",
                props=[("background-color", "%s" % hover_color)])

def global_table():
    th_props = [
        ('font-size', '110%'),
        ('text-align', 'left'),
        ('font-weight', 'bold'),
        ('color', '#6d6d6d'),
        ('background-color', '#FFFFFF'),
        ('border', 'solid 1px'), ('text-align', 'left')
    ]

    # Set CSS properties for td elements in dataframe
    td_props = [('font-size', '16px'), ('border', 'solid 1px'), ('text-align', 'right'),
                ('width', '1px'), ('white-space', 'nowrap'), ('padding', '3px')
    ]
    headers = [
        ('background-color', '#D9E9F7'),
        ('color', 'black')
    ]
    # Set table styles
    styles = [
        global_hover(),
        dict(selector="th", props=th_props),
        dict(selector='th', props=headers),
        dict(selector="td", props=td_props),
        ]
    return styles

def format_numbers(columns):
    dd = {}
    for c in columns:
        dd[c] = lambda x: "{:,.0f}".format(x)
    return dd

def set_sheet_auto_width(sheet, start_row=0):
    dims = {}
    for idx, row in enumerate(sheet.rows):
        for cell in row:
            if cell.value:
                # dims[cell.column_letter] = max((dims.get(cell.column_letter, start_row), 
                #                                 len(unicode(cell.value).strip())))
                if idx < start_row: continue
                current_value = 0
                if dims.get(cell.column_letter):
                    current_value = dims[cell.column_letter]
                clen = len(str(cell.value))
                dims[cell.column_letter] = clen if clen > current_value else current_value
    for col, value in dims.items():
        sheet.column_dimensions[col].width = value+4
    return sheet


def left_alignment():
    return Alignment(horizontal='left',
                    vertical='top',
                    text_rotation=0,
                    wrap_text=True,
                    shrink_to_fit=True,
                    indent=0)
    
def right_alignment():
    return Alignment(horizontal='right',
                    vertical='top',
                    text_rotation=0,
                    wrap_text=True,
                    shrink_to_fit=True,
                    indent=0)

def center_alignment(vertical='top'):
    return Alignment(horizontal='center',
                    vertical=vertical,
                    text_rotation=0,
                    wrap_text=True,
                    shrink_to_fit=True,
                    indent=0)


def title_fill(color="0099CCFF"):
    return PatternFill("solid", fgColor=color)    

def title_font(font='Calibri', size=12):
    return Font(name=font,
                     size=size,
                     bold=True,
                     italic=False,
                     vertAlign=None,
                     underline='none',
                     strike=False,
                     )    
                     
def s_border():
    return  Border(
        left=Side(border_style=borders.BORDER_THIN, color='FF000000'),
        right=Side(border_style=borders.BORDER_THIN, color='FF000000'),
        top=Side(border_style=borders.BORDER_THIN, color='FF000000'),
        bottom=Side(border_style=borders.BORDER_THIN, color='FF000000')
    )
