import pandas as pd
from bz_details import scrape_bz_details
from bz_reviews import scrape_bz_pages


def get_permit_insp_features(permits):
    """
    scraped inspection data (for ADUs, since some of them were missing in public inspections dataset) + inspections
    public dataset merged to gather inspections data.
    :param permits: all permits
    :return:permits with all inspection data
    """
    inspection_requests = pd.DataFrame()
    for i in range(0, 5):
        inspection_requests = inspection_requests.append(
            pd.read_csv('./scraped_data/inspection_requests' + str(i) + '.csv'))

    inspection_requests = inspection_requests.rename(columns={'status': 'Inspection Result', 'date': 'Inspection Date','section':'Inspection Type'})

    inspections = pd.read_csv('./public_data/Inspections.csv')

    inspections['permit_ID'] = inspections['PERMIT'].str.replace(' ', '-')

    inspection_requests = inspection_requests[['Inspection Date', 'Inspection Result', 'permit_ID', 'Inspection Type']]
    inspections = inspections[['Inspection Date', 'Inspection Result', 'permit_ID', 'Inspection Type']]

    inspections = inspections.append(inspection_requests)
    inspections['Inspection Date'] = pd.to_datetime(inspections['Inspection Date'])
    all_first_insp = inspections.sort_values(['permit_ID', 'Inspection Date']).drop_duplicates(['permit_ID'])
    all_numb_insp = inspections[inspections['Inspection Result'] == 'Approved'].groupby(['permit_ID'])[
        'Inspection Type'].size().reset_index(name='insp_count')

    permits = permits.merge(all_first_insp, how='inner')
    permits = permits.merge(all_numb_insp, how='inner')

    return permits



def get_permit_adu_tag(permits):
    """
    Finding is each permit is ADU or not (scraping suspicious ADU's for full decriptions)
    checking full descriptions & permit codes & regex & keywords
    :param permits: all permits
    :return: a dataframe of permit_ID with a binary column is_ADU showing if permit is ADU or not
    """
    permits = permits[(permits['Status'] == 'Permit Finaled') | (permits['Status'] == 'CofO Issued')
                              | (permits['Status'] == 'CofC Issued') | (permits['Status'] == 'CofO on progress')
                              | (permits['Status'] == 'OK for Cofc')]

    permits['Work Description'] = permits['Work Description'].str.lower()
    permits['Permit Sub-Type'].unique()
    permits = permits[permits['Permit Sub-Type'] == '1 or 2 Family Dwelling']

    # Keywords and Regex filters
    adus_raw = permits[((permits['Work Description'].str.contains('|'.join(["accessory dwelling",
                                                                                    "adu", "a.d.u", "accessory",
                                                                                    "dwlling", "dewlling", "convert"]),
                                                                          na=False))
                            | permits['Work Description'].str.match('ab\s*[0-9]')
                            | permits['Work Description'].str.match('sb\s*[0-9]'))
                           & ~(permits['Work Description'].str.contains('fire')
                               | permits['Work Description'].str.contains('sprinkler')
                               | permits['Work Description'].str.contains('installation'))]

    # uncomment for scraping ADU permit full descriprions & inspections.
    '''
    permit_codes = adus_raw['PCIS Permit #'].unique()
    
    for i in range(0,5):
        permit_codes = permit_codes['PCIS Permit #'].unique()[i*5000:(i+1)*5000,]
        inspection_requests, permit_statuses = full_scraper(permit_codes)
        inspection_requests.to_csv('inspection_requests'+str(i)+'.csv')
        full_descriptions.to_csv('full_descriptions_'+str(i)+'.csv')

    '''

    full_descriptions = pd.DataFrame()


    for i in range(0, 5):
        full_descriptions = full_descriptions.append(pd.read_csv("~/full_descriptions" + str(i) + '.csv'))

    full_descriptions['Work Description'] = full_descriptions['full_description'].str.lower()


    permits['permit_ID'] = permits['PCIS Permit #']
    full_adu = full_descriptions.merge(permits, on='permit_ID', how='inner')
    full_adu['issue_date'] = pd.to_datetime(full_adu['Issue Date'])
    full_adu = full_adu[full_adu['issue_date'] > pd.to_datetime('2017-01-01')]

    # Permit code filters
    full_adu = full_adu[
        ((full_adu['permit_ID'].str.slice(start=0, stop=2) == '17')
         | (full_adu['permit_ID'].str.slice(start=0, stop=2) == '18')
         | (full_adu['permit_ID'].str.slice(start=0, stop=2) == '19')
         | (full_adu['permit_ID'].str.slice(start=0, stop=2) == '20'))
        &
        ((full_adu['permit_ID'].str.slice(start=2, stop=5) == '010')
         | (full_adu['permit_ID'].str.slice(start=2, stop=5) == '014')
         | (full_adu['permit_ID'].str.slice(start=2, stop=5) == '016')

         &
         (full_adu['permit_ID'].str.slice(start=8, stop=11) == '000')
         )]
    # Eliminating those with unrelated keywords
    full_adu = full_adu[~(full_adu['Work Description_x'].str.contains("supplemental"))]
    full_adu = full_adu[~(full_adu['Work Description_x'].str.contains("sprinkler"))]
    full_adu = full_adu[~(full_adu['Work Description_x'].str.contains("fire"))]
    permits['is_ADU'] = permits['permit_ID'].isin(full_adu['permit_ID'])
    return permits

