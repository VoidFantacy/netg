# Source-row manifest schema correction

The first metadata-only audit stopped at its expected 45000 distinct source-row
assertion. A recursive integer-list walk had also collected the two endpoints
of source_range. The corrected version reads only the structured
selected_source_rows object and validates its three split keys. The original
script is retained. No fresh query/GT payload or new training input was opened,
and the already frozen E119 training protocol/model is unchanged.
