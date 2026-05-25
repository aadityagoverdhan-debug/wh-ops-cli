import time

def read_sheet(service, spreadsheet_id, range_str, value_render="FORMATTED_VALUE"):
    """Read a single range from a spreadsheet."""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        valueRenderOption=value_render,
    ).execute()
    return result.get('values', [])

def read_sheet_chunked(service, spreadsheet_id, sheet_name, total_rows,
                       cols="A:AA", chunk_size=3000, value_render="UNFORMATTED_VALUE"):
    """Read a large sheet in chunks. Returns all data rows (no header)."""
    all_rows = []
    for start in range(2, total_rows + 1, chunk_size):
        end = min(start + chunk_size - 1, total_rows)
        range_str = f"{sheet_name}!{cols.split(':')[0]}{start}:{cols.split(':')[1]}{end}"
        for attempt in range(3):
            try:
                rows = read_sheet(service, spreadsheet_id, range_str, value_render)
                all_rows.extend(rows)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise
    return all_rows
