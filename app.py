import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from dash import dash_table
import re
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template


# Cargar variables de ambiente
load_dotenv()
DESARROLLO = os.getenv("DESARROLLO")
ESTILO = os.getenv("ESTILO")
ROOT_PASS = os.getenv("ROOT_PASS")


if  DESARROLLO == "True":
    host = "0.0.0.0"
    port = "1234"
else:
    host = "mysql"
    port = "3306"

print(host, port, ROOT_PASS )
con = create_engine(f'mysql+mysqlconnector://root:{ROOT_PASS}@{host}:{port}/votaciones')

# Crear la aplicación Dash
load_figure_template(ESTILO)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])


# Esta línea es para poder correr la aplicación con gunicorn
server = app.server


filtered_df = pd.DataFrame({
    "id_phrase": [""],
    "text": [""]
})


# Definir el diseño del dashboard
app.layout = html.Div([

    ### Primer panel
    dcc.Tabs([
        dcc.Tab(label='W-NOMINATE', children=[

    html.Div([
    html.H1("NOMINATE a través del tiempo"),
    html.Div([
    dcc.Dropdown(
        id='dropdown_año',
        options= [num for num in range(2002, 2024 + 1)],
        value=2021
    ),
    dcc.Graph(id='bar-chart')
        ] , style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'} ),

  html.Div([
    dcc.Graph(id='all-parties')
            ] , style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'} )

        ]),

    html.Div([

    html.Div([
    dcc.Graph(id='1d-nominate')
            ] , style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'} )

            ])

    ]),


        #### SEGUNDO PANEL 
        dcc.Tab(label='DISCURSOS', children=[
               html.Div([

                   

            dcc.Input(id='input_box', type='text', placeholder='Ingrese texto aquí',  debounce = True),
            dcc.Loading(
                id="loading-1",
                type="default",
                children = dash_table.DataTable(
                    id='tabla1-pestaña2',
                    data = filtered_df.to_dict('records'),
                    
                    style_data_conditional=[
                            {'if': {'column_id': 'text'},
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'minWidth': '300px'}
    
                        ],
                    style_cell={'textAlign': 'left'},
                    
                    )
            ) 
            
                

                    ])

        ])

    ])

])


##########################
# AQUÍ EMPIEZA EL SERVIDOR
##########################

# Definir la función de callback para actualizar el gráfico según el año seleccionado
@app.callback(
    Output('bar-chart', 'figure'),
    Output('all-parties', 'figure'),
    Output('1d-nominate', 'figure'),
    [Input('dropdown_año', 'value')],
)




def update_first_tab(dropdown_año):
    
    df = pd.read_sql(sql= f"SELECT party, AVG(coord1D) AS media \
                  from votaciones.nominateByYear \
                  where year = '{dropdown_año}' AND party in ('PS', 'UDI', 'PC', 'PPD' , 'PCS', 'RN', 'EVOP', \
                  'RD',  'DC', 'PREP' ) \
                  group by party", con=con)

    categorias_ordenadas = [x for _, x in sorted(zip(df.media, df.party))]
    valores_y_ordenados = sorted(df.media)


    fig1 = px.scatter(
        y=categorias_ordenadas,
        x=valores_y_ordenados,
        height=500,
        title="Posicionamiento partidos W-NOMINATE 1D",

        labels={
                     "x": "NOMINATE",
                     "y": "",
                 }

    )


    df2 = pd.read_sql(sql=f"SELECT party, coord1D, coord2D \
                      from votaciones.nominateByYear \
                      where year = '{dropdown_año}' AND party in ('PS', 'UDI', 'PC', 'PPD' , 'PCS', 'RN', 'EVOP', \
                      'RD',  'DC', 'PREP' )", con=con)

    #print(df2)
    fig2 = px.scatter(
        df2,
        y="coord2D",
        x="coord1D",
        color="party",
        height=500,
        title="Posicionamiento políticos W-NOMINATE 2D",

    )




    df4 = pd.read_sql(sql=f"SELECT name, party, coord1D \
                  from votaciones.nominateByYear \
                  where year = '{dropdown_año}' AND party in ('PS', 'UDI', 'PC', 'PPD' , 'PCS', 'RN', 'EVOP', \
                  'RD',  'DC', 'PR', 'PREP', 'PDG', 'DEM' )", con=con)

    df4 = df4.sort_values(by= "coord1D",ascending=False)

    fig3 = px.scatter(
        df4,
        y= "name",
        x= "coord1D",
        height=1000,
        color = "party",
        title="Posicionamiento político NOMINATE 1D",
        category_orders={"name": df4["name"].tolist()},

        labels = {
            "coord1D" : "NOMINATE", 
            "name" : ""  
        }

    )
    return fig1, fig2 , fig3



@app.callback(
    Output('tabla1-pestaña2', 'data'),
    [Input('input_box', 'value')]
)

 
def update_second_tab(input_box):

    if input_box is not None and input_box != '':


        filtered_df = pd.read_sql(sql=f"select id_phrase , text, score \
                                        FROM ( \
                                        SELECT  id_phrase , text, MATCH (text) AGAINST ('{input_box}') AS conteo, score \
                                        FROM votaciones.discursos d  \
                                           ) conteo \
                                        where conteo.conteo > 0 \
                                        order by score Desc    \
                                        limit 1000", 
                                    con=con)    
        print(f"Filtré la tabla usando la palabra {input_box}") 
        return filtered_df.to_dict('records')
    else:
        return []
    

    

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
