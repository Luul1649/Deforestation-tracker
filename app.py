import streamlit as st
import sys
import types

# ----------------------------------------------------
# PYTHON 3.14 COMPATIBILITY PATCH FOR GEEMAP (MOCKING)
# ----------------------------------------------------
# Dynamically intercepting the missing 'pkg_resources' tool before geemap initializes
try:
    import pkg_resources
except ModuleNotFoundError:
    # Creating a virtual empty module space to satisfy older geemap background configurations
    mock_pkg = types.ModuleType("pkg_resources")
    mock_pkg.declare_namespace = lambda name: None
    mock_pkg.get_distribution = lambda name: types.SimpleNamespace(version="0.1.0")
    sys.modules["pkg_resources"] = mock_pkg

# Now these can be imported safely without triggering a server crash
import ee
import geemap
import json

st.set_page_config(page_title="Satellite Deforestation Tracker", layout="wide")

st.title("🌲 Space-Borne Canopy Index & Deforestation Tracker")
st.markdown("Monitoring canopy disruption in the **Mau Forest Complex, Kenya** via automated Sentinel-2 satellite pipelines.")

# ----------------------------------------------------
# SECURE SECRETS HANDSHAKE FOR GITHUB DEPLOYMENT
# ----------------------------------------------------
@st.cache_resource
def initialize_ee_cloud():
    try:
        # Fetch credentials securely from Streamlit Cloud Secrets Manager
        gee_credentials = st.secrets["GEE_SECRET_KEY"]
        credentials_dict = json.loads(gee_credentials)
        
        # Authenticate the server via service account token
        ee_creds = ee.ServiceAccountCredentials(credentials_dict['client_email'], key_data=gee_credentials)
        ee.Initialize(ee_creds, project=credentials_dict['project_id'])
    except Exception as e:
        st.error(f"Authentication Failed. Ensure Streamlit Secrets are configured. Error: {e}")

initialize_ee_cloud()

# ----------------------------------------------------
# DATA PIPELINE & INTERACTIVE WIDGET MAP RENDER
# ----------------------------------------------------
@st.cache_data
def process_satellite_layers():
    poi = ee.Geometry.Point([35.7000, -0.6000])
    sentinel_collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                           .filterBounds(poi)
                           .filterDate('2025-01-01', '2025-12-31')
                           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)))
    base_image = sentinel_collection.median()
    ndvi = base_image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return base_image, ndvi

base_image, ndvi = process_satellite_layers()

# Initialize the interactive canvas widget
Map = geemap.Map(center=[-0.6000, 35.7000], zoom=11)
ndvi_palette = ['#e50000', '#ffea00', '#006400']

Map.addLayer(base_image, {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}, 'True Color View (Human Eye)')
Map.addLayer(ndvi, {'min': 0, 'max': 1, 'palette': ndvi_palette}, 'NDVI Mask View (AI Vegetation Index)')

# Render directly onto the web interface screen
Map.to_streamlit(height=600)