def get_permit_performance(permits):
    """
    finding number of days spent on each inspection az a measure of project's performance
    :param permits: all permits
    :return: df of permit_ID and norm_construction_time
    """

    permits['Status Date'] = pd.to_datetime(permits['Status Date'])

    permits['construction_time'] = (permits['Status Date'] - permits['Inspection Date']).dt.days

    permits['insp_count'] = permits['insp_count'].fillna(1)
    permits = permits[
        (permits['insp_count'] > 3) & (permits['construction_time'] > 30) & (permits['construction_time'] < 1000)]


    permits['norm_construction_time'] = permits['construction_time'] / permits['insp_count']
    return permits


def get_ADU_builder_performance(adu_permits):
    """
    for each adu-builder, finding labeling it's ADU performance score by calculating weighted average of
    contractor's performance in previous ADU projects (more weight on recent projects)

    :param adu_permits: adu filtered projects
    :return: df of License # and ADU_performance_score
    """
    adu_permits['t0'] = '2017-01-01'
    adu_permits['t0'] = pd.to_datetime(adu_permits['t0'])

    adu_permits['Issue Date'] = pd.to_datetime(adu_permits['Issue Date'])

    adu_permits['freshness_score'] = (adu_permits['Issue Date'] - adu_permits['t0']).dt.days

    adu_permits['freshness_score'] = adu_permits['freshness_score'] / adu_permits['freshness_score'].max()

    adu_permits['proj_final_score'] = adu_permits['freshness_score'] * adu_permits['norm_construction_time']

    license_scores = adu_permits.groupby(['License #']).agg(
        {'freshness_score': 'sum', 'proj_final_score': 'sum'}).reset_index()

    license_scores['ADU_performance_score'] = license_scores['proj_final_score'] / license_scores['freshness_score']
    return license_scores[['License #','ADU_performance_score']]


def get_avg_construction_time(non_adu_permits):
    """
    Average construction time of each contractor (unnormalized by complexity)
    :param non_adu_permits: all non-adu permits
    :return: df of License # and avg_construction_time
    """
    avg_time = non_adu_permits.groupby(['License #'])['construction_time'].mean().reset_index(name='avg_construction_time')
    return avg_time



