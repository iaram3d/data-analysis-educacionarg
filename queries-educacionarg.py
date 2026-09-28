## Analisis de datos de bbdd sobre establecimientos educativos y productivos en Argentina
## Iara Medina

## Descripcion: limpieza de datos, creacion de modelos relacionales, visualizacion.

import pandas as pd
import duckdb as dd
import seaborn as sns
import matplotlib.pyplot as plt

carpeta = "TablasOriginales"

ee = pd.read_csv(carpeta + '/2022_padron_oficial_establecimientos_educativos - padron2022.csv', skiprows =6, na_values=['', ' ', '-', 'N/D', 'N/A', '0', 's/n', 'S/N', 'sn'])

ep = pd.read_csv(carpeta + '/Datos_por_departamento_actividad_y_sexo.csv')

ep2 = pd.read_csv(carpeta + '/actividades_establecimientos.csv')

poblacion = pd.read_csv(carpeta + '/padron_poblacion.xlsX - Output.csv', skiprows =12)

# Exploracion de los datos de establecimientos educativos

ee_cpnull = ee['C. P.'].isnull().sum() * 100 / len(ee)
print('Porcentaje de nulls en CP: ', round(ee_cpnull,2))

ee_codareanull = ee['Código de área'].isnull().sum() * 100 / len(ee)
print('Porcentaje de nulls en Codigo de Area: ', round(ee_codareanull,2))

ee_direccionesnull = ee['Domicilio'].isnull().sum() * 100 / len(ee)
print('Porcentaje de nulls en Direcciones: ', round(ee_direccionesnull,2))

ee_sinstr = ee['Teléfono'].astype(str).str.replace(r'\D', '', regex=True).copy()
ee_sinstr = ee_sinstr.replace('', pd.NA)
ee_invalidos = pd.to_numeric(ee_sinstr, errors='coerce')
ee_invalidos.loc[ee_invalidos < 99999] = pd.NA
ee_cuentanull = ee_invalidos.isnull().sum()
ee_porcentaje = ee_cuentanull * 100 / len(ee)
print('Porcentaje de telefonos nulls e invalidos: ', round(ee_porcentaje, 2))


ee_mailsinarr = (~ee['Mail'].str.contains('@', na= False)).sum()
ee_mailnull = ee_mailsinarr * 100 / len(ee)
print('Porcentaje de mails nulls e invalidos: ', round((ee_mailnull), 2))

# Exploracion de los datos de establecimientos productivos

ep_sacararea = ep['in_departamentos'].copy()
ep_sacararea = ep_sacararea // 1000
ep_porcentajetot = (ep_sacararea == ep['provincia_id']).sum() * 100 / len(ep)
print(round(ep_porcentajetot, 2))


# Construccion de modelos relacionales

df_ee = ee[ee['Común'] == 1].copy()
df_ee = df_ee[['Jurisdicción', 'Cueanexo', 'Nombre', 'Departamento']]
df_ee.columns = ['provincia', 'CUE_anexo', 'nombre', 'departamento']
df_ee = df_ee.reset_index(drop=True)

diccionariotildes = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u',
                     'Á':'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U',
                     'ñ': 'ni', 'Ñ': 'Ni'}

df_ee['provincia'] = df_ee['provincia'].replace(diccionariotildes, regex=True)
df_ee['provincia'] = df_ee['provincia'].replace('Ciudad de Buenos Aires', 'CABA')
df_ee['provincia'] = df_ee['provincia'].str.lower()

df_ee['departamento'] = df_ee['departamento'].replace(diccionariotildes, regex=True)
df_ee['departamento'] = df_ee['departamento'].str.lower()

df_ep = ep[ep['anio'] == 2022].copy()
df_ep = df_ep.drop(['clae2', 'letra','Establecimientos', 'anio','provincia_id'], axis=1)
df_ep.columns = ['id_departamento', 'departamento', 'provincia', 'clae6', 'genero', 'empleados', 'empresas_exportadoras']
df_ep = df_ep.reset_index(drop=True)

df_ep['provincia'] = df_ep['provincia'].replace(diccionariotildes, regex=True)
df_ep['provincia'] = df_ep['provincia'].str.lower()

df_ep['departamento'] = df_ep['departamento'].replace(diccionariotildes, regex=True)
df_ep['departamento'] = df_ep['departamento'].str.lower()

aux_ep = dd.query("""SELECT DISTINCT id_departamento, clae6
                     FROM df_ep
                     ;""").df()

aux_ep['id_produccion'] = range(1, len(aux_ep)+1)

