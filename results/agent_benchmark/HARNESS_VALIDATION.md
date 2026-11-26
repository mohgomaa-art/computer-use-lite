# Step 3: 20-Task Agent Benchmark (oracle_harness_validation_only)

Harness deterministic validation (**NO LLM inference executed**): `20/20` passed.

| Task | Surface | Passed | Engine ms | Wall ms | Map Est Tok | Screenshot Cap ms | Cap Src |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| b01_order_form | browser | True | 151.33 | 154.33 | 141.6 | 28.79 | playwright |
| b02_password_redaction | browser | True | 223.12 | 241.12 | 139.5 | 39.1 | playwright |
| b03_scrolled_target | browser | True | 63.42 | 155.24 | 37.8 | 47.7 | playwright |
| b04_dynamic_drawer | browser | True | 293.18 | 297.88 | 55.8 | 60.9 | playwright |
| b05_modal_occlusion | browser | True | 105.11 | 108.26 | 47.4 | 50.47 | playwright |
| b06_custom_div_switch | browser | True | 118.08 | 135.82 | 90.0 | 53.64 | playwright |
| b07_open_shadow_dom | browser | True | 175.17 | 179.39 | 75.0 | 62.67 | playwright |
| b08_closed_shadow_dom | browser | True | 67.48 | 70.7 | 23.2 | 46.7 | playwright |
| b09_cross_origin_oopif | browser | True | 92.7 | 92.72 | 25.5 | 59.53 | playwright |
| b10_hover_reveal_menu | browser | True | 194.64 | 198.8 | 23.5 | 38.16 | playwright |
| b11_dense_90_grid_filter | browser | True | 126.78 | 131.13 | 664.0 | 52.05 | playwright |
| b12_opaque_canvas_click | browser | True | 58.79 | 67.22 | 57.5 | 32.85 | playwright |
| d01_notepad_write_report | desktop | True | 205.77 | 397.33 | 469.2 | 180.38 | printwindow |
| d02_notepad_replace_text | desktop | True | 191.88 | 366.67 | 466.8 | 47.52 | printwindow |
| d03_notepad_new_tab | desktop | True | 251.86 | 759.7 | 465.2 | 43.3 | printwindow |
| d04_explorer_view_toggle | desktop | True | 1389.26 | 1725.4 | 704.5 | 158.61 | printwindow |
| d05_chromium_desktop_checkbox | desktop | True | 62.93 | 105.08 | 172.0 | 38.2 | printwindow |
| d06_chromium_desktop_tabs | desktop | True | 75.94 | 108.82 | 177.8 | 41.85 | printwindow |
| d07_chromium_desktop_form | desktop | True | 389.04 | 493.47 | 182.8 | 41.95 | printwindow |
| d08_desktop_stale_fg_safety | desktop | True | 48.5 | 78.23 | 170.5 | 27.6 | printwindow |