def get_weighted_avg_time_per_insp(non_adu_permits):
    """
    finding non-ADU performance score by getting weighted avg of previous projects' performance
    :param non_adu_permits:
    :return: a df of License # and w_avg_time_per_insp
    """


    non_adu_permits['t0'] = '2013-01-01'
    non_adu_permits['t0'] = pd.to_datetime(non_adu_permits['t0'])

    non_adu_permits['Issue Date'] = pd.to_datetime(non_adu_permits['Issue Date'])

    non_adu_permits['freshness_score'] = (non_adu_permits['Issue Date'] - non_adu_permits['t0']).dt.days

    non_adu_permits['freshness_score'] = non_adu_permits['freshness_score'] / non_adu_permits['freshness_score'].max()

    non_adu_permits['proj_final_score'] = non_adu_permits['freshness_score'] * non_adu_permits['norm_construction_time']

    license_scores = non_adu_permits.groupby(['License #']).agg(
        {'freshness_score': 'sum', 'proj_final_score': 'sum'}).reset_index()

    license_scores['w_avg_time_per_insp'] = license_scores['proj_final_score'] / license_scores['freshness_score']
    print(license_scores)
    return license_scores[['License #','w_avg_time_per_insp']]

def get_year_count(permits):
    """
        yearly number of contractor's projects
        :param permits: permit data
        :return: a df of License # and year_proj_count
    """

    year = '2020'
    year_end = '2021'

    permits['Issue Date'] = pd.to_datetime(permits['Issue Date'])

    data_year = permits[(permits['Issue Date'] > pd.to_datetime(year + '.01.01')) &
                            (permits['Issue Date'] < pd.to_datetime(year_end + '.01.01'))].groupby(['License #'])['permit_ID'].size().reset_index(name=year + '_proj_count')


    for i in range(1, 8):
        year = 2020 - i
        year_end = str(year + 1)
        year = str(year)
        new_year = permits[(permits['Issue Date'] > pd.to_datetime(year + '.01.01')) &
                                   (permits['Issue Date'] < pd.to_datetime(year_end + '.01.01'))].groupby(['License #'])['permit_ID'].size().reset_index(name=year + '_proj_count')
        data_year = data_year.merge(new_year, on='License #', how='outer')
    return data_year

def get_year_performance(permits):
    """
    yearly avg performance of contractor's projects
    :param permits: permit data
    :return: a df of License # and year_performance
    """
    year = '2020'
    year_end = '2021'

    permits['Issue Date'] = pd.to_datetime(permits['Issue Date'])

    data_year = permits[(permits['Issue Date'] > pd.to_datetime(year + '.01.01')) &
                            (permits['Issue Date'] < pd.to_datetime(year_end + '.01.01'))].groupby(['License #'])[
        'norm_construction_time'].mean().reset_index(name=year + '_performance')

    for i in range(1, 8):
        year = 2020 - i
        year_end = str(year + 1)
        year = str(year)
        new_year = permits[(permits['Issue Date'] > pd.to_datetime(year + '.01.01')) &
                               (permits['Issue Date'] < pd.to_datetime(year_end + '.01.01'))].groupby(
            ['License #'])['norm_construction_time'].mean().reset_index(name=year + '_performance')
        data_year = data_year.merge(new_year, on='License #', how='outer')
    return data_year

def get_year_avg_numb_insp(permits):
    """
    avg number of inspections a contractor has had in each year
    :param permits:
    :return: a df of License # and year_avg_numb_insp
    """
    year = '2020'
    year_end = '2021'

    permits['Issue Date'] = pd.to_datetime(permits['Issue Date'])

    data_year = permits[(permits['Issue Date'] > pd.to_datetime(year + '.01.01')) &
                            (permits['Issue Date'] < pd.to_datetime(year_end + '.01.01'))].groupby(['License #'])[
        'insp_count'].mean().reset_index(name=year + '_avg_numb_insp')

    for i in range(1, 8):
        year = 2020 - i
        year_end = str(year + 1)
        year = str(year)
        new_year = permits[(permits['Issue Date'] > pd.to_datetime(year + '.01.01')) &
                               (permits['Issue Date'] < pd.to_datetime(year_end + '.01.01'))].groupby(
            ['License #'])['insp_count'].mean().reset_index(name=year + '_avg_numb_insp')
        data_year = data_year.merge(new_year, on='License #', how='outer')
    return data_year



