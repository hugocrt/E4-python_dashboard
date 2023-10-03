from processor.data_processor import DataFrameHolder

# On traite nos données de prix des carburants des voitures en france
df_holder = DataFrameHolder('Fuel_price_FR.csv')
df_holder.process_data()
df_holder.save_processed_dataframe()