df_ep = dd.query("""SELECT aux_ep.id_produccion, df_ep.*
                    FROM df_ep
                    INNER JOIN aux_ep
                    ON aux_ep.clae6 = df_ep.clae6
                    WHERE aux_ep.id_departamento = df_ep.id_departamento
                    ;""").df()


df_departamento = df_ep[['id_departamento', 'departamento', 'provincia']].copy()
df_departamento = dd.query(""" SELECT DISTINCT id_departamento AS ID, departamento, provincia
                               FROM df_departamento 
                               ORDER BY ID 
                               ;""").df() 

                    
df_ee = dd.query("""SELECT df_departamento.ID AS id_departamento, df_ee.CUE_anexo, df_ee.nombre
                 FROM df_ee
                 INNER JOIN df_departamento
                 ON df_departamento.departamento = df_ee.departamento
                 WHERE df_departamento.provincia = df_ee.provincia
                 ;""").df()                    


df_emp = df_ep[['id_produccion', 'genero', 'empleados']].copy()

df_ep = dd.query("""SELECT DISTINCT id_produccion, id_departamento, clae6, empresas_exportadoras
                    FROM df_ep
                    ;""").df()

aux_maternal = ee[ee['Nivel inicial - Jardín maternal'] == 1].copy()
aux_maternal = aux_maternal[['Cueanexo']]
aux_maternal.columns = ['CUE_anexo']
aux_maternal['nivel'] = 'maternal'

aux_jardin = ee[ee['Nivel inicial - Jardín de infantes'] == 1].copy()
aux_jardin = aux_jardin[['Cueanexo']]
aux_jardin.columns = ['CUE_anexo']
aux_jardin['nivel'] = 'inicial'

aux_primario = ee[ee['Primario'] == 1].copy()
aux_primario = aux_primario[['Cueanexo']]
aux_primario.columns = ['CUE_anexo']
aux_primario['nivel'] = 'primario'

aux_secundario = ee[(ee['Secundario'] == 1) | (ee['Secundario - INET'] == 1)].copy()
aux_secundario = aux_secundario[['Cueanexo']]
aux_secundario.columns = ['CUE_anexo']
aux_secundario['nivel'] = 'secundario'

aux_superior = ee[(ee['SNU'] == 1) | (ee['SNU - INET'] == 1)].copy()
aux_superior = aux_superior[['Cueanexo']]
aux_superior.columns = ['CUE_anexo']
aux_superior['nivel'] = 'superior'

df_niv = dd.query(""" SELECT *
                      FROM aux_maternal
                      UNION ALL 
                      SELECT *
                      FROM aux_jardin
                      UNION ALL
                      SELECT *
                      FROM aux_primario
                      UNION ALL
                      SELECT * 
                      FROM aux_secundario
                      UNION ALL
                      SELECT *
                      FROM aux_superior
                      ORDER BY CUE_anexo
                       ;""").df()

poblacion.columns=['1','2','3','4','5']
poblacionbis = poblacion[['2', '3']].copy()

df_poblacion = pd.DataFrame()
df_poblacion['id_departamento'] = df_departamento['ID'].copy()
df_poblacion['Maternal'] = pd.NA
df_poblacion['Inicial'] = pd.NA
df_poblacion['Primario'] = pd.NA
df_poblacion['Secundario'] = pd.NA
df_poblacion['Jovenes'] = pd.NA
df_poblacion['Adultos'] = pd.NA
df_poblacion['Tercera edad'] = pd.NA
df_poblacion.set_index(['id_departamento'], inplace=True)


poblacion = poblacion.astype(str)
poblacion = poblacion.replace(' ','', regex=True)