def get_building_type_count(permits):
    """
    Only for related permit types, count number of completed projects a contractors has built in each type
    :param permits: permits data
    :return: a df of License # and Permit Type_count
    """
    bldgnew_type = permits[permits['Permit Type']=='Bldg-New'].groupby(['License #'])['permit_ID'].size().reset_index(name='Bldg-New_count')
    bldgaltr_type = permits[permits['Permit Type']=='Bldg-Alter/Repair'].groupby(['License #'])['permit_ID'].size().reset_index(name='Bldg-Alter/Repair_count')
    bldgadd_type = permits[permits['Permit Type']=='Bldg-Addition'].groupby(['License #'])['permit_ID'].size().reset_index(name='Bldg-Addition_count')
    data_type = bldgnew_type.merge(bldgaltr_type, how = 'outer')
    data_type = data_type.merge(bldgadd_type, how='outer')
    return data_type

def get_experience(permits):
    """
    experience of each contarctor(days) considering days passed sonce first completed project
    :param permits: permits data
    :return: a df of License # and experience
    """
    permits['IssueDate'] = pd.to_datetime(permits['Issue Date'])

    experience = permits.sort_values(['License #', 'IssueDate']).drop_duplicates(['License #'])[['License #', 'IssueDate']]
    experience['experience'] = (pd.to_datetime('2020-07-01') - experience['IssueDate']).dt.days
    return experience[['experience','License #']]

def get_proj_count(permits,col_name):
    """
    finding # of projects in permits
    :param permits:
    :param col_name: name of column in returned df
    :return: a df of License # and col_name showing number of projects in permits
    """
    proj_count = permits.groupby(['License #'])['permit_ID'].size().reset_index(name=col_name)
    return proj_count

def get_avg_insp(permits,col_name):
    """
    :param permits: permit data
    :param col_name: name of the aggregated column in returned data
    :return: a df of license # and avg # of inspections for each project by contractor
    """
    avg_insp = permits.groupby(['License #'])['insp_count'].mean().reset_index(name=col_name)
    return avg_insp


def get_avg_time_per_insp(permits,col_name):
    """
    :param permits: permits data
    :param col_name: name of the aggregated column in returned data
    :return: a df of license # and avg time for each inspection by contractor
    """
    avg_time_insp = permits.groupby(['License #'])['norm_construction_time'].mean().reset_index(name=col_name)
    return avg_time_insp

def get_avg_eval(permits,col_name):
    """
    :param permits: permits data
    :param col_name: name of the aggregated column in returned data
    :return: a df of license # and avg evaluation of projects for that license #
    """
    avg_eval = permits.groupby(['License #'])['Valuation'].mean().reset_index(name=col_name)
    return avg_eval

def get_buildzoom_data():
    """
    Scrape Buildzoom.com LA results pages and contractor's details data
    :return: a df of 'License #', 'numb_revs', 'rate', 'Home Additions',
                                     'New Constructions', 'Garage Constructions', '< $5k',
                                     '$5k-$20k', '$20k-$50k', '$50k-$100k', '$250k-$500k'
    """
    #uncomment for new scraping
    #scrape_bz_pages()
    #scrape_bz_details()
    bz_general_data = pd.read_csv('./Scraped_data/reviews.csv')

    bz_detail_data = pd.DataFrame()
    for i in range(0, 13):
        bz_detail_data = bz_detail_data.append(
            pd.read_csv('./Scraped_data/details' + str(i) + '.csv'), ignore_index=True)

    bz_detail_data = bz_detail_data.drop_duplicates(['License #'])

    bz_detail_data = bz_detail_data[['License #', 'numb_revs', 'rate', 'Home Additions',
                                     'New Constructions', 'Garage Constructions', '< $5k',
                                     '$5k-$20k', '$20k-$50k', '$50k-$100k', '$250k-$500k']]

    bz_detail_data = bz_detail_data.fillna(0)
    for column in bz_detail_data.columns:
        try:
            print(column)
            bz_detail_data[column] = bz_detail_data[column].str.replace(' projects', '')

            bz_detail_data[column] = bz_detail_data[column].str.replace(' project', '')

            bz_detail_data = bz_detail_data.fillna(0)
            bz_detail_data[column] = bz_detail_data[column].astype(int)
        except AttributeError:
            print("no")
    return bz_detail_data


