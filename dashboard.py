import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Firebase configuration
collection_name = "filmsDashboard"
credenciales = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key": st.secrets["private_key"].replace("\\n", "\n"),
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"]
}

#cred = credentials.Certificate("./secret/credentials.json")
cred = credentials.Certificate(credenciales)

# Load dataset
df_to_import = pd.read_csv("./dataset/movies.csv")

# Function definitions
def is_firebase_initialized():
    """Checks if a Firebase app has been initialized.

    Returns:
        True if a Firebase app has been initialized, False otherwise.
    """
    try:
        # Attempt to access the default app. If it exists, it's initialized.
        firebase_admin.get_app()
        return True
    except ValueError:
        return False
    except Exception as e:
        # Handle other potential exceptions
        print(f"Error checking Firebase initialization: {e}")
        return False


def import_to_firebase(df, collection_name):
    try:
        collection_list = [collection.id for collection in db.collections()]
        if collection_name not in collection_list:
            for index, row in df.iterrows():
                # Convert each row to a dictionary
                row_dict = row.to_dict()
                # Create a new document in the collection
                db.collection(collection_name).add(row_dict)
            print(
                f'DataFrame importado correctamente a la colección "{collection_name}"'
            )
        else:
            print(
                f'La colección "{collection_name}" ya existe. No se importó el DataFrame.'
            )

    except Exception as e:
        print(f"Error al importar DataFrame: {e}")


def read_database_to_dataframe(collection_name) -> pd.DataFrame:
    """Lee todos los documentos de una colección de Firestore y los devuelve como un DataFrame de Pandas."""
    try:
        docs = db.collection(collection_name).stream()
        data = []
        for doc in docs:
            data.append(doc.to_dict())
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"Error al leer datos de Firestore: {e}")
        return None


# Initialize Firebase
if not is_firebase_initialized():
    try:
        firebase_admin.initialize_app(cred)
        print("Firebase app initialized.")
    except Exception as e:
        print(f"Error initializing Firebase app: {e}")
else:
    print("Firebase app already initialized.")

db = firestore.client()

# Import data to Firebase
import_to_firebase(df_to_import, collection_name)

# Read data from Firebase
df_films = read_database_to_dataframe(collection_name)

if df_films is not None:
    print("DataFrame base cargado correctamente.")
    print(df_films.head())
else:
    print("No se pudo cargar el DataFrame base.")

# Streamlit app
st.title("Netflix app")

# Initialize variables for storing results
filter_results = df_films.copy()  # Initialize with all data
search_results = None

# Sidebar for filters
with st.sidebar:
    st.header("Filtros")

    # Checkbox to show all films
    show_all = st.checkbox("Mostrar todos los filmes", value=True)

    # Text input to search films
    film_title = st.text_input("Titulo del filme:")

    # Button to search films
    if st.button("Buscar filmes"):
        if film_title:
            search_results = df_films[
                df_films["name"].str.contains(film_title, case=False)
            ]
        else:
            search_results = df_films.copy()

    # Selector to select director
    directors = df_films["director"].unique().tolist()
    selected_director = st.selectbox("Seleccionar Director", ["Todos"] + directors)

    # Button to filter director
    if st.button("Filtrar director"):
        if selected_director != "Todos":
            filter_results = df_films[df_films["director"] == selected_director]
        else:
            filter_results = df_films.copy()

    # Section to add new film (outside sidebar)
    st.subheader("Nuevo filme")
    new_name = st.text_input("Name:")
    new_company = st.selectbox("Company", df_films["company"].unique().tolist())
    new_director = st.text_input("Director:")

# Apply filters
final_results = filter_results.copy()
if search_results is not None:
    final_results = final_results.merge(search_results, how="inner")

# Show results on the main page
if show_all:
    st.write(f"Lista de filmes")
    st.write(f"Mostrando: {len(final_results)} films de {len(df_films)}")
    st.write(final_results)