for i in range(0,len(poblacion)):
    
    maternal = 0 
    inicial = 0
    primario = 0 
    secundario = 0
    jovenes = 0
    adultos = 0
    tercera_edad = 0
    
    if poblacion.loc[i, '2'][0:4] == 'AREA':
        if poblacion.loc[i, '2'][5] == '0':
            numero = poblacion.loc[i, '2'][6:10]
        else:
            numero = poblacion.loc[i, '2'][5:10] 
        
        numero = int(numero)
        
        datos = []
        
        j = i + 3
        
        while poblacion.loc[j, '2'][0:5] != 'Total':
            edad = poblacion.loc[j, '2']
            casos = poblacion.loc[j, '3']
            datos.append([edad,casos])
            j += 1
        
        bloque = pd.DataFrame(datos)
        bloque.columns=['Edad', 'Casos']
        bloque['Edad'] = bloque['Edad'].astype(int)
        bloque['Casos'] = bloque['Casos'].astype(int)
        
        for k in range(0, len(bloque)):
            if bloque.loc[k, 'Edad'] < 3:
                maternal += bloque.loc[k, 'Casos']
            elif bloque.loc[k, 'Edad'] < 6:
                inicial += bloque.loc[k, 'Casos']
            elif bloque.loc[k, 'Edad'] < 13:
                primario += bloque.loc[k, 'Casos']
            elif bloque.loc[k, 'Edad'] < 19:
                secundario += bloque.loc[k, 'Casos']
            elif bloque.loc[k, 'Edad'] < 31:
                jovenes += bloque.loc[k, 'Casos']
            elif bloque.loc[k, 'Edad'] < 71:
                adultos += bloque.loc[k, 'Casos']
            else:
                tercera_edad += bloque.loc[k, 'Casos']
        
        df_poblacion.loc[numero, 'Maternal'] = maternal
        df_poblacion.loc[numero, 'Inicial'] = inicial
        df_poblacion.loc[numero, 'Primario'] = primario
        df_poblacion.loc[numero, 'Secundario'] = secundario
        df_poblacion.loc[numero, 'Jovenes'] = jovenes
        df_poblacion.loc[numero, 'Adultos'] = adultos
        df_poblacion.loc[numero, 'Tercera edad'] = tercera_edad

nulls_poblacion = df_poblacion[df_poblacion.isnull().all(axis=1)]

df_poblacion.loc[94014] = df_poblacion.loc[94015]
df_poblacion = df_poblacion.drop(94015)

df_poblacion.loc[94007] = df_poblacion.loc[94008]
df_poblacion = df_poblacion.drop(94008)

df_poblacion.loc[6217] = df_poblacion.loc[6218]
df_poblacion = df_poblacion.drop(6218)

rechequeo_nulls = df_poblacion[df_poblacion.isnull().all(axis=1)]

# Consultas sobre los modelos

# Cantidad de EE y poblacion por departamento
df_poblacion_reset = df_poblacion.reset_index()

cols_poblacion = ['Maternal', 'Inicial', 'Primario', 'Secundario', 
                  'Jovenes', 'Adultos', 'Tercera edad']

for col in cols_poblacion:
    df_poblacion_reset[col] = pd.to_numeric(df_poblacion_reset[col], errors='coerce')

entera_ee = dd.query(""" SELECT df_ee.*, df_niv.nivel
                         FROM df_ee
                         INNER JOIN df_niv
                         ON df_ee.CUE_anexo = df_niv.CUE_anexo
                         ;""").df()

reporte1 = """
SELECT 
    d.provincia, d.departamento,
    COUNT(CASE WHEN ee.nivel = 'inicial' THEN 1 END) AS Iniciales,
    SUM(DISTINCT p.Inicial) AS "Poblacion Inicial",
    COUNT(CASE WHEN ee.nivel = 'primario' THEN 1 END) AS Primarios,
    SUM(DISTINCT p.Primario) AS "Poblacion Primaria",
    COUNT(CASE WHEN ee.nivel = 'secundario' THEN 1 END) AS Secundarios,
    SUM(DISTINCT p.Secundario) AS "Poblacion Secundaria",
FROM entera_ee AS ee
JOIN df_departamento AS d ON ee.id_departamento = d.ID 
JOIN df_poblacion_reset AS p ON ee.id_departamento = p.id_departamento
GROUP BY d.provincia, d.departamento
ORDER BY d.provincia ASC, Primarios DESC;
"""
Resultado1 = dd.query(reporte1).df()

# Cantidad de empleados por departamento
entera_ep = dd.query("""SELECT df_ep.*, df_emp.genero, df_emp.empleados
                        FROM df_ep
                        INNER JOIN df_emp
                        ON df_ep.id_produccion = df_emp.id_produccion
                        ;""").df()

reporte2 = """
SELECT 
    d.provincia, d.departamento,
    SUM(ep.empleados) AS "Cantidad total de empleados en 2022"
FROM entera_ep AS ep
JOIN df_departamento AS d ON ep.id_departamento = d.ID 
GROUP BY d.provincia, d.departamento
ORDER BY d.provincia ASC, "Cantidad total de empleados en 2022" DESC;
"""
Resultado2 = dd.query(reporte2).df()

