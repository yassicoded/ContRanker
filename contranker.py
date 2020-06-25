import pandas as pd
from preprocess import aggregate_permit_data
from predict import train_model
from predict import predict_adu_performance_non_ADU_builders


# reding all permits public data
all_permits = pd.read_csv('./public_data/Building_Permits.csv')

#reading general license details
license_details = pd.read_excel('./public_data/LA_licenses.xlsx')
license_details = license_details.rename(columns = {'LicenseNumber':'License #'})

#labeling and feature engineering
license_full_data = aggregate_permit_data(all_permits)

#finding contractors with ADU historical data
adu_builders = license_full_data[license_full_data['ADU_proj_count'] >= 1]
adu_builders = adu_builders.merge(license_details, on = 'License #', how = 'left')


#saving adu-builder data
adu_builders.to_csv('./outputs/adu_builders.csv')
adu_builders = pd.read_csv('./outputs/adu_builders.csv')

# finding non-adu contractors to predict on
non_adu_builders = license_full_data[(license_full_data['ADU_proj_count'] < 2) & (license_full_data['non_ADU_proj_count'] >= 2)]

# training the model on adu-contractors
trained_model = train_model(adu_builders)

# predicting for non-ADU contractors
ranked_non_adu_builders = predict_adu_performance_non_ADU_builders(trained_model,non_adu_builders)
ranked_non_adu_builders = ranked_non_adu_builders.merge(license_details, on = 'License #', how = 'left')

ranked_non_adu_builders.to_csv('./outputs/ranked_contractors.csv')
