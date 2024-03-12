import dash
#import dash_core_components as dcc
from dash import dcc
#import dash_html_components as html
from dash import html
import pickle
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import lightgbm as lgb
import plotly.express as px

# Improved CSS Styling (place this in a separate CSS file)
#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets = ['path/to/bodyEstilo.css']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', "C:/RepositorioProyectoCaro/h-transport-materials-dashboard/styles.css"] # Aquí se carga el archivo CSS personalizado


# Carga de los modelos
def load_model(model_name):
    with open(f'{model_name}.pkl', 'rb') as f:
        return pickle.load(f)
    

models = {
    'COM': load_model("C:/RepositorioProyectoCaro/h-transport-materials-dashboard/modelo_completo_2"),
    'FIN': load_model("C:/RepositorioProyectoCaro/h-transport-materials-dashboard/modelo_finishing_2"),
    'SEW': load_model("C:/RepositorioProyectoCaro/h-transport-materials-dashboard/modelo_sweing_2")
}

# Función de predicción
def predict(model, parameters):
    # Conversión del número de equipo a formato dummy
    for i in range(1, 13):
        if i == parameters['team']:
            parameters['team_' + str(i)] = 1
        else:
            parameters['team_' + str(i)] = 0
    del parameters['team']
    
    # Convertir el diccionario a DataFrame
    data = pd.DataFrame([parameters])

    # Convertir todas las columnas a tipos numéricos
    data = data.apply(pd.to_numeric)

    return model.predict(data)

# Inicializando la aplicación
#app = dash.Dash(__name__)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Definiendo el layout de la aplicación
# Definiendo el layout de la aplicación
app.layout = html.Div(style={'backgroundColor': '#F8F8FF', 'color': '#000000', 'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gridColumnGap': '20px'}, children=[
        
    html.Div([
        html.H1("Análisis de productividad", style={'text-align': 'left', 'font-size': '42px', 'font-weight': 'bold', 'font-family': 'Arial, sans-serif'}),  # Centered heading
        html.H2("Ingrese los parámetros", style={'text-align': 'left','color':'purple','font-size': '36px', 'font-weight': 'bold', 'font-family': 'Arial, sans-serif'}),
    ]),
    
    html.Div(style={'grid-column': '2 / 2', 'height': '5px'}),  # Espacio en blanco
    
    html.Div(className='model-selection', children=[  # Improved input container class
        html.Label('Seleccione el modelo de regresión',style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Dropdown(
            id='model-selection',
            options=[
                {'label': 'Finishing', 'value': 'FIN'},
                {'label': 'Sewing', 'value': 'SEW'},
                {'label': 'Modelo completo', 'value': 'COM'}
            ],
            value='COM',
            className='dropdown-custom'  # Custom class for styling
        )
    ]),

    html.Div(id='output-area'),

    html.Div(className='input-container', children=[  # Improved input container class
        html.Label("Ingrese el overtime",style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Input(
            id='overtime-input',
            type='number',
            value=0,
            className='input-custom'  # Custom class for styling
        )
    ]),

    html.Div(className='input-container', children=[
        html.Label("Ingrese el valor de smv",style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Input(
            id='smv-input',
            type='number',
            value=0,
            className='input-custom'
        )
    ]),

    html.Div(className='input-container', children=[
        html.Label("Ingrese el número de trabajadores",style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Input(
            id='workers-input',
            type='number',
            value=0,
            className='input-custom'
        )
    ]),



    html.Div(className='input-container', children=[
        html.Label("Ingrese el valor de incentivo",style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Input(
            id='incentive-input',
            type='number',
            value=0,
            className='input-custom'
        )
    ]),
    

    html.Div(className='input-container', children=[
        html.Label("Seleccione el equipo",style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Dropdown(
            id='team-input',
            options=[{'label': i, 'value': i} for i in range(1, 13)],
            value=1,
            className='input-custom'
        )
    ]),
    

    html.Div(className='slider-container', children=[  # Improved container class
        html.Label("Seleccione la productividad objetivo",style={'text-align': 'left','font-size': '18px','font-weight': 'bold'}),
        dcc.Slider(
            id='productivity-slider',
            min=0,
            max=1,
            step=0.1,
            value=0.5,
            marks={round(i/10, 2): str(round(i/10,2)) for i in range(0, 11, 1)},
            className='slider-custom'  # Custom class for styling
        )
    ]),

    html.Div(id='slider-output'),

    # Output para mostrar los equipos ordenados por productividad
    html.Div(id='teams-output', style={'grid-column': '1 / 1'}),
    
    # Gráfico de barras para mostrar la productividad de todos los equipos
    html.Div(className='right-container', children=[
            dcc.Graph(id='productivity-bar-chart')
        ]),
    
    
])


# Actualizar la salida y el gráfico de barras de productividad cuando se cambian los parámetros
@app.callback(
    [Output('output-area', 'children'),
     Output('productivity-bar-chart', 'figure'),
     Output('teams-output', 'children')],
    [Input('model-selection', 'value'),
     Input('overtime-input', 'value'),
     Input('workers-input', 'value'),
     Input('smv-input', 'value'),
     Input('incentive-input', 'value'),
     Input('team-input', 'value'),
     Input('productivity-slider', 'value')]
)
def update_output_and_graph(model_name, overtime, workers, smv, incentive, team, productivity):
    model = models[model_name]
    parameters = {'incentive': incentive, 'targeted_productivity': productivity, 'team': team, 'smv': smv, 'over_time': overtime, 'no_of_workers': workers}
    predictions = []
    for i in range(1, 13):
        parameters['team'] = i
        prediction = predict(model, parameters)
        predictions.append(prediction[0])  # Convertir el resultado a un valor numérico
    
    # Ordenar los equipos por productividad
    teams_sorted = [team for _, team in sorted(zip(predictions, range(1, 13)), reverse=True)]
    
    # Crear el gráfico de barras de productividad para todos los equipos
    fig = px.bar(x=teams_sorted, y=predictions, color=predictions)#, color_continuous_scale='Viridis')
    fig.update_layout(title='Productividad de todos los equipos', xaxis_title='Equipo', yaxis_title='Productividad')
    fig.update_yaxes(range=[0.4, max(predictions)])  # Establecer el rango del eje y desde 0.3 hasta el máximo de las predicciones
    
    # Formato del mensaje de productividad estimada
    
    # Formatear la salida de la productividad estimada
    formatted_prediction = f"{predictions[team-1]*100:.2f}%"  # Convertir a porcentaje con 2 decimales
    formatted_output = html.Div([
        html.H3("La productividad actual estimada es", style={'text-align': 'center','font-size': '36px'}),  # Encabezado centrado
        html.H1(formatted_prediction, style={'text-align': 'center', 'font-size': '48px', 'color': 'purple', 'background-color': 'lightgrey'})  # Número grande con fondo de color
    ])
    
    # Crear la lista ordenada de equipos para mostrar como salida
    teams_output = html.Div([
    html.H3("Equipos ordenados por productividad", style={'text-align': 'center', 'font-size': '18px'}),
    html.Ol([html.Li(f"Equipo {team}") for team in teams_sorted], style={'text-align': 'center'})
    ])

    return formatted_output, fig, teams_output

# Iniciando la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)