# Cantidad de empresas exportadoras que emplean mujeres, cantidad de EE y poblacion total por departamento
reporte3 = """
SELECT
    d.provincia, d.departamento,
    SUM(CASE WHEN ep.genero = 'Mujeres' THEN ep.empresas_exportadoras ELSE 0 END) AS Cant_Expo_Mujeres,
    COUNT(DISTINCT ee.CUE_anexo) AS Cant_EE,
    MAX(p.Maternal + p.Inicial + p.Primario + p.Secundario + p.Jovenes + p.Adultos + p."Tercera edad") AS Poblacion_Total
FROM df_departamento AS d
LEFT JOIN entera_ep AS ep ON d.ID = ep.id_departamento 
LEFT JOIN entera_ee AS ee ON d.ID = ee.id_departamento 
LEFT JOIN df_poblacion_reset AS p ON d.ID = p.id_departamento
GROUP BY d.provincia, d.departamento
ORDER BY Cant_EE DESC, Cant_Expo_Mujeres DESC, d.provincia ASC, d.departamento ASC;
"""
Resultado3 = dd.query(reporte3).df()

# Por cada provincia con mas empleados que el promedio, muestro sus departamentos, el identificador de la actividad con mas puestos y cantidad de empleados en el rubro
reporte4 = """
SELECT
    d.provincia, d.departamento,
    CASE WHEN LENGTH(CAST(ep.clae6 AS TEXT)) = 5 THEN LEFT('0' || CAST(ep.clae6 AS TEXT), 3) 
    ELSE LEFT(CAST(ep.clae6  AS TEXT),3) END AS clae3,
    SUM(ep.empleados) AS Cant_empleos
FROM df_departamento AS d
JOIN entera_ep AS ep ON d.ID = ep.id_departamento
GROUP BY d.provincia, d.departamento, ep.clae6
HAVING
    (
        SELECT SUM(ep2.empleados)
        FROM entera_ep AS ep2
        JOIN df_departamento AS d2 ON d2.ID = ep2.id_departamento
        WHERE d2.departamento = d.departamento
          AND d2.provincia = d.provincia
    ) >
    (
        SELECT AVG(sub.total_empleos)
        FROM (
            SELECT d3.provincia, d3.departamento, SUM(ep3.empleados) AS total_empleos
            FROM df_departamento AS d3
            JOIN entera_ep AS ep3 ON d3.ID = ep3.id_departamento
            GROUP BY d3.provincia, d3.departamento
        ) AS sub
        WHERE sub.provincia = d.provincia
    )
    AND SUM(ep.empleados) = (
        SELECT MAX(sub2.total_empleos)
        FROM (
            SELECT ep4.clae6, SUM(ep4.empleados) AS total_empleos
            FROM entera_ep AS ep4
            JOIN df_departamento AS d4 ON d4.ID = ep4.id_departamento
            WHERE d4.departamento = d.departamento
              AND d4.provincia = d.provincia
            GROUP BY ep4.clae6
        ) AS sub2
    )
ORDER BY d.provincia ASC, Cant_empleos DESC;
"""

Resultado4 = dd.sql(reporte4).df()

# Conecto la consulta anterior con los identificadores para visualizar los detalles de la actividad
interpretacion1 = dd.query(""" SELECT Resultado4.*, ep2.clae6_desc
                               FROM Resultado4
                               LEFT OUTER JOIN ep2
                               ON ep2.clae6//1000 = Resultado4.clae3
                               ;""").df() 
                               
# Graficos

# Cantidad de empleados por provincia
cantEMP = """SELECT DISTINCT df_departamento.provincia,
                    SUM(entera_ep.empleados) AS cant_empleados
                    FROM entera_ep
                    JOIN df_departamento
                    ON df_departamento.id = entera_ep.id_departamento
                    GROUP BY df_departamento.provincia
                    ORDER BY cant_empleados DESC;
                    """
            
empleados_por_prov = dd.query(cantEMP).df()
empleados_por_prov.plot(x="provincia", y="cant_empleados", kind="bar", xlabel='',
                        title= "Cantidad de empleados por provincia en 2022", label='Empleados', color="orange")
plt.ticklabel_format(style='plain', axis='y')
plt.tight_layout()
plt.show()

# Cantidad de EE por departamento en función de la población, separando por nivel educativo y grupo etario 
plt.scatter(Resultado1["Poblacion Inicial"], Resultado1["Iniciales"], color="blue", label= "Iniciales (3-5 años)")
plt.scatter(Resultado1["Poblacion Primaria"], Resultado1["Primarios"], color="green", label= "Primarios (6-12 años)")
plt.scatter(Resultado1["Poblacion Secundaria"], Resultado1["Secundarios"], color="orange", label= "Secundarios (13-17 años)")


plt.title('Cantidad de EE por departamento según nivel y población', fontsize=11)
plt.xlabel("Población")
plt.ylabel("Cantidad de EE")
plt.legend()
plt.grid(True)
plt.xscale("log")
plt.yscale("log")
plt.tight_layout()
plt.show()

