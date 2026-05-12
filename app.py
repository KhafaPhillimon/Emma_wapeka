import base64
import io
import pandas as pd
import dash
import dash_auth
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go

# --- Configuration & Constants ---
EXPECTED_COLUMNS = [
    'request_id', 'ip_address', 'timestamp', 'request_type', 
    'requested_resource', 'status_code', 'service_type', 
    'country', 'response_time', 'file_size'
]

external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap'
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title="Log Analytics", suppress_callback_exceptions=True)
server = app.server

# --- Clean SaaS Theme ---
COLORS = {
    'background': '#f8f9fa',
    'sidebar': '#ffffff',
    'card': '#ffffff',
    'border': '#eaedf1',
    'text': '#1f2937',
    'text_muted': '#6b7280',
    'primary': '#2563eb',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444'
}

CHART_TEMPLATE = "plotly_white"

# --- Layout ---
dashboard_layout = html.Div(style={
    'backgroundColor': COLORS['background'], 
    'fontFamily': 'Inter, sans-serif', 
    'minHeight': '100vh',
    'color': COLORS['text'],
    'display': 'flex',
    'flexDirection': 'column'
}, children=[
    
    # Header
    html.Div(style={
        'padding': '16px 32px', 
        'backgroundColor': '#ffffff', 
        'borderBottom': f"1px solid {COLORS['border']}",
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'position': 'sticky', 'top': '0', 'zIndex': '1000'
    }, children=[
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'}, children=[
            html.Img(src='/assets/logo.png', style={'height': '36px', 'objectFit': 'contain'}),
            html.H1("Web Server Analytics", style={'margin': '0', 'fontSize': '18px', 'fontWeight': '600', 'color': '#111827'}),
        ]),
        html.Div(style={'display': 'flex', 'gap': '24px', 'alignItems': 'center'}, children=[
            dcc.Link("Overview", href="/", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            dcc.Link("Traffic", href="/traffic", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            dcc.Link("Services", href="/services", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            dcc.Link("Geography", href="/geography", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            dcc.Link("Performance", href="/performance", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            dcc.Link("Errors", href="/errors", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            dcc.Link("Logs", href="/logs", style={'textDecoration': 'none', 'color': '#475569', 'fontWeight': '500', 'fontSize': '14px'}),
            html.Button("Logout", id='logout-button', n_clicks=0, style={
                'backgroundColor': 'transparent', 'border': f"1px solid {COLORS['danger']}", 
                'color': COLORS['danger'], 'padding': '6px 12px', 'borderRadius': '4px',
                'cursor': 'pointer', 'fontWeight': '600', 'fontSize': '12px', 'marginLeft': '12px'
            })
        ])
    ]),
    
    # Workspace
    html.Div(style={'display': 'flex', 'flex': '1', 'padding': '24px', 'gap': '24px', 'overflow': 'hidden'}, children=[
        
        # Sidebar
        html.Div(style={
            'width': '300px', 'backgroundColor': COLORS['sidebar'], 'borderRadius': '8px', 'padding': '24px',
            'border': f"1px solid {COLORS['border']}", 'display': 'flex', 'flexDirection': 'column', 'gap': '24px',
            'flexShrink': '0', 'overflowY': 'auto', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        }, children=[
            html.H3("Data Source", style={'fontSize': '14px', 'marginTop': '0', 'marginBottom': '12px', 'fontWeight': '600', 'color': COLORS['text_muted']}),
            
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.P('Click or drag CSV file here', style={'margin': '0', 'fontSize': '14px', 'fontWeight': '500', 'color': COLORS['primary']})
                ]),
                style={
                    'width': '100%', 'height': '80px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderColor': '#cbd5e1',
                    'borderRadius': '6px', 'textAlign': 'center', 'backgroundColor': '#f8fafc',
                    'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center', 'cursor': 'pointer'
                },
                multiple=False, accept='.csv'
            ),
            html.Div(id='upload-error', style={'color': COLORS['danger'], 'fontSize': '13px', 'fontWeight': '500'}),
            
            html.Div(id='filters-container', style={'display': 'none'}, children=[
                html.Hr(style={'borderColor': COLORS['border'], 'borderStyle': 'solid', 'borderTop': 'none', 'margin': '24px 0'}),
                html.H3("Filters", style={'fontSize': '14px', 'marginTop': '0', 'marginBottom': '16px', 'fontWeight': '600', 'color': COLORS['text_muted']}),
                
                html.Label("Service Type", style={'fontSize': '13px', 'fontWeight': '500', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(id='filter-service', multi=True, placeholder="All Services", style={'fontSize': '14px'}),
                
                html.Label("Status Code", style={'fontSize': '13px', 'fontWeight': '500', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(id='filter-status', multi=True, placeholder="All Status Codes", style={'fontSize': '14px'}),
                
                html.Label("Country", style={'fontSize': '13px', 'fontWeight': '500', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(id='filter-country', multi=True, placeholder="All Countries", style={'fontSize': '14px'}),
                
                html.Label("Request Type", style={'fontSize': '13px', 'fontWeight': '500', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(id='filter-request-type', multi=True, placeholder="All Types", style={'fontSize': '14px'}),
                
                html.Label("Date Range", style={'fontSize': '13px', 'fontWeight': '500', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}),
                dcc.DatePickerRange(
                    id='filter-date-range',
                    start_date_placeholder_text="Start Date",
                    end_date_placeholder_text="End Date",
                    display_format='YYYY-MM-DD',
                    style={'width': '100%'}
                ),
                
                html.Label("Anomalies", style={'fontSize': '13px', 'fontWeight': '500', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Checklist(
                    id='filter-anomalies',
                    options=[{'label': ' Show Anomalies Only', 'value': 'yes'}],
                    value=[],
                    style={'fontSize': '14px', 'color': COLORS['text']}
                )
            ])
        ]),
        
        # Main Content
        html.Div(style={'flex': '1', 'overflowY': 'auto'}, children=[
            dcc.Loading(
                id="loading", type="default", color=COLORS['primary'],
                children=html.Div(id='dashboard-content')
            )
        ])
    ])
])

login_layout = html.Div(style={
    'height': '100vh', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'backgroundColor': COLORS['background']
}, children=[
    html.Div(style={
        'backgroundColor': '#ffffff', 'padding': '40px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'width': '350px', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'
    }, children=[
        html.Img(src='/assets/logo.png', style={'height': '64px', 'marginBottom': '24px', 'objectFit': 'contain'}),
        html.H2("Sign In", style={'margin': '0 0 24px 0', 'color': COLORS['text'], 'fontWeight': '600', 'fontSize': '24px'}),
        dcc.Input(id='login-email', type='email', placeholder='Email', style={'width': '100%', 'height': '44px', 'padding': '0 16px', 'marginBottom': '16px', 'borderRadius': '6px', 'border': f"1px solid {COLORS['border']}", 'boxSizing': 'border-box', 'fontFamily': 'Inter', 'fontSize': '15px'}),
        dcc.Input(id='login-password', type='password', placeholder='Password', style={'width': '100%', 'height': '44px', 'padding': '0 16px', 'marginBottom': '24px', 'borderRadius': '6px', 'border': f"1px solid {COLORS['border']}", 'boxSizing': 'border-box', 'fontFamily': 'Inter', 'fontSize': '15px'}),
        html.Button('Login', id='login-button', n_clicks=0, style={'width': '100%', 'padding': '12px', 'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none', 'borderRadius': '6px', 'fontWeight': '600', 'cursor': 'pointer', 'fontFamily': 'Inter'}),
        html.Div(id='login-output', style={'color': COLORS['danger'], 'marginTop': '16px', 'fontSize': '14px', 'textAlign': 'center'})
    ])
])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='stored-data'),
    dcc.Store(id='auth-state', storage_type='session', data={'logged_in': False}),
    html.Div(id='page-content')
])

app.validation_layout = html.Div([
    app.layout,
    dashboard_layout,
    login_layout
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'), Input('auth-state', 'data')]
)
def render_page(pathname, auth_state):
    if auth_state and auth_state.get('logged_in'):
        return dashboard_layout
    return login_layout

@app.callback(
    [Output('auth-state', 'data'), Output('login-output', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('login-email', 'value'), State('login-password', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, email, password):
    if n_clicks > 0:
        if email == 'megan@gmail.com' and password == 'Megan123':
            return {'logged_in': True}, ""
        else:
            return dash.no_update, "Invalid email or password"
    return dash.no_update, dash.no_update

@app.callback(
    Output('auth-state', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks and n_clicks > 0:
        return {'logged_in': False}
    return dash.no_update

def create_card(children, flex='1', minWidth='0', height='auto', style_override=None):
    base_style = {
        'backgroundColor': COLORS['card'], 'borderRadius': '8px', 'border': f"1px solid {COLORS['border']}",
        'padding': '20px', 'flex': flex, 'minWidth': minWidth, 'height': height,
        'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'display': 'flex', 'flexDirection': 'column'
    }
    if style_override: base_style.update(style_override)
    return html.Div(style=base_style, children=children)

def create_summary_card(title, value):
    return create_card([
        html.H4(title, style={'margin': '0 0 8px 0', 'fontSize': '13px', 'fontWeight': '500', 'color': COLORS['text_muted']}),
        html.H2(value, style={'margin': '0', 'fontSize': '28px', 'fontWeight': '600', 'color': '#111827'})
    ], minWidth='200px')

def create_section_header(title):
    return html.H2(title, style={'margin': '24px 0 16px 0', 'fontSize': '18px', 'fontWeight': '600', 'color': '#111827'})

@app.callback(
    [Output('stored-data', 'data'), Output('upload-error', 'children'), Output('filters-container', 'style'),
     Output('filter-service', 'options'), Output('filter-service', 'value'),
     Output('filter-status', 'options'), Output('filter-status', 'value'),
     Output('filter-country', 'options'), Output('filter-country', 'value'),
     Output('filter-request-type', 'options'), Output('filter-request-type', 'value'),
     Output('filter-date-range', 'start_date'), Output('filter-date-range', 'end_date'),
     Output('filter-date-range', 'min_date_allowed'), Output('filter-date-range', 'max_date_allowed'),
     Output('filter-anomalies', 'value')],
    [Input('upload-data', 'contents')], [State('upload-data', 'filename')]
)
def process_upload(contents, filename):
    if contents is None:
        return dash.no_update, "", {'display': 'none'}, [], [], [], [], [], [], [], [], None, None, None, None, []
        
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if not filename.lower().endswith('.csv'): 
            return None, "Please upload a CSV.", {'display': 'none'}, [], [], [], [], [], [], [], [], None, None, None, None, []
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp', 'service_type', 'country', 'request_type', 'response_time'])
        df['response_time'] = pd.to_numeric(df['response_time'], errors='coerce')
        df = df.dropna(subset=['response_time'])
        
        df['z_score'] = df.groupby('service_type')['response_time'].transform(lambda x: (x - x.mean()) / x.std())
        df['is_anomaly'] = (df['z_score'].abs() > 2.5) | (df['status_code'].isin([404, 500]))
        
        df['timestamp_str'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['hour'] = df['timestamp'].dt.hour
        df['day_name'] = df['timestamp'].dt.day_name()
        
        services = sorted(df['service_type'].unique())
        statuses = sorted(df['status_code'].unique())
        countries = sorted(df['country'].unique())
        req_types = sorted(df['request_type'].unique())
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        
        return (
            df.to_dict('records'), "", {'display': 'block'}, 
            [{'label': s, 'value': s} for s in services], [], 
            [{'label': str(s), 'value': s} for s in statuses], [],
            [{'label': c, 'value': c} for c in countries], [],
            [{'label': r, 'value': r} for r in req_types], [],
            min_date, max_date, min_date, max_date, []
        )
    except Exception as e:
        return None, f"Error processing file: {str(e)}", {'display': 'none'}, [], [], [], [], [], [], [], [], None, None, None, None, []

@app.callback(
    Output('dashboard-content', 'children'),
    [Input('url', 'pathname'), Input('stored-data', 'data'), 
     Input('filter-service', 'value'), Input('filter-status', 'value'),
     Input('filter-country', 'value'), Input('filter-request-type', 'value'),
     Input('filter-date-range', 'start_date'), Input('filter-date-range', 'end_date'),
     Input('filter-anomalies', 'value')]
)
def update_dashboard(pathname, data, filter_service, filter_status, filter_country, filter_request_type, start_date, end_date, filter_anomalies):
    if not data:
        return html.Div(style={'height': '40vh', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}, children=[
            html.P("No data loaded. Upload a CSV file to view analytics.", style={'color': COLORS['text_muted'], 'fontSize': '15px'})
        ])
        
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp_str'])
    
    if filter_service: df = df[df['service_type'].isin(filter_service)]
    if filter_status: df = df[df['status_code'].isin(filter_status)]
    if filter_country: df = df[df['country'].isin(filter_country)]
    if filter_request_type: df = df[df['request_type'].isin(filter_request_type)]
    if start_date: df = df[df['timestamp'] >= pd.to_datetime(start_date)]
    if end_date: df = df[df['timestamp'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if filter_anomalies and 'yes' in filter_anomalies: df = df[df['is_anomaly'] == True]
        
    if df.empty:
        return html.P("No data matches the selected filters.", style={'color': COLORS['text_muted'], 'marginTop': '20px'})
        
    total_req = len(df)
    anomalies_detected = len(df[df['is_anomaly'] == True])
    pop_service = df['service_type'].value_counts().idxmax() if not df['service_type'].empty else "N/A"
    
    content = []
    
    summary_cards = html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap', 'marginBottom': '8px'}, children=[
        create_summary_card("Total Requests", f"{total_req:,}"),
        create_summary_card("Anomalies", f"{anomalies_detected:,}"),
        create_summary_card("Avg Latency", f"{df['response_time'].mean():.0f} ms"),
        create_summary_card("Latency Std Dev", f"{df['response_time'].std():.0f} ms"),
        create_summary_card("Primary Service", pop_service)
    ])
    content.append(summary_cards)
    
    chart_config = {'displayModeBar': False}

    if pathname in ['/', '/traffic']:
        df['hour_timestamp'] = df['timestamp'].dt.floor('h')
        vol_time = df.groupby('hour_timestamp').size().reset_index(name='Volume')
        fig_line = px.line(vol_time, x='hour_timestamp', y='Volume', title='Request Volume over Time', template=CHART_TEMPLATE)
        fig_line.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        heatmap_data = df.groupby(['day_name', 'hour']).size().reset_index(name='count')
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data['day_name'] = pd.Categorical(heatmap_data['day_name'], categories=days_order, ordered=True)
        heatmap_pivot = heatmap_data.pivot_table(index='day_name', columns='hour', values='count', fill_value=0)
        fig_heat = px.imshow(heatmap_pivot, x=heatmap_pivot.columns, y=heatmap_pivot.index, title="Traffic Density by Hour", template=CHART_TEMPLATE, aspect="auto")
        fig_heat.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        
        content.append(create_section_header("Traffic Volume"))
        content.append(html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
            create_card([dcc.Graph(figure=fig_line, config=chart_config)], flex='2', minWidth='500px'),
            create_card([dcc.Graph(figure=fig_heat, config=chart_config)], flex='1', minWidth='350px')
        ]))

    if pathname in ['/', '/services']:
        service_counts = df['service_type'].value_counts().reset_index()
        service_counts.columns = ['Service', 'Count']
        fig_pie = px.pie(service_counts, names='Service', values='Count', title='Service Request Frequencies', template=CHART_TEMPLATE, hole=0.4)
        fig_pie.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        fig_scatter = px.scatter(df, x='file_size', y='response_time', color='service_type', title='Response Time vs File Size', template=CHART_TEMPLATE, opacity=0.6)
        fig_scatter.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        
        content.append(create_section_header("Service Usage & Correlation"))
        content.append(html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
            create_card([dcc.Graph(figure=fig_pie, config=chart_config)], flex='1', minWidth='350px'),
            create_card([dcc.Graph(figure=fig_scatter, config=chart_config)], flex='2', minWidth='500px')
        ]))

    if pathname in ['/', '/geography']:
        country_counts = df['country'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Requests']
        fig_map = px.choropleth(
            country_counts, locations="Country", locationmode="country names",
            color="Requests", color_continuous_scale="Blues", title="Global Traffic Distribution", template=CHART_TEMPLATE
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0), geo=dict(showframe=False, projection_type='orthographic', showocean=True, oceancolor="#f0f4f8"))
        
        content.append(create_section_header("Geographic Distribution"))
        content.append(html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
            create_card([dcc.Graph(figure=fig_map, config=chart_config)], flex='1', minWidth='500px')
        ]))

    if pathname in ['/', '/performance']:
        df_sorted = df.sort_values('timestamp').copy()
        df_sorted['rolling_avg'] = df_sorted['response_time'].rolling(window=50, min_periods=1).mean()
        df_roll_sample = df_sorted.iloc[::max(1, len(df_sorted)//1000)]
        fig_roll = px.line(df_roll_sample, x='timestamp', y='rolling_avg', title='Response Time Moving Average', template=CHART_TEMPLATE)
        fig_roll.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        fig_box = px.box(df, x='service_type', y='response_time', title='Response Time by Service', template=CHART_TEMPLATE)
        fig_box.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        fig_hist = px.histogram(df, x='response_time', nbins=50, title='Response Time Distribution', template=CHART_TEMPLATE)
        fig_hist.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        
        content.append(create_section_header("Performance"))
        content.append(html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
            create_card([dcc.Graph(figure=fig_roll, config=chart_config)], flex='2', minWidth='500px'),
            create_card([dcc.Graph(figure=fig_box, config=chart_config)], flex='1', minWidth='300px')
        ]))
        content.append(html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
            create_card([dcc.Graph(figure=fig_hist, config=chart_config)], flex='1')
        ]))

    if pathname in ['/', '/errors']:
        stack_data = df.groupby(['request_type', 'status_code']).size().reset_index(name='Count')
        stack_data['status_code'] = stack_data['status_code'].astype(str)
        fig_stack = px.bar(stack_data, x='request_type', y='Count', color='status_code', title='Status Code by Request Type', template=CHART_TEMPLATE)
        fig_stack.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        err_data = df[df['status_code'].isin([404, 500])]
        err_counts = err_data['status_code'].astype(str).value_counts().reset_index(name='Frequency')
        fig_err = px.bar(err_counts, x='status_code', y='Frequency', title='Error Frequency', template=CHART_TEMPLATE)
        fig_err.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        
        content.append(create_section_header("Errors & Diagnostics"))
        content.append(html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
            create_card([dcc.Graph(figure=fig_stack, config=chart_config)], flex='1', minWidth='300px'),
            create_card([dcc.Graph(figure=fig_err, config=chart_config)], flex='1', minWidth='300px')
        ]))

    if pathname in ['/', '/logs']:
        anomaly_df = df[df['is_anomaly'] == True].sort_values('timestamp', ascending=False)
        table_data = anomaly_df[['timestamp_str', 'ip_address', 'service_type', 'status_code', 'response_time', 'z_score']].to_dict('records')
        for row in table_data: row['z_score'] = f"{row['z_score']:.2f}"

        diagnostics_table = dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Timestamp", "id": "timestamp_str"},
                {"name": "IP Address", "id": "ip_address"},
                {"name": "Service", "id": "service_type"},
                {"name": "Status", "id": "status_code"},
                {"name": "Latency (ms)", "id": "response_time"},
                {"name": "Z-Score", "id": "z_score"}
            ],
            page_size=10,
            style_table={'overflowX': 'auto', 'marginTop': '16px'},
            style_header={'backgroundColor': '#f9fafb', 'color': COLORS['text'], 'fontWeight': '600', 'border': f"1px solid {COLORS['border']}", 'textAlign': 'left'},
            style_cell={'color': COLORS['text'], 'border': f"1px solid {COLORS['border']}", 'textAlign': 'left', 'padding': '12px', 'fontSize': '13px'},
            sort_action="native"
        )
        content.append(create_card([
            html.H3("Diagnostic Log", style={'margin': '0 0 4px 0', 'fontSize': '15px', 'fontWeight': '600'}),
            html.P("Filtered view of anomalies and errors.", style={'margin': '0 0 16px 0', 'fontSize': '13px', 'color': COLORS['text_muted']}),
            diagnostics_table
        ]))

    return html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '16px', 'paddingBottom': '40px'}, children=content)

if __name__ == '__main__':
    app.run(debug=True)
