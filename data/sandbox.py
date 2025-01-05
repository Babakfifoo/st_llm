# %%
import pandas as pd
import geopandas as gpd
# %%
data = gpd.read_parquet("./HMA_buildings_prepared.parquet")
# %%
data = data[['id', 'class', 'bbox', 'subtype', 'height', 'num_floors', 'has_parts',
       'AREA', 'PERIMETER', 'RI', 'CNV', 'REC', 'ERI', 'WIDTH',
       'HEIGHT', 'subtype_clean', 'est_subtype_clean', 'commercial', 'other',
       'residential', 'education', 'outbuilding', 'medical', 'est_num_floors',
       'floor_area', 'geometry']]
# %%
data.loc[data.est_num_floors.isna(), "est_num_floors"] = False
# %%
data.est_num_floors = data.est_num_floors.astype(int)
# %%
data.to_parquet("./HMA_buildings_prepared.parquet")
# %%