# Boxplot por cada provincia, de la cantidad de EE por cada departamento de la provincia ordenados por la mediana
Resultado3=Resultado3[['provincia','departamento','Cant_EE']]
mediana = """
    SELECT provincia,
           median(Cant_EE) AS mediana_Cant_EE
    FROM Resultado3
    GROUP BY provincia
    ORDER BY mediana_Cant_EE
"""
orden_mediana = dd.query(mediana).df()

plt.figure(figsize=(16,8))
sns.boxplot(
    data=Resultado3,
    x="provincia",
    y="Cant_EE",
    order=orden_mediana["provincia"],
    color="deeppink")


plt.xticks(rotation=90)
plt.title("Distribución de la cantidad de EE por provincia")
plt.xlabel("Provincia")
plt.ylabel("Cantidad de Establecimientos Educativos por Departamento (EE)")
plt.tight_layout()
plt.yscale('log')
plt.ylabel("Cantidad de EE por Departamento (escala log)")
plt.show()

# Relación entre la cantidad de empleados cada mil habitantes y de EE cada mil habitantes por departamento.
consulta="""SELECT Resultado2.departamento,Resultado2.provincia,
     1000.0 * Resultado2."Cantidad total de empleados en 2022" /
        (Resultado1."Poblacion Inicial" + Resultado1."Poblacion Primaria" + Resultado1."Poblacion Secundaria") AS empleados_por_mil,
    1000.0 * (Resultado1.Iniciales + Resultado1.Primarios + Resultado1.Secundarios) /
        (Resultado1."Poblacion Inicial" + Resultado1."Poblacion Primaria" + Resultado1."Poblacion Secundaria") AS ee_por_mil
FROM Resultado2
JOIN Resultado1 
    ON Resultado2.provincia = Resultado1.provincia AND Resultado2.departamento = Resultado1.departamento
WHERE (Resultado1."Poblacion Inicial" + Resultado1."Poblacion Primaria" + Resultado1."Poblacion Secundaria") > 0"""

relacion = dd.query(consulta).df( )
plt.figure(figsize=(10,6))
plt.scatter(relacion["empleados_por_mil"], relacion["ee_por_mil"], alpha=0.6)
plt.title("Relación entre empleados y EE por cada mil habitantes (2022)")
plt.xlabel("Empleados cada mil habitantes")
plt.ylabel("EE cada mil habitantes")
plt.grid(True)
plt.xscale('log')
plt.show()


# Las 5 actividades con mayor y menor proporción de empleadas mujeres, incluyendo el promedio
promedio = dd.query(""" SELECT SUM(CASE WHEN genero = 'Mujeres' THEN empleados ELSE 0 END) / SUM (empleados) AS proporcion_mujeres
                        FROM df_emp
                        ;""").df()

promedio = float(promedio.iloc[0,0])

propmenor = dd.query(""" SELECT clae6, SUM(CASE WHEN genero = 'Mujeres' THEN empleados ELSE 0 END) / SUM (empleados) AS proporcion_mujeres
                         FROM entera_ep
                         GROUP BY clae6
                         ORDER BY proporcion_mujeres ASC, clae6 ASC
                         LIMIT 5
                         ;""").df()
                         
propmayor = dd.query(""" SELECT clae6, SUM(CASE WHEN genero = 'Mujeres' THEN empleados ELSE 0 END) / SUM (empleados) AS proporcion_mujeres
                         FROM entera_ep
                         GROUP BY clae6
                         ORDER BY proporcion_mujeres DESC, clae6 ASC
                         LIMIT 5
                         ;""").df()

grafico = pd.concat([propmenor, propmayor])

grafico = dd.query(""" SELECT *
                       FROM grafico
                       ORDER BY proporcion_mujeres
                       ;""").df()
                      
grafico.plot(kind = 'barh', x= 'clae6', y='proporcion_mujeres', title='Proporcion de empleadas mujeres por cada actividad', ylabel= 'Actividad', label='', color='hotpink')
plt.axvline(x=promedio, color='blue', linestyle='--', linewidth=2, label='Promedio')
plt.xticks([0.0, 0.2, 0.4, 0.6, 0.8], ["0%","20%", "40%", "60%", "80%"])
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()

# Conecto con los identificadores para visualizar los detalles de la actividad
interpretacion2 = dd.query(""" SELECT grafico.*, ep2.clae6_desc
                               FROM grafico
                               LEFT OUTER JOIN ep2
                               ON grafico.clae6 = ep2.clae6
                               ORDER BY proporcion_mujeres
                              ;""").df() 