def aggregate_permit_data(all_permits):
    """

    :param all_permits: permits data
    :return: aggregated DF of all ADU and non-ADU features of contractors
    """

    all_permits = all_permits[all_permits['License #'] > 0]
    all_permits = all_permits[(all_permits['Permit Type']=='Bldg-Alter/Repair')
                                                 | (all_permits['Permit Type']=='Bldg-Addition')
                                                 | (all_permits['Permit Type']=='Bldg-New')]
    print(all_permits.shape)
    all_permits = get_permit_adu_tag(all_permits)
    print(all_permits.shape)
    all_permits = get_permit_insp_features(all_permits)
    print(all_permits.shape)
    all_permits = get_permit_performance(all_permits)
    all_permits = all_permits[(all_permits['norm_construction_time']>=8) & (all_permits['norm_construction_time']<=50)]
    non_ADU_permits = all_permits[all_permits['is_ADU']==False]
    ADU_permits = all_permits[all_permits['is_ADU']==True]

    license_data = pd.DataFrame()
    license_data['License #'] = all_permits['License #'].unique()
    license_data['is_ADU_builder'] = license_data['License #'].isin(
        all_permits[all_permits['is_ADU'] == True]['License #'])


    license_building_type_count = get_building_type_count(all_permits)
    license_year_count = get_year_count(all_permits)
    license_year_performance = get_year_performance(all_permits)
    license_year_insp = get_year_avg_numb_insp(all_permits)
    license_experience = get_experience(all_permits)
    license_non_ADU_count = get_proj_count(non_ADU_permits,'non_ADU_proj_count')
    license_ADU_count = get_proj_count(ADU_permits,'ADU_proj_count')
    license_non_ADU_avg_numb_insp = get_avg_insp(non_ADU_permits,'non_ADU_avg_insp')
    license_non_ADU_avg_cons_time = get_avg_construction_time(non_ADU_permits)
    license_non_ADU_w_avg_insp = get_weighted_avg_time_per_insp (non_ADU_permits)
    license_non_ADU_avg_time_per_insp = get_avg_time_per_insp(non_ADU_permits,'non_ADU_avg_time_per_insp')
    license_ADU_performance = get_ADU_builder_performance(ADU_permits)
    license_non_ADU_avg_eval= get_avg_eval(non_ADU_permits,'non_ADU_avg_eval')
    license_bz_data = get_buildzoom_data()

    license_data = license_data.merge(license_ADU_performance, how = 'left')
    license_data = license_data.merge(license_building_type_count,how = 'left')
    license_data = license_data.merge(license_year_count,how = 'left')
    license_data = license_data.merge(license_year_performance,how = 'left')
    license_data = license_data.merge(license_year_insp,how = 'left')
    license_data = license_data.merge(license_bz_data,how = 'left')

    license_data = license_data.merge(license_experience,how = 'inner')
    license_data = license_data.merge(license_non_ADU_count,how = 'inner')
    license_data = license_data.merge(license_non_ADU_avg_numb_insp,how = 'inner')
    license_data = license_data.merge(license_non_ADU_w_avg_insp, how = 'inner')
    license_data = license_data.merge(license_non_ADU_avg_cons_time, how = 'inner')
    license_data = license_data.merge(license_non_ADU_avg_time_per_insp,how = 'inner')
    license_data = license_data.merge(license_ADU_count, how = 'outer')
    license_data = license_data.merge(license_non_ADU_avg_eval, how = 'inner')


    adu_data = license_data[license_data['is_ADU_builder']==True].merge(ADU_permits, how = 'inner')
    adu_data.to_csv('./outputs/adu_builder_permit_data.csv')


    license_data = license_data.fillna(0)

    return license_data


