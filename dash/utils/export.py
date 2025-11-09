"""
Data Export Utilities
Functions to export data in various formats
"""
import pandas as pd
import io
import base64
from dash import html, dcc
import dash_bootstrap_components as dbc
import json

def create_excel_download_link(df, filename="data.xlsx", button_text="📥 Download Excel"):
    """
    Create a download button for Excel file

    Args:
        df: pandas DataFrame
        filename: Name of file
        button_text: Text for button

    Returns:
        html.A component with download link
    """
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            # Add formatting
            workbook = writer.book
            worksheet = writer.sheets['Data']
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4f46e5',
                'font_color': 'white'
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

        output.seek(0)
        b64 = base64.b64encode(output.read()).decode()

        return html.A(
            dbc.Button(button_text, color='success', size='sm', className='me-2'),
            href=f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}",
            download=filename
        )
    except Exception as e:
        return dbc.Alert(f"Error creating Excel: {str(e)}", color='warning')

def create_csv_download_link(df, filename="data.csv", button_text="📥 Download CSV"):
    """Create a download button for CSV file"""
    try:
        csv_string = df.to_csv(index=False, encoding='utf-8')
        b64 = base64.b64encode(csv_string.encode()).decode()

        return html.A(
            dbc.Button(button_text, color='info', size='sm', className='me-2'),
            href=f"data:text/csv;base64,{b64}",
            download=filename
        )
    except Exception as e:
        return dbc.Alert(f"Error creating CSV: {str(e)}", color='warning')

def create_json_download_link(data, filename="data.json", button_text="📥 Download JSON"):
    """Create a download button for JSON file"""
    try:
        json_string = json.dumps(data, indent=2)
        b64 = base64.b64encode(json_string.encode()).decode()

        return html.A(
            dbc.Button(button_text, color='warning', size='sm', className='me-2'),
            href=f"data:application/json;base64,{b64}",
            download=filename
        )
    except Exception as e:
        return dbc.Alert(f"Error creating JSON: {str(e)}", color='warning')

def create_export_panel(df, prefix="export", formats=['excel', 'csv']):
    """
    Create a complete export panel with multiple format options

    Args:
        df: pandas DataFrame to export
        prefix: Filename prefix
        formats: List of formats to include ['excel', 'csv', 'json']

    Returns:
        dbc.Card with export buttons
    """
    if df is None or df.empty:
        return dbc.Alert("No data available to export", color='info')

    buttons = []

    if 'excel' in formats:
        buttons.append(create_excel_download_link(df, f"{prefix}.xlsx"))

    if 'csv' in formats:
        buttons.append(create_csv_download_link(df, f"{prefix}.csv"))

    if 'json' in formats:
        data_dict = df.to_dict(orient='records')
        buttons.append(create_json_download_link(data_dict, f"{prefix}.json"))

    return dbc.Card([
        dbc.CardHeader(html.H6("📤 Export Data", className='mb-0')),
        dbc.CardBody([
            html.Div(buttons, className='d-flex flex-wrap gap-2'),
            html.Small(f"Exporting {len(df)} rows, {len(df.columns)} columns",
                      className='text-muted d-block mt-2')
        ])
    ], className='mt-3')

def format_dataframe_for_display(df, max_rows=100):
    """
    Format DataFrame for better display

    Args:
        df: pandas DataFrame
        max_rows: Maximum rows to display

    Returns:
        Formatted DataFrame
    """
    if len(df) > max_rows:
        df_display = df.head(max_rows).copy()
        df_display.loc['...'] = ['...'] * len(df.columns)
    else:
        df_display = df.copy()

    # Format numeric columns
    for col in df_display.select_dtypes(include=['float']).columns:
        df_display[col] = df_display[col].apply(lambda x: f'{x:.2f}' if pd.notna(x) else '')

    return df_display
